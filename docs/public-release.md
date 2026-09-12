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
repository, and several notes also cite `docs/superpowers/` plans that are
withheld. Those citations stay as written — dated notes are never rewritten —
and a public reader should take a pre-cutover SHA as a claim the archive can
verify, not one the public repository can. From the cutover on, registrations
are committed in public first, where anyone can check the timestamp.

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
| `research/2026-08-01-bfl-commercial-licensing.md` | ranks the commercial routes with price estimates and names the critical path — business direction |
| `research/2026-04-09-legal-font-sources.md` | an April Oracle report asserting named vendors' licence terms with "high confidence" and carrying foundry contact addresses — a legal and reputational exposure, not a finding |
| **the product recipe** (36 files, listed in `misc/export_public.py` as `RECIPE`) | `app.py`, the description-to-reference generator, the constructed-reference builder and its probes, the picker analyses and their tests, five result records, and the 15 late-August notes on which reference generators were tried and how the picker behaves. See *The SaaS lane* below |
| `docs/archive/` (5) | stale 2026-03 planning whose links point at the files above |
| `docs/superpowers/` (15) | agent-workflow plans and specs that cite the withheld research by section; the same directory is withheld from the owner's other public repositories for the same reason |
| `docs/PUSH-PREP.md` | the private-push runbook; this document supersedes it |

**Everything else is exported byte-for-byte** — the exporter compares every
staged blob and mode with HEAD's and refuses on any difference — including
`CLAUDE.md`, the force-added eval artifacts behind the README results table,
and every negative result. The one exception is the six generated package
indexes (`analysis/README.md` and its siblings), which the exporter
regenerates in the destination so they list what the export contains; they
are the only paths exempt from the identity check, and the run names them.
The research index (`research/README.md`) says where the withheld notes went
rather than linking to files that are not there.

## The SaaS lane — results public, recipe private

Decided 2026-09-11, after the first export. The repository is a portfolio
piece that may become a service, and those pull in opposite directions. The
resolution: **publish the whole model track, every instrument and its
validation, and the product loop's results; withhold the product loop's
implementation and its how-to.**

What that means concretely:

- **Public.** Training, evaluation and analysis code; the coherence,
  identity and adherence instruments with their validation notes; the README
  narrative including *"a style described in words produces a font"* and *"the
  stencil problem is solved"*; the figures; the loop-closes and stencil notes;
  the eval artifacts behind every table. A reader can see exactly what was
  built, how it was measured, and how often it was wrong.
- **Withheld** (`RECIPE` in `misc/export_public.py`, one rule per path so a
  rename makes the script refuse): `app.py` with the picker, the
  description-to-reference generator and its prompts, the constructed-
  reference builder and the probes that proved it, the picker analyses and
  their tests, the five result records those probes wrote, and the fifteen
  late-August notes that spell out which reference generators were tried, at
  what speed and licence, and how the picker behaves.

The line is *ideas and results out, working implementation in*. `CLAUDE.md`
still describes the recipe in prose because it is the working brief for the
archive too; a competitor gets a description, not a pipeline. What actually
protects a service here is not the code in any case — it is the corpus and
provenance work, the weights, and the licence — but the recipe is the part
that would save a copier the most time, and it costs the portfolio nothing
to hold it: the results it produced are all on display.

A kept test that exercised the generator's label rules now skips when the
module is absent; a kept module may not import a withheld one, and a test
pins that.

