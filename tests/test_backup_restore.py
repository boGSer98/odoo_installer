import unittest

from odoo_installer.backup_restore import run_backup, run_restore, run_restic_check, run_restic_snapshots
from odoo_installer.models import InstallerConfig
from odoo_installer.ssh import CommandResult


class _FakeExecutor:
    def __init__(self, fail_on: set[str] | None = None) -> None:
        self.fail_on = fail_on or set()
        self.commands: list[str] = []

    def run(self, remote_command: str) -> CommandResult:
        self.commands.append(remote_command)
        if remote_command in self.fail_on:
            return CommandResult(command=[remote_command], returncode=1, stdout="", stderr="boom")
        return CommandResult(command=[remote_command], returncode=0, stdout="", stderr="")


def _config() -> InstallerConfig:
    return InstallerConfig(
        host="example.org",
        ssh_user="root",
        install_dir="/opt/odoo",
        service_name="odoo",
        data_dir="/opt/odoo/data",
        db_name="odoo",
        db_user="odoo",
        db_password="secret-db",
        admin_password="secret-admin",
        backup_enabled=True,
        backup_repository_url="sftp:backup@example.com:/backups/customer-odoo",
        backup_password_file="/etc/odoo-backup/restic-password",
    )


class BackupRestoreTests(unittest.TestCase):
    def test_backup_zip_without_filestore_uses_no_filestore_flag(self) -> None:
        executor = _FakeExecutor()
        backup_path = run_backup(
            executor=executor,
            config=_config(),
            backup_dir="/opt/odoo/backups",
            backup_name="nightly.zip",
            dump_format="zip",
            include_filestore=False,
        )

        self.assertEqual(backup_path, "/opt/odoo/backups/nightly.zip")
        joined = "\n".join(executor.commands)
        self.assertIn("mkdir -p /opt/odoo/backups", joined)
        self.assertIn("db dump odoo /opt/odoo/backups/nightly.zip", joined)
        self.assertIn("--format=zip", joined)
        self.assertIn("--no-filestore", joined)

    def test_backup_with_retention_executes_cleanup_command(self) -> None:
        executor = _FakeExecutor()
        run_backup(
            executor=executor,
            config=_config(),
            backup_dir="/opt/odoo/backups",
            backup_name="nightly.dump",
            dump_format="dump",
            include_filestore=True,
            keep_last=5,
        )

        joined = "\n".join(executor.commands)
        self.assertIn("db dump odoo /opt/odoo/backups/nightly.dump", joined)
        self.assertIn("find /opt/odoo/backups -maxdepth 1 -type f -name 'odoo_*.dump'", joined)
        self.assertIn("awk -v RS='\\0' -v ORS='\\0' -v keep=5", joined)

    def test_restore_with_restart_force_and_neutralize(self) -> None:
        executor = _FakeExecutor()
        run_restore(
            executor=executor,
            config=_config(),
            backup_path="/opt/odoo/backups/nightly.zip",
            force=True,
            neutralize=True,
            restart_service=True,
        )

        joined = "\n".join(executor.commands)
        self.assertIn("test -f /opt/odoo/backups/nightly.zip", joined)
        self.assertIn("systemctl stop odoo", joined)
        self.assertIn("db load odoo /opt/odoo/backups/nightly.zip", joined)
        self.assertIn("-f --neutralize", joined)
        self.assertIn("systemctl restart odoo", joined)
        self.assertIn("systemctl --no-pager --full status odoo", joined)

    def test_restic_snapshots_uses_env_file_without_printing_secrets(self) -> None:
        executor = _FakeExecutor()

        run_restic_snapshots(executor=executor, config=_config())

        joined = "\n".join(executor.commands)
        self.assertIn("set -a && . /etc/odoo-backup/env && set +a && restic snapshots", joined)
        self.assertNotIn("secret-db", joined)
        self.assertNotIn("secret-admin", joined)

    def test_restic_check_reads_data_subset_by_default(self) -> None:
        executor = _FakeExecutor()

        run_restic_check(executor=executor, config=_config())

        joined = "\n".join(executor.commands)
        self.assertIn("set -a && . /etc/odoo-backup/env && set +a && restic check --read-data-subset=5%", joined)

    def test_restic_operations_require_backup_enabled(self) -> None:
        executor = _FakeExecutor()
        config = _config()
        config.backup_enabled = False

        with self.assertRaisesRegex(ValueError, "backup_enabled"):
            run_restic_snapshots(executor=executor, config=config)


if __name__ == "__main__":
    unittest.main()
