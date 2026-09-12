"""The denoising trajectory: noise into a typeface, one frame per step.

WHAT THIS ACTUALLY CAPTURES, AND WHY THE DISTINCTION MATTERS. These are the
INTERMEDIATE LATENTS OF ONE 20-STEP RUN, decoded at every step. That is not the
same thing as running the model at 1, 2, 3 ... steps and collecting the results:
a 3-step run follows a different noise schedule and is a different trajectory,
not a snapshot of this one. Both are legitimate figures and they answer
different questions -- "how does an atlas emerge" against "how many steps do I
need". This is the first.

HOW THE FRAMES ARE DECODED, AND WHY IT IS VERIFIED. `callback_on_step_end`
hands back PACKED latents, which are meaningless as an image until they are
unpacked, denormalised against the VAE's batch-norm statistics, unpatchified and
decoded. That is four chances to get a transform backwards and still produce a
plausible-looking animation -- exactly the shape of error this repository keeps
logging.

So the decode is VALIDATED rather than trusted: the final captured latent is
decoded by this file's own code and compared against the image the PIPELINE
returned. They must agree. The tool prints the mean absolute difference and
refuses to write a GIF if it exceeds VALIDATE_TOL.

`latent_ids` are not exposed to the callback, so `prepare_latents` is wrapped to
record the ids the run actually used. The wrapper observes and returns the
original value unchanged; it does not alter generation.

  python viz/generation_progression.py
  python viz/generation_progression.py --reference <path> --steps 20 --word Hamburg
"""
import argparse
import glob
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from atlas_constants import CANVAS, CHARSET                      # noqa: E402
from eval_checkpoint import crop_cell                            # noqa: E402
from viz._common import OUT, REPO, label_font                    # noqa: E402

CHECKPOINT = os.environ.get("FONTGEN_CHECKPOINT",
                            os.path.join("training_glyph_4b_r32_5000",
                                         "checkpoint-5000"))
MODEL_4B = "black-forest-labs/FLUX.2-klein-base-4B"

# A distinctive but legible style, so the emergence is visible rather than
# merely plausible. Falls back to any holdout reference.
DEFAULT_REFS = [
    os.path.join(REPO, "eval_runs", "_candidate_refs", "klein-base-n4",
                 "02-a_chunky_slab_serif_with_blu__s0.png"),
    os.path.join(REPO, "eval_runs", "_synthetic_refs", "oracle"),
]

WORD = "Hamburg"
STEPS = 20
SEED = 42
NEED_MB = 12000
VALIDATE_TOL = 2.0        # mean |diff| out of 255, my decode vs the pipeline's
FRAME_MS = 220
HOLD_MS = 1600            # linger on the finished frame


def free_vram_mb():
    import subprocess
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.free",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=30)
        return int(out.stdout.strip().splitlines()[0])
    except Exception:                                  # noqa: BLE001
        return None


def pick_reference(explicit=None):
    if explicit:
        return explicit if os.path.isfile(explicit) else None
    for cand in DEFAULT_REFS:
        if os.path.isfile(cand):
            return cand
        if os.path.isdir(cand):
            hits = sorted(glob.glob(os.path.join(cand, "*.png")))
            if hits:
                return hits[0]
    return None


def word_strip(atlas, word=WORD, scale=0.62):
    """Compose `word` from an atlas array's own cells, trimmed and butted up."""
    tiles = []
    for ch in word:
        idx = CHARSET.index(ch)
        cell = crop_cell(np.stack([atlas] * 3, -1), idx)[:, :, 0]
        cols = np.flatnonzero((cell > 40).any(axis=0))
        if len(cols):
            cell = cell[:, max(0, cols[0] - 2):cols[-1] + 3]
        tiles.append(cell)
    h = tiles[0].shape[0]
    gap = np.zeros((h, 6), dtype=tiles[0].dtype)
    joined = np.concatenate(
        [t for pair in zip(tiles, [gap] * len(tiles)) for t in pair][:-1],
        axis=1)
    img = Image.fromarray(joined, mode="L").convert("RGB")
    return img.resize((int(img.width * scale), int(img.height * scale)),
                      Image.LANCZOS)


