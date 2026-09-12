"""Apply the Route B patch to a fresh .venv-nunchaku.

The Route B edits live in a vendored file inside the (gitignored) venv:
  nunchaku/models/transformers/transformer_flux2.py
If the venv is rebuilt, run this to restore them.

Usage:
  ./.venv-nunchaku/Scripts/python.exe route_b/apply_route_b_patch.py

It copies route_b/transformer_flux2.patched.py over the installed file (after a
backup). The installed base must be tonera PR #926 (feat/flux2-klein_nunchaku);
the script refuses if it can't find that file. route_b/route_b.patch is the
human-readable unified diff of exactly what changed.
"""
import shutil
from pathlib import Path

import nunchaku


def main():
    target = Path(nunchaku.__file__).parent / "models" / "transformers" / "transformer_flux2.py"
    patched = Path(__file__).parent / "transformer_flux2.patched.py"
    if not target.exists():
        raise SystemExit(
            f"FLUX.2 transformer not found at {target}. The base must be tonera "
            "PR #926 (feat/flux2-klein_nunchaku) hot-patched into nunchaku."
        )
    if not patched.exists():
        raise SystemExit(f"patched reference missing: {patched}")

    cur = target.read_text(encoding="utf-8")
    if "_FORCE_UNFUSED_QKV" in cur:
        print(f"already patched: {target}")
        return
    backup = target.with_suffix(".py.preroutb.bak")
    shutil.copy2(target, backup)
    shutil.copy2(patched, target)
    after = target.read_text(encoding="utf-8")
    assert "_FORCE_UNFUSED_QKV" in after, "patch copy failed"
    print(f"patched {target}\n  backup: {backup}")
    print("verify: set NUNCHAKU_FORCE_UNFUSED_QKV=1 before importing nunchaku, then load_v3_into_nunchaku().")


if __name__ == "__main__":
    main()
