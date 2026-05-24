from __future__ import annotations

from datetime import datetime, UTC
import shlex

from .models import InstallerConfig
from .ssh import SSHExecutor


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


def _print_result(stdout: str, stderr: str) -> None:
    if stdout.strip():
        print(stdout.rstrip())
    if stderr.strip():
        print(stderr.rstrip())


def _run_or_fail(executor: SSHExecutor, command: str, context: str) -> None:
    result = executor.run(command)
    _print_result(result.stdout, result.stderr)
    if not result.ok:
        raise RuntimeError(f"{context} fehlgeschlagen (Exit-Code {result.returncode}).\nKommando: {command}")


def _odoo_runtime_paths(config: InstallerConfig) -> tuple[str, str, str, str]:
    install_dir = config.install_dir.rstrip("/")
    src_dir = f"{install_dir}/src/odoo"
    venv_dir = f"{install_dir}/venv"
    conf_path = f"/etc/{config.service_name}.conf"
    data_dir = (config.data_dir or f"{install_dir}/data").rstrip("/")
    return src_dir, venv_dir, conf_path, data_dir


def _odoo_bin_command(config: InstallerConfig) -> str:
    src_dir, venv_dir, _, _ = _odoo_runtime_paths(config)
    return f"{shlex.quote(venv_dir)}/bin/python3 {shlex.quote(src_dir)}/odoo-bin"


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def _run_retention(
    executor: SSHExecutor,
    config: InstallerConfig,
    backup_root: str,
    dump_ext: str,
    keep_last: int,
) -> None:
    if keep_last <= 0:
        raise ValueError("keep_last muss groesser als 0 sein.")

    pattern = f"{config.db_name}_*.{dump_ext}"
    command = (
        f"find {shlex.quote(backup_root)} -maxdepth 1 -type f -name {shlex.quote(pattern)} "
        "-printf '%T@ %p\\0' | "
        "sort -z -nr | "
        f"awk -v RS='\\0' -v ORS='\\0' -v keep={keep_last} "
        "'NR > keep { sub(/^[^ ]+ /, \"\", $0); print }' | "
        "xargs -0 -r rm -f"
    )
    _run_or_fail(
        executor,
        _sudo(command, config.use_sudo),
        "Backup-Retention",
    )


def run_backup(
    executor: SSHExecutor,
    config: InstallerConfig,
    backup_dir: str | None = None,
    backup_name: str | None = None,
    dump_format: str = "zip",
    include_filestore: bool = True,
    keep_last: int | None = None,
) -> str:
    if dump_format not in {"zip", "dump"}:
        raise ValueError("dump_format muss 'zip' oder 'dump' sein.")

    install_dir = config.install_dir.rstrip("/")
    _, _, conf_path, _ = _odoo_runtime_paths(config)
    backup_root = (backup_dir or f"{install_dir}/backups").rstrip("/")
    ext = "zip" if dump_format == "zip" else "dump"
    filename = backup_name or f"{config.db_name}_{_timestamp()}.{ext}"
    if "." not in filename:
        filename = f"{filename}.{ext}"
    backup_path = f"{backup_root}/{filename}"

    print(f"Starte Backup nach: {backup_path}")
    _run_or_fail(executor, _sudo(f"mkdir -p {shlex.quote(backup_root)}", config.use_sudo), "Backup-Verzeichnis")
    _run_or_fail(
        executor,
        _sudo(
            f"chown -R {shlex.quote(config.odoo_system_user)}:{shlex.quote(config.odoo_system_user)} "
            f"{shlex.quote(backup_root)}",
            config.use_sudo,
        ),
        "Backup-Verzeichnis Besitzrechte",
    )

    options: list[str] = [f"--format={dump_format}", f"--config={shlex.quote(conf_path)}"]
    if dump_format == "zip" and not include_filestore:
        options.append("--no-filestore")

    command = (
        f"{_odoo_bin_command(config)} db dump {shlex.quote(config.db_name)} {shlex.quote(backup_path)} "
        + " ".join(options)
    )
    _run_or_fail(
        executor,
        _as_user(command, config.odoo_system_user, config.use_sudo),
        "Datenbank-Backup",
    )

    if keep_last is not None:
        print(f"Backup-Retention aktiv: neueste {keep_last} Dateien bleiben erhalten.")
        _run_retention(
            executor=executor,
            config=config,
            backup_root=backup_root,
            dump_ext=ext,
            keep_last=keep_last,
        )

    print("Backup erfolgreich erstellt.")
    return backup_path


def run_restore(
    executor: SSHExecutor,
    config: InstallerConfig,
    backup_path: str,
    force: bool = True,
    neutralize: bool = False,
    restart_service: bool = True,
) -> None:
    _, _, conf_path, _ = _odoo_runtime_paths(config)
    service_name = shlex.quote(config.service_name)

    print(f"Starte Restore aus: {backup_path}")
    _run_or_fail(
        executor,
        _sudo(f"test -f {shlex.quote(backup_path)}", config.use_sudo),
        "Pruefung Backup-Datei",
    )

    if restart_service:
        _run_or_fail(executor, _sudo(f"systemctl stop {service_name}", config.use_sudo), "Service stoppen")

    options = [f"--config={shlex.quote(conf_path)}"]
    if force:
        options.append("-f")
    if neutralize:
        options.append("--neutralize")

    command = (
        f"{_odoo_bin_command(config)} db load {shlex.quote(config.db_name)} {shlex.quote(backup_path)} "
        + " ".join(options)
    )
    _run_or_fail(
        executor,
        _as_user(command, config.odoo_system_user, config.use_sudo),
        "Datenbank-Restore",
    )

    if restart_service:
        _run_or_fail(executor, _sudo(f"systemctl restart {service_name}", config.use_sudo), "Service starten")
        _run_or_fail(
            executor,
            _sudo(f"systemctl --no-pager --full status {service_name}", config.use_sudo),
            "Service-Status",
        )

    print("Restore erfolgreich abgeschlossen.")
