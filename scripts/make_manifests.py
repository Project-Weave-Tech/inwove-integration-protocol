#!/usr/bin/env python3
"""List every authored file of every source repository and split the list into reading slices.

Phase 1 of the protocol. Each source in sources.json is cloned at
<sources-dir>/<dir>. The script walks it, sets aside what is listed but not
read line by line (generated files, assets, binaries), sorts the rest into
groups, and cuts each group into slices small enough for one reader to finish.

It writes, into the output folder:
  <slice>.txt        one line per file: bytes, a tab, the path (from the sources dir)
  _index_only.txt    bytes, category, path, for files that are listed but not read
  _summary.json      one entry per slice: slice, group, tier, files, bytes, first, last

Exit codes: 0 done, 2 a usage problem or a source folder that was missing.
"""
import argparse
import fnmatch
import json
import math
import os
import sys

MB = 1024 * 1024
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def source_dir_name(src):
    """The folder a source is cloned into."""
    if src.get("dir"):
        return src["dir"]
    return src["repo"].replace("/", "_")


def source_slug(src):
    """A short name for a source: its slug, else the repo name after the slash."""
    if src.get("slug"):
        return src["slug"]
    if src.get("repo"):
        return src["repo"].split("/")[-1]
    return source_dir_name(src)


def match_rule(relpath, rules):
    """Return (category, reason) of the first rule that matches, else None."""
    name = relpath.rsplit("/", 1)[-1]
    for rule in rules:
        for pat in rule.get("patterns", []):
            target = relpath if "/" in pat else name
            if fnmatch.fnmatchcase(target, pat):
                return rule["category"], rule.get("reason", "")
    return None


def is_binary(path, sniff):
    """A zero byte in the first `sniff` bytes means binary."""
    with open(path, "rb") as f:
        return b"\0" in f.read(sniff)


def walk(root, skip_dirs):
    """Yield paths relative to root: files of a folder first, then its subfolders, sorted."""
    entries = sorted(os.scandir(root), key=lambda e: e.name)
    for e in entries:
        if e.is_symlink():
            continue
        if e.is_file():
            yield e.name
    for e in entries:
        if e.is_symlink() or e.name in skip_dirs:
            continue
        if e.is_dir():
            for sub in walk(e.path, skip_dirs):
                yield e.name + "/" + sub


def cut(rows, max_bytes):
    """Cut [(size, path)] into consecutive parts of about equal size.

    n = ceil(total / max). A new part starts when adding the next file would
    pass 1.1 times total/n, and there are never more than n parts.
    """
    total = sum(s for s, _ in rows)
    n = max(1, math.ceil(total / max_bytes))
    target = total / n
    parts, cur, size = [], [], 0
    for s, p in rows:
        if cur and size + s > target * 1.1 and len(parts) < n - 1:
            parts.append(cur)
            cur, size = [], 0
        cur.append((s, p))
        size += s
    if cur:
        parts.append(cur)
    return parts


def assign_group(relpath, src, slug):
    """Return (group name, tier) for a file of a source."""
    groups = src.get("groups") or []
    if not groups:
        return slug, 1
    rest = None
    for g in groups:
        if g.get("rest"):
            if rest is None:
                rest = g
            continue
        for prefix in g.get("paths", []):
            if relpath.startswith(prefix):
                return g["name"], g.get("tier", 1)
    if rest is not None:
        return rest["name"], rest.get("tier", 1)
    return slug + "-rest", 1


