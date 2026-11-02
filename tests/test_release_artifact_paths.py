"""The release workflow copies artifacts from its production checkout."""

import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

WORKFLOW = (
    Path(__file__).resolve().parents[1] / ".github/workflows/release.yml"
).read_text()


class ReleaseArtifactPaths(unittest.TestCase):
    def test_artifact_build_skips_repeated_tests_inside_container(self):
        step = WORKFLOW.split(
            "      - name: Build release packages and source archive\n", 1
        )[1]
        script = textwrap.dedent(
            step.split("        run: |\n", 1)[1].split("      - uses:", 1)[0]
        )
        for target in ("debian-package-check", "release-packages"):
            for status in (0, 37):
                with (
                    self.subTest(target=target, status=status),
                    tempfile.TemporaryDirectory() as work,
                ):
                    root = Path(work)
                    launcher = root / "workflow-tools/tools"
                    launcher.mkdir(parents=True)
                    (launcher / "run-in-quality-container.sh").write_text(
                        "unset DEB_BUILD_OPTIONS\n"
                        "shift 2\n"
                        'cd "$GITHUB_WORKSPACE/production"\n'
                        'exec "$@"\n'
                    )
                    binaries = root / "bin"
                    binaries.mkdir()
                    for name, body in {
                        "dpkg": "printf 'amd64\\n'\n",
                        "make": 'printf "%s\\n" "$DEB_BUILD_OPTIONS" "$@" '
                        '> "$BUILD_LOG"\nexit "$BUILD_STATUS"\n',
                    }.items():
                        command = binaries / name
                        command.write_text("#!/bin/sh\n" + body)
                        command.chmod(0o755)
                    packages = root / "production/build/debian-source"
                    packages.mkdir(parents=True)
                    (packages / "runtime.deb").write_text("runtime package")
                    archive = packages.parent / "source.tar.gz"
                    archive.write_text("source archive")
                    log = root / "make.log"
                    result = subprocess.run(
                        ["bash", "-e", "-c", script],
                        cwd=root,
                        env=dict(
                            os.environ,
                            PATH=f"{binaries}:{os.environ['PATH']}",
                            GITHUB_WORKSPACE=work,
                            EXPECTED_ARCH="amd64",
                            TAG="v0.1.0-alpha1",
                            PACKAGE_TARGET=target,
                            BUILD_LOG=str(log),
                            BUILD_STATUS=str(status),
                            DEB_BUILD_OPTIONS="outer-value-not-forwarded",
                        ),
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(result.returncode, status, result.stderr)
                    self.assertEqual(
                        log.read_text().splitlines(),
                        ["nocheck", "PACKAGE_VERSION=0.1.0-alpha1", target],
                    )
                    release = root / "release"
                    self.assertEqual(release.exists(), status == 0)
                    if status == 0:
                        self.assertEqual(
                            sorted(path.name for path in release.iterdir()),
                            ["runtime.deb", "source.tar.gz"],
                        )

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
