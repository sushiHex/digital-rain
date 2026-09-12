# AGENTS.md

`CLAUDE.md` is the project brief for every coding agent, whatever it is
called. Read it first and in full: it records what the metrics measure, which
tracks are closed and why, the guards that must not be weakened, and the
statistics that have already been got wrong here. Then read
[`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md) for what a pull request
must include.

Three rules that agents break most:

- **Report outcomes faithfully.** "Suite green" only if you ran it. A number
  is reported with its own metric's noise or not at all.
- **Pre-register before measuring.** Commit the bar, then produce the data.
- **Nothing from the private archive comes here.** `docs/public-release.md`
  says what is withheld; `python analysis/sanitize_for_publish.py --check`
  must pass before every push.
