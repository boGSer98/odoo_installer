import tempfile
from pathlib import Path
import unittest

from odoo_installer.models import InstallerConfig
from odoo_installer.pipeline import build_steps
from odoo_installer.support_ssh import generate_support_key


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

    def test_generate_support_key_creates_copyable_private_and_public_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            generated = generate_support_key("example.org", "itservice-ahd-support", base_dir=Path(tmp))

            self.assertTrue(generated.private_key_path.exists())
            self.assertTrue(generated.public_key_path.exists())
            self.assertIn("BEGIN OPENSSH PRIVATE KEY", generated.private_key)
            self.assertTrue(generated.public_key.startswith("ssh-ed25519 "))
            self.assertIn("itservice-ahd-support@example.org", generated.public_key)

    def test_support_ssh_step_sets_up_key_based_admin_user(self) -> None:
        config = InstallerConfig(
            host="example.org",
            ssh_user="root",
            db_password="secret-db",
            admin_password="secret-admin",
            dry_run=True,
            enable_support_ssh=True,
            support_ssh_user="itservice-ahd-support",
            support_ssh_full_name="IT-Service AHD",
            support_ssh_public_key=PUBLIC_KEY,
        )

        steps = build_steps(config)
        support_step = next(step for step in steps if step.name == "AHD Support-SSH einrichten")
        rendered = "\n".join(support_step.commands)

        self.assertIn("openssh-server", rendered)
        self.assertIn("systemctl enable --now ssh", rendered)
        self.assertIn("useradd --create-home --shell /bin/bash --comment 'IT-Service AHD' itservice-ahd-support", rendered)
        self.assertIn("usermod --comment 'IT-Service AHD' itservice-ahd-support", rendered)
        self.assertIn("/home/itservice-ahd-support/.ssh/authorized_keys", rendered)
        self.assertIn(PUBLIC_KEY, rendered)
        self.assertIn("NOPASSWD:ALL", rendered)
        self.assertIn("visudo -cf /etc/sudoers.d/90-itservice-ahd-support", rendered)


if __name__ == "__main__":
    unittest.main()
