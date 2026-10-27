"""The release workflow copies artifacts from its production checkout."""

import unittest
from pathlib import Path

WORKFLOW = (
    Path(__file__).resolve().parents[1] / ".github/workflows/release.yml"
).read_text()


class ReleaseArtifactPaths(unittest.TestCase):
    def test_release_copies_packages_and_archive_from_production_checkout(self):
        self.assertIn("cp production/build/debian-source/*.deb release/", WORKFLOW)
        self.assertIn("cp production/build/*.tar.gz release/", WORKFLOW)

    def test_index_dispatch_follows_published_release(self):
        publication = WORKFLOW.index('gh release create "$TAG"')
        dispatch = WORKFLOW.index(
            "USBRadioPlus-Workflows/actions/dispatch-package-index@main"
        )
        self.assertLess(publication, dispatch)
        self.assertIn("APT_INDEX_DISPATCH_TOKEN:", WORKFLOW)
        self.assertIn("token: ${{ secrets.APT_INDEX_DISPATCH_TOKEN }}", WORKFLOW)
        self.assertIn("package-repository: ${{ github.repository }}", WORKFLOW)
        self.assertIn("package-tag: ${{ inputs.tag }}", WORKFLOW)
