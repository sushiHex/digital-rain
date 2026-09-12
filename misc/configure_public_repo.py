"""Apply the public repository's labels, settings and branch protection with `gh`.

Idempotent and stated in one place, so the configuration of the public
repository is reviewable in the tree rather than reconstructed from the GitHub
UI. Mirrors the newest of the owner's other public repositories
(`hermes-realtime`, `constructicon`): classic branch protection, a pull request
required with ZERO mandatory approvals (the single-maintainer setting),
required status checks named after the CI jobs, a small triage vocabulary of
labels, squash-only merges.

FAILURES PROPAGATE. Every `gh` call's exit code is kept; the script exits 1
if any required step failed and says which, and the final verification reads
the protection back rather than trusting the PUT. Two settings exist only on
PUBLIC repositories for a personal account -- secret scanning and private
vulnerability reporting -- so on the private-first repository they return
HTTP 422 and 404 respectively and are reported as "deferred", not as
failures. Re-run after the visibility flip and they take; the run then
reports them applied.

It never changes visibility. That is one command, and it is the owner's:

  gh repo edit sushiHex/digital-rain --visibility public --accept-visibility-change-consequences

  python misc/configure_public_repo.py --repo sushiHex/digital-rain
  python misc/configure_public_repo.py --repo sushiHex/digital-rain --dry-run
"""

# repo root on sys.path so `python misc/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import json
import subprocess
import sys

# (name, colour, description). GitHub's defaults are left alone.
LABELS = (
    ("needs-triage", "ededed", "Not yet read by the maintainer"),
    ("investigation", "0e8a16", "Find something out; may end negatively"),
    ("decision", "5319e7", "A choice is requested, with the evidence that would settle it"),
    ("ready", "1d76db", "Scoped, unblocked, and open to a contributor"),
    ("finding", "fbca04", "A number or comparison entering the record; needs its noise and its registration"),
    ("licensing", "b60205", "Touches the corpus, weights, outputs or a hosted demo -- both blockers are unresolved"),
)

# Must match the job names in .github/workflows/ci.yml exactly.
REQUIRED_CHECKS = ("tests (3.12)", "tests (3.14)", "public-audit")

# `enforce_admins` is False on purpose: a single maintainer with no second
# reviewer needs a way to land a hotfix without opening a pull request against
# themselves. It means the owner CAN bypass every rule below; the rules bind
# contributors, not the owner. Flip it to True when a second maintainer joins.
PROTECTION = {
    "required_status_checks": {"strict": True, "contexts": list(REQUIRED_CHECKS)},
    "enforce_admins": False,
    "required_pull_request_reviews": {
        "dismiss_stale_reviews": True,
        "require_code_owner_reviews": False,
        "required_approving_review_count": 0,
    },
    "restrictions": None,
    "required_linear_history": True,
    "allow_force_pushes": False,
    "allow_deletions": False,
    "required_conversation_resolution": True,
}

SETTINGS = [
    "--enable-issues", "--enable-wiki=false", "--enable-projects=false",
    "--enable-discussions=false", "--delete-branch-on-merge",
    "--enable-squash-merge", "--enable-merge-commit=false",
    "--enable-rebase-merge=false", "--allow-update-branch",
]

# Public-only for a personal account; tolerated while private.
SECRET_SCANNING = ["--enable-secret-scanning",
                   "--enable-secret-scanning-push-protection"]

DESCRIPTION = ("Glyph-conditioned font generation research: FLUX.2-klein + LoRA "
               "with a glyph-latent conditioning channel. Primarily a record of "
               "measuring the project's own instruments.")
TOPICS = ("diffusion-models", "lora", "font-generation", "flux", "typography",
          "research", "pre-registration")


class Runner:
    def __init__(self, dry_run):
        self.dry_run = dry_run
        self.failed = []
        self.deferred = []

    def gh(self, args, stdin=None, public_only=False):
        cmd = ["gh", *args]
        if self.dry_run:
            print("  would run:", " ".join(cmd))
            return None
        proc = subprocess.run(cmd, input=stdin, capture_output=True, text=True)
        if proc.returncode != 0:
            err = proc.stderr.strip()
            # Secret scanning answers 422 while private; the private
            # vulnerability reporting endpoint answers 404. Both mean "not
            # on this repository yet", not "the request was wrong".
            if public_only and ("422" in err or "404" in err):
                print(f"  deferred (public repositories only): {' '.join(args[:3])}")
                self.deferred.append(" ".join(args[:3]))
            else:
                print(f"  FAILED: {' '.join(cmd)}\n    {err}", file=sys.stderr)
                self.failed.append(" ".join(args[:3]))
        return proc


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", required=True, help="OWNER/NAME")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    repo, r = args.repo, Runner(args.dry_run)

    print("labels")
    for name, colour, desc in LABELS:
        r.gh(["label", "create", name, "-R", repo, "--color", colour,
              "--description", desc, "--force"])

    print("settings")
    r.gh(["repo", "edit", repo, "-d", DESCRIPTION, *SETTINGS])
    r.gh(["repo", "edit", repo, *sum((["--add-topic", t] for t in TOPICS), [])])

    print("secret scanning")
    r.gh(["repo", "edit", repo, *SECRET_SCANNING], public_only=True)

    print("private vulnerability reporting (the channel SECURITY.md points at)")
    r.gh(["api", "-X", "PUT", f"repos/{repo}/private-vulnerability-reporting"],
         public_only=True)

    print("branch protection on main")
    r.gh(["api", "-X", "PUT", f"repos/{repo}/branches/main/protection",
          "-H", "Accept: application/vnd.github+json", "--input", "-"],
         stdin=json.dumps(PROTECTION))

    if args.dry_run:
        return 0

    print("verification")
    proc = subprocess.run(["gh", "api", f"repos/{repo}/branches/main/protection",
                           "--jq", ".required_status_checks.contexts"],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        r.failed.append("read back branch protection")
        print(f"  FAILED to read protection back: {proc.stderr.strip()}",
              file=sys.stderr)
    else:
        got = set(json.loads(proc.stdout or "[]"))
        if got != set(REQUIRED_CHECKS):
            r.failed.append("required checks mismatch")
            print(f"  required checks are {sorted(got)}, expected "
                  f"{sorted(REQUIRED_CHECKS)}", file=sys.stderr)
        else:
            print(f"  required checks: {sorted(got)}")

    if r.deferred:
        print("\ndeferred until the repository is public (re-run then): "
              + "; ".join(r.deferred))
    if r.failed:
        print(f"\nFAILED {len(r.failed)} step(s): " + "; ".join(r.failed),
              file=sys.stderr)
        return 1
    print("\nall required steps applied and verified.")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
