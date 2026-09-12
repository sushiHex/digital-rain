"""Build the treatment the generator will not draw, onto the style it will.

WHY THIS EXISTS. No text-to-image model will invent a stencil -- sixteen images
across three mechanisms, no break anywhere. But the glyph-conditioned LoRA
PROPAGATES a treatment it is handed, to the ninety-two letters it was never
given (`research/2026-08-28-hand-it-a-stencil-and-it-propagates-one.md`). So
for the rare treatments the answer is geometry, not a better generator.

THE DESIGN DECISION THAT MATTERS. The obvious version applies the treatment to a
NEUTRAL font. That throws the description away: "a heavy angular blackletter
stencil" would come back as a stencilled plain sans, with the blackletter lost.

So the treatment is applied to a DRAWN CANDIDATE instead. The generator supplies
the style it is good at; geometry supplies the treatment it refuses. The
constructed reference then carries both, and it is built from the most coherent
candidate rather than an arbitrary one, because `reference_gate` already ranks
them and a treatment applied to an incoherent pair inherits the incoherence.

WHAT THIS IS NOT. It does not make the generator better, and it does not cover
every rare attribute -- only the three that can be constructed by an existing
transform. Anything else a user types is still bounded by what the model draws.
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import re

# Detection is deliberately NARROW. A loose pattern would construct a stencil
# for "a face with no stencil breaks", and a false construction is worse than a
# missing one: it puts an option in front of the user that they did not ask for.
TREATMENTS = {
    "stencil": r"\bstencil(?:led|s)?\b",
    "inline": r"\binline\b",
    "outline": r"\boutline[dn]?\b",
}

# A negation anywhere in the clause suppresses detection. Cheap, and it covers
# the phrasings the twelve prompt set actually uses ("no ...", "without ...").
NEGATION = r"\b(?:no|not|without|never|un)\b[^.,;]{0,24}$"


def detect(description):
    """Treatment names a description asks for, in a fixed order.

    Returns [] when nothing matches, which is the common case -- eight of the
    twelve prompt set name no constructible treatment at all.
    """
    text = (description or "").lower()
    found = []
    for name, pattern in TREATMENTS.items():
        m = re.search(pattern, text)
        if not m:
            continue
        if re.search(NEGATION, text[:m.start()]):
            continue
        found.append(name)
    return found


def best_candidate(paths, chars=None):
    """The most coherent of a set of references, by the gate's own distance.

    Falls back to the first path when nothing can be scored, rather than
    refusing -- this is a convenience, and it must never be the reason a
    constructed option is withheld.
    """
    try:
        from analysis.reference_gate import reference_consistency
        from analysis.style_coherence import load_stats

        stats = load_stats()
        scored = []
        for p in paths:
            rc = reference_consistency(p, stats, chars=chars or "Kg")
            if rc:
                scored.append((rc["distance"], p))
        if scored:
            return min(scored)[1]
    except Exception:                                  # noqa: BLE001
        pass
    return paths[0] if paths else None


def construct(source_path, treatment, seed=0):
    """Apply one treatment to a reference image. Returns a PIL image or None."""
    try:
        import numpy as np
        from PIL import Image

        from analysis.synthesise_transforms import (draw_params,
                                                    transform_reference)

        params = draw_params(np.random.default_rng(seed))
        with Image.open(source_path) as im:
            return transform_reference(im.convert("RGB"), treatment, params)
    except Exception:                                  # noqa: BLE001
        return None


def build(description, paths, seed=0):
    """(treatment, PIL image) for every treatment the description asks for.

    Empty when the description names none, when no source can be chosen, or
    when a transform fails -- all of which are ordinary, not errors.
    """
    treatments = detect(description)
    if not treatments:
        return []
    source = best_candidate(paths)
    if source is None:
        return []
    out = []
    for name in treatments:
        img = construct(source, name, seed=seed)
        if img is not None:
            out.append((name, img))
    return out
