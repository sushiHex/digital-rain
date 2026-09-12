## What and why

<!-- One paragraph: the problem, the change, the mechanism. Link the issue;
     use "Refs #N" for partial work and "Closes #N" only when this finishes it. -->

## Evidence

<!-- The exact commands you ran and what they printed. "Suite green" only if
     you ran it. State the checks you did not run and why. -->

- [ ] `python -m pytest` green locally; new tests are GPU-free (no model loads, no network, no CUDA, no files outside the repository)
- [ ] Tests written first for behaviour changes; for a fix, the regression test fails without it (say so)
- [ ] Docs updated when behaviour changed (`CLAUDE.md` is the agent-facing brief and must stay truthful; `README.md` is user-facing)
- [ ] Cross-platform: `pathlib` or forward slashes, no drive letters, no hardcoded separators

## Any number this adds to the record?

<!-- README, CLAUDE.md, a research note, a package README. -->

- [ ] No number is added or changed
- [ ] A number is added or changed, and below it states: the metric, the effect divided by **that metric's own** SD (CLAUDE.md, *TRAINING-run variance*), seeds and fonts or families, and whether the bar was committed before the data (link the registration commit). Model-track and product-track numbers are never compared.

## Public-repository boundary

<!-- This repository is public. The private archive holds what is withheld;
     see docs/public-release.md. -->

- [ ] No secrets, home-directory paths, machine names, session URLs, or private corpora in the diff (`python analysis/sanitize_for_publish.py --check` passes; CI runs it too)
- [ ] No font files, model weights, or generated fonts are added -- both licensing blockers in the README are unresolved
- [ ] Nothing from the private archive is brought over: `research/sessions/`, `docs/archive/`, `docs/superpowers/`, the March 2026 research, or the product recipe (`app.py`, the reference generator, the constructed-reference code, the picker probes and their notes)

## Rights

Code is AGPL-3.0-only, notes and figures CC BY 4.0, records CC0 (`docs/licensing.md`). Outside contributions are accepted under `.github/CLA.md` and are **not merged until the author's line is in `.github/CLA-signatures.md`**.

- [ ] My signature line is in `.github/CLA-signatures.md` (in this PR or an earlier one), or I am the maintainer
- [ ] Anything here that is not my own work is identified with its licence
