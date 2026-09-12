"""Probe the env for Nunchaku feasibility: Python / torch / CUDA / GPU arch /
whether nunchaku is already importable."""
import sys
print("python:", sys.version.split()[0])
try:
    import torch
    print("torch:", torch.__version__)
    print("torch cuda:", torch.version.cuda)
    print("cuda available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        cc = torch.cuda.get_device_capability(0)
        print("gpu:", torch.cuda.get_device_name(0), "sm", f"{cc[0]}{cc[1]}")
except Exception as e:
    print("torch FAIL:", type(e).__name__, e)
for mod in ("nunchaku", "diffusers"):
    try:
        m = __import__(mod)
        print(f"{mod}:", getattr(m, "__version__", "?"))
    except Exception as e:
        print(f"{mod}: NOT importable ({type(e).__name__})")
