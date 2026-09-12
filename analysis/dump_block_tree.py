"""Dump SVDQW4A4Linear paths in block 0 (double) and single block 0, to fix the key map."""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

from nunchaku_v3_lora import _load_transformer
from nunchaku.models.linear import SVDQW4A4Linear

tf = _load_transformer()
print("=== transformer_blocks.0 SVDQW4A4Linear ===")
b = tf.transformer_blocks[0]
for n, m in b.named_modules():
    if isinstance(m, SVDQW4A4Linear):
        print(f"  transformer_blocks.0.{n:32s} in={m.in_features} out={m.out_features}")
print("\n=== single_transformer_blocks.0 SVDQW4A4Linear ===")
s = tf.single_transformer_blocks[0]
for n, m in s.named_modules():
    if isinstance(m, SVDQW4A4Linear):
        print(f"  single_transformer_blocks.0.{n:32s} in={m.in_features} out={m.out_features}")
print("\n=== double block 0 top-level children ===")
print("  ", [n for n, _ in b.named_children()])
print("=== single block 0 top-level children ===")
print("  ", [n for n, _ in s.named_children()])
