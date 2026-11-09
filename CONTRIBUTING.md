# Contributing

This repository holds a method, and the method is meant to change. Every change goes through a pull request.

## What a change looks like

- **A new rule** goes in `PROTOCOL.md`. It says what it protects. If it came from something going wrong, add a row
  to the table in section 8: what happened, and the rule now.
- **A changed size or count** goes in `protocol.json`, with its reason updated beside it. If the evidence for the
  old value came from a run, say what your run showed instead.
- **A rule whose reason no longer holds** is removed, not kept "just in case".
- **The template or script that carries a rule changes in the same pull request** as the rule.
- **A new placeholder** is listed in `templates/PLACEHOLDERS.md` in the same pull request as the template that uses
  it. A test checks this.
- **Bump the version** in `protocol.json` and add a `CHANGELOG.md` entry when the phases or the gates change.

## Rules for the files

- Plain words, short sentences. No arrows or shorthand symbols in prose. No invented labels.
- No personal names, account names, local paths, tokens, keys or private addresses in any file, example, test or
  commit message. Name projects and organisations, never people.
- Nothing from a source that is not public.
- Scripts use the Python standard library only, run on Python 3.9 or newer, have `--help`, and never run code
  from the repositories they read.

## Before you open the pull request

```sh
python3 -m unittest discover -s tests
for s in scripts/*.py; do python3 "$s" --help > /dev/null || echo "broken: $s"; done
```

If you change the facts page, run `scripts/citecheck.py` on it against clones at the commits it lists, and say the
result in the pull request.

## Reporting a run

If you ran the method on your own project, a pull request that adds `examples/<your-project>/` (its
`sources.json`, its slices as names and sizes, and a short account of what was found and built) helps the next
person most. Leave out the reports themselves if they hold anything that is not yours to publish.
