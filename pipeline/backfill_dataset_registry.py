"""Backfill experiments/_dataset_registry.json from existing manifests.

Walks experiments/*/manifest.json, builds a per-(dataset_dir, hash) record,
and seeds the registry so future runs have a baseline to validate against.
If the same dataset_dir appears with multiple hashes, prints a warning and
records the OLDEST hash as the canonical one (since that's what the dir
"originally" contained).

Refuses to clobber an existing registry unless --force is passed.
"""

# repo root on sys.path so `python pipeline/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import json
from pathlib import Path
from collections import defaultdict

from pipeline.experiment_runner import DATASET_REGISTRY, _atomic_write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true",
                        help="Overwrite an existing _dataset_registry.json. Without this flag, "
                             "the script aborts if the registry already exists to prevent "
                             "clobbering accumulated entries.")
    args = parser.parse_args()

    if DATASET_REGISTRY.exists() and not args.force:
        raise SystemExit(
            f"ABORT: {DATASET_REGISTRY} already exists. Backfill would overwrite it.\n"
            f"  Pass --force to overwrite (you will lose any entries added since the original "
            f"backfill that don't appear in any manifest).\n"
            f"  Or inspect the file and delete it manually if you intend to rebuild from scratch."
        )

    manifests = sorted(Path("experiments").glob("*/manifest.json"))
    by_dir = defaultdict(list)
    for m in manifests:
        try:
            data = json.loads(m.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  skip {m}: {e}")
            continue
        d = data.get("dataset_dir")
        h = data.get("dataset_hash")
        ts = data.get("timestamp", "")
        if not d or not h:
            continue
        by_dir[d].append((ts, h, m.parent.name))

    registry = {}
    print(f"Found {len(manifests)} manifests, {len(by_dir)} unique dataset dirs.\n")
    for d, entries in by_dir.items():
        entries.sort()
        unique_hashes = sorted(set(h for _, h, _ in entries))
        if len(unique_hashes) > 1:
            print(f"WARN: {d} has {len(unique_hashes)} different hashes across runs:")
            for ts, h, exp in entries:
                print(f"  {ts}  {h}  {exp}")
            print(f"  Recording OLDEST hash ({unique_hashes[0]}) as canonical.")
            print()
        _, h, exp_name = entries[0]
        registry[d] = {"hash": h, "first_seen_in": exp_name}

    _atomic_write_json(DATASET_REGISTRY, registry)
    print(f"Wrote {DATASET_REGISTRY}")
    print(f"  {len(registry)} entries seeded.")


if __name__ == "__main__":
    main()
