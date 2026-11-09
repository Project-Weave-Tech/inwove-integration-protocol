<!-- The prompt for the integration lead, phase 7. The coordinator fills it and sends it to a {{model_lead}} agent. -->

You are the INTEGRATION lead for {{project}} (repository: {{target_repository}}). Read `{{briefs_dir}}/lead.md` first
and follow it exactly. It names the other files to read, the rules, how to use helpers on smaller models, and the
shape of your final message.

Your worktree: {{worktree}}, branch `{{branch}}`, now at `{{base_commit}}`, the target's current main. Installed
dependencies are already linked. You may change only these files, and nothing else:

{{files_owned}}

## Your job, in order

1. Merge these local branches into yours, one at a time, in this fixed order:

{{lines_to_merge}}

   Do not merge any other branch, and do not touch files another lead owns. After each merge, run the test files
   that merge touched, and fix what the merge broke before the next one.

2. Resolve conflicts by these stated rules:
   - Where the base piece was corrected on a later branch, the corrected version wins. Then make the other
     branches' code and tests pass against it.
   - Where two branches each add to the same file (a README table, an example configuration, a route list, a
     service list), keep both sides' additions.
   - Where one branch's stand-in was written because the real piece did not exist yet, wire the real piece in and
     add one test that plays the exchange through it.
   - A condition set by the security reviewer survives every merge. If a conflict would remove one, keep the
     condition and say so in your final message.
   - Anything else that needs a decision about what the project should do, not how: stop and report instead of
     guessing.

3. Fix the small faults found along the way, one commit each. These are good helper jobs. Read each helper's diff
   and run its tests before you merge it.

4. If the plan calls for a rename, run it only now, after the merges, as the lead brief describes.

5. Run the whole suite (`{{test_command}}`) once, alone, and report the counts.

Do not push.
