import io
import unittest

from odoo_installer.ui import TerminalUI


class TerminalUITests(unittest.TestCase):
    def test_banner_and_key_values_render_without_color(self) -> None:
        stream = io.StringIO()
        ui = TerminalUI(stream=stream, force_color=False)

        ui.banner("AHD Odoo Installer", "Ubuntu 24.04")
        ui.key_values({"Host": "example.org", "Support-SSH": True})

        output = stream.getvalue()
        self.assertIn("AHD Odoo Installer", output)
        self.assertIn("Ubuntu 24.04", output)
        self.assertIn("Host", output)
        self.assertIn("example.org", output)
        self.assertIn("Support-SSH", output)

    def test_checklist_marks_active_and_inactive_items(self) -> None:
        stream = io.StringIO()
        ui = TerminalUI(stream=stream, force_color=False)

        ui.checklist([("Odoo", True), ("Certbot", False)])

        output = stream.getvalue()
        self.assertIn("● Odoo", output)
        self.assertIn("○ Certbot", output)


if __name__ == "__main__":
    unittest.main()
