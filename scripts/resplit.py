#!/usr/bin/env python3
"""Cut a slice that came back partial into smaller parts.

Reads manifests/<SLICE>.txt (one line per file: bytes, a tab, the path) and
writes manifests/<SLICE>.a.txt, .b.txt and so on, each near the same size and
no bigger than MAX_MB. The original manifest stays in place as the record; the
parts are what new readers are given.

Exit codes: 0 done, 2 a usage problem (missing manifest, bad size, too many
parts, or a part file that already exists).
"""
import argparse
import os
import string
import sys


def cut(rows, cap_bytes):
    """Cut [(size, path)] into consecutive parts of about equal size.

    n = ceil(total / cap). A new part starts when adding the next file would
    pass 1.1 times total/n, and there are never more than n parts.
    """
    total = sum(s for s, _ in rows)
    n = max(1, -(-total // int(cap_bytes)))
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


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0] + " The original manifest is left in place as the "
                    "record; the parts are what new readers read.",
        epilog="example:\n  python3 scripts/resplit.py vti-docs 0.75",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slice", help="slice name, without .txt")
    ap.add_argument("max_mb", help="largest part in MB (protocol.json: reading.resplit_mb)")
    ap.add_argument("--manifests", default="manifests", help="manifests folder (default: manifests)")
    ap.add_argument("--force", action="store_true", help="overwrite existing part files")
    args = ap.parse_args(argv)

    try:
        cap = float(args.max_mb) * 1024 * 1024
        if not cap >= 1:
            raise ValueError
    except ValueError:
        print("error: MAX_MB must be a number above zero, got %r" % args.max_mb, file=sys.stderr)
        return 2
    src = os.path.join(args.manifests, args.slice + ".txt")
    if not os.path.isfile(src):
        print("error: no manifest at " + src, file=sys.stderr)
        return 2
    with open(src) as f:
        rows = [l.rstrip("\n").split("\t", 1) for l in f if l.strip()]
    try:
        rows = [(int(s), p) for s, p in rows]
    except ValueError:
        print("error: %s is not 'bytes<TAB>path' lines" % src, file=sys.stderr)
        return 2
    if not rows:
        print("error: %s is empty" % src, file=sys.stderr)
        return 2

    parts = cut(rows, cap)
    if len(parts) > len(string.ascii_lowercase):
        print("error: %d parts is more than 26; use a larger MAX_MB" % len(parts), file=sys.stderr)
        return 2
    outs = [os.path.join(args.manifests, "%s.%s.txt" % (args.slice, string.ascii_lowercase[i]))
            for i in range(len(parts))]
    existing = [o for o in outs if os.path.exists(o)]
    if existing and not args.force:
        print("error: part files already exist (use --force): " + ", ".join(existing), file=sys.stderr)
        return 2
    for i, (part, out) in enumerate(zip(parts, outs)):
        with open(out, "w") as f:
            f.write("".join("%d\t%s\n" % (s, p) for s, p in part))
        print("%s.%s: %d files, %.0f KB  %s … %s" % (
            args.slice, string.ascii_lowercase[i], len(part),
            sum(s for s, _ in part) / 1024, part[0][1].split("/", 2)[-1], part[-1][1].split("/", 2)[-1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
