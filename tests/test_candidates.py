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
                            "librptadv-iax2-client2",
                            "librptadv-iax2-client-dev",
                        ],
                    }
                ]
            )
        )

    def test_codec_providers_are_valid_candidate_sources(self):
        self.assertTrue(
            self.validate(
                [
                    {
                        "repository": "rptadv-codec-adapters",
                        "sha": "a" * 40,
                        "packages": ["librptadv-codec-dev", "librptadv-codec-g7111"],
                    }
                ]
            )
        )

    def test_pinned_dtmf_library_is_a_valid_candidate_source(self):
        self.assertTrue(
            self.validate(
                [
                    {
                        "repository": "librptadvdtmf",
                        "sha": "7a3ec75544be9891567849b1f2badb43f63905b6",
                        "packages": ["librptadvdtmf1", "librptadvdtmf-dev"],
                    }
                ]
            )
        )

    def test_schedule_candidate_requires_immutable_revision(self):
        for revision, accepted in (
            ("622e81add8ac478385883fdaf5e9939ecce35109", True),
            ("main", False),
            ("$(id)", False),
            ("a" * 39, False),
        ):
            with self.subTest(revision=revision):
                self.assertEqual(
                    self.validate(
                        [
                            {
                                "repository": "librptadvschedule",
                                "sha": revision,
                                "packages": [
                                    "librptadvschedule1",
                                    "librptadvschedule-dev",
                                ],
                            }
                        ]
                    ),
                    accepted,
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
