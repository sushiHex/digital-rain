# Public release — the two repositories, what is withheld, and the gates

> **Decision, 2026-09-11.** The private repository `sushiHex/digital-rain`
> (full history, 260+ commits) becomes **`sushiHex/digital-rain-private`**, the
> archive. A **fresh** `sushiHex/digital-rain` is built from the current tree by
> `misc/export_public.py` and is the public-facing repository, where issues and
> pull requests live. Contributors work there. This mirrors the pattern already
> used for `mainframe-mcp` / `mainframe-mcp-private`, `claude-oracle` and
> `hermes-realtime`.
>
> This supersedes `docs/PUSH-PREP.md`, the record of the *private* push,
> which is itself withheld from the public tree (so it is named here, not
> linked).

## Why a fresh history rather than a rewritten one

The private history carries three things a public one should not: a home
path committed at `a9868ac` (via a session capture's `cwd:` front matter),
three session captures, and twenty-four files of market and business research
for a possible commercial direction. Rewriting 260 commits to remove them is
fragile and cannot be reviewed in full. Exporting the *current* tree as one
initial commit is a single operation whose output can be read end to end
before it is pushed, and the private repository keeps the whole record — the
commit messages, the pre-registration timestamps, the corrections.

The cost is that the public repository's history starts on the export date.
The pre-registration discipline this project relies on ("the bar was committed
before the data") is therefore **provable only from the private archive** for
anything before the cutover. The research notes state their registration
commits by SHA; those SHAs resolve in `digital-rain-private`, not in the public
repository. From the cutover on, registrations are committed in public first.

## What is withheld, and why

`python misc/export_public.py --list` prints the partition. Every rule must
match at least one tracked file, or the script refuses to run — a rule that
matches nothing is a guard that has silently died, the same shape as the glob
mismatch that dropped a description from the transfer test without erroring.

| withheld | why |
|---|---|
| `research/sessions/` (3) | session captures written by an editor hook — private working memory, not research |
| `research/2026-03-2?-oracle-*.md` (21) | the March 2026 Oracle rounds: market sizing, pricing, competitors, go-to-market. Business research for a possible commercial direction |
| `research/RESEARCH.md`, `research/BRAINSTORM.md` | the synthesis those rounds fed, and the original positioning memo |
| `docs/archive/` (5) | stale 2026-03 planning whose links point at the files above |
| `docs/superpowers/` (15) | agent-workflow plans and specs that cite the withheld research by section; the same directory is withheld from the owner's other public repositories for the same reason |
| `docs/PUSH-PREP.md` | the private-push runbook; this document supersedes it |

**Everything else is exported byte-for-byte**, including `CLAUDE.md`, the
force-added eval artifacts behind the README results table, and every negative
result. The research index (`research/README.md`) says where the March rounds
went rather than linking to files that are not there.

In the public repository every rule above matches nothing — that is what an
export is — so `misc/export_public.py` refuses to run there, and the tests
that pin the rules skip rather than fail. A public tree must never re-export
itself.

Any public-facing wording change is made in the **private** tree first and
exported; the exporter never edits content. That keeps the two trees identical
where they overlap and makes a re-export a pure filter.

## Gates before any change of visibility

All four, every time. Two are the same gates the private push used; two are
new because the threat model changed.

1. **`python misc/export_public.py --list`** — read the partition. The
   withheld half must be exactly the table above.
2. **The sanitizer passes on the exported tree.** The exporter runs
   `analysis/sanitize_for_publish.py --check` *in the destination* after
   staging and refuses to commit if it fails. The gate runs on what will be
   pushed, not on what was meant to be. It caught nothing on 2026-08-18,
   caught a regression on 2026-08-24, and on 2026-09-11 was found to have a
   hole — JSON doubles backslashes and the pattern allowed one — that let three
   tracked records carry a home path while it reported clean.
   `tests/test_sanitize_for_publish.py` now pins every spelling.
3. **The test suite is green in the exported tree**, not only in the private
   one. The public tree lacks `font_pool/`, `dataset_*/`, model weights and the
   untracked eval outputs; a test that quietly depended on any of them passes
   privately and fails for every contributor. Run `python -m pytest` inside the
   export before the first push, and CI runs it on every pull request after.
4. **`git log` of the export has no author email but the GitHub noreply
   address.** The private history is already clean on this (checked 2026-07-29
   and again 2026-09-11); the export inherits the committing identity, so it
   is checked once more on the fresh repository.

Weights and a hosted demo remain blocked **regardless of repository
visibility** — see the README's licensing section. Publishing the code does
not touch either constraint: the right-to-train question is about the corpus
inputs and the OFL-derivative question is about generated outputs, and neither
is a property of the source tree.

## The licence question is now live

The repository carries **no licence**: all rights reserved, pending a decision
(`LICENSE` records why MIT was withdrawn and what AGPL-3.0 and BSL 1.1 would
each mean). That was a free choice while the repository was private. Public,
it has two consequences the owner should decide on rather than inherit:

- **Readers may look and fork, and nothing more.** GitHub's terms permit
  viewing and forking of any public repository; no licence means no right to
  run, modify or redistribute. That is a legitimate source-available posture,
  and it is the posture until a licence is chosen.
- **A pull request to an unlicensed project is legally murky.** The PR
  template asks contributors to confirm they hold the rights to what they
  submit and that it may be relicensed under whatever this repository adopts.
  That is the minimum; a real CLA or a chosen licence is the fix. AGPL-3.0
  plus a commercial licence for paying customers is the usual open-core
  arrangement and is the one `LICENSE` points at.

## Runbook

Run from the private clone (`repos/fonts`). Every step before the last is
reversible.

```bash
# 0. gates
python -m pytest                                   # green privately
python misc/export_public.py --list                # read the partition

# 1. rename the private repository; GitHub redirects the old URL
gh repo rename digital-rain-private -R sushiHex/digital-rain --yes
git remote set-url origin https://github.com/sushiHex/digital-rain-private.git

# 2. build the public tree next to this clone, review it, commit it
python misc/export_public.py --dest ../digital-rain            # stages; sanitizer runs
git -C ../digital-rain status                                  # read it
python misc/export_public.py --dest ../digital-rain --commit
python -m pytest --rootdir ../digital-rain ../digital-rain/tests   # green in the export

# 3. create the public repository PRIVATE first, push, verify, then flip
gh repo create sushiHex/digital-rain --private --source ../digital-rain --remote origin --push
gh repo view sushiHex/digital-rain --json visibility,defaultBranchRef
gh run list -R sushiHex/digital-rain            # CI green on the initial commit
# labels, settings and branch protection: python misc/configure_public_repo.py

# 4. the irreversible step -- owner only, after reading steps 0-3's output
gh repo edit sushiHex/digital-rain --visibility public --accept-visibility-change-consequences
```

Step 3 creates the repository private on purpose. Once a repository is public
its content can be forked, cached and indexed within minutes; a private
first push lets the owner read the exported tree *on GitHub* — file listing,
rendered README, Actions run — before anything is irreversible.

## After the cutover — which repository is the working one

**The public repository is the working repository.** Every change lands there
by pull request; issues are filed there; CI runs there. `digital-rain-private`
is an archive: full history, the withheld research, and nothing new.

Two rules follow, and both are easy to break by habit:

- **Do not develop in the private clone and re-export.** The exporter is
  one-directional and overwrites; a re-export after pull requests have merged
  in public would revert them. `misc/export_public.py` is kept in the public
  tree because it documents what was withheld, and so that a *second* clean
  export can be produced before cutover if the first is rejected — not as a
  sync mechanism.
- **Anything that must stay private goes in the private repository by hand**,
  as a normal commit there. Session captures, business research, credentials.
  The public clone's hooks write session captures into `research/sessions/`
  of whatever tree they run in; that directory is gitignored in the public
  tree for this reason.

## The contributor workflow

Issues and pull requests on the public repository, mirroring the newest of the
other public `sushiHex` repositories (`hermes-realtime`, `constructicon`):
structured issue forms, an evidence-first pull request template, a small
triage vocabulary of labels, and classic branch protection with a pull request
required and zero mandatory approvals — the single-maintainer setting. The
pieces, all in the tree:

- `.github/ISSUE_TEMPLATE/` — `bug.yml`, `proposal.yml` (a decision),
  `work.yml`, and `finding.yml` — a **research finding**, because a claim with
  a number in it is the unit of contribution here and it needs its
  pre-registration, its sample and its own metric's noise stated up front (see
  `CLAUDE.md`, *A single-seed A/B cannot resolve a model difference*).
  `config.yml` disables blank issues and routes vulnerabilities to private
  reporting.
- `.github/PULL_REQUEST_TEMPLATE.md` — what changed, the exact evidence, the
  claim check for any number the PR adds to the record, the public boundary,
  the contributor's rights confirmation.
- `.github/CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md` — GitHub
  finds them under `.github/`, which keeps the repo root to `README.md`,
  `CLAUDE.md` and `AGENTS.md` (a pointer to `CLAUDE.md` for non-Claude agents).
- `.github/workflows/ci.yml` — `python -m pytest` on Python 3.12 and 3.14 on a
  CPU runner with `FONTGEN_NO_MODEL_DOWNLOADS=1`, plus a `public-audit` job
  that runs the sanitizer. Tests that need the GPU, the corpus, weights or
  potrace skip; gate 3 above checks that the suite passes without them.
  Third-party actions are pinned to full commit SHAs.
- `.github/CODEOWNERS` — `@sushiHex` on everything, named again on the files
  that define the boundary.
- `.github/dependabot.yml` — weekly for GitHub Actions only; the Python floors
  are `>=` and would only generate noise.
- Labels beyond GitHub's defaults: `needs-triage`, `investigation`,
  `decision`, `ready`, `finding`, `licensing`.
- Branch protection on `main`: pull request required (zero approvals
  mandated), the three CI checks required and up to date, linear history,
  conversation resolution, no force-push, no deletion. Squash merges only,
  head branch deleted on merge.
- `CLAUDE.md` stays: it is the project's conventions, it is what an agent
  working on a contributor's machine reads first, and everything in it is
  public-safe.

## Record

| date | what |
|---|---|
| 2026-07-29 | private push audit (`PUSH-PREP.md`) |
| 2026-08-18 | MIT withdrawn; all rights reserved pending a decision |
| 2026-08-24 | sanitizer caught a home path that entered via a session capture |
| 2026-09-11 | sanitizer found to miss JSON-escaped paths; fixed and pinned. Runners moved to `runners/`. Exporter written. Decision to go public via a fresh repository. |
