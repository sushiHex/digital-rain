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

`--list` prints BOTH halves. The withheld half is what the rules caught; the
kept half is what will be published, and a newly tracked file that no rule
names lands there without any other signal. Read the kept half too.

WHAT IT CHECKS BEFORE IT WRITES.

  * the destination is not the private repository, not inside it, not a
    symlink or junction, and does not contain it -- `--dest .` would otherwise
    delete the private tree and record the deletion
  * the private tree is clean (uncommitted work is not exported, and a dirty
    tree usually means the export was run mid-task)
  * the destination is empty, or a git repository with a clean tree whose
    EVERY commit was made by this script -- once a pull request has merged in
    public, a re-export would revert it, so the script refuses
  * after staging, every staged blob and mode is IDENTICAL to HEAD's (the
    byte-for-byte claim is checked, not assumed; autocrlf cannot slip in)
  * `sanitize_for_publish.py --check` passes ON THE DESTINATION -- the gate
    runs on what will be pushed, not on what was meant to be
  * `--commit` refuses unless the committing identity is a GitHub noreply
    address, so a second export from another machine cannot publish a
    personal email

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

# Commit subjects this script writes. A destination whose history holds any
# OTHER subject has been worked in, and is not re-exported over.
INITIAL_SUBJECT = "Initial public release"
SYNC_SUBJECT = "sync: "
NOREPLY = "@users.noreply.github.com"

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
    ("research/2026-04-09-legal-font-sources.md",
     "an April Oracle report asserting named vendors' licence terms with "
     "'high confidence' and carrying foundry contact addresses -- a legal "
     "and reputational exposure, not a finding"),
    ("research/2026-08-01-bfl-commercial-licensing.md",
     "ranks the commercial routes with price estimates and names the "
     "critical path -- business direction, not the technical record"),
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


def modes_at_head(repo):
    """{path: (mode, blob sha)} for every file at HEAD."""
    out = run(["git", "ls-tree", "-r", "HEAD", "-z"], repo).stdout
    result = {}
    for entry in out.split("\0"):
        if not entry:
            continue
        meta, path = entry.split("\t", 1)
        mode, _kind, sha = meta.split()
        result[path] = (mode, sha)
    return result


def staged_modes(repo):
    """{path: (mode, blob sha)} for every staged file."""
    out = run(["git", "ls-files", "-s", "-z"], repo).stdout
    result = {}
    for entry in out.split("\0"):
        if not entry:
            continue
        meta, path = entry.split("\t", 1)
        mode, sha, _stage = meta.split()
        result[path] = (mode, sha)
    return result


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
    print(f"KEPT -- {len(kept)} files will be published:")
    for p in kept:
        print(f"    {p}")
    print()
    for pat, paths in excluded.items():
        print(f"WITHHELD [{pat}] -- {reasons[pat]}")
        for p in paths:
            print(f"    {p}")
        if not paths:
            print("    (matches nothing)")
        print()


def is_clean(repo):
    return run(["git", "status", "--porcelain"], repo).stdout.strip() == ""


def check_dest_is_safe(dest, repo=REPO):
    """The destination must be a separate, ordinary directory.

    `--dest .`, a symlink or junction, or any nesting either way would make
    `prepare_dest` delete the private tree -- and `--commit` record it.
    """
    if os.path.lexists(dest) and os.path.islink(dest):
        raise SystemExit(f"refusing: {dest} is a symlink or junction")
    real_dest = os.path.realpath(dest)
    real_repo = os.path.realpath(repo)
    if os.path.normcase(real_dest) == os.path.normcase(real_repo):
        raise SystemExit("refusing: the destination IS the private repository")
    for inner, outer, what in ((real_dest, real_repo, "inside"),
                               (real_repo, real_dest, "a parent of")):
        try:
            common = os.path.commonpath([os.path.normcase(inner),
                                         os.path.normcase(outer)])
        except ValueError:            # different drives: cannot be nested
            continue
        if common == os.path.normcase(outer):
            raise SystemExit(f"refusing: the destination is {what} the private "
                             "repository")


def foreign_commits(dest):
    """Commit subjects in dest that this script did not write."""
    if run(["git", "rev-parse", "--verify", "-q", "HEAD"], dest, check=False).returncode != 0:
        return []
    subjects = run(["git", "log", "--format=%s"], dest).stdout.splitlines()
    return [s for s in subjects
            if not (s.startswith(INITIAL_SUBJECT) or s.startswith(SYNC_SUBJECT))]


