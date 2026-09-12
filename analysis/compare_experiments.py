"""Compare two experiments side by side.

Usage:
  python analysis/compare_experiments.py experiments/<run_a> experiments/<run_b>

Checks run *provenance* (same dataset hash, same hyperparameters, common
checkpoints) and reports CLEAN/PARTIAL/DIRTY. For the statistical comparison
of two scored eval runs, use analysis/compare_runs.py instead.
"""
import argparse
import json
from pathlib import Path


def load_manifest(exp_dir):
    return json.loads((Path(exp_dir) / "manifest.json").read_text())


def load_snapshot(exp_dir):
    return json.loads((Path(exp_dir) / "dataset_snapshot.json").read_text())


def compare_datasets(snap_a, snap_b):
    stems_a = {f["stem"] for f in snap_a["fonts"]}
    stems_b = {f["stem"] for f in snap_b["fonts"]}
    only_a = stems_a - stems_b
    only_b = stems_b - stems_a
    common = stems_a & stems_b

    print(f"Dataset A: {len(stems_a)} fonts")
    print(f"Dataset B: {len(stems_b)} fonts")
    print(f"Common: {len(common)}")
    print(f"Only in A: {len(only_a)}")
    print(f"Only in B: {len(only_b)}")
    if only_a:
        print(f"  A unique: {sorted(only_a)[:10]}{'...' if len(only_a) > 10 else ''}")
    if only_b:
        print(f"  B unique: {sorted(only_b)[:10]}{'...' if len(only_b) > 10 else ''}")
    return len(only_a) == 0 and len(only_b) == 0


def compare_hyperparameters(m_a, m_b):
    h_a = m_a.get("hyperparameters", {})
    h_b = m_b.get("hyperparameters", {})
    keys = set(h_a.keys()) | set(h_b.keys())
    diffs = []
    for k in sorted(keys):
        va = h_a.get(k, "<missing>")
        vb = h_b.get(k, "<missing>")
        if va != vb:
            diffs.append((k, va, vb))

    if diffs:
        print(f"\nHyperparameter differences ({len(diffs)}):")
        for k, va, vb in diffs:
            print(f"  {k}: A={va}  B={vb}")
    else:
        print("\nHyperparameters: IDENTICAL")
    return len(diffs) == 0


def main():
    parser = argparse.ArgumentParser(description="Compare two experiment runs")
    parser.add_argument("exp_a")
    parser.add_argument("exp_b")
    args = parser.parse_args()

    print(f"=== Comparing experiments ===")
    print(f"A: {args.exp_a}")
    print(f"B: {args.exp_b}\n")

    m_a = load_manifest(args.exp_a)
    m_b = load_manifest(args.exp_b)
    snap_a = load_snapshot(args.exp_a)
    snap_b = load_snapshot(args.exp_b)

    print(f"--- Manifests ---")
    print(f"A: {m_a['name']} ({m_a['timestamp']}) git={m_a['git_commit'][:8]} hash={m_a['dataset_hash']}")
    print(f"B: {m_b['name']} ({m_b['timestamp']}) git={m_b['git_commit'][:8]} hash={m_b['dataset_hash']}")
    print()
    print(f"A status: {m_a.get('status')}")
    print(f"B status: {m_b.get('status')}")

    print(f"\n--- Datasets ---")
    datasets_match = compare_datasets(snap_a, snap_b)

    hparams_match = compare_hyperparameters(m_a, m_b)

    print(f"\n--- Verdict ---")
    if datasets_match and hparams_match:
        print("CLEAN comparison -- datasets and hyperparameters match exactly")
    elif datasets_match:
        print("PARTIAL -- datasets match but hyperparameters differ")
    elif hparams_match:
        print("PARTIAL -- hyperparameters match but datasets differ")
    else:
        print("DIRTY -- both datasets AND hyperparameters differ")

    # Find common checkpoints
    ckpts_a = {p.name for p in (Path(args.exp_a) / "checkpoints").glob("checkpoint-*")}
    ckpts_b = {p.name for p in (Path(args.exp_b) / "checkpoints").glob("checkpoint-*")}
    common_ckpts = sorted(ckpts_a & ckpts_b, key=lambda n: int(n.split("-")[1]))

    print(f"\n--- Checkpoints ---")
    print(f"A has: {sorted(ckpts_a)}")
    print(f"B has: {sorted(ckpts_b)}")
    print(f"Comparable: {common_ckpts}")


if __name__ == "__main__":
    main()
