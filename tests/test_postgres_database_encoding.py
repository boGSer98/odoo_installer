import shlex
import subprocess
import unittest

from odoo_installer.models import InstallerConfig
from odoo_installer.pipeline import build_steps


class PostgresDatabaseEncodingTests(unittest.TestCase):
    def _postgres_command(self) -> str:
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
        step = next(step for step in build_steps(config) if step.name == "PostgreSQL einrichten")
        return "\n".join(step.commands)

    def test_database_is_created_with_utf8_encoding_and_locale(self) -> None:
        rendered = self._postgres_command()

        self.assertIn("--encoding=UTF8", rendered)
        self.assertIn("--locale=C.UTF-8", rendered)
        self.assertIn("--template=template0", rendered)
        self.assertIn("pg_encoding_to_char(encoding)", rendered)

    def test_uninitialized_non_utf8_database_is_recreated(self) -> None:
        rendered = self._postgres_command()

        self.assertIn("ir_module_module", rendered)
        self.assertIn("dropdb odoo", rendered)
        self.assertIn("Datenbank odoo ist noch nicht initialisiert", rendered)
        self.assertIn("bereits als Odoo-Datenbank initialisiert, hat aber kein UTF8-Encoding", rendered)

    def test_generated_postgres_script_has_valid_bash_syntax(self) -> None:
        command = self._postgres_command()
        script = shlex.split(command)[-1]

        result = subprocess.run(["bash", "-n"], input=script, text=True, capture_output=True)

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
