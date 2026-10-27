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

    def test_focused_target_cannot_supply_shell_commands(self):
        workflow = (ROOT / ".github/workflows/codec-focused.yml").read_text()
        self.assertIn("^[0-9a-f]{40}$", workflow)
        self.assertIn('case "$TARGET" in test|abi-check|install-check', workflow)
        self.assertIn('make "$TARGET"', workflow)
        self.assertIn("packages: read", workflow)
