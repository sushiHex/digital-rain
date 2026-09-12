"""First-block (FB) step-caching ported to the patched FLUX.2 forward (Route B).

Nunchaku ships FBCache for FLUX.1 / FLUX.1-V2 / SANA but NOT for FLUX.2. This
adapts `cached_forward_v2`'s logic to our NunchakuFlux2Transformer2DModel forward
(which has separate img/txt modulation, our rotary construction, and the
unfused-qkv path). It reuses nunchaku's `check_and_apply_cache` + cache context
unchanged — only the forward + run-remaining helpers are FLUX.2-specific.

Mechanism: run the first double block; if its residual is ~unchanged vs the
previous step (within threshold) reuse the cached aggregate residual and skip the
rest; else compute the rest and cache. With double-fb, same for single blocks.

NOTE: FBCache benefit scales with step count. At 3-4 steps (our sub-minute point)
there's little inter-step redundancy, so the gain is modest; it pays off at high
step counts, which our quality results say we don't need. Measure with spike_cache.py.

Usage:
  from route_b_cache import apply_cache_on_flux2_pipe
  apply_cache_on_flux2_pipe(pipe, residual_diff_threshold=0.12, use_double_fb_cache=True)
"""
import functools

import torch
from diffusers import DiffusionPipeline
from diffusers.models.modeling_outputs import Transformer2DModelOutput

import nunchaku.models.transformers.transformer_flux2 as _tf
from nunchaku.caching.fbcache import cache_context, check_and_apply_cache, create_cache_context


def _double(self, block, h, enc, mod_img, mod_txt, dbl_rotary, jak):
    return block(hidden_states=h, encoder_hidden_states=enc, temb_mod_img=mod_img,
                 temb_mod_txt=mod_txt, image_rotary_emb=dbl_rotary, joint_attention_kwargs=jak)


def _single(self, block, h, mod_single, single_rotary, jak):
    return block(hidden_states=h, encoder_hidden_states=None, temb_mod=mod_single,
                 image_rotary_emb=single_rotary, joint_attention_kwargs=jak)


def _run_remaining_multi(self, hidden_states, encoder_hidden_states, *, rk):
    oh, oe = hidden_states, encoder_hidden_states
    for block in self.transformer_blocks[1:]:
        encoder_hidden_states, hidden_states = _double(
            self, block, hidden_states, encoder_hidden_states,
            rk["mod_img"], rk["mod_txt"], rk["dbl_rotary"], rk["jak"])
    hidden_states = hidden_states.contiguous()
    encoder_hidden_states = encoder_hidden_states.contiguous()
    return hidden_states, encoder_hidden_states, hidden_states - oh, encoder_hidden_states - oe


def _run_remaining_single(self, cat_states, *, rk):
    oc = cat_states
    for block in self.single_transformer_blocks[1:]:
        cat_states = _single(self, block, cat_states, rk["mod_single"], rk["single_rotary"], rk["jak"])
    cat_states = cat_states.contiguous()
    return cat_states, cat_states - oc


def _run_remaining_all(self, hidden_states, encoder_hidden_states, *, rk):
    oh, oe = hidden_states, encoder_hidden_states
    for block in self.transformer_blocks[1:]:
        encoder_hidden_states, hidden_states = _double(
            self, block, hidden_states, encoder_hidden_states,
            rk["mod_img"], rk["mod_txt"], rk["dbl_rotary"], rk["jak"])
    cat_states = torch.cat([encoder_hidden_states, hidden_states], dim=1)
    for block in self.single_transformer_blocks:
        cat_states = _single(self, block, cat_states, rk["mod_single"], rk["single_rotary"], rk["jak"])
    n = rk["num_txt_tokens"]
    enc = cat_states[:, :n, ...].contiguous()
    hid = cat_states[:, n:, ...].contiguous()
    return hid, enc, hid - oh, enc - oe


