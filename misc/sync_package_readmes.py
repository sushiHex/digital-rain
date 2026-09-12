"""Regenerate each package README's `## Contents (N)` list from module docstrings.

WHY. Every topical package carries a README listing its modules. They were
maintained by hand and drifted badly: `analysis/README.md` claimed 16 modules
while the directory held 40, so two thirds of the tools this project built --
including every instrument behind its headline findings -- were undiscoverable
from the package's own index. studies/ and pipeline/ each listed 14 of 16;
probes/ listed 20 of 21.

WHAT IT TOUCHES. Only the run of `- \\`name.py\\` -- description` lines directly
below a `## Contents (N)` heading, and the count in that heading. Prose before
the heading and any section after the list are preserved. Packages with no such
heading (`viz/`, `route_b/`) are skipped -- their READMEs use a different,
hand-written format that says more than a name list would. `cleanup/` joined the
generated set on 2026-09-11; its eight modules carry no docstrings, so its list
is names only until they do.

DESCRIPTIONS come from the first sentence of each module docstring, with wrapped
lines joined first. The previous hand-maintained entries were cut at the
docstring's first physical line, which truncated mid-clause ("decide whether
captions move the").

  python misc/sync_package_readmes.py --check     # exit 1 if any README is stale
  python misc/sync_package_readmes.py --fix
"""

# repo root on sys.path so `python misc/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import ast
import glob
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGES = ("analysis", "studies", "pipeline", "probes", "benchmarks", "misc",
            "cleanup")

HEADING = re.compile(r"^## Contents \(\d+\)\s*$", re.M)
# re.M matters for the findall() diagnostic below; .match() on single lines is
# unaffected either way.
ENTRY = re.compile(r"^- `[^`]+\.py`.*$", re.M)
SKIP = {"__init__.py", "_common.py"}
MAX_DESC = 110


def first_sentence(docstring):
    """First sentence of a docstring, with wrapped lines joined."""
    if not docstring:
        return ""
    para = docstring.strip().split("\n\n")[0]
    text = " ".join(line.strip() for line in para.splitlines()).strip()
    if not text:
        return ""
    # Split on sentence end, but not on the dot inside a filename or version.
    m = re.search(r"(?<![A-Z0-9])\.(?:\s|$)", text)
    if m:
        text = text[:m.start() + 1]
    if len(text) > MAX_DESC:
        text = text[:MAX_DESC].rstrip() + "..."
    return text


def module_docstring(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return ast.get_docstring(ast.parse(fh.read()))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return None


def entries_for(package):
    paths = sorted(glob.glob(os.path.join(REPO, package, "*.py")))
    out = []
    for path in paths:
        name = os.path.basename(path)
        if name in SKIP:
            continue
        desc = first_sentence(module_docstring(path))
        out.append(f"- `{name}` — {desc}" if desc else f"- `{name}`")
    return out


def rebuild(text, entries):
    """Replace the entry run under `## Contents (N)`; return None if no heading."""
    m = HEADING.search(text)
    if not m:
        return None
    lines = text.splitlines()
    start = text[:m.start()].count("\n")          # index of the heading line
    i = start + 1
    while i < len(lines) and not ENTRY.match(lines[i]):
        if lines[i].strip():                       # non-blank, non-entry: list absent
            break
        i += 1
    first_entry = i
    while i < len(lines) and ENTRY.match(lines[i]):
        i += 1
    rebuilt = (lines[:start]
               + [f"## Contents ({len(entries)})", ""]
               + entries
               + lines[i:])
    if first_entry == i:                           # nothing matched; insert cleanly
        rebuilt = (lines[:start]
                   + [f"## Contents ({len(entries)})", ""]
                   + entries
                   + [""] + lines[start + 1:])
    return "\n".join(rebuilt).rstrip("\n") + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="report staleness, change nothing")
    mode.add_argument("--fix", action="store_true", help="rewrite the lists in place")
    args = ap.parse_args()

    stale = []
    for package in PACKAGES:
        readme = os.path.join(REPO, package, "README.md")
        if not os.path.isfile(readme):
            continue
        with open(readme, encoding="utf-8") as fh:
            current = fh.read()
        entries = entries_for(package)
        updated = rebuild(current, entries)
        if updated is None:
            print(f"  {package:<12} no '## Contents (N)' heading - skipped")
            continue
        listed = len(ENTRY.findall(current))
        if updated == current:
            print(f"  {package:<12} up to date ({len(entries)})")
            continue
        stale.append(package)
        # ASCII only in console output; this runs on a cp1252 Windows terminal.
        print(f"  {package:<12} STALE - lists {listed}, directory has {len(entries)}")
        if args.fix:
            with open(readme, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(updated)

    if not stale:
        print("\nall package READMEs current.")
        return 0
    if args.fix:
        print(f"\nrewrote {len(stale)}: {', '.join(stale)}")
        return 0
    print(f"\n{len(stale)} stale: {', '.join(stale)}"
          "\nrun: python misc/sync_package_readmes.py --fix")
    return 1


if __name__ == "__main__":
    _sys.exit(main())
