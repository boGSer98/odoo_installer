import unittest

from odoo_installer.models import InstallerConfig
from odoo_installer.pipeline import build_steps


PUBLIC_KEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKeyOnlyForUnitTests ahd@example"


class SupportSSHTests(unittest.TestCase):
    def test_support_ssh_requires_public_key(self) -> None:
        config = InstallerConfig(
            host="example.org",
            ssh_user="root",
            db_password="secret-db",
            admin_password="secret-admin",
            enable_support_ssh=True,
        )

        self.assertIn("Support-SSH benoetigt einen SSH Public Key.", config.validate())

    def test_support_ssh_step_sets_up_key_based_admin_user(self) -> None:
        config = InstallerConfig(
            host="example.org",
            ssh_user="root",
            db_password="secret-db",
            admin_password="secret-admin",
            dry_run=True,
            enable_support_ssh=True,
            support_ssh_user="ahd-support",
            support_ssh_public_key=PUBLIC_KEY,
        )

        steps = build_steps(config)
        support_step = next(step for step in steps if step.name == "AHD Support-SSH einrichten")
        rendered = "\n".join(support_step.commands)

        self.assertIn("openssh-server", rendered)
        self.assertIn("systemctl enable --now ssh", rendered)
        self.assertIn("useradd --create-home --shell /bin/bash ahd-support", rendered)
        self.assertIn("/home/ahd-support/.ssh/authorized_keys", rendered)
        self.assertIn(PUBLIC_KEY, rendered)
        self.assertIn("NOPASSWD:ALL", rendered)
        self.assertIn("visudo -cf /etc/sudoers.d/90-ahd-support", rendered)


if __name__ == "__main__":
    unittest.main()
