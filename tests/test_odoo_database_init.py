import unittest

from odoo_installer.models import InstallerConfig
from odoo_installer.pipeline import build_steps


class OdooDatabaseInitTests(unittest.TestCase):
    def test_service_step_initializes_empty_database_before_starting_service(self) -> None:
        config = InstallerConfig(
            host="localhost",
            ssh_user="root",
            execution_mode="local",
            db_name="odoo",
            db_user="odoo",
            db_password="secret-db",
            admin_password="secret-admin",
            dry_run=True,
        )

        steps = build_steps(config)
        service_step = next(step for step in steps if step.name == "Odoo konfigurieren und Service starten")
        rendered = "\n".join(service_step.commands)

        self.assertIn("SELECT to_regclass", rendered)
        self.assertIn("public.ir_module_module", rendered)
        self.assertIn("odoo-bin", rendered)
        self.assertIn("-i base", rendered)
        self.assertIn("--without-demo=all", rendered)
        self.assertIn("--stop-after-init", rendered)
        self.assertIn("cd /opt/odoo/src/odoo", rendered)
        self.assertIn("tail -n 120 /opt/odoo/logs/odoo.log", rendered)
        init_command = next(command for command in service_step.commands if "-i base" in command)
        self.assertNotIn(" || ", init_command)
        self.assertIn("Odoo-Basismodul nicht gefunden", init_command)

        init_index = next(i for i, command in enumerate(service_step.commands) if "-i base" in command)
        restart_index = next(i for i, command in enumerate(service_step.commands) if "systemctl restart" in command)
        self.assertLess(init_index, restart_index)

    def test_odoo_config_includes_core_and_standard_addons_paths(self) -> None:
        config = InstallerConfig(
            host="localhost",
            ssh_user="root",
            execution_mode="local",
            db_password="secret-db",
            admin_password="secret-admin",
            dry_run=True,
        )

        steps = build_steps(config)
        service_step = next(step for step in steps if step.name == "Odoo konfigurieren und Service starten")
        rendered = "\n".join(service_step.commands)

        self.assertIn(
            "addons_path = /opt/odoo/src/odoo/odoo/addons,/opt/odoo/src/odoo/addons,/opt/odoo/custom-addons",
            rendered,
        )


if __name__ == "__main__":
    unittest.main()
