"""Documentation publication uses the already-validated main revision."""

from pathlib import Path
import re
import os
import subprocess
import tempfile
import textwrap
import unittest


WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/documentation.yml"


class DocumentationWorkflow(unittest.TestCase):
    def test_publishes_generated_docs_from_validated_main(self):
        source = WORKFLOW.read_text()
        self.assertIn("code_ref:", source)
        self.assertIn("git merge-base --is-ancestor", source)
        self.assertIn('"quality / Required quality gate"', source)
        self.assertIn("make docs", source)
        self.assertIn("build/doxygen/html", source)
        self.assertIn("actions/upload-pages-artifact@", source)
        self.assertIn("actions/deploy-pages@", source)
        self.assertIn("pages: write", source)
        self.assertIn("id-token: write", source)

    def test_publication_shell_programs_pass_shellcheck(self):
        source = WORKFLOW.read_text()
        scripts = re.findall(r"(?m)^        run: \|\n((?:          .*\n|\n)+)", source)
        self.assertEqual(len(scripts), 2)
        for script in scripts:
            subprocess.run(
                ["shellcheck", "--shell=bash", "-"],
                input=textwrap.dedent(script), text=True, check=True,
            )

    def test_publication_ignores_private_rustdoc_lock_but_keeps_html(self):
        source = WORKFLOW.read_text()
        copy = source.split('          site="$RUNNER_TEMP/shared-library-docs"\n', 1)[1]
        copy = copy.split("      - uses: actions/configure-pages@", 1)[0]
        script = 'site="$RUNNER_TEMP/shared-library-docs"\n' + textwrap.dedent(copy)
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            root.chmod(0o755)
            (root / "build/doxygen/html").mkdir(parents=True)
            (root / "build/doxygen/html/index.html").write_text("Doxygen page")
            (root / "target/doc/rptadvsquelch").mkdir(parents=True)
            (root / "target/doc/rptadvsquelch/index.html").write_text("Rustdoc page")
            lock = root / "target/doc/.lock"
            lock.write_text("private build lock")
            lock.chmod(0o600)
            output = root / "output"
            output.mkdir(mode=0o777)
            output.chmod(0o777)
            result = subprocess.run(
                ["runuser", "-u", "nobody", "--", "bash", "-e", "-c", script],
                cwd=root, env=dict(os.environ, RUNNER_TEMP=str(output)),
                text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            site = output / "shared-library-docs"
            self.assertEqual((site / "index.html").read_text(), "Doxygen page")
            self.assertEqual(
                (site / "rust/rptadvsquelch/index.html").read_text(), "Rustdoc page"
            )
            self.assertFalse((site / "rust/.lock").exists())


if __name__ == "__main__":
    unittest.main()
