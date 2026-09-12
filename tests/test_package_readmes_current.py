"""Pin the package README indexes to the directories they claim to describe.

WHY THIS EXISTS. Every topical package carries a README listing its modules,
maintained by hand. They drifted: `analysis/README.md` advertised 16 modules
against a directory of 40, so two thirds of this project's tooling -- including
`training_variance.py`, `claim_ledger.py` and `retrieval_baseline.py`, the
instruments behind its central findings -- could not be found from the package's
own index. A reader who trusted the README concluded the tools did not exist.

The list is generated now (`misc/sync_package_readmes.py`). This test is what
stops it silently going stale again the next time a module is added.
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "misc", "sync_package_readmes.py")


def test_package_readmes_list_every_module():
    """--check exits 0 when every generated index matches its directory."""
    proc = subprocess.run([sys.executable, TOOL, "--check"],
                          cwd=REPO, capture_output=True, text=True)
    assert proc.returncode == 0, (
        "A package README no longer lists its modules. Run:\n"
        "    python misc/sync_package_readmes.py --fix\n\n" + proc.stdout + proc.stderr)


def test_check_mode_does_not_write():
    """--check must be read-only, or the test itself would hide the drift."""
    readme = os.path.join(REPO, "analysis", "README.md")
    before = open(readme, encoding="utf-8").read()
    subprocess.run([sys.executable, TOOL, "--check"],
                   cwd=REPO, capture_output=True, text=True)
    assert open(readme, encoding="utf-8").read() == before


def test_detects_a_missing_entry(tmp_path):
    """Deleting one entry from a generated list must fail --check.

    Without this, a --check that always passed would satisfy the test above.
    """
    readme = os.path.join(REPO, "analysis", "README.md")
    original = open(readme, encoding="utf-8").read()
    lines = original.splitlines()
    kept = [ln for ln in lines if not ln.startswith("- `compare_runs.py`")]
    assert len(kept) == len(lines) - 1, "expected compare_runs.py in the index"
    try:
        with open(readme, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(kept) + "\n")
        proc = subprocess.run([sys.executable, TOOL, "--check"],
                              cwd=REPO, capture_output=True, text=True)
        assert proc.returncode == 1, "--check passed on an index missing an entry"
    finally:
        with open(readme, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(original)
