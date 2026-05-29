from __future__ import annotations

from dataclasses import dataclass, field
import shlex
import sys

from .models import InstallerConfig
from .state import ProgressState
from .ssh import SSHExecutor
from .ui import ui


@dataclass(slots=True)
class Step:
    name: str
    commands: list[str]
    rollback_commands: list[str] = field(default_factory=list)


class InstallStatusBar:
    def __init__(self, total: int, width: int = 30) -> None:
        self.total = max(total, 1)
        self.width = width
        self.interactive = sys.stdout.isatty()
        self._last_len = 0
        self._active = False

    def _line(self, completed: int, step_name: str, note: str = "") -> str:
        ratio = min(max(completed / self.total, 0.0), 1.0)
        filled = int(round(ratio * self.width))
        bar = "#" * filled + "-" * (self.width - filled)
        percent = int(round(ratio * 100))
        suffix = f" | {step_name}"
        if note:
            suffix += f" ({note})"
        return f"[{bar}] {percent:3d}% ({completed}/{self.total}){suffix}"

    def render(self, completed: int, step_name: str, note: str = "") -> None:
        line = self._line(completed, step_name, note=note)
        if self.interactive:
            padded = line.ljust(self._last_len)
            sys.stdout.write("\r" + padded)
            sys.stdout.flush()
            self._last_len = max(self._last_len, len(line))
            self._active = True
            return
        print(line)

    def pause(self) -> None:
        if self.interactive and self._active:
            sys.stdout.write("\n")
            sys.stdout.flush()
            self._active = False
            self._last_len = 0

    def finish(self) -> None:
        if self.interactive and self._active:
            sys.stdout.write("\n")
            sys.stdout.flush()
            self._active = False
            self._last_len = 0


def _sudo(command: str, use_sudo: bool) -> str:
    if not use_sudo:
        return command
    return f"sudo {command}"


def _as_user(command: str, user: str, use_sudo: bool) -> str:
    quoted_user = shlex.quote(user)
    quoted_command = shlex.quote(command)
    if use_sudo:
        return f"sudo -u {quoted_user} bash -lc {quoted_command}"
    return f"runuser -u {quoted_user} -- bash -lc {quoted_command}"


def _write_file_command(path: str, content: str, use_sudo: bool) -> str:
    quoted_path = shlex.quote(path)
    if use_sudo:
        return f"cat <<'EOF' | sudo tee {quoted_path} >/dev/null\n{content}\nEOF"
    return f"cat <<'EOF' > {quoted_path}\n{content}\nEOF"


def _write_owned_file_command(path: str, content: str, owner: str, mode: str, use_sudo: bool) -> str:
    write_command = _write_file_command(path, content, use_sudo)
    quoted_path = shlex.quote(path)
    quoted_owner = shlex.quote(owner)
    quoted_mode = shlex.quote(mode)
    return "set -e\n" + "\n".join(
        [
            write_command,
            _sudo(f"chown {quoted_owner}:{quoted_owner} {quoted_path}", use_sudo),
            _sudo(f"chmod {quoted_mode} {quoted_path}", use_sudo),
        ]
    )


def _sql_literal(value: str) -> str:
    return value.replace("'", "''")


def _print_result(stdout: str, stderr: str) -> None:
    if stdout.strip():
        print(stdout.rstrip())
    if stderr.strip():
        print(stderr.rstrip())


def _run_rollback(executor: SSHExecutor, steps: list[Step], touched_steps: set[int]) -> list[str]:
    if not touched_steps:
        return []

    print("\nRollback gestartet (best effort).")
    errors: list[str] = []

    for step_index in sorted(touched_steps, reverse=True):
        step = steps[step_index]
        if not step.rollback_commands:
            print(f"[ROLLBACK] Kein automatischer Rollback fuer '{step.name}'.")
            continue

        print(f"[ROLLBACK] {step.name}")
        for command in step.rollback_commands:
            result = executor.run(command)
            _print_result(result.stdout, result.stderr)
            if not result.ok:
                errors.append(
                    f"Rollback fehlgeschlagen in Schritt '{step.name}' "
                    f"(Exit-Code {result.returncode}): {command}"
                )

    return errors


