import unittest

from odoo_installer.models import InstallerConfig
from odoo_installer.pipeline import build_steps


class CustomAddonsTests(unittest.TestCase):
    def test_additional_custom_addon_paths_are_created_and_added_to_odoo_config(self) -> None:
        config = InstallerConfig(
            host="localhost",
            ssh_user="root",
            execution_mode="local",
            db_password="secret-db",
            admin_password="secret-admin",
            custom_addons_paths=["/srv/odoo/customer-addons", "/srv/odoo/partner-addons"],
            dry_run=True,
        )

        steps = build_steps(config)
        rendered = "\n".join(command for step in steps for command in step.commands)

        self.assertIn("/srv/odoo/customer-addons", rendered)
        self.assertIn("/srv/odoo/partner-addons", rendered)
        self.assertIn(
            "addons_path = /opt/odoo/src/odoo/odoo/addons,/opt/odoo/src/odoo/addons,/opt/odoo/custom-addons,/srv/odoo/customer-addons,/srv/odoo/partner-addons",
            rendered,
        )

    def test_custom_addon_repositories_are_synced_as_odoo_user_and_added_to_addons_path(self) -> None:
        config = InstallerConfig(
            host="localhost",
            ssh_user="root",
            execution_mode="local",
            db_password="secret-db",
            admin_password="secret-admin",
            custom_addons_repositories=[
                {
                    "url": "https://github.com/example/customer-addons.git",
                    "branch": "19.0",
                    "target": "/opt/odoo/custom-addons/customer",
                }
            ],
            dry_run=True,
        )

        steps = build_steps(config)
        custom_step = next(step for step in steps if step.name == "Custom-Addons vorbereiten")
        rendered = "\n".join(custom_step.commands)
        all_commands = "\n".join(command for step in steps for command in step.commands)

        self.assertIn("git clone --branch 19.0 https://github.com/example/customer-addons.git /opt/odoo/custom-addons/customer", rendered)
        self.assertIn("git pull --ff-only origin 19.0", rendered)
        self.assertIn("sudo -u odoo bash -lc", rendered)
        self.assertIn("/opt/odoo/custom-addons/customer", all_commands)
        self.assertIn("addons_path =", all_commands)

    def test_custom_addon_requirements_are_optional_and_only_installed_when_enabled(self) -> None:
        config = InstallerConfig(
            host="localhost",
            ssh_user="root",
            execution_mode="local",
            db_password="secret-db",
            admin_password="secret-admin",
            custom_addons_repositories=[
                {
                    "url": "https://github.com/example/customer-addons.git",
                    "branch": "19.0",
                    "target": "/opt/odoo/custom-addons/customer",
                }
            ],
            custom_addons_install_python_requirements=True,
            dry_run=True,
        )

        steps = build_steps(config)
        custom_step = next(step for step in steps if step.name == "Custom-Addons vorbereiten")
        rendered = "\n".join(custom_step.commands)

        self.assertIn("/opt/odoo/venv/bin/pip install -r /opt/odoo/custom-addons/customer/requirements.txt", rendered)

    def test_custom_addon_paths_and_repository_targets_must_be_absolute(self) -> None:
        config = InstallerConfig(
            host="example.org",
            ssh_user="root",
            db_password="secret-db",
            admin_password="secret-admin",
            custom_addons_paths=["relative/path"],
            custom_addons_repositories=[
                {"url": "https://github.com/example/addons.git", "branch": "19.0", "target": "relative/target"}
            ],
        )

        errors = config.validate()

        self.assertIn("Custom-Addon-Pfad muss absolut sein: relative/path", errors)
        self.assertIn("Custom-Addon-Repository target muss absolut sein: relative/target", errors)


if __name__ == "__main__":
    unittest.main()
