# Security policy

This is a research repository: training and evaluation scripts, analysis
tools, and a local Gradio demo. Nothing here is meant to be exposed to an
untrusted network, and no hosted service exists.

## Reporting a vulnerability

Use GitHub's **Report a vulnerability** form on the repository's Security tab.
It creates a private advisory visible to the maintainer. Do not open a public
issue for an undisclosed vulnerability.

Include the affected commit, the component, minimal reproduction steps, and
the impact. Replace any sensitive value with `[REDACTED]`.

## What counts

- Code that reads or writes outside the repository or the paths it is told
  to use, or that follows a path from an untrusted input.
- A script that would leak local state into a tracked file: the publication
  gate (`analysis/sanitize_for_publish.py`) exists because that has happened.
- Anything that fetches and executes remote content without pinning it.

Font files, model weights and generated fonts carry licensing questions, not
security ones; those go in an issue, not an advisory. See the README's
Licensing section.

## Response

Best effort, no fixed timeline. The maintainer will reproduce against an
exact commit and coordinate disclosure after a fix or a documented mitigation
exists.