def run_preflight(executor: SSHExecutor, config: InstallerConfig) -> list[str]:
    warnings: list[str] = []

    connectivity = executor.run("echo connected")
    if not connectivity.ok or "connected" not in connectivity.stdout:
        raise RuntimeError(f"SSH-Verbindung fehlgeschlagen:\n{connectivity.stderr.strip()}")

    os_check = executor.run("source /etc/os-release && printf '%s:%s' \"$ID\" \"$VERSION_ID\"")
    if not os_check.ok:
        raise RuntimeError(f"OS-Pruefung fehlgeschlagen:\n{os_check.stderr.strip()}")
    os_value = os_check.stdout.strip().lower()
    if not config.dry_run and os_value != "ubuntu:24.04":
        raise RuntimeError(
            f"Zielsystem ist nicht Ubuntu 24.04 (erkannt: {os_value}). "
            "Der Installer ist aktuell nur dafuer ausgelegt."
        )

    if config.use_sudo and not config.dry_run:
        sudo_check = executor.run("sudo -n true")
        if not sudo_check.ok:
            raise RuntimeError(
                "Sudo ohne interaktive Passworteingabe ist nicht verfuegbar. "
                "Bitte passwortloses sudo konfigurieren oder als root verbinden."
            )

    mem_check = executor.run("free -m | awk '/Mem:/ {print $2}'")
    if mem_check.ok and mem_check.stdout.strip().isdigit():
        memory_mb = int(mem_check.stdout.strip())
        if memory_mb < 4096:
            warnings.append(f"Niedriger RAM erkannt ({memory_mb} MB). Empfehlung: mindestens 4096 MB.")

    disk_check = executor.run("df -Pm / | awk 'NR==2 {print $4}'")
    if disk_check.ok and disk_check.stdout.strip().isdigit():
        free_mb = int(disk_check.stdout.strip())
        if free_mb < 10240:
            warnings.append(
                f"Wenig freier Speicher erkannt ({free_mb} MB). Empfehlung: mindestens 10240 MB frei."
            )

    port_check = executor.run(
        "ss -ltn | awk '{print $4}' | "
        f"grep -E ':({config.http_port}|{config.longpolling_port})$' | wc -l || true"
    )
    if port_check.ok and port_check.stdout.strip().isdigit():
        used = int(port_check.stdout.strip())
        if used > 0:
            warnings.append(
                f"Mindestens einer der Zielports {config.http_port}/{config.longpolling_port} ist bereits belegt."
            )

    return warnings


