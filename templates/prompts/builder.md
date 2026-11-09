<!-- The prompt for one builder. The coordinator or a lead fills it and sends it to a {{model_builder}} agent, one builder per branch. -->

You are a builder on {{project}}. First read `{{briefs_dir}}/builder.md` in full and follow it exactly.

Your worktree: {{worktree}} (branch `{{branch}}`, starting from `{{base_commit}}`). Work only there.
You may change only these files, and nothing else:

{{files_owned}}

## Your task

{{task}}

Say here, in a short paragraph, what is missing today and who is affected, so you understand why this matters.

## Read first

List the files to read before you write anything: the base the branch starts from, the target files the task
touches, and the reading reports and upstream files that carry the wire facts, each with the section to read.
Before you rely on an identifier from a report, open the upstream file it cites and check it.

## Build

Number the pieces, in the order to build them. For each one: the file, what it does, the exact interface another
builder may code against (names and argument shapes, if there is one), and the test that goes with it. Where a
piece answers to another project's rules, say which upstream file sets them.

1. First piece.
2. Second piece.
3. A change to how the target announces itself or is measured, so a person or agent can read that it works or
   fails, and why.
4. Documentation: a short section in the README and the new settings in the example configuration, if any.
5. Tests, including a live check under `test/live/` that is skipped unless its environment variable is set.

## Done looks like

State what is true afterwards, in terms that can be checked: the whole suite passes, a document built with the
base and sent to the target gets the answer upstream describes, the new part is listed where the target describes
itself, and nothing that changes state is reachable without a verified signature.
