import tempfile
import unittest
from pathlib import Path

from scripts.inject_analytics import BEACON_URL, configure


class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.site = Path(self.directory.name)
        for name in ("index.html", "add.html"):
            (self.site / name).write_text("<!doctype html><html><body>QOTD</body></html>")

    def test_no_token_leaves_pages_unchanged(self):
        self.assertFalse(configure(self.site, ""))
        for name in ("index.html", "add.html"):
            self.assertNotIn(BEACON_URL, (self.site / name).read_text())

    def test_injects_once_into_both_pages(self):
        self.assertTrue(configure(self.site, "0123456789abcdef0123456789abcdef"))
        for name in ("index.html", "add.html"):
            html = (self.site / name).read_text()
            self.assertEqual(html.count(BEACON_URL), 1)
            self.assertIn('data-cf-beacon=\'{"token":"0123456789abcdef0123456789abcdef"}\'', html)
            self.assertTrue(html.endswith("</html>"))
        with self.assertRaises(ValueError):
            configure(self.site, "0123456789abcdef0123456789abcdef")

    def test_accepts_official_cloudflare_snippet(self):
        snippet = (
            "<!-- Cloudflare Web Analytics --><script type='module' "
            "src='https://static.cloudflareinsights.com/beacon.min.js' "
            "data-cf-beacon='{\"token\": \"0123456789abcdef0123456789abcdef\"}'"
            "></script><!-- End Cloudflare Web Analytics -->"
        )
        self.assertTrue(configure(self.site, snippet))
        for name in ("index.html", "add.html"):
            html = (self.site / name).read_text()
            self.assertEqual(html.count(BEACON_URL), 1)
            self.assertNotIn("Cloudflare Web Analytics -->", html)

    def test_invalid_tokens_rejected_without_changing_pages(self):
        for token in (
            "bad", "evil\" onclick=alert(1)", "x" * 129,
            "https://static.cloudflareinsights.com/beacon.min.js no token",
        ):
            with self.assertRaises(ValueError):
                configure(self.site, token)
        for name in ("index.html", "add.html"):
            self.assertNotIn(BEACON_URL, (self.site / name).read_text())


if __name__ == "__main__":
    unittest.main()
