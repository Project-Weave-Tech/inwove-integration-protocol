"""Tests for scripts/check_coverage.py, on tiny reports and manifests in a temp folder."""
import contextlib
import importlib.util
import io
import os
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "check_coverage", os.path.join(HERE, "..", "scripts", "check_coverage.py"))
cc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cc)

MANIFEST = "10\towner_repo/src/a.rs\n20\towner_repo/src/b.rs\n"


def report(rows, heading="## Coverage"):
    body = "\n".join(rows)
    return ("# Report\n\nSome text.\n\n%s\n\n| File | Notes |\n|---|---|\n%s\n" % (heading, body))


class CheckCoverageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.mpath = os.path.join(self.tmp.name, "m.txt")
        self.rpath = os.path.join(self.tmp.name, "r.md")
        with open(self.mpath, "w") as f:
            f.write(MANIFEST)

    def check(self, text, *extra):
        with open(self.rpath, "w") as f:
            f.write(text)
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = cc.main([self.rpath, self.mpath] + list(extra))
        return code, out.getvalue()

    def test_full_coverage_passes(self):
        code, out = self.check(report([
            "| `owner_repo/src/a.rs` | read |", "| `owner_repo/src/b.rs` | read |"]))
        self.assertEqual(code, 0)
        self.assertIn("covered: 2 of 2", out)

    def test_missing_file_fails(self):
        code, out = self.check(report(["| `owner_repo/src/a.rs` | read |"]))
        self.assertEqual(code, 1)
        self.assertIn("owner_repo/src/b.rs", out)

    def test_flagged_row_fails_unless_allowed(self):
        text = report(["| `owner_repo/src/a.rs` | read |", "| `owner_repo/src/b.rs` | Partial: to line 400 |"])
        code, out = self.check(text)
        self.assertEqual(code, 1)
        self.assertIn("to line 400", out)
        self.assertEqual(self.check(text, "--allow-partial")[0], 0)

    def test_short_path_matches_by_suffix(self):
        code, _ = self.check(report(["| `src/a.rs` | read |", "| src/b.rs | read |"]))
        self.assertEqual(code, 0)

    def test_suffix_must_start_at_a_folder(self):
        code, out = self.check(report(["| `rc/a.rs` | read |", "| `src/b.rs` | read |"]))
        self.assertEqual(code, 1)
        self.assertIn("note:", out)
        self.assertIn("rc/a.rs", out)

    def test_no_coverage_section_exits_2(self):
        self.assertEqual(self.check("# Report\n\n| a | b |\n|---|---|\n| x | y |\n")[0], 2)

    def test_last_coverage_heading_wins(self):
        text = (report(["| `owner_repo/src/a.rs` | read |"]) + "\n### Coverage, second pass\n\n"
                "| File | Notes |\n|---|---|\n| `owner_repo/src/a.rs` | ok |\n| `owner_repo/src/b.rs` | ok |\n")
        self.assertEqual(self.check(text)[0], 0)

    def test_missing_file_is_usage_error(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cc.main([self.rpath + ".nope", self.mpath]), 2)


    def test_alias_defined_in_prose(self):
        text = ("# Report\n\n## Coverage\n\n`S/` = `owner_repo/src/`. All read.\n\n"
                "| # | File | Lines |\n|---|---|---|\n| 1 | S/a.rs | 1-9 |\n| 2 | S/b.rs | 1-4 |\n")
        code, out = self.check(text)
        self.assertEqual(code, 0, out)

    def test_several_coverage_sections_count_together(self):
        text = ("# Report\n\n## Coverage so far\n\n| File | Lines |\n|---|---|\n| `src/a.rs` | all |\n\n"
                "## Notes\n\ntext\n\n## Coverage so far (more)\n\n| File | Lines |\n|---|---|\n| `src/b.rs` | all |\n")
        code, out = self.check(text)
        self.assertEqual(code, 0, out)

    def test_name_without_dot_in_first_cell(self):
        with open(self.mpath, "w") as f:
            f.write("5\towner_repo/NOTICE\n")
        code, out = self.check(report(["| NOTICE | all |"]))
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
