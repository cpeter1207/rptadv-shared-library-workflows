"""Documentation publication uses the already-validated main revision."""

from pathlib import Path
import re
import subprocess
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


if __name__ == "__main__":
    unittest.main()
