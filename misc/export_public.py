"""Export the public tree: every file tracked at HEAD, minus a stated exclusion list.

WHY A FILTER, NOT A HISTORY REWRITE. The private repository's history carries
things a public one should not: a home path committed at a9868ac, session
captures, five months of market research for a possible commercial direction.
Rewriting 260 commits to remove them is fragile and unreviewable. Exporting
the CURRENT tree as a fresh history is a single operation whose output can be
read in full before it is pushed, and the private repository keeps the whole
record. The two trees are otherwise byte-identical: every public-facing wording
change is made in the private tree first, so this script never edits content.

WHAT IS EXCLUDED, AND WHY EACH LINE IS HERE. See `EXCLUDE`. Every rule must
match at least one tracked file -- a rule that matches nothing is a rule that
has silently stopped protecting something (a renamed directory, say), and the
script refuses to run rather than export with a dead guard. The exclusions are
documented for a reader of the PUBLIC repository too, because this file is
exported with everything else: what was withheld is stated, not hidden.

WHAT IT CHECKS BEFORE IT WRITES.

  * the private tree is clean (uncommitted work is not exported, and a dirty
    tree usually means the export was run mid-task)
  * the destination is empty, or a git repository with a clean tree
  * after staging, `sanitize_for_publish.py --check` passes ON THE DESTINATION
    -- the gate runs on what will be pushed, not on what was meant to be

WHAT IT NEVER DOES. Push. Change visibility. Edit a file's content.

  python misc/export_public.py --list                 # what goes, what stays, why
  python misc/export_public.py --dest ../digital-rain # export and stage
  python misc/export_public.py --dest ../digital-rain --commit
"""

# repo root on sys.path so `python misc/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import fnmatch
import io
import os
import shutil
import subprocess
import sys
import tarfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DEST = os.path.normpath(os.path.join(REPO, "..", "digital-rain"))
SANITIZER = os.path.join("analysis", "sanitize_for_publish.py")

# (pattern, reason). A pattern ending in "/" is a directory prefix; anything
# else is an fnmatch glob against the repo-relative path.
EXCLUDE = (
    ("research/sessions/",
     "session captures -- private working memory written by an editor hook, "
     "not research"),
    ("research/2026-03-2?-oracle-*.md",
     "March 2026 Oracle rounds: market sizing, pricing, competitors, "
     "go-to-market -- business research for a possible commercial direction, "
     "not the technical record"),
    ("research/RESEARCH.md",
     "the synthesised business research the March rounds fed"),
    ("research/BRAINSTORM.md",
     "the original concept and positioning memo"),
    ("docs/archive/",
     "stale 2026-03 planning whose links point at the excluded research"),
    ("docs/superpowers/",
     "agent-workflow plans and specs that cite the withheld research by "
     "section; the same directory is withheld from the owner's other public "
     "repositories for the same reason"),
    ("docs/PUSH-PREP.md",
     "the private-push runbook; docs/public-release.md supersedes it"),
    (".claude/",
     "editor configuration, never tracked -- listed so that it stays that way"),
)

# Rules allowed to match nothing: they guard against a FUTURE mistake rather
# than excluding something that exists today.
MAY_BE_EMPTY = {".claude/"}


def run(args, cwd, check=True, **kw):
    return subprocess.run(args, cwd=cwd, check=check, capture_output=True,
                          text=True, **kw)


def tracked_at_head(repo):
    out = run(["git", "ls-tree", "-r", "HEAD", "--name-only", "-z"], repo).stdout
    return sorted(p for p in out.split("\0") if p)


def matches(path, pattern):
    if pattern.endswith("/"):
        return path.startswith(pattern)
    return fnmatch.fnmatchcase(path, pattern)


def partition(paths, rules=EXCLUDE):
    """(kept, {pattern: [excluded paths]}) -- every path lands in exactly one."""
    kept, excluded = [], {pat: [] for pat, _ in rules}
    for p in paths:
        for pat, _ in rules:
            if matches(p, pat):
                excluded[pat].append(p)
                break
        else:
            kept.append(p)
    return kept, excluded


def dead_rules(excluded, rules=EXCLUDE):
    return [pat for pat, _ in rules
            if not excluded[pat] and pat not in MAY_BE_EMPTY]


def is_export(excluded):
    """True when NO rule matches anything: this tree is itself a public export.

    In the public repository every rule is dead by construction, which is the
    one situation where dead rules are not a bug -- they are the evidence the
    export happened. `main()` still refuses to run there, because a public
    tree must never re-export itself; the tests use this to skip instead.
    """
    return all(not paths for paths in excluded.values())


def print_listing(kept, excluded, rules=EXCLUDE):
    reasons = dict(rules)
    print(f"kept: {len(kept)} files\n")
    for pat, paths in excluded.items():
        print(f"excluded [{pat}] -- {reasons[pat]}")
        for p in paths:
            print(f"    {p}")
        if not paths:
            print("    (matches nothing)")
        print()


def is_clean(repo):
    return run(["git", "status", "--porcelain"], repo).stdout.strip() == ""


