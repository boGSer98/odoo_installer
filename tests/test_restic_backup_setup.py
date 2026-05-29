import shlex
import subprocess
import unittest

from odoo_installer.models import InstallerConfig
from odoo_installer.pipeline import build_steps


class ResticBackupSetupTests(unittest.TestCase):
    def _config(self) -> InstallerConfig:
        return InstallerConfig(
            host="localhost",
            ssh_user="root",
            execution_mode="local",
            db_password="secret-db",
            admin_password="secret-admin",
            backup_enabled=True,
            backup_repository_url="sftp:backup@example.com:/backups/customer-odoo",
            backup_password_file="/etc/odoo-backup/restic-password",
            backup_schedule="0 2 * * *",
            backup_retention_daily=7,
            backup_retention_weekly=4,
            backup_retention_monthly=6,
            dry_run=True,
        )

    def test_restic_backup_step_installs_restic_and_writes_secure_files(self) -> None:
        steps = build_steps(self._config())
        backup_step = next(step for step in steps if step.name == "Restic Cloud-Backup einrichten")
        rendered = "\n".join(backup_step.commands)

        self.assertIn("apt-get install -y restic", rendered)
        self.assertIn("install -d -m 700 -o root -g root /etc/odoo-backup", rendered)
        self.assertIn("RESTIC_REPOSITORY=sftp:backup@example.com:/backups/customer-odoo", rendered)
        self.assertIn("RESTIC_PASSWORD_FILE=/etc/odoo-backup/restic-password", rendered)
        self.assertIn("chmod 600 /etc/odoo-backup/env", rendered)
        self.assertIn("test -f /etc/odoo-backup/restic-password", rendered)
        self.assertNotIn("secret-db", rendered)
        self.assertNotIn("secret-admin", rendered)

    def test_backup_script_dumps_database_and_backs_up_filestore_config_and_custom_addons(self) -> None:
        steps = build_steps(self._config())
        backup_step = next(step for step in steps if step.name == "Restic Cloud-Backup einrichten")
        rendered = "\n".join(backup_step.commands)

        self.assertIn("sudo -u postgres pg_dump -Fc -f", rendered)
        self.assertIn("/var/lib/odoo-backup/work", rendered)
        self.assertIn("restic backup", rendered)
        self.assertIn("/var/lib/odoo-backup/work/odoo.dump", rendered)
        self.assertIn("/opt/odoo/data/filestore/odoo", rendered)
        self.assertIn("/etc/odoo.conf", rendered)
        self.assertIn("/opt/odoo/custom-addons", rendered)
        self.assertIn("restic forget --prune --keep-daily 7 --keep-weekly 4 --keep-monthly 6", rendered)
        self.assertIn("LOCK_FILE=/var/lock/odoo-backup.lock", rendered)
        self.assertIn("flock -n 9", rendered)

    def test_cron_job_uses_configured_schedule_and_log_file(self) -> None:
        steps = build_steps(self._config())
        backup_step = next(step for step in steps if step.name == "Restic Cloud-Backup einrichten")
        rendered = "\n".join(backup_step.commands)

        self.assertIn("/etc/cron.d/odoo-backup", rendered)
        self.assertIn("0 2 * * * root /usr/local/sbin/odoo-backup >> /var/log/odoo-backup.log 2>&1", rendered)
        self.assertIn("chmod 644 /etc/cron.d/odoo-backup", rendered)

    def test_restic_backup_script_has_valid_bash_syntax(self) -> None:
        steps = build_steps(self._config())
        backup_step = next(step for step in steps if step.name == "Restic Cloud-Backup einrichten")
        script_command = next(command for command in backup_step.commands if "/usr/local/sbin/odoo-backup" in command)
        parts = shlex.split(script_command)
        script = parts[parts.index("tee") + 1] if "tee" in parts else ""
        # Extract heredoc body from command because the actual script is piped into tee.
        heredoc_start = script_command.index("\n") + 1
        heredoc_end = script_command.rindex("\nEOF")
        script_body = script_command[heredoc_start:heredoc_end]

        self.assertEqual(script, "/usr/local/sbin/odoo-backup")
        result = subprocess.run(["bash", "-n"], input=script_body, text=True, capture_output=True)

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_restic_backup_validation_requires_repository_password_file_and_schedule(self) -> None:
        config = InstallerConfig(
            host="example.org",
            ssh_user="root",
            db_password="secret-db",
            admin_password="secret-admin",
            backup_enabled=True,
            backup_repository_url="",
            backup_password_file="relative/password",
            backup_schedule="",
        )

        errors = config.validate()

        self.assertIn("Backup-Repository-URL darf nicht leer sein.", errors)
        self.assertIn("Backup-Passwortdatei muss ein absoluter Linux-Pfad sein.", errors)
        self.assertIn("Backup-Zeitplan darf nicht leer sein.", errors)


if __name__ == "__main__":
    unittest.main()
