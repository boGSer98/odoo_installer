import tempfile
from pathlib import Path
import unittest

from odoo_installer.models import InstallerConfig
from odoo_installer.state import ProgressState


def _config(host: str = "example.org") -> InstallerConfig:
    return InstallerConfig(
        host=host,
        ssh_user="root",
        db_password="secret-db",
        admin_password="secret-admin",
    )


class ProgressStateTests(unittest.TestCase):
    def test_marks_and_skips_completed_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            state_path = Path(tmp_dir) / "state.json"
            state = ProgressState(state_path, _config(), resume=False)
            self.assertFalse(state.should_skip(0, 0))
            state.mark_done(0, 0)
            self.assertTrue(state.should_skip(0, 0))

            resumed = ProgressState(state_path, _config(), resume=True)
            self.assertTrue(resumed.should_skip(0, 0))

    def test_resume_detects_config_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            state_path = Path(tmp_dir) / "state.json"
            ProgressState(state_path, _config(host="a.example.org"), resume=False)

            with self.assertRaises(RuntimeError):
                ProgressState(state_path, _config(host="b.example.org"), resume=True)

    def test_clear_removes_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            state_path = Path(tmp_dir) / "state.json"
            state = ProgressState(state_path, _config(), resume=False)
            self.assertTrue(state_path.exists())
            state.clear()
            self.assertFalse(state_path.exists())


if __name__ == "__main__":
    unittest.main()
