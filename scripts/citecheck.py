#!/usr/bin/env python3
"""Check every citation in a markdown page against cloned sources.

A citation is written in backticks, like `owner/repo: path/to/file.py:10-20`.
The line part is optional. For each one this script looks in the clone of
that repository and says whether the file (or folder) exists, and whether
the cited lines are inside the file.

Where a repository's clone lives:
  1. a --map owner/repo=folder option (folder is inside the sources folder), else
  2. the "dir" of the matching source in a --sources-file, else
  3. the default, owner_repo.

The script only reads files. It never runs anything it finds.
Exit codes: 0 nothing broken and no clone missing, 1 otherwise, 2 usage error.
"""
import argparse
import json
import os
import re
import sys

# `owner/repo: path` or `owner/repo: path:12` or `owner/repo: path:12-20`
PATTERN = re.compile(
    r'`([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+): ([^`:]+?)(?::(\d+)(?:-(\d+))?)?`')


def load_dirs(sources_file):
    """Return {repo: dir} from a sources.json file."""
    with open(sources_file, encoding='utf8') as f:
        data = json.load(f)
    dirs = {}
    for s in data.get('sources', []):
        if s.get('repo') and s.get('dir'):
            dirs[s['repo']] = s['dir']
    return dirs


def count_lines(path):
    with open(path, encoding='utf8', errors='replace') as f:
        return sum(1 for _ in f)


def inside(root, target):
    """True when target is root itself or below it (symlinks resolved)."""
    root = os.path.realpath(root)
    target = os.path.realpath(target)
    return target == root or target.startswith(root + os.sep)


def check_page(page, text, src, dirs, totals, problems, no_clone):
    """Check one page's text; update totals, problems and no_clone."""
    for m in PATTERN.finditer(text):
        repo, path, a, b = m.groups()
        where = f'{page}:{text.count(chr(10), 0, m.start()) + 1}'
        folder = os.path.join(src, dirs.get(repo, repo.replace('/', '_')))
        if not os.path.isdir(folder):
            totals['noclone'] += 1
            no_clone.setdefault(repo, folder)
            continue
        d = os.path.join(folder, path)
        if not inside(folder, d):
            totals['bad'] += 1
            problems.add(f'{where}: OUTSIDE {repo}: {path}')
            continue
        if not os.path.exists(d):
            totals['bad'] += 1
            problems.add(f'{where}: MISSING {repo}: {path}')
            continue
        if a is None:
            totals['nolines'] += 1
            continue
        end = b if b is not None else a
        shown = f'{a}-{b}' if b is not None else a
        if os.path.isdir(d):
            totals['bad'] += 1
            problems.add(f'{where}: DIR WITH LINE {repo}: {path}:{shown}')
        elif int(end) < int(a):
            totals['bad'] += 1
            problems.add(f'{where}: BAD RANGE {repo}: {path}:{shown}')
        else:
            n = count_lines(d)
            if int(end) > n:
                totals['bad'] += 1
                problems.add(
                    f'{where}: PAST END {repo}: {path}:{shown} (file has {n})')
            else:
                totals['ok'] += 1


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__.split('\n\n')[0],
        epilog='example:\n  python3 scripts/citecheck.py report.md '
               '--sources sources --map owner/repo=my-clone\n'
               '  python3 scripts/citecheck.py a.md b.md --sources sources '
               '--sources-file sources.json',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('pages', nargs='+', metavar='PAGE',
                    help='markdown page(s) to check')
    ap.add_argument('--sources', required=True, metavar='DIR',
                    help='folder holding the clones')
    ap.add_argument('--map', action='append', default=[],
                    metavar='owner/repo=folder',
                    help='clone folder for a repository (repeatable)')
    ap.add_argument('--sources-file', metavar='sources.json',
                    help='read each source\'s "dir" for its "repo"')
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code not in (0, None) else 0

    dirs = {}
    try:
        if args.sources_file:
            dirs.update(load_dirs(args.sources_file))
    except (OSError, ValueError) as e:
        print(f'cannot read --sources-file: {e}', file=sys.stderr)
        return 2
    for item in args.map:
        repo, sep, folder = item.partition('=')
        if not sep or not repo or not folder:
            print(f'bad --map "{item}": use owner/repo=folder',
                  file=sys.stderr)
            return 2
        dirs[repo] = folder
    if not os.path.isdir(args.sources):
        print(f'no such sources folder: {args.sources}', file=sys.stderr)
        return 2

    totals = {'ok': 0, 'nolines': 0, 'bad': 0, 'noclone': 0}
    problems = set()
    no_clone = {}
    for page in args.pages:
        try:
            with open(page, encoding='utf8', errors='replace') as f:
                text = f.read()
        except OSError as e:
            print(f'cannot read page {page}: {e}', file=sys.stderr)
            return 2
        check_page(page, text, args.sources, dirs, totals, problems, no_clone)

    for p in sorted(problems):
        print(p)
    for repo in sorted(no_clone):
        print(f'NO CLONE {repo} (looked for {no_clone[repo]})')
    print(f'cites with a line that exist: {totals["ok"]}; '
          f'cites without a line: {totals["nolines"]}; '
          f'broken: {totals["bad"]}; '
          f'cites to repositories with no clone: {totals["noclone"]}')
    return 1 if totals['bad'] or no_clone else 0


if __name__ == '__main__':
    sys.exit(main())