def prepare_dest(dest):
    """Empty the destination of everything but .git; refuse a dirty or worked-in tree."""
    check_dest_is_safe(dest)
    if os.path.isdir(os.path.join(dest, ".git")):
        if not is_clean(dest):
            raise SystemExit(f"refusing: {dest} has uncommitted changes")
        foreign = foreign_commits(dest)
        if foreign:
            raise SystemExit(
                f"refusing: {dest} has {len(foreign)} commit(s) this script did "
                f"not make (first: {foreign[0]!r}). Work has landed there; a "
                "re-export would revert it. The public repository is the "
                "working one now.")
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
                         "HEAD and the listing disagree (an export-ignore "
                         "attribute, or a symlink, would do this)")
    return written


def stage(dest, keep, repo=REPO):
    """Stage exactly `keep`, then prove every blob and mode matches HEAD.

    Deletions via -A, ignored-but-tracked files via -f, the executable bit via
    update-index (Windows has no such bit, so `git add` alone would drop it),
    and then the staged (mode, sha) of every path is compared with HEAD's.
    """
    if not os.path.isdir(os.path.join(dest, ".git")):
        run(["git", "init", "-q", "-b", "main"], dest)
    run(["git", "add", "-A"], dest)
    spec = os.path.join(dest, ".git", "export-pathspec")
    with open(spec, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(keep) + "\n")
    run(["git", "add", "-f", "--pathspec-from-file=" + spec], dest)
    os.remove(spec)
    head = modes_at_head(repo)
    executable = [p for p in keep if head[p][0] == "100755"]
    # update-index takes paths as arguments, not a pathspec file; batches of
    # 200 keep the command line short on every platform.
    for i in range(0, len(executable), 200):
        run(["git", "update-index", "--chmod=+x", "--", *executable[i:i + 200]], dest)

    staged = staged_modes(dest)
    if sorted(staged) != sorted(keep):
        extra = sorted(set(staged) - set(keep))
        missing = sorted(set(keep) - set(staged))
        raise SystemExit(f"staged set differs from the listing: extra={extra[:5]} "
                         f"missing={missing[:5]}")
    differing = [p for p in keep if staged[p] != head[p]]
    if differing:
        p = differing[0]
        raise SystemExit(f"{len(differing)} staged file(s) differ from HEAD in "
                         f"blob or mode, first {p}: staged {staged[p]} vs HEAD "
                         f"{head[p]}. Line-ending conversion or a mode drop -- "
                         "nothing was committed")


def gate(dest):
    proc = subprocess.run([sys.executable, SANITIZER, "--check"], cwd=dest,
                          capture_output=True, text=True)
    sys.stdout.write(proc.stdout)
    if proc.returncode != 0:
        raise SystemExit("the sanitizer FAILED on the exported tree; nothing "
                         "was committed")


def committer_email(dest):
    proc = run(["git", "config", "user.email"], dest, check=False)
    return proc.stdout.strip()


def commit(dest, repo):
    email = committer_email(dest)
    if not email.endswith(NOREPLY):
        raise SystemExit(f"refusing to commit as {email or '(no email set)'}: the "
                         f"public history takes only a GitHub noreply address "
                         f"({NOREPLY}). Set it with `git -C <dest> config "
                         "user.email` and re-run.")
    sha = run(["git", "rev-parse", "--short=12", "HEAD"], repo).stdout.strip()
    if run(["git", "rev-parse", "--verify", "-q", "HEAD"], dest, check=False).returncode != 0:
        subject = f"{INITIAL_SUBJECT} (from digital-rain-private @ {sha})"
    else:
        subject = f"{SYNC_SUBJECT}digital-rain-private @ {sha}"
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
                    help="print both halves of the partition and exit")
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
    print(f"exported {n} files to {dest}; withheld {n_ex} under "
          f"{len(EXCLUDE)} rules (--list shows both halves); every staged blob "
          "and mode matches HEAD\n")
    gate(dest)
    if args.commit:
        commit(dest, REPO)
    else:
        print("\nstaged, not committed. Review with `git -C <dest> status`, "
              "then re-run with --commit.")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
