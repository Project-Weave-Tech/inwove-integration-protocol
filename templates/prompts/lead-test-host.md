<!-- The prompt for the test host lead. The coordinator fills it and sends it to a {{model_lead}} agent. Use it when the target runs real copies of other projects' services for testing. -->

You are the TEST HOST lead for {{project}} (repository: {{target_repository}}). Read `{{briefs_dir}}/lead.md` first and
follow it exactly. It names the other files to read, the rules, how to use helpers on smaller models, and the shape
of your final message.

Your worktree: {{worktree}}, branch `{{branch}}`, now at `{{base_commit}}`. Installed dependencies are already
linked. You own these files, and nothing else:

{{files_owned}}

Background: the test host runs real copies of other projects' services for the target to talk to. Its first files
guessed feature names and settings and could not build or boot. A local branch rebuilt them from the pinned
sources. If nothing in it has ever been built or run (for example because the machine the agents work on does not
run containers or compilers for other projects), its first run in the repository's checks is its first real test.

The services it runs, and the pinned sources for each:

{{services}}

Upstream at the pins is for reading only. Never build or run it.

## Your job

1. Merge the rebuilt branch into yours and reconcile it with whatever main gained since. Every condition set by the
   security reviewer on main must survive: for example body size caps, per-address request limits, paths limited to
   the methods they need, and refusals of insecure settings. Where the rebuilt files and main disagree, the
   reviewer's condition wins, and you say so.
2. Make the entrypoints refuse to start on an insecure setting in the file or in the environment, and export the
   explicit values they depend on. Check each cited line in the pinned source yourself first.
3. Check every identifier in the host's files against the pinned source, a second time, line by line, because
   nobody has. That means every feature name, binary name, flag, setup-file key, port, path and environment name in
   each container file, entrypoint, proxy template, setup script, compose file, smoke test and workflow. Each must
   be found in the pinned source. Split the check across helpers, one service each. Each helper returns a table
   with three columns: the claim, the source file and line, and a verdict (found, wrong, not found). Fix what is
   wrong. List what cannot be confirmed without a real build.
4. Make the first run of the repository's checks as likely to pass as reading allows. Read the workflow as the
   runner would: paths, contexts, build arguments, caching, time limits, and what it prints on failure so the next
   fix is quick. No secrets in it.
5. Every shell script must parse under `sh`, `bash` 3.2 and `dash` (`bash -n`, `sh -n`, `dash -n` where present).
   Run the host's own test file and whatever of its entrypoint tests runs on this machine.
6. If the plan calls for a rename, apply it to your files as the lead brief describes. Service names, volume names,
   setting names and addresses stay.
7. Run the whole suite (`{{test_command}}`) once, alone, and report the counts.

In your final message add a section for {{security_reviewer}}: every place this line differs from what the reviewer
has already read, each in one plain sentence.

Do not push.
