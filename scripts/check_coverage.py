#!/usr/bin/env python3
"""Check a reader's report against its slice.

The report is markdown. Its coverage sections are the headings whose text
starts with "Coverage" (any level); all of them count. Each table row in it names a file in one
of its cells, usually in backticks (often the first, sometimes after a number).
A manifest path P is covered by a row path R when P == R or P ends with "/" + R
(readers often drop the folder prefix). A report may define a short prefix
anywhere, written like `S/` = `some/long/prefix/`; rows that start with `S/` are
read with the prefix put back. A short capital prefix the report never defines
is dropped and the rest matched by its tail.
A row is flagged when any cell holds a word that says the file was not fully
read (partial, unread, skim, and so on).

Exit codes: 0 every file covered and nothing flagged (flags are allowed with
--allow-partial), 1 not covered or flagged, 2 a usage problem.
"""
import argparse
import re
import sys

FLAGS = ["partial", "unread", "not read", "grep", "skim", "skipped", "could not", "to line"]
HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")


ALIAS = re.compile(r"`?\b([A-Z][A-Za-z]{0,3})/`?\s*=\s*`([^`\s]+)`")
SHORT = re.compile(r"^[A-Z]{1,3}/")


def coverage_rows(text):
    """Return the table rows (lists of cells) of every Coverage section, or None.

    Readers who append as they go often write several ("Coverage so far"), so
    all of them count. Short prefixes such as `S/` = `a/long/prefix/` are
    collected from the whole report and put back in each row.
    """
    lines = text.splitlines()
    aliases = {}
    for a, full in ALIAS.findall(text):
        aliases[a + "/"] = full if full.endswith("/") else full + "/"
    starts = []
    for i, line in enumerate(lines):
        m = HEADING.match(line)
        if m and m.group(2).lower().startswith("coverage"):
            starts.append((i, len(m.group(1))))
    if not starts:
        return None
    rows = []
    for start, level in starts:
        in_table = False
        for line in lines[start + 1:]:
            m = HEADING.match(line)
            if m and len(m.group(1)) <= level:
                break
            st = line.strip()
            if not st.startswith("|"):
                in_table = False
                continue
            cells = [c.strip() for c in st.strip("|").split("|")]
            if not in_table:  # the first row of a table is its header
                in_table = True
                continue
            if all(re.fullmatch(r":?-+:?", c) for c in cells if c) and any(cells):
                continue  # the |---| line
            rows.append([expand(c, aliases) for c in cells])
    return rows


def expand(cell, aliases):
    """Put a header-defined prefix back: `S/x.rs` with S/ = a/b/ becomes `a/b/x.rs`."""
    for a, full in aliases.items():
        p = row_path(cell)
        if p.startswith(a):
            return cell.replace(p, full + p[len(a):], 1)
    p = row_path(cell)
    if SHORT.match(p):  # a short prefix the report never defined: match on the rest
        return cell.replace(p, p.split("/", 1)[1], 1)
    return cell


def row_path(cell):
    """The file named in a first cell: the backticked part if any, without ./"""
    m = re.search(r"`([^`]+)`", cell)
    p = (m.group(1) if m else cell).strip()
    return p[2:] if p.startswith("./") else p


def looks_like_path(cell):
    """True when a cell's text could name a file: no spaces, and a dot or a slash."""
    p = row_path(cell)
    return bool(p) and " " not in p and ("/" in p or "." in p) and not re.fullmatch(r"[\d.,\-]+", p)


def suffixes(path):
    """The path and every tail of it that starts after a slash."""
    out = [path]
    i = path.find("/")
    while i != -1:
        out.append(path[i + 1:])
        i = path.find("/", i + 1)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0] + " Exit 0 when every manifest file is covered "
                    "and nothing is flagged.",
        epilog="example:\n  python3 scripts/check_coverage.py reports/vti-docs.md manifests/vti-docs.txt",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report", help="the reader's report (markdown)")
    ap.add_argument("manifest", help="the slice manifest (bytes<TAB>path lines)")
    ap.add_argument("--allow-partial", action="store_true",
                    help="do not fail on flagged rows (missing files still fail)")
    args = ap.parse_args(argv)

    try:
        with open(args.report) as f:
            report = f.read()
        with open(args.manifest) as f:
            paths = [l.rstrip("\n").split("\t", 1)[-1] for l in f if l.strip()]
    except OSError as e:
        print("error: " + str(e), file=sys.stderr)
        return 2
    rows = coverage_rows(report)
    if rows is None:
        print("error: no heading starting with 'Coverage' in " + args.report, file=sys.stderr)
        return 2

    named = {}   # a path a row names: the row's index
    first = []   # the first path-like cell of each row, for the note on extra rows
    flagged = []
    for i, cells in enumerate(rows):
        cands = [row_path(c) for c in cells if looks_like_path(c)]
        # a name without a dot or a slash (NOTICE, Dockerfile) counts in the first cell that is not a number
        lead = next((row_path(c) for c in cells if c and not re.fullmatch(r"[\d.,\-]+", c)), None)
        if lead and " " not in lead and lead not in cands:
            cands.insert(0, lead)
        if not cands:
            continue
        first.append((i, cands[0]))
        for c in cands:
            named.setdefault(c, i)
        if any(w in c.lower() for c in cells for w in FLAGS):
            flagged.append("| " + " | ".join(cells) + " |")
    matched_rows, uncovered = set(), []
    for p in paths:
        hit = [named[s] for s in suffixes(p) if s in named]
        if hit:
            matched_rows.update(hit)
        else:
            uncovered.append(p)
    extra = [c for i, c in first if i not in matched_rows]

    print("covered: %d of %d files" % (len(paths) - len(uncovered), len(paths)))
    if uncovered:
        print("not covered:")
        for p in uncovered:
            print("  " + p)
    if flagged:
        print("flagged rows:")
        for r in flagged:
            print("  " + r)
    if extra:
        print("note: rows naming files not in the manifest:")
        for r in extra:
            print("  " + r)
    if uncovered or (flagged and not args.allow_partial):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
