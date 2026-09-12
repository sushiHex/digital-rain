"""Apply the public repository's labels, settings and branch protection with `gh`.

Idempotent and stated in one place, so the configuration of the public
repository is reviewable in the tree rather than reconstructed from the GitHub
UI. Mirrors the newest of the owner's other public repositories
(`hermes-realtime`, `constructicon`): classic branch protection, a pull request
required with ZERO mandatory approvals (the single-maintainer setting),
required status checks named after the CI jobs, a small triage vocabulary of
labels, squash-only merges.

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

# (name, colour, description). GitHub's nine defaults are left alone.
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

# Secret scanning is only offered on PUBLIC repositories for a personal
# account: on the private-first repository the flag returns HTTP 422 ("not
# available for this repository") and, sent in the same call, made the whole
# settings request read as failed even though GitHub had applied the rest.
# Sent separately and tolerated; re-run this script once the repository is
# public and it takes.
SECRET_SCANNING = ["--enable-secret-scanning",
                   "--enable-secret-scanning-push-protection"]

DESCRIPTION = ("Glyph-conditioned font generation research: FLUX.2-klein + LoRA "
               "with a glyph-latent conditioning channel. Primarily a record of "
               "measuring the project's own instruments.")
TOPICS = ("diffusion-models", "lora", "font-generation", "flux", "typography",
          "research", "pre-registration")


def gh(args, dry_run, stdin=None):
    cmd = ["gh", *args]
    if dry_run:
        print("  would run:", " ".join(cmd))
        return None
    proc = subprocess.run(cmd, input=stdin, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"  FAILED: {' '.join(cmd)}\n{proc.stderr.strip()}", file=sys.stderr)
    return proc


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", required=True, help="OWNER/NAME")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    repo, dry = args.repo, args.dry_run

    print("labels")
    for name, colour, desc in LABELS:
        gh(["label", "create", name, "-R", repo, "--color", colour,
            "--description", desc, "--force"], dry)

    print("settings")
    gh(["repo", "edit", repo, "-d", DESCRIPTION, *SETTINGS], dry)
    gh(["repo", "edit", repo, *sum((["--add-topic", t] for t in TOPICS), [])], dry)
    print("secret scanning (public repositories only; a 422 here is expected while private)")
    gh(["repo", "edit", repo, *SECRET_SCANNING], dry)

    print("branch protection on main")
    gh(["api", "-X", "PUT", f"repos/{repo}/branches/main/protection",
        "-H", "Accept: application/vnd.github+json", "--input", "-"],
       dry, stdin=json.dumps(PROTECTION))

    if not dry:
        proc = subprocess.run(["gh", "api", f"repos/{repo}/branches/main/protection",
                               "--jq", ".required_status_checks.contexts"],
                              capture_output=True, text=True)
        print("required checks now:", proc.stdout.strip())
    return 0


if __name__ == "__main__":
    _sys.exit(main())
