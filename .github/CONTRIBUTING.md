# Contributing to digital-rain

Contributions are welcome, from people and from coding agents. If you are an
agent, treat this file and `CLAUDE.md` as binding for any pull request you
open here.

## Public development, private archive

**This public repository is the development home.** Code, issues, reviews and
pull requests live here; branch from `main` and merge reviewed pull requests
into it. `sushiHex/digital-rain-private` is the full-history archive and holds
what is withheld from publication — session captures, the March 2026 business
research, superseded planning. It is not the upstream for public code, and
nothing is re-exported over public `main`. What was withheld, and why, is
stated in [`docs/public-release.md`](../docs/public-release.md) and printed by
`python misc/export_public.py --list`.

## Dev setup

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu   # or the CUDA index, README Setup
pip install -r requirements.txt gradio pytest
python -m pytest
```

**No GPU is needed to contribute.** The suite passes without a GPU, the font
corpus, model weights, potrace or a network — tests that need any of those
skip — and it must stay that way: a new test must not load a model, hit the
network, assume CUDA, or read a file outside the repository. CI runs
`python -m pytest` on a CPU-only Linux runner with
`FONTGEN_NO_MODEL_DOWNLOADS=1`; if it does not pass there, it does not merge.

Training, the eval harness and the product loop need the GPU and are run by
hand. Results from them are reported with their noise, not as CI output.

## What a pull request must include

1. **Tests, written first.** A fix needs the regression test that fails
   without it; say so in the description.
2. **A green suite locally**, and the exact commands you ran. "Suite green"
   only if you ran it.
3. **Honest numbers.** Any number entering `README.md`, `CLAUDE.md`, a
   research note or a package README states the metric, the effect divided by
   **that metric's own** SD, and the seeds and fonts or families it rests on.
   Read the first four sections of `CLAUDE.md` before quoting anything:
   `char_acc` is not letter correctness, a single-seed A/B cannot resolve a
   model difference, and training-run variance swallows most of the record.
   Model-track and product-track numbers are never compared.
4. **Pre-registration for any measurement.** The bar, the statistic and the
   sample are fixed in the script's docstring and **committed before the data
   is produced**, so the commit timestamp proves the bar preceded the result.
   Link that commit in the pull request. A result without a registration is
   exploratory and is labelled as such.
5. **The public boundary respected.** No secrets, home-directory paths,
   machine names or session URLs (`python analysis/sanitize_for_publish.py
   --check` passes, and CI runs it). No font files, weights or generated fonts
   — both licensing blockers in the README are unresolved.
6. **Docs updated** when behaviour changes. `CLAUDE.md` is the agent-facing
   brief and must stay truthful; `README.md` is user-facing; dated notes in
   `research/` are never rewritten — add a marked correction or a new note.

## Conventions

- Python 3.12+. `python`, not `python3`; `python -m pytest`, not bare `pytest`.
- Local imports are package-qualified (`from analysis.compare_runs import …`);
  package modules keep the two-line `sys.path` bootstrap so both
  `python pkg/x.py` and `python -m pkg.x` work.
- Findings go in `research/YYYY-MM-DD-slug.md`; architecture in `docs/`; no
  loose `.md` in the repo root except `README.md`, `CLAUDE.md` and `AGENTS.md`.
- Package READMEs are generated: `python misc/sync_package_readmes.py --fix`.
- Commit subjects are `type: what changed, in plain words` (`fix:`, `feat:`,
  `research:`, `docs:`, `viz:`, `chore:`), and the body says why.
- Windows and Linux both matter: `pathlib` or forward slashes, no drive
  letters, no hardcoded separators.
- Negative results are recorded, not deleted.

## Rights

The repository is published **without a licence** (`LICENSE` explains why, and
what AGPL-3.0 and BSL 1.1 would each mean). Until one is chosen, submitting a
pull request means you hold the rights to what you submit and agree the
copyright holder may distribute it under whatever licence this repository
adopts. The pull request template asks you to confirm that.

**Until a licence or a contributor agreement is in place, pull requests from
outside the maintainer are reviewed but held, not merged.** A checkbox is not
a rights assignment, and merging outside code into an unlicensed tree would
cloud any later relicensing. Issues, findings and review comments are welcome
now; code lands once the licence question is settled.

## Reporting

Issues use the forms: bug, research finding, proposal or decision, work item.
Vulnerabilities go through
[private vulnerability reporting](https://github.com/sushiHex/digital-rain/security/advisories/new),
never a public issue.
