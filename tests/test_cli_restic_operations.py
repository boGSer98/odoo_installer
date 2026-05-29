import unittest

from odoo_installer.cli import parse_args


class CliResticOperationTests(unittest.TestCase):
    def test_restic_snapshots_is_exclusive_operation(self) -> None:
        args = parse_args(["--config", "run-config.json", "--restic-snapshots", "--yes"])

        self.assertTrue(args.restic_snapshots)
        self.assertFalse(args.restic_check)

    def test_restic_check_accepts_read_data_subset(self) -> None:
        args = parse_args([
            "--config",
            "run-config.json",
            "--restic-check",
            "--restic-read-data-subset",
            "10%",
            "--yes",
        ])

        self.assertTrue(args.restic_check)
        self.assertEqual(args.restic_read_data_subset, "10%")


if __name__ == "__main__":
    unittest.main()
