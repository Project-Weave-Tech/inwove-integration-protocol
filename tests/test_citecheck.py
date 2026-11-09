"""Tests for scripts/citecheck.py (temp folders only)."""
import contextlib
import importlib.util
import io
import os
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location(
    'citecheck', os.path.join(ROOT, 'scripts', 'citecheck.py'))
citecheck = importlib.util.module_from_spec(spec)
spec.loader.exec_module(citecheck)


class CiteCheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.src = os.path.join(self.tmp.name, 'src')
        clone = os.path.join(self.src, 'example-org_example-repo')
        os.makedirs(os.path.join(clone, 'lib'))
        with open(os.path.join(clone, 'lib', 'a.py'), 'w') as f:
            f.write('one\ntwo\nthree\n')

    def run_check(self, text, *extra):
        page = os.path.join(self.tmp.name, 'page.md')
        with open(page, 'w') as f:
            f.write(text)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = citecheck.main([page, '--sources', self.src, *extra])
        return code, out.getvalue()

    def test_good_cite(self):
        code, out = self.run_check('`example-org/example-repo: lib/a.py:1-3`')
        self.assertEqual(code, 0)
        self.assertIn('exist: 1;', out)
        self.assertIn('broken: 0', out)

    def test_missing_file_with_page_line(self):
        code, out = self.run_check('x\n\n`example-org/example-repo: lib/b.py`')
        self.assertEqual(code, 1)
        self.assertIn('page.md:3: MISSING example-org/example-repo: lib/b.py', out)

    def test_past_end(self):
        code, out = self.run_check('`example-org/example-repo: lib/a.py:2-9`')
        self.assertEqual(code, 1)
        self.assertIn('PAST END', out)
        self.assertIn('file has 3', out)

    def test_directory_with_line(self):
        code, out = self.run_check('`example-org/example-repo: lib:4`')
        self.assertEqual(code, 1)
        self.assertIn('DIR WITH LINE', out)

    def test_no_line_cite_counted_apart(self):
        code, out = self.run_check('`example-org/example-repo: lib/a.py`')
        self.assertEqual(code, 0)
        self.assertIn('without a line: 1', out)
        self.assertIn('exist: 0', out)

    def test_missing_clone_reported_once(self):
        code, out = self.run_check(
            '`owner/gone: a.py:1` and `owner/gone: b.py`')
        self.assertEqual(code, 1)
        self.assertEqual(out.count('NO CLONE owner/gone'), 1)
        self.assertIn('broken: 0', out)
        self.assertIn('no clone: 2', out)

    def test_map_option(self):
        os.rename(os.path.join(self.src, 'example-org_example-repo'),
                  os.path.join(self.src, 'elsewhere'))
        code, out = self.run_check('`example-org/example-repo: lib/a.py:1`',
                                   '--map', 'example-org/example-repo=elsewhere')
        self.assertEqual(code, 0)
        self.assertIn('exist: 1;', out)

    def test_sources_file_dir(self):
        os.rename(os.path.join(self.src, 'example-org_example-repo'),
                  os.path.join(self.src, 'short'))
        sf = os.path.join(self.tmp.name, 'sources.json')
        with open(sf, 'w') as f:
            f.write('{"sources": [{"repo": "example-org/example-repo", '
                    '"dir": "short"}]}')
        code, _ = self.run_check('`example-org/example-repo: lib/a.py:1`',
                                 '--sources-file', sf)
        self.assertEqual(code, 0)

    def test_dotdot_refused(self):
        secret = os.path.join(self.src, 'secret.txt')
        with open(secret, 'w') as f:
            f.write('x\n')
        code, out = self.run_check(
            '`example-org/example-repo: ../secret.txt:1`')
        self.assertEqual(code, 1)
        self.assertIn('OUTSIDE', out)

    def test_bad_range(self):
        code, out = self.run_check('`example-org/example-repo: lib/a.py:3-1`')
        self.assertEqual(code, 1)
        self.assertIn('BAD RANGE', out)

    def test_usage_errors(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(citecheck.main(['--sources', self.src]), 2)
            self.assertEqual(
                citecheck.main(['nope.md', '--sources', self.src]), 2)


if __name__ == '__main__':
    unittest.main()
