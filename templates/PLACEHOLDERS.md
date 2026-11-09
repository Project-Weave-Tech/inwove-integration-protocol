# Placeholders

Templates hold `{{name}}` placeholders. `scripts/render_run.py` fills the run-level ones from `sources.json` and
`protocol.json`. It leaves the per-agent ones for the coordinator to fill when it writes each prompt, and lists them
for each file it renders. A placeholder name is lower case with underscores. Add a new one here, in the same pull
request as the template that uses it.

## Run-level (filled by `render_run.py`)

From `sources.json`, `run`:

| Name | What it becomes |
|---|---|
| `run_name` | `run.name` |
| `date` | `run.date` |
| `protocol_version` | `run.protocol_version`, else `protocol.json` `version` |
| `model_coordinator`, `model_lead`, `model_reader`, `model_builder`, `model_helper_build`, `model_helper_check` | `run.models.*`; if missing, the tier named in `protocol.json` `roles` |

From `sources.json`, `target`:

| Name | What it becomes |
|---|---|
| `project` | `target.name` |
| `project_description` | `target.description` |
| `project_url` | `target.url` |
| `target_repository` | `target.repository` (words, for example "the InWove room's repository") |
| `target_commit` | `target.commit_read` |
| `goal` | `target.goal` |
| `done_test` | `target.done_test` as a numbered list |
| `target_rules` | `target.rules` as a bulleted list |
| `needs_a_person` | `target.needs_a_person` as a bulleted list of code-quoted paths |
| `out_of_scope` | `target.out_of_scope` as a bulleted list |
| `commit_author_name`, `commit_author_email` | `target.commit_author.*` |
| `test_command`, `single_test_command` | `target.test_command`, `target.single_test_command` |
| `security_reviewer` | `target.security_reviewer`, else "the security reviewer": who answers the shape of a change that widens what the project reaches or holds |

From `sources.json`, `sources`:

| Name | What it becomes |
|---|---|
| `sources_list` | one bullet per source: its name, the commit read, its licence |
| `source_count` | how many sources |
| `pins` | one bullet per pin: the source, the pinned commit, the release if given, why |

From `protocol.json`:

| Name | What it becomes |
|---|---|
| `slice_max_mb`, `resplit_mb`, `readers_at_once` | `reading.*.value` |
| `report_every_files`, `report_every_kb` | `reading.report_every.files`, `.kb` |
| `helpers_per_lead` | `building.helpers_per_lead.value` |
| `reader_final_lines`, `builder_final_lines`, `lead_final_lines` | `final_message_lines.*` |
| `co_author_line` | `commits.co_author_line` |

Paths (from the command line and `run`):

| Name | What it becomes |
|---|---|
| `run_dir` | the `--out` folder |
| `sources_dir` | `run.sources_dir`, relative to the run folder unless absolute (default `sources`) |
| `manifests_dir`, `reports_dir`, `briefs_dir`, `scratch_dir` | `<run_dir>/manifests`, `/reports`, `/briefs`, `/scratch` |

## Per-agent (left for the coordinator)

| Name | Used in | What to put there |
|---|---|---|
| `slice`, `manifest_path`, `report_path` | reader prompt (`render_run.py` fills these per slice when manifests exist) | the slice's name and its two files |
| `slice_note` | reader prompt | what this slice is and what to look for, or a stated exception to the reading rule |
| `worktree`, `branch`, `base_commit` | builder and lead prompts | where the agent works |
| `task` | builder prompt | the job, with the files to read and what done looks like |
| `files_owned` | lead and builder prompts | the files this agent may change, and nothing else |
| `lead_name` | lead brief | integration, test host, review, design, or another |
| `findings_path` | review lead prompt | where `findings.md` is written |
| `lines_to_merge` | integration lead prompt | the branches, in merge order, with the rules for each conflict |
| `services` | test host lead prompt | the services the test host runs and the pinned sources for each |
| `branches_to_review` | review lead prompt | each branch with its diff range and how deeply to read it |
| `unbuilt` | design lead prompt | each piece not built yet, one line each |
| `brief_number`, `brief_name` | build brief | `NN` and a short name |
