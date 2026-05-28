import unittest
import shutil
import platform

from odoo_installer.ssh import LocalExecutor


class LocalExecutorTests(unittest.TestCase):
    def test_dry_run_emits_local_marker(self) -> None:
        executor = LocalExecutor(dry_run=True)
        result = executor.run("echo connected")
        self.assertTrue(result.ok)
        self.assertIn("[DRY-RUN][LOCAL]", result.stdout)
        self.assertIn("bash -lc", result.stdout)

    def test_real_run_executes_command(self) -> None:
        if platform.system() != "Linux":
            self.skipTest("Real-run Test wird nur unter Linux ausgefuehrt.")
        if shutil.which("bash") is None:
            self.skipTest("bash ist auf diesem System nicht verfuegbar.")
        executor = LocalExecutor(dry_run=False)
        result = executor.run("printf '%s' connected")
        self.assertTrue(result.ok)
        self.assertEqual(result.stdout, "connected")


if __name__ == "__main__":
    unittest.main()
