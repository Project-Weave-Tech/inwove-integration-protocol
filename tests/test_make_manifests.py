"""Tests for scripts/make_manifests.py, on tiny fake repositories in a temp folder."""
import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "make_manifests", os.path.join(HERE, "..", "scripts", "make_manifests.py"))
mm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mm)

PROTOCOL = {"reading": {
    "slice_max_mb": {"value": 2.0},
    "skip_dirs": {"value": [".git", "node_modules"]},
    "binary_sniff_bytes": {"value": 8192},
    "index_only": {"rules": [
        {"category": "lockfile", "patterns": ["*.lock", "package-lock.json"], "reason": "generated"},
        {"category": "asset", "patterns": ["*.png"], "reason": "picture"},
    ]},
}}


def put(root, rel, data=b"x"):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data if isinstance(data, bytes) else data.encode())


class Case(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = self.tmp.name
        self.src = os.path.join(self.dir, "sources")
        self.out = os.path.join(self.dir, "out")
        self.sources_file = os.path.join(self.dir, "sources.json")
        self.protocol = os.path.join(self.dir, "protocol.json")
        with open(self.protocol, "w") as f:
            json.dump(PROTOCOL, f)

    def run_mm(self, sources, *extra):
        with open(self.sources_file, "w") as f:
            json.dump({"sources": sources}, f)
        argv = ["--sources-file", self.sources_file, "--sources-dir", self.src,
                "--out", self.out, "--protocol", self.protocol] + list(extra)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return mm.main(argv)

    def lines(self, name):
        with open(os.path.join(self.out, name)) as f:
            return [l.rstrip("\n") for l in f if l.strip()]

    def summary(self):
        with open(os.path.join(self.out, "_summary.json")) as f:
            return json.load(f)


class MakeManifestsTest(Case):
    def test_index_only_by_name_and_path(self):
        put(self.src, "owner_repo/a.py", "print(1)")
        put(self.src, "owner_repo/deep/yarn.lock", "x")
        put(self.src, "owner_repo/docs/gen/out.txt", "x")
        put(self.src, "owner_repo/logo.png", "x")
        src = {"repo": "owner/repo", "index_only": [
            {"category": "generated", "patterns": ["docs/gen/*"], "reason": "made by a tool"}]}
        self.assertEqual(self.run_mm([src]), 0)
        self.assertEqual(self.lines("repo.txt"), ["8\towner_repo/a.py"])
        idx = self.lines("_index_only.txt")
        self.assertIn("1\tlockfile\towner_repo/deep/yarn.lock", idx)
        self.assertIn("1\tgenerated\towner_repo/docs/gen/out.txt", idx)
        self.assertIn("1\tasset\towner_repo/logo.png", idx)

    def test_binary_and_skip_dirs_and_symlink(self):
        put(self.src, "owner_repo/data.bin", b"ab\0cd")
        put(self.src, "owner_repo/ok.txt", "hello")
        put(self.src, "owner_repo/node_modules/pkg/i.js", "x")
        put(self.src, "owner_repo/.git/config", "x")
        os.symlink(os.path.join(self.src, "owner_repo", "ok.txt"),
                   os.path.join(self.src, "owner_repo", "link.txt"))
        self.assertEqual(self.run_mm([{"repo": "owner/repo"}]), 0)
        self.assertEqual(self.lines("repo.txt"), ["5\towner_repo/ok.txt"])
        self.assertEqual(self.lines("_index_only.txt"), ["5\tbinary\towner_repo/data.bin"])

    def test_order_files_before_subfolders(self):
        put(self.src, "owner_repo/b.txt", "1")
        put(self.src, "owner_repo/a/z.txt", "1")
        put(self.src, "owner_repo/c.txt", "1")
        self.run_mm([{"repo": "owner/repo"}])
        paths = [l.split("\t")[1] for l in self.lines("repo.txt")]
        self.assertEqual(paths, ["owner_repo/b.txt", "owner_repo/c.txt", "owner_repo/a/z.txt"])

    def test_groups_and_rest(self):
        put(self.src, "example-org_example-repo/api/a.rs", "1")
        put(self.src, "example-org_example-repo/docs/d.md", "1")
        put(self.src, "example-org_example-repo/other/o.md", "1")
        src = {"repo": "example-org/example-repo", "slug": "ex", "groups": [
            {"name": "ex-api", "tier": 2, "paths": ["api/"]},
            {"name": "ex-docs", "tier": 1, "paths": ["docs/"]}]}
        self.run_mm([src])
        names = [s["slice"] for s in self.summary()]
        self.assertEqual(names, ["ex-docs", "ex-rest", "ex-api"])  # tier 1 first
        self.assertEqual(self.lines("ex-rest.txt"), ["1\texample-org_example-repo/other/o.md"])

    def test_no_groups_is_one_group_by_slug(self):
        put(self.src, "x_y/a.txt", "1")
        self.run_mm([{"repo": "x/y", "slug": "why"}])
        self.assertEqual([s["slice"] for s in self.summary()], ["why"])

    def test_shared_group_across_sources(self):
        put(self.src, "o_a/f1.txt", "11")
        put(self.src, "o_b/f2.txt", "22")
        g = [{"name": "apps", "tier": 1, "rest": True}]
        self.run_mm([{"repo": "o/a", "groups": g}, {"repo": "o/b", "groups": g}])
        self.assertEqual(self.lines("apps.txt"), ["2\to_a/f1.txt", "2\to_b/f2.txt"])
        self.assertEqual(len(self.summary()), 1)

    def test_splitting_sizes_and_names(self):
        for i in range(9):
            put(self.src, "o_a/f%d.txt" % i, "x" * 1000)
        # 9000 bytes in total, 3000 at most per slice: 3 parts
        self.assertEqual(self.run_mm([{"repo": "o/a"}], "--max-mb", str(3000 / 1048576)), 0)
        s = self.summary()
        self.assertEqual([x["slice"] for x in s], ["a-1of3", "a-2of3", "a-3of3"])
        self.assertEqual(sum(x["files"] for x in s), 9)
        self.assertEqual(sum(x["bytes"] for x in s), 9000)
        self.assertTrue(all(x["bytes"] <= 3300 for x in s))
        self.assertEqual(s[0]["first"], "o_a/f0.txt")
        self.assertEqual(s[2]["last"], "o_a/f8.txt")

    def test_summary_contents(self):
        put(self.src, "o_a/a.txt", "abc")
        put(self.src, "o_a/b.txt", "de")
        self.run_mm([{"repo": "o/a"}])
        self.assertEqual(self.summary(), [{"slice": "a", "group": "a", "tier": 1, "files": 2,
                                           "bytes": 5, "first": "o_a/a.txt", "last": "o_a/b.txt"}])

    def test_refuses_to_overwrite(self):
        put(self.src, "o_a/a.txt", "abc")
        self.assertEqual(self.run_mm([{"repo": "o/a"}]), 0)
        self.assertEqual(self.run_mm([{"repo": "o/a"}]), 2)
        self.assertEqual(self.run_mm([{"repo": "o/a"}], "--force"), 0)

    def test_missing_folder_warns_and_exits_2(self):
        put(self.src, "o_a/a.txt", "abc")
        self.assertEqual(self.run_mm([{"repo": "o/a"}, {"repo": "o/gone"}]), 2)
        self.assertTrue(os.path.exists(os.path.join(self.out, "a.txt")))

    def test_dir_field_names_the_folder(self):
        put(self.src, "custom/a.txt", "abc")
        self.assertEqual(self.run_mm([{"repo": None, "dir": "custom", "slug": "cu"}]), 0)
        self.assertEqual(self.lines("cu.txt"), ["3\tcustom/a.txt"])


    def test_clone_commands_print_and_write_nothing(self):
        with open(self.sources_file, "w") as f:
            json.dump({"sources": [{"repo": "owner/repo", "url": "https://example.org/owner/repo",
                                    "commit": "abc123"}, {"name": "target", "dir": "t"}]}, f)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = mm.main(["--sources-file", self.sources_file, "--sources-dir", "src",
                            "--protocol", self.protocol, "--clone-commands"])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("git clone --filter=blob:none https://example.org/owner/repo src/owner_repo", out)
        self.assertIn("checkout --detach abc123", out)
        self.assertIn("# target: no url", out)
        self.assertFalse(os.path.exists(self.out))


if __name__ == "__main__":
    unittest.main()
