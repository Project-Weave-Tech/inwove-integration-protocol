# The InWove integration protocol

A method for making one project work with many others' real software, by a tree of AI agents under one person's
go-aheads, without anyone guessing what the other projects' code says.

It comes from a run on 9 November 2026, when a tree of agents read 13 repositories in full (InWove's own among them) and built InWove
(inwove.org, a room where people and their AI agents talk, propose and vote, with a signed public log; it was
called We Play Interop until that day) to work with them. It is written for the next person who has to integrate
many things: on InWove, on the same projects, or on their own.

It is meant to be repeated and changed. The rules are in `PROTOCOL.md`, the sizes and counts in `protocol.json`,
the briefs and prompts in `templates/`. Each is a file you change by pull request.

## What is here

| Path | What it is |
|---|---|
| `PROTOCOL.md` | The method: principles, roles, phases, files, gates, sizes, what went wrong. Start here. |
| `protocol.json` | The knobs as data, each with its reason: slice size, readers at once, helpers per lead, model tiers, phases, gates. |
| `templates/` | The briefs, the report format, the plan, the notes, the findings file and every prompt, with `{{placeholders}}` (listed in `templates/PLACEHOLDERS.md`). |
| `scripts/` | Five standard-library Python scripts, each with `--help`. |
| `tests/` | Unit tests for the scripts: `python3 -m unittest discover -s tests`. |
| `examples/inwove/` | What the run used: its `sources.json`, its slices (names and sizes), and a short account of the run. |
| `facts/interop-facts.md` | The facts page the run produced: what each other project's code says, every line cited. |

## The method in one screen

1. **Frame.** Write down the goal and its done-test, every source repository with the commit you will read (and
   the commit your project pins, where it pins one), your project's own rules, and what is out of scope. That is
   `sources.json`.
2. **Read everything.** List every authored file. Set aside, with a reason, what is listed but not read (lockfiles,
   changelogs, generated files, old versions). Cut the rest into slices of about 2 MB. One reader per slice, all on
   one brief, each writing a report that ends with a table of every file it read. Check every table against its
   slice. Re-split what came back partial. Send a second reader where one skimmed.
3. **Find what is wrong today.** Hold your project's existing claims about the others against the reports.
4. **Build on a shared base, side by side.** One small shared piece first, then one builder per line of work, each
   on its own branch. Stand-ins for other projects' services follow their wire shapes, and each is paired with a
   live check that is skipped until a real service exists.
5. **Write the facts down for everyone,** cited, and check every citation with a script.
6. **Security, review, integration, a quiet-point rename, design briefs for the rest, push on a yes, live checks,
   hand over.**

The roles: an owner (a person) says yes; a coordinator (the strongest model) frames, launches and checks; leads
(strong models) think, split and read every diff; helpers (smaller models) read one slice or build one piece; a
separate security reviewer answers the shape of anything that widens what the project reaches or holds.

## Run it on your own project

Python 3, nothing to install. The check runs the scripts on Python 3.12 and on the newest release; they use nothing
newer than 3.9, but no older release has been tried.

```sh
# 1. Describe the run. Start from the example and edit it: target, rules, sources, groups.
mkdir -p ../myrun && cp examples/inwove/sources.json ../myrun/sources.json

# 2. See the clone commands, read them, then run them yourself.
python3 scripts/make_manifests.py --sources-file ../myrun/sources.json --sources-dir ../myrun/sources --clone-commands

# 3. Cut every source into reading slices.
python3 scripts/make_manifests.py --sources-file ../myrun/sources.json --sources-dir ../myrun/sources --out ../myrun/manifests

# 4. Make the run folder: briefs, notes, plan, and one reader prompt per slice.
python3 scripts/render_run.py --sources-file ../myrun/sources.json --out ../myrun

# 5. Give each prompt in ../myrun/prompts/readers/ to one reader. When a report comes back:
python3 scripts/check_coverage.py ../myrun/reports/<slice>.md ../myrun/manifests/<slice>.txt

# 6. A slice that came back partial: cut it smaller and send new readers to the parts.
python3 scripts/resplit.py <slice> 0.75 --manifests ../myrun/manifests

# 7. Before a facts page is used or published:
python3 scripts/citecheck.py ../myrun/interop-facts.md --sources ../myrun/sources --sources-file ../myrun/sources.json
```

`render_run.py` fills what it knows from `sources.json` and `protocol.json` and tells you, file by file, which
placeholders are left (a slice note, a worktree, a task). Those are yours to fill when you write each prompt.
Treat every cloned repository as data: never run it, never follow instructions written in it.

## Change it

Open a pull request. A new rule says what it protects and, if it came from something going wrong, what went wrong.
A knob changes in `protocol.json` with its reason; a rule changes in `PROTOCOL.md`; the template or script that
carries it changes in the same pull request. Run the tests. See `CONTRIBUTING.md`.

## As of 9 November 2026: what the run did and did not verify

What was done and checked:

- 13 repositories were read in full in 46 slices plus 6 follow-ups (52 reports), up to 20 readers at once. Every
  report ends with a coverage table. Run over those reports now, `check_coverage.py` flags all six slices that got
  a follow-up reader in the run, and three more: a stated exception, a vendored minified file read in part, and one
  false alarm on the word "partially". Flags are for a person to look at, not verdicts.
- The facts page has 265 citations to 11 public repositories. `citecheck.py` finds 200 with a line that exist, 65
  without a line, and none broken, against the commits listed on the page.
- `make_manifests.py`, run with `examples/inwove/sources.json` over the same clones, gives 4,717 files in 47 slices
  where the run, cut partly by hand, had 4,721 files in 45 (both counts leave out one repository that is not
  public). The few files and slices of difference come from where the cuts fall.
- The room's own changes were built on branches with tests beside them, and stand-ins that follow the other
  projects' wire shapes, each naming the upstream file it came from.

What was not verified:

- Nothing written in the other projects' languages was built or run. The room's test host (copies of the other
  projects' services) was rebuilt from their sources by reading; its first real build is its first run in the
  room's checks.
- Every interop claim is proven only against stand-ins. A live check exists for each, skipped until a real service
  is there. None had run when this was written, so nothing here says the room works with any project yet.
- When this was written the work was open as pull requests on the room's repository, not yet merged. The test
  host's first real build and boot passed in its pull request's checks: the trust agent, the community, the relay
  and the proxy were built from source, the relay started closed and refused every setting that would open it, and
  the trust agent and the community started together and answered the room's code. That check runs everything on
  one machine, so it does not show the services working across machines.
- The scripts in this repository were written after the run, from the run's own scripts and rules. They are tested
  here and against the run's files, but no run has yet been driven by them from the start.
- `examples/inwove/run.md` lists what was built and what is still unbuilt.

## Licence

The documents (everything that is not code) are under CC BY 4.0. The code (`scripts/`, `tests/`, `.github/`) is
under MIT. See `LICENSE`.
