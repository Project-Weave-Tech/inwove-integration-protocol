"""Tests for scripts/render_run.py (temp folders, plus this repository)."""
import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location(
    'render_run', os.path.join(ROOT, 'scripts', 'render_run.py'))
render_run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(render_run)

EXAMPLE = os.path.join(ROOT, 'examples', 'inwove', 'sources.json')
PROTOCOL = os.path.join(ROOT, 'protocol.json')
REAL_TEMPLATES = os.path.join(ROOT, 'templates')


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = render_run.main(argv)
    return code, out.getvalue(), err.getvalue()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(text)


def read(path):
    with open(path) as f:
        return f.read()


class ValuesTest(unittest.TestCase):
    def setUp(self):
        with open(EXAMPLE) as f:
            self.sources = json.load(f)
        with open(PROTOCOL) as f:
            self.protocol = json.load(f)
        self.values, self.missing = render_run.build_values(
            self.sources, self.protocol, 'runs/x')

    def test_example_values(self):
        v = self.values
        self.assertEqual(v['run_name'], 'inwove')
        self.assertEqual(v['project'], 'InWove')
        self.assertEqual(v['model_reader'], 'sonnet')
        self.assertEqual(v['slice_max_mb'], '2.0')
        self.assertEqual(v['report_every_kb'], '150')
        self.assertEqual(v['manifests_dir'], 'runs/x/manifests')
        self.assertEqual(self.missing, [])

    def test_lists_render_one_item_per_line(self):
        v = self.values
        self.assertTrue(v['done_test'].startswith('1. Private notebooks'))
        self.assertIn('\n2. ', v['done_test'])
        self.assertTrue(v['needs_a_person'].startswith('- `rules.json`\n'))
        self.assertTrue(v['target_rules'].startswith('- Plain JavaScript'))

    def test_sources_and_pins(self):
        v = self.values
        lines = v['sources_list'].split('\n')
        self.assertEqual(lines[0], '- InWove')  # no repo: its name
        self.assertIn('- `OpenVTC/verifiable-trust-infrastructure` at '
                      '`83ff0104e93347e0236b30555e2f0b85e2b031be` (Apache-2.0)',
                      lines)
        self.assertIn('pinned at `c6964c4612131089e1add0f47575894e1bd8a565`: ',
                      v['pins'])

    def test_model_falls_back_to_role_tier(self):
        del self.sources['run']['models']
        v, _ = render_run.build_values(self.sources, self.protocol, 'r')
        self.assertEqual(v['model_reader'], 'mid')
        self.assertEqual(v['model_helper_check'], 'small')

    def test_missing_value_reported(self):
        del self.sources['target']['goal']
        v, missing = render_run.build_values(self.sources, self.protocol, 'r')
        self.assertNotIn('goal', v)
        self.assertEqual(missing, ['goal'])

    def test_list_values_writes_nothing(self):
        code, out, _ = run(['--sources-file', EXAMPLE, '--list-values'])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)['project'], 'InWove')


class RenderTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        t = os.path.join(self.tmp.name, 'templates')
        self.templates = t
        write(os.path.join(t, 'PLACEHOLDERS.md'), 'vocab {{project}}\n')
        write(os.path.join(t, 'reader-brief.md'), 'Read for {{ project }}. {{slice_note}}\n')
        write(os.path.join(t, 'build-plan.md'), 'plan {{run_name}}\n')
        write(os.path.join(t, 'notes.md'), 'notes {{date}}\n')
        write(os.path.join(t, 'extra', 'other.md'), 'x {{goal}}\n')
        write(os.path.join(t, 'prompts', 'reader.md'),
              '{{slice}} {{manifest_path}} {{report_path}} {{project}}\n')
        write(os.path.join(t, 'prompts', 'lead.md'), '{{lead_name}} {{unknown_thing}}\n')
        self.out = os.path.join(self.tmp.name, 'run')

    def go(self, *extra):
        return run(['--sources-file', EXAMPLE, '--out', self.out,
                    '--templates', self.templates, *extra])

    def test_mapping_and_filling(self):
        code, stdout, _ = self.go()
        self.assertEqual(code, 0)
        o = self.out
        self.assertEqual(read(f'{o}/briefs/reader.md'),
                         'Read for InWove. {{slice_note}}\n')
        self.assertEqual(read(f'{o}/plan.md'), 'plan inwove\n')
        self.assertTrue(os.path.isfile(f'{o}/notes.md'))
        self.assertTrue(os.path.isfile(f'{o}/extra/other.md'))
        self.assertTrue(os.path.isfile(f'{o}/prompts/lead.md'))
        self.assertTrue(os.path.isfile(f'{o}/sources.json'))
        self.assertEqual(read(f'{o}/PLACEHOLDERS.md'), 'vocab {{project}}\n')
        for d in ('manifests', 'reports', 'briefs', 'scratch'):
            self.assertTrue(os.path.isdir(f'{o}/{d}'))
        self.assertFalse(os.path.exists(f'{o}/briefs/PLACEHOLDERS.md'))

    def test_unknown_placeholders_left_and_reported(self):
        code, stdout, _ = self.go()
        self.assertEqual(read(f'{self.out}/prompts/lead.md'),
                         '{{lead_name}} {{unknown_thing}}\n')
        line = [l for l in stdout.splitlines() if l.endswith('lead.md')
                or 'prompts/lead.md' in l][0]
        self.assertIn('lead_name', line)
        self.assertIn('unknown_thing', line)

    def test_reader_prompts_per_slice(self):
        write(f'{self.out}/manifests/_summary.json',
              json.dumps({'slices': [{'slice': 'part-a'}, 'part-b']}))
        # a file already there, so --force is needed
        code, _, _ = self.go('--force')
        self.assertEqual(code, 0)
        text = read(f'{self.out}/prompts/readers/part-a.md')
        self.assertEqual(text, f'part-a {self.out}/manifests/part-a.txt '
                               f'{self.out}/reports/part-a.md InWove\n')
        self.assertTrue(os.path.isfile(f'{self.out}/prompts/readers/part-b.md'))

    def test_refuses_without_force_and_never_deletes(self):
        keep = f'{self.out}/mine.txt'
        write(keep, 'keep')
        code, _, err = self.go()
        self.assertEqual(code, 2)
        self.assertIn('--force', err)
        self.assertFalse(os.path.exists(f'{self.out}/notes.md'))
        code, _, _ = self.go('--force')
        self.assertEqual(code, 0)
        self.assertEqual(read(keep), 'keep')

    def test_missing_run_level_value_exits_1(self):
        with open(EXAMPLE) as f:
            data = json.load(f)
        del data['target']['goal']
        sf = os.path.join(self.tmp.name, 's.json')
        write(sf, json.dumps(data))
        code, _, err = run(['--sources-file', sf, '--out', self.out,
                            '--templates', self.templates])
        self.assertEqual(code, 1)
        self.assertIn('goal', err)
        self.assertEqual(read(f'{self.out}/extra/other.md'), 'x {{goal}}\n')

    def test_no_out_is_usage_error(self):
        code, _, _ = run(['--sources-file', EXAMPLE])
        self.assertEqual(code, 2)

    @unittest.skipUnless(
        os.path.isfile(os.path.join(REAL_TEMPLATES, 'reader-brief.md')),
        'templates/reader-brief.md does not exist yet')
    def test_real_templates_render(self):
        out = os.path.join(self.tmp.name, 'real')
        code, _, err = run(['--sources-file', EXAMPLE, '--out', out])
        self.assertEqual(code, 0, err)
        self.assertTrue(os.path.isfile(f'{out}/briefs/reader.md'))


class PlaceholderListTest(unittest.TestCase):
    """Every placeholder a template uses is listed in templates/PLACEHOLDERS.md."""

    @unittest.skipUnless(os.path.isdir(REAL_TEMPLATES), 'no templates folder')
    def test_every_placeholder_is_documented(self):
        import re
        with open(os.path.join(REAL_TEMPLATES, 'PLACEHOLDERS.md')) as f:
            listed = set(re.findall(r'`([a-z0-9_]+)`', f.read()))
        used = {}
        for base, _, files in os.walk(REAL_TEMPLATES):
            for name in files:
                if name.endswith('.md') and name != 'PLACEHOLDERS.md':
                    with open(os.path.join(base, name)) as f:
                        for ph in re.findall(r'\{\{\s*([a-z0-9_]+)\s*\}\}', f.read()):
                            used.setdefault(ph, name)
        missing = {k: v for k, v in used.items() if k not in listed}
        self.assertEqual(missing, {}, 'placeholders used but not listed in PLACEHOLDERS.md')


if __name__ == '__main__':
    unittest.main()