def build(sources, sources_dir, protocol, max_mb):
    """Return (groups, index_rows, missing). groups: name -> {tier, rows}."""
    reading = protocol["reading"]
    skip_dirs = set(reading["skip_dirs"]["value"])
    sniff = reading["binary_sniff_bytes"]["value"]
    base_rules = reading["index_only"]["rules"]
    groups, index_rows, missing = {}, [], []
    for src in sources:
        folder = source_dir_name(src)
        root = os.path.join(sources_dir, folder)
        if not os.path.isdir(root):
            print("warning: folder not found, skipping: " + root, file=sys.stderr)
            missing.append(folder)
            continue
        slug = source_slug(src)
        rules = list(src.get("index_only", [])) + list(base_rules)  # the source's own first
        for rel in walk(root, skip_dirs):
            full = os.path.join(root, rel)
            size = os.path.getsize(full)
            path = folder + "/" + rel
            hit = match_rule(rel, rules)
            if hit:
                index_rows.append((size, hit[0], path))
                continue
            if is_binary(full, sniff):
                index_rows.append((size, "binary", path))
                continue
            name, tier = assign_group(rel, src, slug)
            g = groups.setdefault(name, {"tier": tier, "rows": []})
            g["rows"].append((size, path))
    return groups, index_rows, missing


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0] + " See the top of this file for the output files.",
        epilog="example:\n  python3 scripts/make_manifests.py --sources-file sources.json "
               "--sources-dir sources --out manifests",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sources-file", required=True, help="sources.json of the run")
    ap.add_argument("--sources-dir", required=True, help="folder holding the clones")
    ap.add_argument("--out", help="folder to write the manifests into (required unless --clone-commands)")
    ap.add_argument("--protocol", default=os.path.join(ROOT, "protocol.json"),
                    help="protocol.json (default: the one beside the scripts folder)")
    ap.add_argument("--clone-commands", action="store_true",
                    help="print the git commands that clone each source at its commit, and stop "
                         "(nothing is run; read them, then run them yourself)")
    ap.add_argument("--max-mb", type=float, default=None,
                    help="largest slice in MB (default: reading.slice_max_mb in protocol.json)")
    ap.add_argument("--force", action="store_true", help="write into a folder that already holds .txt manifests")
    args = ap.parse_args(argv)

    try:
        with open(args.sources_file) as f:
            sources = json.load(f)["sources"]
        with open(args.protocol) as f:
            protocol = json.load(f)
        max_mb = args.max_mb if args.max_mb is not None else protocol["reading"]["slice_max_mb"]["value"]
    except (OSError, ValueError, KeyError) as e:
        print("error: " + str(e), file=sys.stderr)
        return 2
    if args.clone_commands:
        for src in sources:
            if not src.get("url"):
                print("# %s: no url in sources.json; put its clone at %s/%s yourself"
                      % (src.get("name") or src.get("repo") or "?", args.sources_dir, source_dir_name(src)))
                continue
            dest = "%s/%s" % (args.sources_dir, source_dir_name(src))
            print("git clone --filter=blob:none %s %s" % (src["url"], dest))
            if src.get("commit"):
                print("git -C %s checkout --detach %s" % (dest, src["commit"]))
        return 0
    if not args.out:
        print("error: --out is required", file=sys.stderr)
        return 2
    if max_mb <= 0:
        print("error: --max-mb must be above zero", file=sys.stderr)
        return 2
    if os.path.isdir(args.out) and not args.force and any(
            n.endswith(".txt") for n in os.listdir(args.out)):
        print("error: %s already holds .txt manifests; use --force to overwrite" % args.out, file=sys.stderr)
        return 2

    groups, index_rows, missing = build(sources, args.sources_dir, protocol, max_mb)
    os.makedirs(args.out, exist_ok=True)
    max_bytes = int(max_mb * MB)

    # tier 1 groups first, then tier 2 and so on; first seen first within a tier
    order = sorted(groups, key=lambda n: groups[n]["tier"])
    summary, total_files, total_bytes = [], 0, 0
    for name in order:
        rows = groups[name]["rows"]
        parts = cut(rows, max_bytes)
        n = len(parts)
        for i, part in enumerate(parts, 1):
            slice_name = name if n == 1 else "%s-%dof%d" % (name, i, n)
            with open(os.path.join(args.out, slice_name + ".txt"), "w") as f:
                f.write("".join("%d\t%s\n" % (s, p) for s, p in part))
            nbytes = sum(s for s, _ in part)
            summary.append({"slice": slice_name, "group": name, "tier": groups[name]["tier"],
                            "files": len(part), "bytes": nbytes,
                            "first": part[0][1], "last": part[-1][1]})
            print("%s: %d files, %.0f KB" % (slice_name, len(part), nbytes / 1024))
            total_files += len(part)
            total_bytes += nbytes
    with open(os.path.join(args.out, "_index_only.txt"), "w") as f:
        f.write("".join("%d\t%s\t%s\n" % r for r in index_rows))
    with open(os.path.join(args.out, "_summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
        f.write("\n")
    print("total: %d slices, %d files, %.1f MB; %d index-only files"
          % (len(summary), total_files, total_bytes / MB, len(index_rows)))
    if missing:
        print("missing source folders: " + ", ".join(missing), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
