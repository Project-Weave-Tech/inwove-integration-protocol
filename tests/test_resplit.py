"""Tests for scripts/resplit.py, on a tiny manifest in a temp folder."""
import contextlib
import importlib.util
import io
import os
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "resplit", os.path.join(HERE, "..", "scripts", "resplit.py"))
rs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rs)

MB = 1024 * 1024


class ResplitTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.m = self.tmp.name
        # 12 files of 100 KB each: 1.2 MB in total
        self.rows = [(100 * 1024, "repo_a/dir/f%02d.txt" % i) for i in range(12)]
        self.write("big", self.rows)

    def write(self, name, rows):
        with open(os.path.join(self.m, name + ".txt"), "w") as f:
            f.write("".join("%d\t%s\n" % r for r in rows))

    def run_rs(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = rs.main(list(args) + ["--manifests", self.m])
        return code, out.getvalue()

    def read(self, name):
        with open(os.path.join(self.m, name)) as f:
            return [(int(a), b) for a, b in (l.rstrip("\n").split("\t", 1) for l in f if l.strip())]

    def test_parts_sum_to_original(self):
        code, _ = self.run_rs("big", "0.5")
        self.assertEqual(code, 0)
        joined = []
        for letter in "abc":
            joined += self.read("big.%s.txt" % letter)
        self.assertEqual(joined, self.rows)
        self.assertFalse(os.path.exists(os.path.join(self.m, "big.d.txt")))

    def test_sizes_near_equal(self):
        self.run_rs("big", "0.5")
        sizes = [sum(s for s, _ in self.read("big.%s.txt" % l)) for l in "abc"]
        self.assertLessEqual(max(sizes) - min(sizes), 100 * 1024 * 2)
        self.assertTrue(all(s <= 0.5 * MB * 1.1 for s in sizes))

    def test_names_and_original_kept(self):
        _, out = self.run_rs("big", "0.5")
        self.assertTrue(os.path.exists(os.path.join(self.m, "big.a.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.m, "big.b.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.m, "big.txt")))
        self.assertEqual(self.read("big.txt"), self.rows)
        self.assertIn("big.a: ", out)
        self.assertIn("f00.txt … ", out)

    def test_refuses_to_overwrite(self):
        self.assertEqual(self.run_rs("big", "0.5")[0], 0)
        self.assertEqual(self.run_rs("big", "0.5")[0], 2)
        self.assertEqual(self.run_rs("big", "0.5", "--force")[0], 0)

    def test_errors(self):
        self.assertEqual(self.run_rs("nope", "1")[0], 2)
        self.assertEqual(self.run_rs("big", "abc")[0], 2)
        self.assertEqual(self.run_rs("big", "0")[0], 2)

    def test_more_than_26_parts_refused(self):
        self.write("huge", [(1024, "repo_a/f%03d.txt" % i) for i in range(100)])
        code, _ = self.run_rs("huge", str(1024 * 3 / MB))  # about 34 parts
        self.assertEqual(code, 2)
        self.assertFalse(os.path.exists(os.path.join(self.m, "huge.a.txt")))


if __name__ == "__main__":
    unittest.main()
