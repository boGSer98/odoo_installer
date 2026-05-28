import json
from pathlib import Path
import tempfile
import unittest

from odoo_installer.cli import _load_config, _save_config
from odoo_installer.models import InstallerConfig


def _config(dry_run: bool) -> InstallerConfig:
    return InstallerConfig(
        db_password="secret-db",
        admin_password="secret-admin",
        dry_run=dry_run,
    )


class CliConfigTests(unittest.TestCase):
    def test_save_config_persists_dry_run_as_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "run-config.json"
            _save_config(path, _config(dry_run=True))
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("dry_run", payload)
            self.assertFalse(payload["dry_run"])

    def test_load_config_resets_dry_run_to_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "run-config.json"
            path.write_text(
                json.dumps(
                    {
                        "db_password": "secret-db",
                        "admin_password": "secret-admin",
                        "dry_run": True,
                    }
                ),
                encoding="utf-8",
            )
            config = _load_config(path)
            self.assertFalse(config.dry_run)


if __name__ == "__main__":
    unittest.main()
