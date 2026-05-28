import unittest

from odoo_installer.models import InstallerConfig
from odoo_installer.pipeline import build_steps


class PipelineDbInitTests(unittest.TestCase):
    def test_service_step_contains_database_initialization(self) -> None:
        config = InstallerConfig(
            db_password="secret-db",
            admin_password="secret-admin",
        )
        steps = build_steps(config)
        joined = "\n".join(command for step in steps for command in step.commands)
        self.assertIn("db init odoo", joined)
        self.assertIn("-i base --stop-after-init", joined)


if __name__ == "__main__":
    unittest.main()
