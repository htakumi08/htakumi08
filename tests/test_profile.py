import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

from scripts import update_profile as profile


class ProfileTests(unittest.TestCase):
    def test_summary_ignores_forks_private_and_profile_repo(self):
        repos = [
            {"name": "demo", "fork": False, "private": False, "stargazers_count": 2, "language": "Go"},
            {"name": "fork", "fork": True, "private": False, "stargazers_count": 900, "language": "Python"},
            {"name": "secret", "fork": False, "private": True, "stargazers_count": 8, "language": "Rust"},
            {"name": "htakumi08", "fork": False, "private": False, "stargazers_count": 1, "language": "Python"},
        ]
        result = profile.summarize(repos)
        self.assertEqual(result, {"projects": 1, "stars": 2, "languages": {"Go": 1}})

    def test_empty_profile_renders_valid_svg(self):
        data = {"summary": {"projects": 0, "stars": 0, "languages": {}}, "days": []}
        for svg in profile.render_assets(data).values():
            ET.fromstring(svg)
            self.assertNotIn("nan", svg.lower())

    def test_calendar_positions_keep_weekdays_and_missing_cells(self):
        days = [{"date": "2026-10-26", "weekday": 1, "count": 2, "week": 0},
                {"date": "2026-10-28", "weekday": 3, "count": 5, "week": 0}]
        svg = profile.render_city(days)
        self.assertIn("2026-10-26: 2 contributions", svg)
        self.assertIn("2026-10-28: 5 contributions", svg)
        self.assertEqual(svg.count('class="building"'), 2)
        ET.fromstring(svg)

    def test_labels_are_xml_escaped(self):
        svg = profile.render_stats({"projects": 1, "stars": 0, "languages": {"C<&": 1}}, [])
        root = ET.fromstring(svg)
        self.assertIn("C<&", "".join(root.itertext()))

    def test_failed_fetch_does_not_replace_existing_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "stats.svg").write_text("previous-good-image")
            with patch.object(profile, "fetch_data", side_effect=RuntimeError("API unavailable")):
                with self.assertRaises(RuntimeError):
                    profile.update(target)
            self.assertEqual((target / "stats.svg").read_text(), "previous-good-image")


if __name__ == "__main__":
    unittest.main()