def build_steps(config: InstallerConfig) -> list[Step]:
    install_dir = config.install_dir.rstrip("/")
    data_dir = (config.data_dir or f"{install_dir}/data").rstrip("/")
    src_dir = f"{install_dir}/src/odoo"
    venv_dir = f"{install_dir}/venv"
    conf_path = f"/etc/{config.service_name}.conf"
    service_path = f"/etc/systemd/system/{config.service_name}.service"
    log_dir = f"{install_dir}/logs"

    packages = [
        "git",
        "curl",
        "ca-certificates",
        "build-essential",
        "python3",
        "python3-dev",
        "python3-venv",
        "python3-pip",
        "libxml2-dev",
        "libxslt1-dev",
        "libldap2-dev",
        "libsasl2-dev",
        "libjpeg-dev",
        "zlib1g-dev",
        "libpq-dev",
        "libffi-dev",
        "libssl-dev",
        "libxmlsec1-dev",
        "libyaml-dev",
        "postgresql",
        "postgresql-client",
        "wkhtmltopdf",
    ]

    db_user = shlex.quote(config.db_user)
    db_name = shlex.quote(config.db_name)
    db_user_sql = _sql_literal(config.db_user)
    db_name_sql = _sql_literal(config.db_name)
    db_password_sql = _sql_literal(config.db_password)

    commands_install = [
        _sudo("apt-get update", config.use_sudo),
        _sudo(
            "DEBIAN_FRONTEND=noninteractive apt-get install -y " + " ".join(packages),
            config.use_sudo,
        ),
        _sudo(
            f"id -u {shlex.quote(config.odoo_system_user)} >/dev/null 2>&1 || "
            f"useradd --system --create-home --home-dir {shlex.quote(install_dir)} "
            f"--shell /bin/bash {shlex.quote(config.odoo_system_user)}",
            config.use_sudo,
        ),
        _sudo(
            f"mkdir -p {shlex.quote(install_dir)} {shlex.quote(log_dir)} "
            f"{shlex.quote(install_dir)}/custom-addons {shlex.quote(install_dir)}/src "
            f"{shlex.quote(data_dir)}",
            config.use_sudo,
        ),
        _sudo(
            f"chown -R {shlex.quote(config.odoo_system_user)}:{shlex.quote(config.odoo_system_user)} "
            f"{shlex.quote(install_dir)}",
            config.use_sudo,
        ),
    ]

    commands_postgres = [
        _as_user(
            f"psql -tc \"SELECT 1 FROM pg_roles WHERE rolname='{db_user_sql}'\" | grep -q 1 || "
            f"createuser --createdb --no-createrole --no-superuser {db_user}",
            "postgres",
            config.use_sudo,
        ),
        _as_user(
            f"psql -c \"ALTER USER {config.db_user} WITH PASSWORD '{db_password_sql}'\"",
            "postgres",
            config.use_sudo,
        ),
        _as_user(
            f"psql -tc \"SELECT 1 FROM pg_database WHERE datname='{db_name_sql}'\" | grep -q 1 || "
            f"createdb -O {db_user} {db_name}",
            "postgres",
            config.use_sudo,
        ),
    ]

    commands_odoo = [
        _as_user(
            f"if [ ! -d {shlex.quote(src_dir)}/.git ]; then "
            f"git clone --depth 1 --branch {shlex.quote(config.odoo_version)} "
            f"https://github.com/odoo/odoo.git {shlex.quote(src_dir)}; "
            "else "
            f"cd {shlex.quote(src_dir)} && git fetch --depth 1 origin {shlex.quote(config.odoo_version)} "
            f"&& git checkout {shlex.quote(config.odoo_version)}; fi",
            config.odoo_system_user,
            config.use_sudo,
        ),
        _as_user(
            f"python3 -m venv {shlex.quote(venv_dir)}",
            config.odoo_system_user,
            config.use_sudo,
        ),
        _as_user(
            f"{shlex.quote(venv_dir)}/bin/pip install --upgrade pip wheel",
            config.odoo_system_user,
            config.use_sudo,
        ),
        _as_user(
            f"{shlex.quote(venv_dir)}/bin/pip install -r {shlex.quote(src_dir)}/requirements.txt",
            config.odoo_system_user,
            config.use_sudo,
        ),
    ]

    config_file = """[options]
admin_passwd = {admin_password}
db_host = False
db_port = False
db_user = {db_user}
db_password = {db_password}
db_name = {db_name}
addons_path = {src_dir}/odoo/addons,{src_dir}/addons,{install_dir}/custom-addons
logfile = {log_dir}/odoo.log
data_dir = {data_dir}
proxy_mode = {proxy_mode}
xmlrpc_port = {http_port}
longpolling_port = {longpolling_port}
""".format(
        admin_password=config.admin_password,
        db_user=config.db_user,
        db_password=config.db_password,
        db_name=config.db_name,
        src_dir=src_dir,
        install_dir=install_dir,
        log_dir=log_dir,
        data_dir=data_dir,
        proxy_mode="True" if config.enable_nginx else "False",
        http_port=config.http_port,
        longpolling_port=config.longpolling_port,
    )

    service_file = """[Unit]
Description=Odoo Service ({service_name})
After=network.target postgresql.service

[Service]
Type=simple
User={odoo_user}
Group={odoo_user}
ExecStart={venv_dir}/bin/python3 {src_dir}/odoo-bin -c {conf_path}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
""".format(
        service_name=config.service_name,
        odoo_user=config.odoo_system_user,
        venv_dir=venv_dir,
        src_dir=src_dir,
        conf_path=conf_path,
    )

    init_db_script = """set -u
if psql -d {db_name} -Atc \"SELECT to_regclass('public.ir_module_module')\" | grep -qx ir_module_module; then
    echo 'Odoo-Datenbank ist bereits initialisiert.'
else
    echo 'Odoo-Datenbank wird initialisiert (-i base).'
    if [ ! -x {python_bin} ]; then
        echo 'Python der Odoo-venv nicht gefunden oder nicht ausfuehrbar: {python_bin}' >&2
        exit 1
    fi
    if [ ! -f {odoo_bin} ]; then
        echo 'odoo-bin nicht gefunden: {odoo_bin}' >&2
        exit 1
    fi
    if [ ! -f {base_manifest} ]; then
        echo 'Odoo-Basismodul nicht gefunden: {base_manifest}' >&2
        echo 'Bitte pruefe Odoo-Quellcode und addons_path.' >&2
        exit 1
    fi
    cd {src_dir}
    {python_bin} {odoo_bin} -c {conf_path} -d {db_name} -i base --without-demo=all --stop-after-init
    rc=$?
    if [ $rc -ne 0 ]; then
        echo 'Odoo-Datenbankinitialisierung fehlgeschlagen. Letzte Logzeilen:' >&2
        if [ -f {log_file} ]; then
            tail -n 120 {log_file} >&2
        else
            echo 'Logdatei noch nicht vorhanden: {log_file}' >&2
        fi
        exit $rc
    fi
fi""".format(
        db_name=shlex.quote(config.db_name),
        src_dir=shlex.quote(src_dir),
        python_bin=shlex.quote(f"{venv_dir}/bin/python3"),
        odoo_bin=shlex.quote(f"{src_dir}/odoo-bin"),
        conf_path=shlex.quote(conf_path),
        log_file=shlex.quote(f"{log_dir}/odoo.log"),
        base_manifest=shlex.quote(f"{src_dir}/odoo/addons/base/__manifest__.py"),
    )
    init_db_command = _as_user(init_db_script, config.odoo_system_user, config.use_sudo)

    commands_service = [
        _write_file_command(conf_path, config_file.rstrip(), config.use_sudo),
        _sudo(
            f"chown {shlex.quote(config.odoo_system_user)}:{shlex.quote(config.odoo_system_user)} {shlex.quote(conf_path)}",
            config.use_sudo,
        ),
        init_db_command,
        _write_file_command(service_path, service_file.rstrip(), config.use_sudo),
        _sudo("systemctl daemon-reload", config.use_sudo),
        _sudo(f"systemctl enable {shlex.quote(config.service_name)}", config.use_sudo),
        _sudo(f"systemctl restart {shlex.quote(config.service_name)}", config.use_sudo),
        _sudo(f"systemctl --no-pager --full status {shlex.quote(config.service_name)}", config.use_sudo),
    ]

    commands_service_rollback = [
        _sudo(f"systemctl disable --now {shlex.quote(config.service_name)} || true", config.use_sudo),
        _sudo(f"rm -f {shlex.quote(service_path)}", config.use_sudo),
        _sudo("systemctl daemon-reload", config.use_sudo),
        _sudo(f"rm -f {shlex.quote(conf_path)}", config.use_sudo),
    ]

    steps = [
        Step(name="System vorbereiten", commands=commands_install),
    ]

    if config.enable_support_ssh:
        support_user = shlex.quote(config.support_ssh_user)
        support_full_name = shlex.quote(config.support_ssh_full_name)
        support_home = f"/home/{config.support_ssh_user}"
        authorized_keys = f"{support_home}/.ssh/authorized_keys"
        sudoers_path = f"/etc/sudoers.d/90-{config.support_ssh_user}"
        sudoers_content = f"{config.support_ssh_user} ALL=(ALL) NOPASSWD:ALL"
        ssh_commands = [
            _sudo("DEBIAN_FRONTEND=noninteractive apt-get install -y openssh-server", config.use_sudo),
            _sudo("systemctl enable --now ssh", config.use_sudo),
            _sudo(
                f"id -u {support_user} >/dev/null 2>&1 || "
                f"useradd --create-home --shell /bin/bash --comment {support_full_name} {support_user}",
                config.use_sudo,
            ),
            _sudo(f"usermod --comment {support_full_name} {support_user}", config.use_sudo),
            _sudo(f"passwd -l {support_user} || true", config.use_sudo),
            _sudo(f"usermod -aG sudo {support_user}", config.use_sudo),
            _sudo(
                f"install -d -m 700 -o {support_user} -g {support_user} {shlex.quote(support_home)}/.ssh",
                config.use_sudo,
            ),
            _write_owned_file_command(
                authorized_keys,
                config.support_ssh_public_key.strip(),
                config.support_ssh_user,
                "600",
                config.use_sudo,
            ),
            _write_file_command(sudoers_path, sudoers_content, config.use_sudo),
            _sudo(f"chmod 440 {shlex.quote(sudoers_path)}", config.use_sudo),
            _sudo(f"visudo -cf {shlex.quote(sudoers_path)}", config.use_sudo),
        ]
        ssh_rollback = [
            _sudo(f"rm -f {shlex.quote(sudoers_path)}", config.use_sudo),
            _sudo(f"userdel -r {support_user} || true", config.use_sudo),
        ]
        steps.append(
            Step(
                name="AHD Support-SSH einrichten",
                commands=ssh_commands,
                rollback_commands=ssh_rollback,
            )
        )

    steps.extend(
        [
            Step(name="PostgreSQL einrichten", commands=commands_postgres),
            Step(name="Odoo Quellcode und Python Umgebung", commands=commands_odoo),
            Step(
                name="Odoo konfigurieren und Service starten",
                commands=commands_service,
                rollback_commands=commands_service_rollback,
            ),
        ]
    )

    if config.enable_nginx:
        domain = config.domain or "_"
        nginx_conf = f"/etc/nginx/sites-available/{config.service_name}"
        nginx_file = """upstream odoo_backend {{
    server 127.0.0.1:{http_port};
}}

server {{
    listen 80;
    server_name {domain};

    proxy_read_timeout 720s;
    proxy_connect_timeout 720s;
    proxy_send_timeout 720s;

    location / {{
        proxy_pass http://odoo_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
""".format(http_port=config.http_port, domain=domain)

        nginx_commands = [
            _sudo("DEBIAN_FRONTEND=noninteractive apt-get install -y nginx", config.use_sudo),
            _write_file_command(nginx_conf, nginx_file.rstrip(), config.use_sudo),
            _sudo(
                f"ln -sf {shlex.quote(nginx_conf)} /etc/nginx/sites-enabled/{shlex.quote(config.service_name)}",
                config.use_sudo,
            ),
            _sudo("nginx -t", config.use_sudo),
            _sudo("systemctl restart nginx", config.use_sudo),
        ]
        nginx_rollback = [
            _sudo(f"rm -f /etc/nginx/sites-enabled/{shlex.quote(config.service_name)}", config.use_sudo),
            _sudo(f"rm -f {shlex.quote(nginx_conf)}", config.use_sudo),
            _sudo("nginx -t || true", config.use_sudo),
            _sudo("systemctl restart nginx || true", config.use_sudo),
        ]
        steps.append(
            Step(
                name="Nginx Reverse Proxy",
                commands=nginx_commands,
                rollback_commands=nginx_rollback,
            )
        )

    if config.enable_certbot and config.domain:
        certbot_commands = [
            _sudo(
                "DEBIAN_FRONTEND=noninteractive apt-get install -y certbot python3-certbot-nginx",
                config.use_sudo,
            ),
            _sudo(
                f"certbot --nginx -d {shlex.quote(config.domain)} --non-interactive --agree-tos "
                "--register-unsafely-without-email --redirect",
                config.use_sudo,
            ),
        ]
        steps.append(Step(name="TLS via Let's Encrypt", commands=certbot_commands))

    if config.enable_ufw:
        ufw_commands = [
            _sudo("DEBIAN_FRONTEND=noninteractive apt-get install -y ufw", config.use_sudo),
            _sudo(f"ufw allow {config.ssh_port}/tcp", config.use_sudo),
            _sudo("ufw allow OpenSSH", config.use_sudo),
            _sudo("ufw allow 80/tcp", config.use_sudo),
            _sudo("ufw allow 443/tcp", config.use_sudo),
            _sudo("ufw --force enable", config.use_sudo),
            _sudo("ufw status", config.use_sudo),
        ]
        steps.append(Step(name="Firewall Basisregeln", commands=ufw_commands))

    return steps