**Kept on purpose, and worth knowing about:** `research/corpus_provenance.json`
and `research/unlicensed_corpus_fonts.json` name the 49 proprietary fonts the
early corpus contained and where they came from. They are the evidence behind
a claim the README already makes in plain words (*"the corpus contained 49
fonts under vendor terms permitting rendering but not conversion"*), and
withholding the evidence while publishing the claim would invert this
project's whole posture. A reader who would rather not publish the itemised
list adds one line to `EXCLUDE`.

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
   one. The public tree lacks `font_pool/`, `google-fonts/`, `dataset_*/`,
   model weights and the untracked eval outputs; a test that quietly depended
   on any of them passes privately and fails for every contributor. **`cd`
   into the export first** — `pytest --rootdir` does not change directory, and
   run from the private clone the tests read the private tree's files through
   relative paths and pass for the wrong reason. Measured 2026-09-11: private
   356 passed, 0 skipped; export 327 passed, **29 skipped** — the corpus-
   dependent font-quality and variable-font pairing tests, potrace, and the
   two model downloads. "Green publicly" is weaker than "green privately" by
   exactly that list; CI prints it with `-rs` so it stays visible.
4. **Every commit in the export is authored by the GitHub noreply address.**
   The exporter refuses to commit under anything else, so a second export
   from another machine cannot publish a personal email. Check the pushed
   result too: `git -C ../digital-rain log --format=%ae | sort -u` must print
   one `@users.noreply.github.com` line.

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
  A checkbox is not a rights assignment. So **outside pull requests are held,
  not merged, until a licence or a contributor agreement exists** —
  `CONTRIBUTING.md` says so up front. AGPL-3.0 plus a commercial licence for
  paying customers is the usual open-core arrangement and is the one `LICENSE`
  points at; choosing it is the decision that unblocks contributions.

## Runbook

Run from the private clone (`repos/fonts`). Every step before the last is
reversible.

```bash
# 0. gates
python -m pytest                                   # green privately
python misc/export_public.py --list                # read the partition

# 1. rename the private repository. GitHub redirects the old URL ONLY until
#    step 3 creates a new repository under it -- after that, any clone or
#    automation still pointing at sushiHex/digital-rain reaches the fresh
#    public repository, not the archive. Update every remote you have first.
gh repo rename digital-rain-private -R sushiHex/digital-rain --yes
git remote set-url origin https://github.com/sushiHex/digital-rain-private.git

# 2. build the public tree next to this clone, review it, commit it
python misc/export_public.py --dest ../digital-rain            # stages; sanitizer runs
git -C ../digital-rain status                                  # read it
python misc/export_public.py --dest ../digital-rain --commit
(cd ../digital-rain && FONTGEN_NO_MODEL_DOWNLOADS=1 python -m pytest -rs)   # green IN the export
git -C ../digital-rain log --format=%ae | sort -u                           # one noreply address

# 3. create the public repository PRIVATE first, push, verify, then flip
gh repo create sushiHex/digital-rain --private --source ../digital-rain --remote origin --push
gh repo view sushiHex/digital-rain --json visibility,defaultBranchRef
gh run list -R sushiHex/digital-rain            # CI green on the initial commit
# labels, settings and branch protection: python misc/configure_public_repo.py

# 4. the irreversible step -- owner only, after reading steps 0-3's output
gh repo edit sushiHex/digital-rain --visibility public --accept-visibility-change-consequences
python misc/configure_public_repo.py --repo sushiHex/digital-rain   # again: secret scanning only exists on public repos
```

Steps 1–3 were run on 2026-09-11. `digital-rain-private` is renamed and
carries `main` plus the parked `wip/monospace-constructor` branch; the new
`digital-rain` holds the export as one initial commit, private, with labels,
settings and branch protection applied and CI running. Step 4 has **not** been
run.

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
  in public would revert them. So the exporter **enforces the cutover**: it
  re-exports only into a tree whose every commit it wrote itself, and refuses
  the moment the public history holds a commit it did not make. Before that
  moment, re-exporting to fix the initial release is allowed and was done
  (three export commits); after it, the private archive is read-only for
  public purposes. `misc/export_public.py` stays in the public tree because it
  documents what was withheld and refuses to run there.
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
  head branch deleted on merge. **`enforce_admins` is off**, so the owner can
  bypass all of it; the rules bind contributors, not the single maintainer,
  who has no second reviewer to open a pull request against. Turn it on when
  a second maintainer joins.
- **A first-time contributor's workflow run waits for the owner's approval**
  (GitHub's default for pull requests from new forks). Until it is approved
  the required checks never report, so the PR looks blocked; the approval
  button is on the PR's Checks tab.
- `CLAUDE.md` stays: it is the project's conventions, it is what an agent
  working on a contributor's machine reads first, and everything in it is
  public-safe.

## Cross-review, 2026-09-11 — what was adopted and what was not

An independent model reviewed the export design, the sanitizer, the runner
move, the CI and the licence posture against the source (22 findings). What
changed because of it, and what was rejected with the reason, so it is not
re-litigated:

**Adopted.** The listing now prints the kept half, not only the withheld one
(a newly tracked file lands in the kept half with no other signal). Two more
research files withheld (the commercial-route note and the vendor-licence
survey). The exporter refuses a destination that is, contains, or sits inside
the private repository or is a symlink; refuses to re-export over a tree with
commits it did not write; verifies every staged blob and mode against HEAD;
sets the executable bit Windows cannot; refuses to commit under a non-noreply
address. All 43 runners were tracked as `100644` and would have been
"Permission denied" on Linux — now `100755`, pinned by a test. The sanitizer
gained Linux, macOS and UNC home paths, fine-grained GitHub, AWS, Slack and
bearer token shapes, and a hard block on tracked fonts, weights and archives.
CI lists its skips and runs checksum-pinned gitleaks over the whole history,
because GitHub's own secret scanning starts only after the flip. The
configuration script propagates failures and enables private vulnerability
reporting, the channel `SECURITY.md` promises. The runbook's gate-3 command
did not `cd` into the export and would have read private files; fixed. The
name-reuse consequence for the rename redirect is stated. Outside pull
requests are held until a licence exists. `LICENSE` names the Apache-2.0
components it does not cover.

**Rejected, with reasons.** *Withhold `docs/strategy-2026-08.md`* — read in
full, it is a technical scorecard of a research plan with one sentence
mentioning a commercial model; not business material. *Withhold the corpus
provenance records* — they are the evidence for a claim the README makes
openly; see above. *`pip install -e .` is broken* — verified with a dry run
on 2026-09-11: the editable build succeeds; the README keeps it and now also
shows CI's dependency-only install. *Turn on `enforce_admins`* — deliberately
off for a single maintainer with no second reviewer; documented above, to be
flipped when that changes. *Pin dependencies with hashes* — accepted as a
known weakness and stated in the workflow; a research repository with `>=`
floors is not going to carry a lockfile yet.

## Record

| date | what |
|---|---|
| 2026-07-29 | private push audit (`PUSH-PREP.md`) |
| 2026-08-18 | MIT withdrawn; all rights reserved pending a decision |
| 2026-08-24 | sanitizer caught a home path that entered via a session capture |
| 2026-09-11 | sanitizer found to miss JSON-escaped paths; fixed and pinned. Runners moved to `runners/`. Exporter written. Decision to go public via a fresh repository. Steps 1–3 run: renamed, exported, private-first `digital-rain` created, configured, CI green. Cross-review (22 findings) folded in. The SaaS-lane carve-out decided and applied: 550 files public, 86 withheld. Step 4 not run. |
