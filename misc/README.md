# misc/

**Uncategorized utilities.**

Model merging, model listing, validation helpers.

Run from the repo root, either way:

```bash
python misc/<script>.py --help
python -m misc.<script> --help
```

Scripts import repo-root modules (`atlas_constants`, `eval_checkpoint`, ...); a two-line
`sys.path` bootstrap at the top of each makes direct-path invocation work too.

## Contents (12)

- `backup_private.py` — Back up the non-available data into `backup/` in the private repository, verify it, and restore it -- never de...
- `configure_public_repo.py` — Apply the public repository's labels, settings and branch protection with `gh`.
- `count_running.py` — Count the live processes whose command line contains every given substring.
- `export_public.py` — Export the public tree: every file tracked at HEAD, minus a stated exclusion list.
- `route_b_cache.py` — First-block (FB) step-caching ported to the patched FLUX.2 forward (Route B).
- `sync_package_readmes.py` — Regenerate each package README's `## Contents (N)` list from module docstrings.
- `test_flux2_glyphs.py` — Test FLUX.2-klein-4B for generating font glyph images on RTX 3090.
- `test_flux_glyphs.py` — Test Flux.1 Dev for generating font glyph images on RTX 3090.
- `test_nunchaku.py` — Trial: Nunchaku (SVDQuant W4A4/INT4) FLUX.2-klein-9B + Ref2Font V3 LoRA on the 3090.
- `test_refs.py` — Quick 10-step training test comparing reference character candidates.
- `test_repair.py` — Test the NeutralPaste repair stage on the SAVED 8-seed atlases (no generation): consensus vs consensus + verif...
- `test_sdedit_repair.py` — Compare repair strategies on saved 8-seed atlases (consensus base): consensus  |  + NeutralPaste repair  |  +...
