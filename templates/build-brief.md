<!-- One build brief, written by a design lead as {{briefs_dir}}/{{brief_number}}-{{brief_name}}.md and sized for one {{model_builder}} session. -->

# {{brief_number}}-{{brief_name}}

Read `{{briefs_dir}}/builder.md` first and follow it. It holds the target's rules and how to commit.

## Goal

Two sentences: what a person or another project can do after this build that they could not do before, and the
single test that shows it.

## Files to add or change

- `path/to/new-file` (new): what it owns.
- `path/to/existing-file` (change): the part that changes.

If a file is on the needs-a-person list, say so here and say why it cannot be avoided.

## Wire facts

Every identifier the build relies on, each with its upstream source. Open each upstream file yourself before you
use it. If a fact cannot be confirmed, say "not stated" and stop that part.

| Fact (quoted exactly) | Upstream source |
|---|---|
| the type address, route, header, field or version | `owner/repo: path:line` |

## Steps

1. The first small step, and the test that goes with it.
2. The next step.
3. Keep each step small enough to commit on its own.

## Tests

- A stand-in for the other project's service that follows the upstream shapes. For each shape, a comment names the
  file it was read from. It proves the target agrees with itself; it does not prove interop.
- A live check under `test/live/`, skipped unless its environment variable is set. Name the variable, and what the
  real thing must be (a service address, an identifier, a credential file).
- Run only the test files you touch while working; the whole suite once, alone, at the end.

## What a person or agent can read to see it working or failing

Name the place (an information route, a view, a log line of counts and reasons) and what it shows. It must say why
something failed, not only that it did. It holds no content: counts, sizes, outcomes and reasons only.

## What not to touch

Files and behaviour outside this build, including other builders' files and anything on the needs-a-person list
that this build does not need.

## What is left for a person to decide

Questions this build leaves open, each with what the answers would change. Do not decide them in code.
