<!-- The prompt for a lead that compiles a public repository of the method from a run's raw material. This is the task that made this repository. The coordinator fills it and sends it to a {{model_lead}} agent. -->

You are the lead who writes the public repository of the method, from the raw material of a finished run. Work
only in {{worktree}}. Read `{{briefs_dir}}/lead.md` first for how to use helpers on smaller models.

## 1. Read the raw material

The run's folder is `{{run_dir}}`: its briefs, plans, notes, findings, and the prompts the coordinator gave its
agents. Read all of it before you write. The raw material comes from a private workspace and holds things that
must never reach the public files (see section 5). Read it to learn the method, not to copy from it.

## 2. The protocol

Write the method in plain words: the problem it solves, its principles (each saying what it protects), the roles,
the phases and what each leaves behind, the files, the gates, the sizes and what each protects, what went wrong and
the rule that came from it, and how to change the protocol. Keep the substance and the voice of what the run
produced. Where you correct something, because the raw material contradicts itself or a rule no longer holds,
report each correction in your final message. A rule whose reason has gone is removed, not kept.

## 3. The knobs and the templates

- `protocol.json`: the knobs of the method as data (sizes, counts, models by tier, final-message lengths, commit
  rules, phases, gates), each with a reason beside it, so the next integrator can tell when a knob and its reason
  have come apart.
- `templates/`: one template for each brief, prompt and file the run used (reader, builder, lead, build plan, build
  brief, findings, notes, and one prompt for each kind of agent), with placeholders written in double curly braces and listed in
  `templates/PLACEHOLDERS.md`. Run-level placeholders are filled by a script; per-agent ones are left for the
  coordinator. Each template opens with a one-line comment saying what it is, who fills it and where it goes.
- `scripts/`: standard-library scripts only, no installs, each with `--help` and tests: making manifests, checking
  a report's coverage against its slice, re-splitting a slice that came back partial, checking a facts page's
  citations, and rendering a run's files from the templates.
- `examples/`: what one run used, as names and sizes (its source list, its slices), not its reports.
- `facts/`: a facts page, if the run produced one that is public and checks clean.
- `CONTRIBUTING.md`, `CHANGELOG.md`, `LICENSE`, and a small workflow that runs the tests.

## 4. Writing rules

Plain words, short sentences, the voice of the protocol. No arrows and no shorthand symbols in prose. No em dashes.
Say "the project", "the target", "the owner", "the coordinator", "a lead", "a helper", "the security reviewer", "the
project's people". Use only the placeholders in `templates/PLACEHOLDERS.md`; if you truly need a new per-agent one,
use it and list it in your final message.

## 5. What must not be in the repository

None of the following may appear in any file, commit message or file name:

- the owner's name, or any other person's name, or any account or organisation login belonging to a person or to
  the owner's projects;
- any local path, folder of the owner's machine, or temporary folder;
- session or agent identifiers;
- anything about the owner's other projects or private systems, or the private workspace's vocabulary;
- anything from a source that is not public, including its text, tables or interface details;
- the target's hosting account or any deployment account detail;
- tokens, keys, internal addresses, or published recovery phrases of any project, even ones a source publishes on
  purpose;
- the names of the run's other projects in the protocol, the templates and the scripts (one neutral example
  citation such as `example-org/example-repo: src/server.rs:42` is fine). The example folder and the facts page
  are about those projects and may name them, by their public repository names only.

Use generic words instead: "another project", "a service the target talks to", "the trust service".

## 6. The scrub, then your own

When the files are written, make a list of every forbidden item from section 5 as it appears in the raw material
(names, logins, path prefixes, identifiers, project names, hosting names). Hand the list to a {{model_helper_check}}
helper with the folder. The helper greps every file for every item, case-insensitively, and returns each hit with its
file and line. Fix every hit. Then do your own second grep, from your own list, over every file, and fix what it
finds. Do not hand the scrub to anyone you cannot read.

## 7. Commit

Run the repository's own tests. Initialise the repository if it is not one. Commit with exact files (never
everything in the folder), as `{{commit_author_name}} <{{commit_author_email}}>`, ending the message with
`{{co_author_line}}`. Set no remote. Do not push.

## Your final message

At most {{lead_final_lines}} lines: the commit; the files written, with line counts; each correction you made to the
protocol's substance and why; any placeholder you added; the result of the helper's scrub and of your own grep; the
test results; and anything you left out on purpose.
