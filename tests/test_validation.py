import unittest

from odoo_installer.models import InstallerConfig


def _base_config() -> InstallerConfig:
    return InstallerConfig(
        host="example.org",
        ssh_user="root",
        db_password="secret-db",
        admin_password="secret-admin",
    )


class ValidationTests(unittest.TestCase):
    def test_valid_config_has_no_errors(self) -> None:
        config = _base_config()
        self.assertEqual(config.validate(), [])

    def test_certbot_requires_domain(self) -> None:
        config = _base_config()
        config.enable_nginx = True
        config.enable_certbot = True
        config.domain = None
        errors = config.validate()
        self.assertIn("Certbot benoetigt eine Domain.", errors)

    def test_ports_must_differ(self) -> None:
        config = _base_config()
        config.http_port = 8069
        config.longpolling_port = 8069
        errors = config.validate()
        self.assertIn("HTTP-Port und Longpolling-Port muessen unterschiedlich sein.", errors)

    def test_safe_dict_masks_passwords(self) -> None:
        config = _base_config()
        config.ssh_password = "linux-login-secret"
        safe = config.safe_dict()
        self.assertEqual(safe["ssh_password"], "***")
        self.assertEqual(safe["db_password"], "***")
        self.assertEqual(safe["admin_password"], "***")

    def test_invalid_host_key_mode_is_rejected(self) -> None:
        config = _base_config()
        config.ssh_host_key_mode = "unknown"
        errors = config.validate()
        self.assertIn("ssh_host_key_mode muss 'strict', 'accept-new' oder 'insecure' sein.", errors)

    def test_local_mode_does_not_require_ssh_target(self) -> None:
        config = InstallerConfig(
            host="",
            ssh_user="",
            execution_mode="local",
            db_password="secret-db",
            admin_password="secret-admin",
        )

        self.assertEqual(config.validate(), [])

    def test_invalid_execution_mode_is_rejected(self) -> None:
        config = _base_config()
        config.execution_mode = "invalid"

        self.assertIn("execution_mode muss 'local' oder 'ssh' sein.", config.validate())


if __name__ == "__main__":
    unittest.main()
