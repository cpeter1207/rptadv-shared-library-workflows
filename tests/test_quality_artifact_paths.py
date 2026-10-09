"""Coverage evidence is relative to the production checkout, not the runner."""

from pathlib import Path
import unittest


WORKFLOW = (
    Path(__file__).resolve().parents[1] / ".github/workflows/quality.yml"
).read_text()


class QualityArtifactPaths(unittest.TestCase):
    def test_coverage_upload_uses_the_production_checkout(self):
        self.assertIn("path: production/build/coverage", WORKFLOW)
        self.assertNotIn("path: build/coverage", WORKFLOW)