def run_installation(
    executor: SSHExecutor,
    config: InstallerConfig,
    progress: ProgressState | None = None,
    rollback_on_fail: bool = False,
) -> None:
    warnings = run_preflight(executor, config)
    if warnings:
        ui.warning("Preflight-Warnungen:")
        for warning in warnings:
            print(f"- {warning}")

    steps = build_steps(config)
    total_commands = sum(len(step.commands) for step in steps)
    status_bar = InstallStatusBar(total=total_commands)
    completed_commands = 0
    touched_steps: set[int] = set()

    ui.section("Installation starten", "🚀")
    ui.info(f"{len(steps)} Schritte, {total_commands} Kommandos")
    status_bar.render(completed_commands, "Start")

    for step_index, step in enumerate(steps):
        status_bar.pause()
        ui.section(step.name, f"{step_index + 1}")
        status_bar.render(completed_commands, step.name)
        for command_index, command in enumerate(step.commands):
            if progress and progress.should_skip(step_index, command_index):
                completed_commands += 1
                ui.info(f"Resume: Schritt {step_index + 1}, Kommando {command_index + 1} uebersprungen")
                status_bar.render(completed_commands, step.name, note="resume")
                continue

            touched_steps.add(step_index)
            ui.command_status(step.name, command_index + 1, len(step.commands))
            result = executor.run(command)
            status_bar.pause()
            _print_result(result.stdout, result.stderr)
            if not result.ok:
                message = (
                    "Fehler bei Installationsschritt "
                    f"'{step.name}'\nKommando: {command}\nExit-Code: {result.returncode}"
                )

                if rollback_on_fail:
                    rollback_errors = _run_rollback(executor, steps, touched_steps)
                    if progress:
                        progress.clear()
                    message += (
                        "\nRollback ausgefuehrt (best effort). "
                        "Der lokale Resume-State wurde aus Sicherheitsgruenden geloescht."
                    )
                    if rollback_errors:
                        message += "\nRollback-Fehler:\n" + "\n".join(f"- {entry}" for entry in rollback_errors)

                status_bar.finish()
                raise RuntimeError(message)

            completed_commands += 1
            status_bar.render(completed_commands, step.name)
            if progress:
                progress.mark_done(step_index, command_index)

    status_bar.finish()
