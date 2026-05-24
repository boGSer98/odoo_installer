import unittest

from odoo_installer.backup_restore import run_backup, run_restore
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


if __name__ == "__main__":
    unittest.main()