def decode_latents(pipe, latents, latent_ids, height=CANVAS, width=CANVAS):
    """Packed latents -> PIL image, copying the pipeline's own final block.

    Kept as a literal transcription of `Flux2KleinPipeline.__call__`'s decode so
    a divergence is visible as a diff rather than hidden in a paraphrase.
    """
    import torch

    # no_grad, because the VAE's parameters require grad and `postprocess`
    # calls .numpy() on the result. Without it the decode raises rather than
    # returning something subtly wrong, which is the better failure -- but it
    # still costs a whole generation to discover, hence the latent cache.
    with torch.no_grad():
        latent_height = 2 * (int(height) // (pipe.vae_scale_factor * 2))
        latent_width = 2 * (int(width) // (pipe.vae_scale_factor * 2))
        lat = pipe._unpack_latents_with_ids(latents, latent_ids,
                                            latent_height // 2, latent_width // 2)
        bn_mean = pipe.vae.bn.running_mean.view(1, -1, 1, 1).to(lat.device,
                                                                lat.dtype)
        bn_std = torch.sqrt(
            pipe.vae.bn.running_var.view(1, -1, 1, 1)
            + pipe.vae.config.batch_norm_eps
        ).to(lat.device, lat.dtype)
        lat = lat * bn_std + bn_mean
        lat = pipe._unpatchify_latents(lat)
        image = pipe.vae.decode(lat, return_dict=False)[0]
        return pipe.image_processor.postprocess(image, output_type="pil")[0]


def compose(strip, atlas_img, step, total, thumb=190):
    """One frame: the word large, the whole atlas small, and the step count."""
    pad, gap = 18, 16
    thumb_img = atlas_img.resize((thumb, thumb), Image.LANCZOS)
    w = pad * 2 + thumb + gap + max(strip.width, 320)
    h = pad * 2 + max(thumb, strip.height + 34)
    frame = Image.new("RGB", (w, h), (14, 14, 14))
    frame.paste(thumb_img, (pad, (h - thumb) // 2))
    frame.paste(strip, (pad + thumb + gap, (h - strip.height) // 2 + 12))
    draw = ImageDraw.Draw(frame)
    label = "noise" if step == 0 else f"step {step} / {total}"
    draw.text((pad + thumb + gap, pad - 4), label,
              fill=(235, 235, 235), font=label_font(19, bold=True))
    return frame


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--reference", default=None)
    ap.add_argument("--steps", type=int, default=STEPS)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--word", default=WORD)
    ap.add_argument("--checkpoint", default=CHECKPOINT)
    args = ap.parse_args()

    ref_path = pick_reference(args.reference)
    if ref_path is None:
        print("no reference image found; pass --reference", file=sys.stderr)
        return 2
    free = free_vram_mb()
    if free is not None and free < NEED_MB:
        print(f"refusing to start: {free} MiB free, need {NEED_MB}. The 3090 is "
              "shared -- wait, do not evict.", file=sys.stderr)
        return 2

    import torch

    from conditioning_config import expected_conditioning
    from generation_lib import load_generation_pipe

    # Conditioning comes FROM THE CHECKPOINT. Hardcoding it is how candidate_gen
    # mis-conditioned every candidate it ever produced.
    cond = expected_conditioning(args.checkpoint) or {}
    print(f"reference:  {os.path.basename(ref_path)}")
    print(f"checkpoint: {args.checkpoint}")
    print(f"conditioning: prompt_style={cond.get('prompt_style')} "
          f"ref_chars={cond.get('reference_chars')} "
          f"use_template={cond.get('use_template')}")

    pipe, prompt_embeds, neg_embeds = load_generation_pipe(
        args.checkpoint,
        use_template=cond.get("use_template", True),
        template_pt=cond.get("template_pt"),
        model=MODEL_4B,
        reference_chars=cond.get("reference_chars"),
        prompt_style=cond.get("prompt_style"),
    )

    # `latent_ids` never reach the callback, so record what the run used. This
    # observes and returns the original value; it does not change generation.
    captured = {}
    original_prepare = pipe.prepare_latents

    def spy_prepare(*a, **k):
        out = original_prepare(*a, **k)
        captured.setdefault("latent_ids", out[1])
        return out

    pipe.prepare_latents = spy_prepare

    frames_latents = []

    def on_step(p, i, t, kwargs):
        frames_latents.append(kwargs["latents"].detach().clone())
        return kwargs

    ref = Image.open(ref_path).convert("RGB")
    ref_small = ref.resize((512, 512), Image.LANCZOS)

    print(f"\ngenerating {args.steps} steps ...")
    result = pipe(
        prompt_embeds=prompt_embeds,
        negative_prompt_embeds=neg_embeds,
        image=[ref_small],
        height=CANVAS, width=CANVAS,
        num_inference_steps=args.steps,
        generator=torch.Generator("cpu").manual_seed(args.seed),
        callback_on_step_end=on_step,
        callback_on_step_end_tensor_inputs=["latents"],
    ).images[0]
    pipe.prepare_latents = original_prepare

    if "latent_ids" not in captured:
        print("prepare_latents was never called; cannot decode", file=sys.stderr)
        return 2
    print(f"captured {len(frames_latents)} intermediate latents")

    # CACHE BEFORE DECODING. Generation is minutes; decoding is seconds, and
    # the decode is the fiddly half. A bug there should not cost another run --
    # which it did once, on a missing no_grad.
    cache = os.path.join(OUT, "progression", "latents.pt")
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    torch.save({"latents": [t.cpu() for t in frames_latents],
                "latent_ids": captured["latent_ids"].cpu(),
                "reference": ref_path, "steps": args.steps, "seed": args.seed},
               cache)
    print(f"cached latents to {cache}")

    # --- VALIDATE the decode against the pipeline's own output ------------
    mine_final = decode_latents(pipe, frames_latents[-1], captured["latent_ids"])
    diff = float(np.abs(np.asarray(mine_final, dtype=float)
                        - np.asarray(result, dtype=float)).mean())
    print(f"\n  decode check: mean |diff| vs the pipeline's own image = {diff:.3f}"
          f"  (tolerance {VALIDATE_TOL})")
    if diff > VALIDATE_TOL:
        print("  DECODE DOES NOT MATCH. Refusing to write a GIF from frames "
              "this file cannot prove it decoded correctly.", file=sys.stderr)
        return 2
    print("  matches -- the intermediate frames are decoded the same way.\n")

    out_dir = os.path.join(OUT, "progression")
    os.makedirs(out_dir, exist_ok=True)
    frames, total = [], len(frames_latents)
    for i, lat in enumerate(frames_latents, start=1):
        img = mine_final if i == total else decode_latents(
            pipe, lat, captured["latent_ids"])
        atlas = np.asarray(img.convert("L"))
        img.save(os.path.join(out_dir, f"step_{i:02d}.png"))
        frames.append(compose(word_strip(atlas, args.word), img, i, total))
        print(f"  decoded step {i}/{total}", flush=True)

    gif = os.path.join(OUT, "generation_progression.gif")
    durations = [FRAME_MS] * (len(frames) - 1) + [HOLD_MS]
    frames[0].save(gif, save_all=True, append_images=frames[1:],
                   duration=durations, loop=0, optimize=True)
    kb = os.path.getsize(gif) // 1024
    print(f"\nwrote {gif}  ({len(frames)} frames, {kb} KB)")
    print(f"wrote {out_dir}/step_NN.png  (full atlases)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
