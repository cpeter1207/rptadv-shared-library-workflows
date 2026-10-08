"""The release workflow copies artifacts from its production checkout."""

from pathlib import Path
import unittest


WORKFLOW = (
    Path(__file__).resolve().parents[1] / ".github/workflows/release.yml"
).read_text()


class ReleaseArtifactPaths(unittest.TestCase):
    def test_release_copies_packages_and_archive_from_production_checkout(self):
        self.assertIn("cp production/build/debian-source/*.deb release/", WORKFLOW)
        self.assertIn("cp production/build/*.tar.gz release/", WORKFLOW)