def cached_forward_flux2(self, hidden_states, encoder_hidden_states=None, timestep=None,
                         img_ids=None, txt_ids=None, guidance=None, joint_attention_kwargs=None,
                         return_dict=True, kv_cache=None, kv_cache_mode=None, num_ref_tokens=0,
                         ref_fixed_timestep=0.0):
    # Caching disabled / unsupported config -> original forward.
    if (self.residual_diff_threshold_multi < 0.0 or kv_cache_mode is not None
            or getattr(self, "offload", False)):
        return self._original_forward(
            hidden_states=hidden_states, encoder_hidden_states=encoder_hidden_states,
            timestep=timestep, img_ids=img_ids, txt_ids=txt_ids, guidance=guidance,
            joint_attention_kwargs=joint_attention_kwargs, return_dict=return_dict,
            kv_cache=kv_cache, kv_cache_mode=kv_cache_mode, num_ref_tokens=num_ref_tokens,
            ref_fixed_timestep=ref_fixed_timestep)

    num_txt_tokens = encoder_hidden_states.shape[1]
    timestep = timestep.to(hidden_states.dtype) * 1000
    if guidance is not None:
        guidance = guidance.to(hidden_states.dtype) * 1000
    temb = self.time_guidance_embed(timestep, guidance)
    mod_img = self.double_stream_modulation_img(temb)
    mod_txt = self.double_stream_modulation_txt(temb)
    mod_single = self.single_stream_modulation(temb)
    hidden_states = self.x_embedder(hidden_states)
    encoder_hidden_states = self.context_embedder(encoder_hidden_states)

    if img_ids.ndim == 3:
        img_ids = img_ids[0]
    if txt_ids.ndim == 3:
        txt_ids = txt_ids[0]
    image_rotary_emb = self.pos_embed(img_ids)
    text_rotary_emb = self.pos_embed(txt_ids)
    if _tf._FORCE_UNFUSED_QKV:
        dbl_rotary = (image_rotary_emb, text_rotary_emb)
        single_rotary = (
            torch.cat([text_rotary_emb[0], image_rotary_emb[0]], dim=0),
            torch.cat([text_rotary_emb[1], image_rotary_emb[1]], dim=0),
        )
    else:
        dbl_rotary = (_tf._pack_flux2_rotary_emb(image_rotary_emb),
                      _tf._pack_flux2_rotary_emb(text_rotary_emb))
        single_rotary = _tf._pack_flux2_rotary_emb((
            torch.cat([text_rotary_emb[0], image_rotary_emb[0]], dim=0),
            torch.cat([text_rotary_emb[1], image_rotary_emb[1]], dim=0),
        ))

    rk = {"mod_img": mod_img, "mod_txt": mod_txt, "mod_single": mod_single,
          "dbl_rotary": dbl_rotary, "single_rotary": single_rotary,
          "jak": joint_attention_kwargs, "num_txt_tokens": num_txt_tokens}
    verbose = getattr(self, "verbose", False)

    # --- MULTI (double) stage ---
    original_hidden_states = hidden_states
    encoder_hidden_states, hidden_states = _double(
        self, self.transformer_blocks[0], hidden_states, encoder_hidden_states,
        mod_img, mod_txt, dbl_rotary, joint_attention_kwargs)
    first_residual_multi = hidden_states - original_hidden_states

    remaining = _run_remaining_multi if self.use_double_fb_cache else _run_remaining_all
    hidden_states, encoder_hidden_states, _ = check_and_apply_cache(
        first_residual=first_residual_multi, hidden_states=hidden_states,
        encoder_hidden_states=encoder_hidden_states, threshold=self.residual_diff_threshold_multi,
        parallelized=False, mode="multi", verbose=verbose,
        call_remaining_fn=lambda hidden_states, encoder_hidden_states, **kw: remaining(
            self, hidden_states, encoder_hidden_states, rk=rk),
        remaining_kwargs={})

    if self.use_double_fb_cache:
        # --- SINGLE stage ---
        cat_states = torch.cat([encoder_hidden_states, hidden_states], dim=1)
        original_cat = cat_states
        cat_states = _single(self, self.single_transformer_blocks[0], cat_states,
                             mod_single, single_rotary, joint_attention_kwargs)
        first_residual_single = cat_states - original_cat
        cat_states, _, _ = check_and_apply_cache(
            first_residual=first_residual_single, hidden_states=cat_states,
            encoder_hidden_states=None, threshold=self.residual_diff_threshold_single,
            parallelized=False, mode="single", verbose=verbose,
            call_remaining_fn=lambda hidden_states, encoder_hidden_states, **kw: _run_remaining_single(
                self, hidden_states, rk=rk),
            remaining_kwargs={})
        hidden_states = cat_states[:, num_txt_tokens:, ...]

    hidden_states = self.norm_out(hidden_states, temb)
    output = self.proj_out(hidden_states)
    if not return_dict:
        return (output,)
    return Transformer2DModelOutput(sample=output)


def apply_cache_on_flux2(transformer, *, use_double_fb_cache=True, residual_diff_threshold=0.12,
                         residual_diff_threshold_multi=None, residual_diff_threshold_single=None):
    if residual_diff_threshold_multi is None:
        residual_diff_threshold_multi = residual_diff_threshold
    if residual_diff_threshold_single is None:
        residual_diff_threshold_single = residual_diff_threshold

    transformer.residual_diff_threshold_multi = residual_diff_threshold_multi
    transformer.residual_diff_threshold_single = residual_diff_threshold_single
    transformer.use_double_fb_cache = use_double_fb_cache
    transformer.verbose = False

    if not getattr(transformer, "_is_flux2_cached", False):
        transformer._original_forward = transformer.forward
        transformer.forward = cached_forward_flux2.__get__(transformer, transformer.__class__)
        transformer._is_flux2_cached = True
    return transformer


def disable_cache_on_flux2(transformer):
    """Set threshold<0 to bypass caching (keeps the wrapper installed)."""
    transformer.residual_diff_threshold_multi = -1.0


def apply_cache_on_flux2_pipe(pipe: DiffusionPipeline, **kwargs):
    if not getattr(pipe, "_is_flux2_cached", False):
        original_call = pipe.__class__.__call__

        @functools.wraps(original_call)
        def new_call(self, *args, **kw):
            with cache_context(create_cache_context()):
                return original_call(self, *args, **kw)

        pipe.__class__.__call__ = new_call
        pipe.__class__._is_flux2_cached = True
    apply_cache_on_flux2(pipe.transformer, **kwargs)
    return pipe
