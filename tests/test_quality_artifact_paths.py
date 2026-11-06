"""Coverage and native container access follow the selected source contracts."""

import unittest
from pathlib import Path

WORKFLOW = (
    Path(__file__).resolve().parents[1] / ".github/workflows/quality.yml"
).read_text()


class QualityArtifactPaths(unittest.TestCase):
    def test_coverage_upload_uses_the_production_checkout(self):
        self.assertIn("path: production/build/coverage", WORKFLOW)
        self.assertNotIn("path: build/coverage", WORKFLOW)

    def test_native_docker_socket_is_default_off_and_forwarded_only_to_packages(self):
        interface = WORKFLOW.split("permissions:", 1)[0]
        self.assertRegex(
            interface,
            r"native_docker_socket:\n(?:        description: [^\n]+\n)?"
            r"        type: boolean\n        default: false",
        )
        package_step = WORKFLOW.split(
            "      - name: Build, test, package, and verify staged installation\n", 1
        )[1].split("      - name:", 1)[0]
        self.assertIn(
            "RPTADV_CONTAINER_DOCKER_SOCKET: "
            "${{ inputs.native_docker_socket && '1' || '0' }}",
            package_step,
        )
        self.assertEqual(WORKFLOW.count("RPTADV_CONTAINER_DOCKER_SOCKET:"), 1)
