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

    def test_published_radio_adapters_are_valid_candidate_sources(self):
        packages = {
            "librptadvradio": ["librptadvradio4", "librptadvradio-dev"],
            "rptadv-portaudio-alsa-adapter": [
                "librptadv-portaudio-alsa-adapter2",
                "librptadv-portaudio-alsa-adapter-dev",
            ],
            "rptadv-gpio-adapter": [
                "librptadv-gpio-adapter1",
                "librptadv-gpio-adapter-dev",
            ],
            "rptadv-ffmpeg-adapter": [
                "librptadv-ffmpeg-adapter1",
                "librptadv-ffmpeg-adapter-dev",
            ],
        }
        self.assertTrue(
            self.validate(
                [
                    {
                        "repository": repository,
                        "sha": "a" * 40,
                        "packages": package_names,
                    }
                    for repository, package_names in packages.items()
                ]
            )
        )

    def test_published_iax2_library_is_a_valid_candidate_source(self):
        self.assertTrue(
            self.validate(
                [
                    {
                        "repository": "librptadviax2",
                        "sha": "a" * 40,
                        "packages": [
                            "librptadv-iax2-client1",
                            "librptadv-iax2-client-dev",
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
