<!-- The coordinator's notes, kept in the run folder as notes.md from phase 0 on. Written by the coordinator only; leads and builders read it. -->

# Notes: {{run_name}}

**Re-read this after any loss of context.** It is the memory of the run. The summary in your head is not.

## The task, in the owner's words

Quote the owner. Then, below it, the goal and the done-test as written down in `sources.json`:

{{goal}}

{{done_test}}

Out of scope:

{{out_of_scope}}

## How the reading is run

- The brief: `{{briefs_dir}}/reader.md`. The report skeleton: `{{briefs_dir}}/report-format.md`.
- Manifests: `{{manifests_dir}}`, one per slice, made by `scripts/make_manifests.py`. Reports: `{{reports_dir}}`.
- The queue: which slices are launched, which are done, which came back partial and were re-split, which got a
  second reader. Keep it as a table: slice, state, report path, coverage checked (yes or no).
- At most {{readers_at_once}} readers at once.

## Pins

{{pins}}

Where the target pins another commit than the one read, say which commit the build uses and why.

## What is wrong today in the target

Phase 2. Each existing claim about another project in the target, held against a cited source.

| What the file says | What the source says | Where |
|---|---|---|
| `path/in/target:line`: the claim as written | the fact, quoted exactly | `owner/repo: path:line` |

## Facts from the reports that decide the build

Each fact with its citation, written by the coordinator after reading the reports. A builder relies on this list
only after opening the cited file.

1. The fact, quoted exactly. Source: `owner/repo: path:line`, from `{{reports_dir}}/<slice>.md`.
2. Where upstream contradicted an earlier report, say so and say which one the code follows.

## Decisions so far

Date, what was decided, who decided it (the owner, the security reviewer, the project's people, or the
coordinator), and what it changes.

## Progress log

One line each, with the time.

- <date and time>: what was launched, finished, merged or found.

## Stopped here

For a hand-over. What state every branch is in, what was running when work stopped, what to do first, and what to
leave alone. Then point at the plan file for the jobs.
