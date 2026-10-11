#!/usr/bin/env python3
"""reqpin: check requirements.txt files for unpinned deps, duplicates, bad lines."""
import argparse
import json
import re
import sys

NAME_RE = re.compile(r"^([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)\s*(\[[^\]]*\])?\s*(.*)$")
CLAUSE_RE = re.compile(r"^(===|==|~=|!=|<=|>=|<|>)\s*[A-Za-z0-9.*+!_-]+$")
VCS_PREFIXES = ("git+", "hg+", "svn+", "bzr+")


def logical_lines(text):
    """Yield (lineno, text) with backslash continuations joined, comments removed."""
    buf, start = "", 0
    for no, raw in enumerate(text.splitlines(), 1):
        if not buf:
            start = no
        line = raw.rstrip()
        if line.endswith("\\"):
            buf += line[:-1] + " "
            continue
        buf += line
        out = re.sub(r"(^|\s)#.*$", "", buf).strip()
        buf = ""
        if out:
            yield start, out
    if buf:
        out = re.sub(r"(^|\s)#.*$", "", buf).strip()
        if out:
            yield start, out


def normalize(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def check_text(text, require_hashes=False):
    """Return a list of problem dicts: {line, kind, message}."""
    problems = []
    seen = {}

    def add(no, kind, msg):
        problems.append({"line": no, "kind": kind, "message": msg})

    for no, line in logical_lines(text):
        tokens = line.split()
        first = tokens[0]
        if first in ("-r", "-c", "--requirement", "--constraint") or \
                first.startswith(("-r", "-c", "--requirement=", "--constraint=")) and not first.startswith("--c") or \
                first.startswith(("--requirement=", "--constraint=")):
            continue
        editable = first in ("-e", "--editable") or first.startswith("--editable=")
        if first.startswith("-") and not editable:
            continue  # other pip options (index urls etc.)
        hashes = re.findall(r"--hash[= ]\S+", line)
        body = re.sub(r"\s--hash[= ]\S+", "", " " + line).strip()
        if editable:
            body = re.sub(r"^(-e|--editable)[= ]?\s*", "", body)
        body, _, marker = body.partition(";")
        body, marker = body.strip(), marker.strip()
        is_url = body.startswith(VCS_PREFIXES) or "://" in body
        if is_url:
            continue  # pinned by location; not checked further
        m = NAME_RE.match(body)
        if not m:
            add(no, "bad-line", "cannot parse: %s" % line)
            continue
        name, _extras, spec = m.groups()
        if "@" in spec and "://" in spec:
            continue  # name @ url
        spec = spec.strip()
        if spec.startswith("(") and spec.endswith(")"):
            spec = spec[1:-1]
        clauses = [c.strip() for c in spec.split(",")] if spec else []
        if any(not CLAUSE_RE.match(c) for c in clauses):
            add(no, "bad-line", "invalid version specifier: %s" % line)
            continue
        key = (normalize(name), marker)
        if key in seen:
            add(no, "duplicate", "%s already listed on line %d" % (name, seen[key]))
        else:
            seen[key] = no
        pinned = any(re.match(r"^===?\s*[^*]+$", c) for c in clauses)
        if not pinned:
            add(no, "unpinned", "%s is not pinned with ==" % name)
        if require_hashes and not hashes:
            add(no, "missing-hash", "%s has no --hash" % name)
    return sorted(problems, key=lambda p: p["line"])


def main(argv=None):
    ap = argparse.ArgumentParser(prog="reqpin", description=__doc__)
    ap.add_argument("files", nargs="+", help="requirements files ('-' for stdin)")
    ap.add_argument("--require-hashes", action="store_true", help="flag requirements lacking --hash")
    ap.add_argument("--json", action="store_true", help="JSON output")
    args = ap.parse_args(argv)
    result = {}
    for f in args.files:
        try:
            text = sys.stdin.read() if f == "-" else open(f, encoding="utf-8").read()
        except OSError as e:
            print("reqpin: %s" % e, file=sys.stderr)
            return 2
        result[f] = check_text(text, args.require_hashes)
    total = sum(len(v) for v in result.values())
    if args.json:
        print(json.dumps({"problems": result, "total": total}, indent=2))
    else:
        for f, probs in result.items():
            for p in probs:
                print("%s:%d: %s: %s" % (f, p["line"], p["kind"], p["message"]))
        print("%d problem(s)" % total)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
