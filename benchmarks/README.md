# benchmarks/

**Latency and throughput measurement.**

Timing runs on the generation path.

Run from the repo root, either way:

```bash
python benchmarks/<script>.py --help
python -m benchmarks.<script> --help
```

Scripts import repo-root modules (`atlas_constants`, `eval_checkpoint`, ...); a two-line
`sys.path` bootstrap at the top of each makes direct-path invocation work too.

## Contents (2)

- `benchmark_latency.py` — Controlled per-step latency benchmark for ONE model in a fresh process.
- `benchmark_route_b.py` — Route B speed gate: full-generation latency, fused vs unfused QKV path.
