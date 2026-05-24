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
        safe = config.safe_dict()
        self.assertEqual(safe["db_password"], "***")
        self.assertEqual(safe["admin_password"], "***")


if __name__ == "__main__":
    unittest.main()
