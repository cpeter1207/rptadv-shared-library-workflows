"""Codec image inputs retain legacy callers and pin each native image pair."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CodecImages(unittest.TestCase):
    def test_prebuilt_input_preserves_source_owned_default(self):
        workflow = (ROOT / ".github/workflows/quality.yml").read_text()
        self.assertIn("quality_image:", workflow)
        self.assertEqual(workflow.count("if: inputs.quality_image == ''"), 2)
        self.assertIn("inputs.quality_image || 'shared-quality:local'", workflow)
        self.assertIn("make platform-verify QUALITY_IMAGE=", workflow)

    def test_manifest_uses_same_run_attempt(self):
        workflow = (ROOT / ".github/workflows/codec-images.yml").read_text()
        self.assertIn("github.run_id", workflow)
        self.assertIn("github.run_attempt", workflow)
        self.assertIn('"$IMAGE:$RUN_TAG-amd64" "$IMAGE:$RUN_TAG-arm64"', workflow)
        self.assertNotIn("-candidate", workflow)

    def test_private_backends_use_reviewed_provider_revision(self):
        workflow = (ROOT / ".github/workflows/codec-images.yml").read_text()
        image = (ROOT / "containers/codecs.Dockerfile").read_text()
        self.assertIn("repository: cpeter1207/rptadv-codec-adapters", workflow)
        self.assertIn("path: codec-bootstrap", workflow)
        self.assertIn("context: .", workflow)
        self.assertIn("packaging/external/build.py", image)
        self.assertIn("RPTADV_CODEC_SOURCE_CACHE", image)
        self.assertIn("RPTADV_CODEC_BACKEND_LIBDIR", image)

    def test_focused_target_cannot_supply_shell_commands(self):
        workflow = (ROOT / ".github/workflows/codec-focused.yml").read_text()
        self.assertIn("^[0-9a-f]{40}$", workflow)
        self.assertIn('case "$TARGET" in test|abi-check|install-check', workflow)
        self.assertIn('make "$TARGET"', workflow)
        self.assertIn("packages: read", workflow)
        self.assertIn("codec-coverage-amd64", workflow)
