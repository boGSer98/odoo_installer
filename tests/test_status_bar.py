import unittest

from odoo_installer.pipeline import InstallStatusBar


class StatusBarTests(unittest.TestCase):
    def test_line_contains_percent_and_counts(self) -> None:
        bar = InstallStatusBar(total=10, width=10)
        line = bar._line(3, "System vorbereiten")
        self.assertIn("[###-------]", line)
        self.assertIn(" 30% (3/10)", line)
        self.assertIn("System vorbereiten", line)

    def test_line_clamps_to_100_percent(self) -> None:
        bar = InstallStatusBar(total=2, width=10)
        line = bar._line(3, "Done")
        self.assertIn("100% (3/2)", line)


if __name__ == "__main__":
    unittest.main()
