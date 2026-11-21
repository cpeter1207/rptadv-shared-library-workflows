"""Exercise the isolated candidate build with small verified installer archives."""

import hashlib
import os
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path

ACTION = Path(__file__).resolve().parents[1] / "actions/install-candidate-dependencies"
PIN = "238811360fc34908a8ea9d4174bfe49d874d2a0e"
DEPS = (
    "cargo (>= 1.93) | cargo-web (>= 1.93), debhelper-compat (= 13), "
    "pkg-config, rustc (>= 1.93) | rustc-web (>= 1.93)"
)


class ScheduleBuild(unittest.TestCase):
    def test_only_pinned_schedule_uses_the_specialized_builder(self):
        source = (ACTION / "build.sh").read_text()
        script = source.split('    cd "$directory"\n', 1)[1].split("\n  )", 1)[0]
        mocks = """
bash() { echo "$*"; }
mk-build-deps() { echo normal; }
dpkg-buildpackage() { echo package; }
"""
        for repo, revision, expected in (
            ("librptadvschedule", PIN, "/action/build-schedule.sh amd64 /tmp"),
            ("librptadvschedule", "0" * 40, "normal\npackage"),
            ("USBRadioPlus", PIN, "normal\npackage"),
        ):
            with self.subTest(repo=repo, revision=revision):
                result = subprocess.run(
                    ["bash", "-ec", mocks + script],
                    env=dict(
                        os.environ,
                        repository=repo,
                        revision=revision,
                        action_directory="/action",
                        architecture="amd64",
                        workspace="/tmp",
                    ),
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.stdout.strip(), expected)

    def test_exact_rust_database_diagnostics(self):
        source = (ACTION / "build-schedule.sh").read_text()
        script = "flags=()\n" + source.split("flags=()\n", 1)[1]
        mocks = """
dpkg-checkbuilddeps() { printf '%s\\n' "$DIAGNOSTIC" >&2; return "$STATUS"; }
dpkg-buildpackage() { echo "$*"; }
"""
        cargo = "cargo (>= 1.93) | cargo-web (>= 1.93)"
        rustc = "rustc (>= 1.93) | rustc-web (>= 1.93)"
        for spelling in ("Unmet", "unmet"):
            prefix = f"dpkg-checkbuilddeps: error: {spelling} build dependencies: "
            for diagnostic, status, accepted in (
                (prefix + cargo, 1, True),
                (prefix + rustc, 1, True),
                (prefix + cargo + " " + rustc, 1, True),
                (prefix + cargo + " pkg-config", 1, False),
                (prefix + cargo, 2, False),
                (cargo, 1, False),
                (prefix + cargo + "\nextra diagnostic", 1, False),
            ):
                with self.subTest(diagnostic=diagnostic, status=status):
                    result = subprocess.run(
                        ["bash", "-ec", mocks + script],
                        env=dict(os.environ, DIAGNOSTIC=diagnostic, STATUS=str(status)),
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertEqual(result.returncode == 0, accepted, result.stderr)
                    self.assertEqual(
                        result.stdout.strip(), "-us -uc -b -d" if accepted else ""
                    )

    def test_compiler_architecture_hashes_and_original_debian_dependencies(self):
        for arch, target, version, host_ok, db, corrupt, expected in (
            ("amd64", "x86_64", "1.93.0", True, "missing-rust", False, "-us -uc -b -d"),
            ("arm64", "aarch64", "1.93.0", True, "complete", False, "-us -uc -b"),
            ("arm64", "aarch64", "1.93.0", True, "missing-nonrust", False, None),
            ("amd64", "x86_64", "1.88.0", True, "missing-rust", False, None),
            ("amd64", "x86_64", "bad-cargo", True, "missing-rust", False, None),
            ("arm64", "aarch64", "1.93.0", False, "missing-rust", False, None),
            ("amd64", "x86_64", "1.93.0", True, "complete", True, None),
        ):
            with (
                self.subTest(
                    arch=arch, version=version, host_ok=host_ok, db=db, corrupt=corrupt
                ),
                tempfile.TemporaryDirectory() as work,
            ):
                self.run_fixture(
                    Path(work),
                    arch,
                    target + "-unknown-linux-gnu",
                    version,
                    host_ok,
                    db,
                    corrupt,
                    expected,
                )

    def run_fixture(
        self, root, arch, target, version, host_ok, db, corrupt, expected, *, config=None
    ):
        config = config or {
            "script": "build-schedule.sh",
            "release": "1.93.0",
            "date": "2026-01-22",
            "dependencies": DEPS,
            "packages": {"debhelper-compat": "13", "pkg-config": "1"},
            "non_rust": "debhelper-compat (= 13), pkg-config",
            "temporary": "schedule-rust.*",
        }
        release = config["release"]
        action = root / "action"
        action.mkdir()
        shutil.copy(ACTION / config["script"], action)
        commands = root / "bin"
        commands.mkdir()
        for name, program in {
            "curl": 'url=${!#}\nfile=${url##*/}\ntest "$url" = "https://static.rust-lang.org/dist/$FIXTURE_DATE/$file"\ncp "$FIXTURE_ROOT/$file" .',
            "apt-get": 'echo "$*" > "$FIXTURE_ROOT/apt"',
            "dpkg-checkbuilddeps": 'exec /usr/bin/dpkg-checkbuilddeps -I --admindir="$FIXTURE_ROOT/db" "$@"',
            "dpkg-buildpackage": 'echo "$*" > "$FIXTURE_ROOT/built"\ntest "$(command -v rustc)" = "$RUSTC"\ntest "$(command -v cargo)" = "$CARGO"',
            "rustc": 'echo "rustc 1.88.0 (caller)"',
        }.items():
            path = commands / name
            path.write_text("#!/bin/bash\nset -eu\n" + program + "\n")
            path.chmod(0o755)
        # Preserve production archive names, exercising the real checksum, tar
        # extraction and install order. Only fixture archive contents differ.
        lock = f"rust-{release}-{arch}.sha256"
        lines = []
        for line in (ACTION / lock).read_text().splitlines():
            _, filename = line.split()
            directory = root / filename.removesuffix(".tar.xz")
            directory.mkdir()
            component = directory.name.removesuffix(f"-{release}-{target}")
            installer = 'set -eu\nprefix=${1#--prefix=}\ntest "$2" = --disable-ldconfig\nmkdir -p "$prefix/bin"\n'
            if component in ("rustc", "cargo"):
                binary = directory / component
                if component == "rustc":
                    output = f"host: {target if host_ok else 'wrong-host'}\nrelease: {version if version != 'bad-cargo' else release}"
                else:
                    output = f"cargo {version} (fixture)"
                binary.write_text(f"#!/bin/sh\necho '{output}'\n")
                binary.chmod(0o755)
                installer += f'cp "$(dirname "$0")/{component}" "$prefix/bin/"\n'
            (directory / "install.sh").write_text(installer)
            archive = root / filename
            with tarfile.open(archive, "w:xz") as tar:
                tar.add(directory, arcname=directory.name)
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            lines.append(f"{digest}  {filename}")
            if corrupt and component == "rust-std":
                archive.write_bytes(b"corrupt")
        (action / lock).write_text("\n".join(lines) + "\n")

        (root / "debian").mkdir()
        (root / "debian/control").write_text(
            f"Source: fixture\nBuild-Depends: {config['dependencies']}\n"
        )
        (root / "db").mkdir()
        packages = dict(config["packages"])
        if db == "missing-nonrust":
            del packages["pkg-config"]
        if db == "complete":
            packages.update(rustc=release, cargo=release)
        (root / "db/status").write_text(
            "".join(
                f"Package: {name}\nStatus: install ok installed\nVersion: {ver}\nArchitecture: all\n\n"
                for name, ver in packages.items()
            )
        )
        result = subprocess.run(
            [
                "bash",
                "-ec",
                'before=$(rustc --version); bash "$1" "$2" "$3"; test "$(rustc --version)" = "$before"',
                "bash",
                str(action / config["script"]),
                arch,
                str(root),
            ],
            cwd=root,
            env=dict(
                os.environ,
                FIXTURE_ROOT=str(root),
                FIXTURE_DATE=config["date"],
                PATH=f"{commands}:{os.environ['PATH']}",
            ),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode == 0, expected is not None, result.stderr)
        self.assertEqual(list(root.glob(config["temporary"])), [])
        if expected is None:
            self.assertFalse((root / "built").exists())
        else:
            self.assertEqual((root / "built").read_text().strip(), expected)
            self.assertEqual(
                (root / "apt").read_text().strip(),
                "-y --no-install-recommends satisfy " + config["non_rust"],
            )
