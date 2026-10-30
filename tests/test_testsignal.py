from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from testsignal.core import Change, DEFAULT_CONFIG, build_report, candidate_tests, classify, normalise, render_text


class CoreTests(unittest.TestCase):
    def test_python_candidate_paths_are_stable(self):
        self.assertEqual(candidate_tests("src/api/parser.py", DEFAULT_CONFIG), [
            "__tests__/api/parser_test.py", "__tests__/api/test_parser.py", "src/api/test_parser.py",
            "test/api/parser_test.py", "test/api/test_parser.py", "tests/api/parser_test.py", "tests/api/test_parser.py",
        ])

    def test_classification_and_exclusion(self):
        config = {**DEFAULT_CONFIG, "exclude": ["generated/**"]}
        self.assertEqual(classify("tests/test_api.py", config), "test")
        self.assertEqual(classify("src/api.py", config), "source")
        self.assertEqual(classify("generated/client.py", config), "excluded")
        self.assertEqual(classify("notes.txt", config), "unsupported")

    def test_normalise_preserves_dot_prefixed_tracked_path(self):
        self.assertEqual(normalise(".config/app.py"), ".config/app.py")
        self.assertEqual(normalise("./src/app.py"), "src/app.py")

    def test_report_only_requires_supported_active_source(self):
        report = build_report([Change("M", "src/parser.py"), Change("M", "tests/test_parser.py"),
                               Change("M", "notes.txt"), Change("D", "src/old.py")], "a", "b", DEFAULT_CONFIG)
        self.assertEqual(report["sources"][0]["result"], "matched")
        self.assertEqual(report["unmatched"], [])
        self.assertIn("Unsupported: notes.txt", render_text(report))


class CliIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        self.cmd("git", "init", "-q")
        self.cmd("git", "config", "user.email", "test@example.invalid")
        self.cmd("git", "config", "user.name", "Test")
        self.write("src/parser.py", "def parse(): return 1\n")
        self.write("src/formatter.py", "def format_value(): return 1\n")
        self.write("tests/test_parser.py", "def test_parse(): assert True\n")
        self.write("generated/client.py", "VALUE = 1\n")
        self.write("notes.txt", "baseline\n")
        self.write(".testsignal.json", '{"exclude": ["generated/**"]}\n')
        self.cmd("git", "add", ".")
        self.cmd("git", "commit", "-qm", "base")
        self.write("src/parser.py", "def parse(): return 2\n")
        self.write("tests/test_parser.py", "def test_parse(): assert 2 == 2\n")
        self.write("src/formatter.py", "def format_value(): return 2\n")
        self.write("generated/client.py", "VALUE = 2\n")
        self.write("notes.txt", "changed\n")
        self.cmd("git", "add", ".")
        self.cmd("git", "commit", "-qm", "change")

    def tearDown(self):
        self.temp.cleanup()

    def cmd(self, *command, check=True):
        return subprocess.run(command, cwd=self.repo, text=True, capture_output=True, check=check)

    def write(self, relative, content):
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def cli(self, *args):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT / "src")
        return subprocess.run([sys.executable, "-m", "testsignal", "--base", "HEAD~1", "--head", "HEAD", *args], cwd=self.repo, text=True, capture_output=True, env=env)

    def test_json_reports_matched_unmatched_excluded_and_unsupported(self):
        result = self.cli("--format", "json")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        by_path = {item["path"]: item for item in report["sources"]}
        self.assertEqual(by_path["src/parser.py"]["matching_changed_tests"], ["tests/test_parser.py"])
        self.assertEqual(by_path["src/parser.py"]["result"], "matched")
        self.assertEqual(by_path["src/formatter.py"]["result"], "unmatched")
        self.assertEqual(report["exclusions"], ["generated/client.py"])
        self.assertEqual(report["changed_paths"]["unsupported"], ["notes.txt"])

    def test_strict_and_bad_revision_fail_cleanly(self):
        strict = self.cli("--strict", "--format", "json")
        self.assertEqual(strict.returncode, 1)
        broken = self.cli("--base", "not-a-revision")
        self.assertEqual(broken.returncode, 2)
        self.assertIn("testsignal: error:", broken.stderr)
        self.assertNotIn("Traceback", broken.stderr)


if __name__ == "__main__":
    unittest.main()
