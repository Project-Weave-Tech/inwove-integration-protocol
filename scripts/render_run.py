#!/usr/bin/env python3
"""Make a run folder from the templates.

Reads sources.json (this run) and protocol.json (the method's knobs), builds
the run-level values listed in templates/PLACEHOLDERS.md, and renders every
markdown template into the run folder, replacing {{name}} wherever the name is
a run-level value. Every other placeholder is left as it is: those are the
per-agent ones the coordinator fills later. If manifests/_summary.json already
exists in the run folder, one reader prompt per slice is written too.

_summary.json may be a list of slices, or an object with a "slices" list (or
an object whose keys are the slices). A slice is a name, or an object with a
"slice" or "name" field.

Exit codes: 0 done, 1 a run-level value could not be filled, 2 usage error.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Where each template goes in the run folder. A template not listed here
# keeps its relative path (templates/prompts/x.md -> <run>/prompts/x.md).
OUTPUT_MAP = {
    'reader-brief.md': 'briefs/reader.md',
    'builder-brief.md': 'briefs/builder.md',
    'lead-brief.md': 'briefs/lead.md',
    'report-format.md': 'briefs/report-format.md',
    'build-brief.md': 'briefs/build-brief.md',
    'notes.md': 'notes.md',
    'build-plan.md': 'plan.md',
    'findings.md': 'findings.md',
}
SKIP = 'PLACEHOLDERS.md'  # copied unchanged
READER_PROMPT = 'prompts/reader.md'
EMPTY_DIRS = ('manifests', 'reports', 'briefs', 'scratch')
PLACEHOLDER = re.compile(r'\{\{\s*([a-z0-9_]+)\s*\}\}')
MODEL_KEYS = {  # value name -> (run.models key, protocol.json roles key)
    'model_coordinator': ('coordinator', 'coordinator'),
    'model_lead': ('lead', 'lead'),
    'model_reader': ('reader', 'reader'),
    'model_builder': ('builder', 'builder'),
    'model_helper_build': ('helper_build', 'helper'),
    'model_helper_check': ('helper_check', 'checker'),
}


def dig(data, *keys):
    """Follow keys into nested dicts; None when any step is missing."""
    for k in keys:
        if not isinstance(data, dict) or k not in data:
            return None
        data = data[k]
    return data


def bullets(items):
    return '\n'.join(f'- {i}' for i in items)


def text_of(v):
    if isinstance(v, float) and v == int(v):
        return str(v)  # 2.0 stays "2.0"
    return str(v)


def source_line(s):
    if s.get('repo'):
        return f'`{s["repo"]}` at `{s.get("commit", "?")}` ({s.get("licence", "?")})'
    return s.get('name', '?')


def pin_lines(sources):
    out = []
    for s in sources:
        label = f'`{s["repo"]}`' if s.get('repo') else s.get('name', '?')
        for p in s.get('pins', []):
            rel = f' ({p["release"]})' if p.get('release') else ''
            out.append(f'{label} pinned at `{p.get("commit", "?")}`{rel}: '
                       f'{p.get("why", "")}')
    return out


def build_values(sources, protocol, run_dir):
    """Return (values, missing): run-level values and names that had none."""
    v = {}
    run = sources.get('run', {})
    tgt = sources.get('target', {})
    srcs = sources.get('sources', [])

    def put(name, value):
        if value is not None:
            v[name] = value if isinstance(value, str) else text_of(value)

    put('run_name', run.get('name'))
    put('date', run.get('date'))
    put('protocol_version', run.get('protocol_version') or protocol.get('version'))
    for name, (mkey, rkey) in MODEL_KEYS.items():
        put(name, dig(run, 'models', mkey) or dig(protocol, 'roles', rkey, 'tier'))

    for name, key in [('project', 'name'), ('project_description', 'description'),
                      ('project_url', 'url'), ('target_repository', 'repository'),
                      ('target_commit', 'commit_read'), ('goal', 'goal'),
                      ('test_command', 'test_command'),
                      ('single_test_command', 'single_test_command')]:
        put(name, tgt.get(key))
    put('security_reviewer', tgt.get('security_reviewer') or 'the security reviewer')
    put('commit_author_name', dig(tgt, 'commit_author', 'name'))
    put('commit_author_email', dig(tgt, 'commit_author', 'email'))
    if isinstance(tgt.get('done_test'), list):
        put('done_test', '\n'.join(f'{i}. {t}' for i, t in enumerate(tgt['done_test'], 1)))
    if isinstance(tgt.get('rules'), list):
        put('target_rules', bullets(tgt['rules']))
    if isinstance(tgt.get('needs_a_person'), list):
        put('needs_a_person', bullets(f'`{p}`' for p in tgt['needs_a_person']))
    if isinstance(tgt.get('out_of_scope'), list):
        put('out_of_scope', bullets(tgt['out_of_scope']))

    if 'sources' in sources:
        put('sources_list', bullets(source_line(s) for s in srcs))
        put('source_count', len(srcs))
        put('pins', bullets(pin_lines(srcs)))

    for name, path in [('slice_max_mb', ('reading', 'slice_max_mb', 'value')),
                       ('resplit_mb', ('reading', 'resplit_mb', 'value')),
                       ('readers_at_once', ('reading', 'readers_at_once', 'value')),
                       ('report_every_files', ('reading', 'report_every', 'files')),
                       ('report_every_kb', ('reading', 'report_every', 'kb')),
                       ('helpers_per_lead', ('building', 'helpers_per_lead', 'value')),
                       ('reader_final_lines', ('final_message_lines', 'reader')),
                       ('builder_final_lines', ('final_message_lines', 'builder')),
                       ('lead_final_lines', ('final_message_lines', 'lead')),
                       ('co_author_line', ('commits', 'co_author_line'))]:
        put(name, dig(protocol, *path))

    put('run_dir', run_dir)
    sdir = run.get('sources_dir', 'sources')
    if not os.path.isabs(sdir):  # relative to the run folder, as PLACEHOLDERS.md says
        sdir = f'{run_dir}/{sdir}'
    put('sources_dir', sdir)
    for d in ('manifests', 'reports', 'briefs', 'scratch'):
        put(f'{d}_dir', f'{run_dir}/{d}')

    wanted = ['run_name', 'date', 'protocol_version', *MODEL_KEYS, 'project',
              'project_description', 'project_url', 'target_repository',
              'target_commit', 'goal', 'done_test', 'target_rules',
              'needs_a_person', 'out_of_scope', 'commit_author_name',
              'commit_author_email', 'test_command', 'single_test_command',
              'sources_list', 'source_count', 'pins', 'slice_max_mb',
              'resplit_mb', 'readers_at_once', 'report_every_files',
              'report_every_kb', 'helpers_per_lead', 'reader_final_lines',
              'builder_final_lines', 'lead_final_lines', 'co_author_line',
              'run_dir', 'sources_dir', 'manifests_dir', 'reports_dir',
              'briefs_dir', 'scratch_dir']
    return v, [n for n in wanted if n not in v]


def fill(text, values):
    """Replace known {{name}}; leave every other placeholder untouched."""
    return PLACEHOLDER.sub(lambda m: values.get(m.group(1), m.group(0)), text)


def unfilled(text):
    return sorted(set(PLACEHOLDER.findall(text)))


def read_slices(summary_path):
    with open(summary_path, encoding='utf8') as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = data['slices'] if isinstance(data.get('slices'), list) else list(data)
    names = []
    for s in data:
        if isinstance(s, dict):
            s = s.get('slice') or s.get('name')
        if isinstance(s, str):
            names.append(s)
    return names


def has_files(folder):
    """True when the folder holds files, not counting manifests/ and the clones,
    which make_manifests.py and git put there before the first render, and
    the run's own sources.json."""
    skip = {os.path.join(folder, 'manifests'), os.path.join(folder, 'sources')}
    for base, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if os.path.join(base, d) not in skip]
        if base == folder:
            files = [f for f in files if f != 'sources.json']  # the run's own input
        if files:
            return True
    return False


