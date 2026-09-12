"""Do variable-font named instances carry STRUCTURAL diversity, or cosmetic?

atlas_constants.load_truetype_pinned pins every variable font to "Regular", so
the corpus trains on exactly one instance per font and axes like Bitcount's
ELSH/ELXP (element shape/expansion), Sixtyfour/Workbench's BLED/SCAN (bleed,
scanline) and Doto's ROND (roundness) are unused. 13 distinctive variable fonts
hold 128 named instances between them.

If instances are structurally diverse, instancing multiplies the distinctive
tail (93 fonts) without any new font files -- aimed exactly at the failure
mode. If they are cosmetic (weight-only), it adds near-duplicates and the
redistribution ceiling applies.

Test: render every named instance, embed, and compare the instance spread
against two reference scales measured on the same metric --
  (a) the spread ACROSS distinct distinctive fonts (the "real diversity" bar)
  (b) the spread across weight-only variants (the "cosmetic" floor)

  python probes/spike_variable_instances.py
"""

# repo root on sys.path so `python probes/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import json

import numpy as np
from fontTools.ttLib import TTFont

import build_dataset
from analysis.select_expansion_set import embed_atlas, index_fonts
from atlas_constants import CANVAS

PROBE = [
    "Bitcount[CRSV,ELSH,ELXP,slnt,wght]",
    "Doto[ROND,wght]",
    "Sixtyfour[BLED,SCAN]",
    "Workbench[BLED,SCAN]",
]


_INDEX = None


def find_ttf(stem):
    """Exact-stem lookup over the repo's font search path.

    index_fonts() is the single home for that path; this only memoizes it,
    because the walk covers ~18k files across four trees.
    """
    global _INDEX
    if _INDEX is None:
        _INDEX = index_fonts(("google-fonts", "font_pool", "font_pool_selected",
                              "extra-fonts"))
    return _INDEX.get(stem)


def render_instance(path, instance_name):
    """render_atlas, but pinned to a NAMED instance rather than to coordinates.

    Distinct from select_expansion_set.render_coords, which pins explicit axis
    values; both go through render_atlas's loader parameter rather than
    swapping a module global.
    """
    from PIL import ImageFont

    def loader(font_path, size):
        f = ImageFont.truetype(str(font_path), size)
        f.set_variation_by_name(instance_name)
        return f

    return np.asarray(
        build_dataset.render_atlas(path, CANVAS, loader=loader).convert("RGB"))


def mean_pairwise_distance(V):
    """Mean pairwise cosine distance within a set of unit vectors."""
    if len(V) < 2:
        return float("nan")
    S = V @ V.T
    iu = np.triu_indices(len(V), k=1)
    return float(1.0 - S[iu].mean())


def main():
    from cleanup.models import build_dino_embed_fn
    embed_fn = build_dino_embed_fn()

    # Reference scale (a): spread across DISTINCT distinctive corpus fonts.
    corpus = json.load(open("research/font_distinctiveness.json"))["scores"]
    p90 = np.percentile(np.array(list(corpus.values())), 90)
    top = sorted((k for k in corpus if corpus[k] >= p90), key=lambda k: -corpus[k])[:12]
    V = []
    for stem in top:
        p = find_ttf(stem)
        if not p:
            continue
        try:
            V.append(embed_atlas(np.asarray(
                build_dataset.render_atlas(p, CANVAS).convert("RGB")), embed_fn))
        except Exception:
            continue
    across_fonts = mean_pairwise_distance(np.stack(V))
    print(f"REFERENCE (a) mean pairwise distance across {len(V)} distinct "
          f"distinctive fonts: {across_fonts:.4f}")

    print(f"\n{'font':40}{'instances':>10}{'spread':>9}   vs reference")
    for stem in PROBE:
        p = find_ttf(stem)
        if not p:
            print(f"  {stem[:38]:38} NOT FOUND")
            continue
        f = TTFont(p, lazy=True)
        labels = [f["name"].getDebugName(i.subfamilyNameID)
                  for i in f["fvar"].instances]
        vecs, ok = [], []
        for nm in labels:
            try:
                vecs.append(embed_atlas(render_instance(p, nm), embed_fn))
                ok.append(nm)
            except Exception:
                continue
        if len(vecs) < 2:
            print(f"  {stem[:38]:38} only {len(vecs)} instance(s) rendered")
            continue
        spread = mean_pairwise_distance(np.stack(vecs))
        pct = 100 * spread / across_fonts
        print(f"  {stem[:38]:38}{len(ok):>10}{spread:>9.4f}   {pct:5.1f}% of across-font")


if __name__ == "__main__":
    main()
