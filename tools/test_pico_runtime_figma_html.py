import pathlib
import unittest


HTML_PATH = pathlib.Path("docs/diagrams/pico-runtime-figma/index.html")


class PicoRuntimeFigmaHtmlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = HTML_PATH.read_text(encoding="utf-8")

    def test_deck_matches_display_only_scope(self):
        self.assertEqual(self.html.count('<section class="slide">'), 2)
        self.assertIn("Display-only runtime flow", self.html)
        self.assertIn("display-only mode", self.html.lower())
        for forbidden in (
            "Frame 3",
            "Editable source of truth",
            "60 s status reporting",
            "600 s baseline snapshots",
            "Show or store local results",
            "event files",
            "local history files",
            "baseline checkpoints",
            "FULL_LOCAL",
            "EVENT_ONLY",
            "USB_STREAM",
            "logging mode",
            "logging modes",
            "storage.py",
            "csv",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, self.html)

    def test_capture_source_stays_ascii_safe(self):
        self.assertTrue(self.html.isascii())
        for forbidden in (
            'content: "?"',
            "`r`n",
            "?",
            "?",
            "?",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, self.html)

    def test_overview_connectors_use_arrowheads(self):
        self.assertIn(".flow-card:not(:last-child)::after", self.html)
        self.assertIn("border-left: 10px solid #6f86a0;", self.html)
        before_rule = self.html.split(".flow-card:not(:last-child)::before", 1)[1].split("}", 1)[0]
        self.assertNotIn("border-radius: 50%;", before_rule)


if __name__ == "__main__":
    unittest.main()