def prepare_dest(dest):
    """Empty the destination of everything but .git; refuse a dirty tree."""
    if os.path.isdir(os.path.join(dest, ".git")):
        if not is_clean(dest):
            raise SystemExit(f"refusing: {dest} has uncommitted changes")
    elif os.path.isdir(dest) and os.listdir(dest):
        raise SystemExit(f"refusing: {dest} exists, is not empty and is not a "
                         "git repository")
    os.makedirs(dest, exist_ok=True)
    for name in os.listdir(dest):
        if name == ".git":
            continue
        full = os.path.join(dest, name)
        if os.path.isdir(full) and not os.path.islink(full):
            shutil.rmtree(full)
        else:
            os.remove(full)


def extract_head(repo, dest, keep):
    """Write the HEAD blobs of `keep` into dest, byte for byte."""
    tar_bytes = subprocess.run(["git", "archive", "--format=tar", "HEAD"],
                               cwd=repo, check=True, capture_output=True).stdout
    wanted = set(keep)
    written = 0
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:") as tf:
        for member in tf:
            if member.name not in wanted or not member.isfile():
                continue
            target = os.path.join(dest, member.name)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with tf.extractfile(member) as src, open(target, "wb") as out:
                shutil.copyfileobj(src, out)
            if member.mode & 0o111:
                os.chmod(target, member.mode)
            written += 1
    if written != len(wanted):
        raise SystemExit(f"wrote {written} files but expected {len(wanted)}: "
                         "HEAD and the listing disagree")
    return written


def stage(dest, keep):
    """Stage exactly `keep`: deletions via -A, ignored-but-tracked via -f."""
    if not os.path.isdir(os.path.join(dest, ".git")):
        run(["git", "init", "-q", "-b", "main"], dest)
    run(["git", "add", "-A"], dest)
    spec = os.path.join(dest, ".git", "export-pathspec")
    with open(spec, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(keep) + "\n")
    run(["git", "add", "-f", "--pathspec-from-file=" + spec], dest)
    os.remove(spec)
    staged = sorted(p for p in run(["git", "ls-files", "-z"], dest).stdout.split("\0") if p)
    if staged != sorted(keep):
        extra = sorted(set(staged) - set(keep))
        missing = sorted(set(keep) - set(staged))
        raise SystemExit(f"staged set differs from the listing: extra={extra[:5]} "
                         f"missing={missing[:5]}")


def gate(dest):
    proc = subprocess.run([sys.executable, SANITIZER, "--check"], cwd=dest,
                          capture_output=True, text=True)
    sys.stdout.write(proc.stdout)
    if proc.returncode != 0:
        raise SystemExit("the sanitizer FAILED on the exported tree; nothing "
                         "was committed")


def commit(dest, repo):
    sha = run(["git", "rev-parse", "--short=12", "HEAD"], repo).stdout.strip()
    if run(["git", "rev-parse", "--verify", "-q", "HEAD"], dest, check=False).returncode != 0:
        subject = f"Initial public release (from digital-rain-private @ {sha})"
    else:
        subject = f"sync: digital-rain-private @ {sha}"
    body = ("Exported by misc/export_public.py -- every file tracked at that "
            "commit, minus the exclusions the script states.")
    if run(["git", "diff", "--cached", "--quiet"], dest, check=False).returncode == 0:
        print("nothing to commit: the export matches the last one")
        return
    run(["git", "commit", "-q", "-m", subject, "-m", body], dest)
    print(f"committed: {subject}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dest", default=DEFAULT_DEST)
    ap.add_argument("--list", action="store_true",
                    help="print the partition and exit")
    ap.add_argument("--commit", action="store_true",
                    help="commit the staged export in --dest (never pushes)")
    ap.add_argument("--allow-dirty", action="store_true",
                    help="export HEAD even if the working tree has changes")
    args = ap.parse_args(argv)

    keep, excluded = partition(tracked_at_head(REPO))
    if is_export(excluded):
        raise SystemExit("refusing: this tree is itself a public export (no "
                         "exclusion rule matches anything). Export from the "
                         "private archive, never from the public repository.")
    dead = dead_rules(excluded)
    if dead:
        raise SystemExit(f"exclusion rules that match nothing: {dead}. A dead "
                         "guard is a bug; fix the rule or delete it.")
    if args.list:
        print_listing(keep, excluded)
        return 0

    if not args.allow_dirty and not is_clean(REPO):
        raise SystemExit("refusing: the private tree has uncommitted changes "
                         "(commit them, or --allow-dirty to export HEAD anyway)")

    dest = os.path.abspath(args.dest)
    prepare_dest(dest)
    n = extract_head(REPO, dest, keep)
    stage(dest, keep)
    n_ex = sum(len(v) for v in excluded.values())
    print(f"exported {n} files to {dest}; excluded {n_ex} under "
          f"{len(EXCLUDE)} rules (--list shows them)\n")
    gate(dest)
    if args.commit:
        commit(dest, REPO)
    else:
        print("\nstaged, not committed. Review with `git -C <dest> status`, "
              "then re-run with --commit.")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