def write(path, text, written):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf8', newline='') as f:
        f.write(text)
    written.append((path, unfilled(text)))


def main(argv=None):
    ap = argparse.ArgumentParser(
        description='Make a run folder from the templates, filling the '
                    'run-level placeholders from sources.json and protocol.json.',
        epilog='example:\n  python3 scripts/render_run.py '
               '--sources-file examples/inwove/sources.json --out runs/first',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--sources-file', required=True, metavar='sources.json')
    ap.add_argument('--out', metavar='RUN_DIR',
                    help='the run folder to make (required unless --list-values)')
    ap.add_argument('--protocol', default=os.path.join(ROOT, 'protocol.json'))
    ap.add_argument('--templates', default=os.path.join(ROOT, 'templates'))
    ap.add_argument('--force', action='store_true',
                    help='write into a folder that already holds files '
                         '(overwrites what it renders, deletes nothing)')
    ap.add_argument('--list-values', action='store_true',
                    help='print the run-level values as JSON and write nothing')
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code not in (0, None) else 0
    if not args.list_values and not args.out:
        print('--out is required (unless --list-values)', file=sys.stderr)
        return 2
    try:
        with open(args.sources_file, encoding='utf8') as f:
            sources = json.load(f)
        with open(args.protocol, encoding='utf8') as f:
            protocol = json.load(f)
    except (OSError, ValueError) as e:
        print(f'cannot read input: {e}', file=sys.stderr)
        return 2

    run_dir = (args.out or '').rstrip('/') or '.'
    values, missing = build_values(sources, protocol, run_dir)
    if args.list_values:
        print(json.dumps(values, indent=2, ensure_ascii=False))
        return 1 if missing else 0
    if not os.path.isdir(args.templates):
        print(f'no such templates folder: {args.templates}', file=sys.stderr)
        return 2
    if os.path.isdir(run_dir) and has_files(run_dir) and not args.force:
        print(f'{run_dir} already holds files; use --force to overwrite '
              'what is rendered (nothing is deleted)', file=sys.stderr)
        return 2

    written = []
    for d in EMPTY_DIRS:
        os.makedirs(os.path.join(run_dir, d), exist_ok=True)
    for base, _, files in sorted(os.walk(args.templates)):
        for name in sorted(files):
            if not name.endswith('.md'):
                continue
            rel = os.path.relpath(os.path.join(base, name), args.templates)
            rel = rel.replace(os.sep, '/')
            with open(os.path.join(base, name), encoding='utf8', newline='') as f:
                text = f.read()
            if rel == SKIP:
                write(os.path.join(run_dir, SKIP), text, written)
                written[-1] = (written[-1][0], [])  # its placeholders are examples, not gaps
                continue
            write(os.path.join(run_dir, OUTPUT_MAP.get(rel, rel)),
                  fill(text, values), written)
    with open(args.sources_file, encoding='utf8', newline='') as f:
        write(os.path.join(run_dir, 'sources.json'), f.read(), written)

    summary = os.path.join(run_dir, 'manifests', '_summary.json')
    reader = os.path.join(args.templates, *READER_PROMPT.split('/'))
    if os.path.isfile(summary) and os.path.isfile(reader):
        with open(reader, encoding='utf8', newline='') as f:
            tpl = f.read()
        try:
            slices = read_slices(summary)
        except (OSError, ValueError, KeyError) as e:
            print(f'cannot read {summary}: {e}', file=sys.stderr)
            return 2
        for s in slices:
            if not re.fullmatch(r'[A-Za-z0-9_.-]+', s) or s.startswith('.'):
                print(f'skipped slice with an unsafe name: {s!r}', file=sys.stderr)
                continue
            v = dict(values, slice=s,
                     manifest_path=f'{run_dir}/manifests/{s}.txt',
                     report_path=f'{run_dir}/reports/{s}.md')
            write(os.path.join(run_dir, 'prompts', 'readers', f'{s}.md'),
                  fill(tpl, v), written)

    for path, left in written:
        extra = '  still to fill: ' + ', '.join(left) if left else ''
        print(f'wrote {path}{extra}')
    if missing:
        print('could not fill run-level values: ' + ', '.join(missing),
              file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
