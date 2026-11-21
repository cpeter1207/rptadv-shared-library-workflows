"""Pinned radio candidates need their declared native compiler, not Debian 1.85."""

import os
import subprocess
import tempfile

import test_schedule_build as schedule
import unittest
from pathlib import Path

ACTION = Path(__file__).resolve().parents[1] / "actions/install-candidate-dependencies"
PIN = "83c715249516b176fca0297bffb2b145e98c8d27"


class RadioBuild(unittest.TestCase):
    def test_only_reviewed_radio_pin_selects_native_compiler_builder(self):
        source = (ACTION / "build.sh").read_text()
        script = source.split('    cd "$directory"\n', 1)[1].split("\n  )", 1)[0]
        mocks = """
bash() { echo "$*"; }
mk-build-deps() { echo normal; }
dpkg-buildpackage() { echo package; }
"""
        for repo, revision, arch, expected in (
            ("librptadvradio", PIN, "amd64", "/action/build-radio.sh amd64 /tmp"),
            ("librptadvradio", PIN, "arm64", "/action/build-radio.sh arm64 /tmp"),
            ("librptadvradio", "0" * 40, "amd64", "normal\npackage"),
            ("USBRadioPlus", PIN, "amd64", "normal\npackage"),
        ):
            with self.subTest(repo=repo, revision=revision, arch=arch):
                result = subprocess.run(
                    ["bash", "-ec", mocks + script],
                    env=dict(
                        os.environ,
                        repository=repo,
                        revision=revision,
                        action_directory="/action",
                        architecture=arch,
                        workspace="/tmp",
                    ),
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.stdout.strip(), expected)

    def test_verified_native_compiler_and_original_dependency_fences(self):
        non_rust = (
            "debhelper-compat (= 13), librptadvctcss-dev (>= 0.1.0~alpha2-1), "
            "librptadvdcs-dev (>= 0.1.0~alpha1-1), "
            "librptadvsquelch-dev (>= 0.1.0~alpha2-1), "
            "librptadv-samplerate-adapter-dev (>= 0.2.0~alpha2-1), pkg-config"
        )
        config = {
            "script": "build-radio.sh",
            "release": "1.87.0",
            "date": "2025-05-15",
            "dependencies": "cargo (>= 1.87), " + non_rust + ", rustc (>= 1.87)",
            "packages": {
                "debhelper-compat": "13",
                "librptadvctcss-dev": "0.1.0~alpha2-1",
                "librptadvdcs-dev": "0.1.0~alpha1-1",
                "librptadvsquelch-dev": "0.1.0~alpha2-1",
                "librptadv-samplerate-adapter-dev": "0.2.0~alpha2-1",
                "pkg-config": "1",
            },
            "non_rust": non_rust,
            "temporary": "radio-rust.*",
        }
        for arch, target, version, host_ok, db, corrupt, expected in (
            ("amd64", "x86_64", "1.87.0", True, "missing-rust", False, "-us -uc -b -d"),
            ("arm64", "aarch64", "1.87.0", True, "complete", False, "-us -uc -b"),
            ("arm64", "aarch64", "1.87.0", True, "missing-nonrust", False, None),
            ("amd64", "x86_64", "1.85.0", True, "missing-rust", False, None),
            ("amd64", "x86_64", "bad-cargo", True, "missing-rust", False, None),
            ("arm64", "aarch64", "1.87.0", False, "missing-rust", False, None),
            ("amd64", "x86_64", "1.87.0", True, "complete", True, None),
        ):
            with self.subTest(arch=arch, version=version, host_ok=host_ok, db=db, corrupt=corrupt), tempfile.TemporaryDirectory() as work:
                schedule.ScheduleBuild.run_fixture(
                    self, Path(work), arch, target + "-unknown-linux-gnu", version,
                    host_ok, db, corrupt, expected, config=config,
                )
