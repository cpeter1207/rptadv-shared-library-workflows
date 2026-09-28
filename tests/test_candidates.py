"""Candidate ABI inputs must be immutable, bounded project-owned data."""

import json
import subprocess
import unittest
from pathlib import Path

VALIDATOR = (
    Path(__file__).resolve().parents[1]
    / "actions/install-candidate-dependencies/manifest.jq"
)


class CandidateManifest(unittest.TestCase):
    def validate(self, value):
        return (
            subprocess.run(
                ["jq", "-e", "-f", str(VALIDATOR)],
                input=json.dumps(value),
                text=True,
                capture_output=True,
                check=False,
            ).returncode
            == 0
        )

    def test_exact_source_with_current_abi_packages(self):
        self.assertTrue(
            self.validate(
                [
                    {
                        "repository": "rate_adjusting_pcm_ring",
                        "sha": "1234567890abcdef" * 2 + "12345678",
                        "packages": [
                            "librate-adjusting-pcm-ring3",
                            "librate-adjusting-pcm-ring3-dev",
                        ],
                    }
                ]
            )
        )

    def test_moving_refs_and_unrelated_or_shell_inputs_rejected(self):
        for field, value in (
            ("sha", "main"),
            ("sha", "$(id)"),
            ("sha", "a" * 39),
            ("repository", "../other"),
            ("repository", "unrelated"),
            ("packages", []),
            ("packages", ["../lib.so"]),
            ("packages", ["libx; id"]),
        ):
            entry = {
                "repository": "librptadvradio",
                "sha": "a" * 40,
                "packages": ["librptadvradio4"],
            }
            entry[field] = value
            with self.subTest(field=field, value=value):
                self.assertFalse(self.validate([entry]))

    def test_empty_or_missing_manifest_fields_rejected(self):
        for value in ([], {}, [{}], None):
            with self.subTest(value=value):
                self.assertFalse(self.validate(value))
