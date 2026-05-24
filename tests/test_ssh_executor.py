import unittest

from odoo_installer.ssh import SSHExecutor


class SSHExecutorTests(unittest.TestCase):
    def test_dry_run_key_mode_includes_accept_new_and_batchmode(self) -> None:
        executor = SSHExecutor(
            host="example.org",
            user="root",
            host_key_mode="accept-new",
            dry_run=True,
        )
        result = executor.run("echo connected")
        self.assertTrue(result.ok)
        self.assertIn("StrictHostKeyChecking=accept-new", result.stdout)
        self.assertIn("BatchMode=yes", result.stdout)

    def test_dry_run_password_mode_uses_password_auth_options(self) -> None:
        executor = SSHExecutor(
            host="example.org",
            user="root",
            ssh_password="secret",
            host_key_mode="insecure",
            dry_run=True,
        )
        result = executor.run("echo connected")
        self.assertTrue(result.ok)
        self.assertIn("BatchMode=no", result.stdout)
        self.assertIn("PreferredAuthentications=password,keyboard-interactive,publickey", result.stdout)
        self.assertIn("StrictHostKeyChecking=no", result.stdout)
        self.assertIn("UserKnownHostsFile=", result.stdout)


if __name__ == "__main__":
    unittest.main()
