"""Pin the data backup to the two things it must never do: lose data, or lie.

`misc/backup_private.py` is the tool that makes the private repository a backup
of the data that cannot be re-downloaded or re-derived exactly -- written after
`git worktree remove --force` followed NTFS junctions and emptied five data
directories on 2026-09-11. A backup tool is only worth having if its failure
modes are the safe ones, so the properties pinned here are failure properties:

  * `make` REFUSES on a dead include pattern and writes nothing. A pattern that
    matches no file is a rule that has silently stopped protecting something --
    the same shape as the glob mismatches that dropped a description from the
    transfer test without erroring. Deadness is judged BEFORE the licence
    exclusion, or a pattern whose every match is excluded would read as rotten.
  * The LICENCE EXCLUSION actually drops files. The 87 stems that may not be
    uploaded are read from the tracked JSON, and a missing JSON is an error
    rather than an empty set -- defaulting to "exclude nothing" uploads them.
  * `verify` FAILS on a single flipped byte, and names the file.
  * `restore` NEVER overwrites, never escapes the root, never writes through a
    junction, and never leaves a half-written file. A destination that exists
    with different content stops the WHOLE run before any file of any item is
    written; a key that could escape the root is refused; a symlink or junction
    anywhere in a destination's existing ancestry is refused -- that is the
    incident exactly; and every file is staged, hashed and only then moved.
  * `restore` is IDEMPOTENT: a second run skips every identical file and writes
    nothing at all.
  * A file too large for GitHub round-trips through numbered parts byte for byte.
  * A file left behind in the backup is REPORTED, never deleted.
  * THE STORAGE LAYOUT REACHES GIT. Checked against the real `.gitignore` in a
    throwaway repository, because `git check-ignore --no-index` does not
    simulate directory traversal and would answer the wrong question.

Every test but that last one runs on `tmp_path` against a fake tree. Nothing
here reads or writes the real data directories.
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from misc import backup_private as bp  # noqa: E402

REPO = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------- the fixture

def _fake_root(tmp_path, big=b""):
    """A root with two items: `alpha` (three small files), `beta` (one big one)."""
    root = tmp_path / "root"
    (root / "live_a" / "sub").mkdir(parents=True)
    (root / "live_a" / "sub" / "one.bin").write_bytes(b"one" * 10)
    (root / "live_a" / "sub" / "two.bin").write_bytes(b"two" * 10)
    (root / "live_a" / "note.txt").write_bytes(b"a note\n")
    (root / "live_b").mkdir()
    (root / "live_b" / "big.bin").write_bytes(big or b"B" * 40)
    items = (
        bp.Item("alpha", "live_a", ("sub/*.bin", "note.txt"),
                "python refresh_alpha.py"),
        bp.Item("beta", "live_b", ("big.bin",)),
    )
    return root, items


def _dirs(tmp_path, **kw):
    root, items = _fake_root(tmp_path, **kw)
    return root, tmp_path / "backup", items


def _all_files(directory):
    """Every file under `directory`, as sorted posix relative paths."""
    out = []
    for base, _dirnames, names in os.walk(directory):
        for name in names:
            full = os.path.join(base, name)
            out.append(os.path.relpath(full, directory).replace(os.sep, "/"))
    return sorted(out)


# ------------------------------------------------------------- 1. make/verify

def test_make_then_verify_passes_and_the_manifest_lists_every_file(tmp_path, capsys):
    root, backup, items = _dirs(tmp_path)
    assert bp.make(str(root), str(backup), items) == 0
    capsys.readouterr()
    assert bp.verify(str(backup)) == 0

    physical = _all_files(backup)
    assert "alpha/sub/one.bin" in physical
    assert "alpha/note.txt" in physical
    assert "beta/big.bin" in physical
    for generated in (bp.MANIFEST_NAME, bp.CHUNKS_NAME, bp.README_NAME):
        assert generated in physical

    lines = (backup / bp.MANIFEST_NAME).read_text(encoding="utf-8").splitlines()
    paths = [ln.split("  ", 1)[1] for ln in lines]
    # one line per physical file EXCEPT the manifest itself, sorted, sha256sum format
    assert paths == sorted(p for p in physical if p != bp.MANIFEST_NAME)
    assert paths == sorted(paths)
    for ln in lines:
        digest, path = ln.split("  ", 1)
        assert re.fullmatch(r"[0-9a-f]{64}", digest), ln
        assert "\\" not in path, "manifest paths are posix"

    assert bp.sha256_file(str(backup / "alpha" / "note.txt")) == \
        bp.sha256_file(str(root / "live_a" / "note.txt"))


# ---------------------------------------------------------------- 2. chunking

def test_a_large_file_round_trips_through_parts(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(bp, "CHUNK_LIMIT", 64)
    monkeypatch.setattr(bp, "PART_SIZE", 32)
    payload = bytes(range(256)) * 3            # 768 bytes -> 24 parts
    root, backup, items = _dirs(tmp_path, big=payload)
    bp.make(str(root), str(backup), items)
    capsys.readouterr()

    key = "beta/big.bin"
    assert not (backup / "beta" / "big.bin").exists(), "the whole file is not stored"
    chunks = bp.read_chunks(str(backup))
    assert key in chunks
    assert chunks[key]["size"] == len(payload)
    assert chunks[key]["sha256"] == bp.sha256_file(str(root / "live_b" / "big.bin"))
    assert chunks[key]["parts"] == [f"{key}.part{i:02d}" for i in range(24)]
    for part in chunks[key]["parts"]:
        assert (backup / part).exists()
    assert (backup / (key + ".part00")).stat().st_size == 32

    assert bp.verify(str(backup)) == 0
    capsys.readouterr()

    fresh = tmp_path / "fresh"
    assert bp.restore(str(fresh), str(backup), items) == 0
    assert (fresh / "live_b" / "big.bin").read_bytes() == payload


# ------------------------------------------------------------ 3. a flipped byte

def test_verify_fails_on_one_flipped_byte(tmp_path, capsys):
    root, backup, items = _dirs(tmp_path)
    bp.make(str(root), str(backup), items)
    capsys.readouterr()

    target = backup / "alpha" / "note.txt"
    data = bytearray(target.read_bytes())
    data[0] ^= 0x01
    target.write_bytes(bytes(data))

    assert bp.verify(str(backup)) == 1
    out = capsys.readouterr().out
    assert "alpha/note.txt" in out
    assert "MISMATCH" in out


# --------------------------------------------------------------- 4. dead rules

def test_make_refuses_a_pattern_that_matches_nothing(tmp_path):
    root, backup, items = _dirs(tmp_path)
    items = items + (bp.Item("gamma", "live_a", ("absent/*.bin",)),)
    with pytest.raises(bp.BackupError, match=r"absent/\*\.bin"):
        bp.make(str(root), str(backup), items)
    assert not backup.exists(), "a refusal must write nothing at all"


def test_make_refuses_a_missing_live_directory(tmp_path):
    root, backup, items = _dirs(tmp_path)
    items = items + (bp.Item("gamma", "live_c", ("*.bin",)),)
    with pytest.raises(bp.BackupError, match="live_c"):
        bp.make(str(root), str(backup), items)
    assert not backup.exists()


def test_a_recursive_pattern_over_an_empty_directory_is_still_dead(tmp_path):
    root, backup, items = _dirs(tmp_path)
    (root / "live_empty").mkdir()
    items = items + (bp.Item("gamma", "live_empty", ("**/*",)),)
    with pytest.raises(bp.BackupError, match=r"\*\*/\*"):
        bp.make(str(root), str(backup), items)
    assert not backup.exists()


# ------------------------------------------------------- 5. restore, and again

def test_restore_writes_everything_then_becomes_a_no_op(tmp_path, capsys):
    root, backup, items = _dirs(tmp_path)
    bp.make(str(root), str(backup), items)
    capsys.readouterr()

    fresh = tmp_path / "fresh"
    assert bp.restore(str(fresh), str(backup), items) == 0
    out = capsys.readouterr().out
    assert "wrote 4" in out
    for rel in ("live_a/sub/one.bin", "live_a/sub/two.bin", "live_a/note.txt",
                "live_b/big.bin"):
        assert (fresh / rel).exists(), rel
    assert (fresh / "live_a" / "note.txt").read_bytes() == \
        (root / "live_a" / "note.txt").read_bytes()
    assert not any(p.endswith(bp.STAGING_SUFFIX) for p in _all_files(fresh)), \
        "no staging file may survive a successful restore"

    stamps = {p: (fresh / p).stat().st_mtime_ns for p in _all_files(fresh)}
    assert bp.restore(str(fresh), str(backup), items) == 0
    out = capsys.readouterr().out
    assert "wrote 0" in out and "skipped 4" in out
    assert {p: (fresh / p).stat().st_mtime_ns for p in _all_files(fresh)} == stamps


# --------------------------------------------------------- 6. a conflict stops

def test_restore_refuses_a_differing_destination_before_writing_anything(tmp_path,
                                                                        capsys):
    root, backup, items = _dirs(tmp_path)
    bp.make(str(root), str(backup), items)
    capsys.readouterr()

    fresh = tmp_path / "fresh"
    # `beta` is the SECOND item: the refusal must still keep `alpha` untouched.
    (fresh / "live_b").mkdir(parents=True)
    (fresh / "live_b" / "big.bin").write_bytes(b"a different file entirely")

    with pytest.raises(bp.BackupError, match="live_b/big.bin"):
        bp.restore(str(fresh), str(backup), items)

    assert (fresh / "live_b" / "big.bin").read_bytes() == b"a different file entirely"
    assert not (fresh / "live_a").exists(), \
        "no file of any item may be written when one item conflicts"


# -------------------------------------------------- 7. restore verifies first

def test_restore_refuses_when_verify_fails(tmp_path, capsys):
    root, backup, items = _dirs(tmp_path)
    bp.make(str(root), str(backup), items)
    capsys.readouterr()
    (backup / "alpha" / "note.txt").write_bytes(b"corrupted\n")

    fresh = tmp_path / "fresh"
    with pytest.raises(bp.BackupError, match="verif"):
        bp.restore(str(fresh), str(backup), items)
    assert not fresh.exists()


# ------------------------------------------------------------- 8. stale files

def test_make_reports_a_stale_file_and_does_not_delete_it(tmp_path, capsys):
    root, backup, items = _dirs(tmp_path)
    bp.make(str(root), str(backup), items)
    capsys.readouterr()

    orphan = backup / "alpha" / "sub" / "gone.bin"
    orphan.write_bytes(b"no longer has a source")

    bp.make(str(root), str(backup), items)
    out = capsys.readouterr().out
    assert "STALE" in out
    assert "alpha/sub/gone.bin" in out
    assert orphan.exists(), "a stale file is reported, never deleted"


# ------------------------------------------------------- A. licence exclusion

def test_exclude_stems_drops_every_file_of_that_stem(tmp_path, capsys):
    """And a pattern emptied by the exclusion is ALIVE, not dead.

    `dataset_v2/atlases/*.txt` is exactly this case on the real corpus: all
    three captions belong to `arial`, `arialbi` and `ariblk`, so the licence
    filter empties the pattern. Refusing there would make `make` unusable.
    """
    root = tmp_path / "root"
    (root / "live").mkdir(parents=True)
    (root / "live" / "a.png").write_bytes(b"a")
    (root / "live" / "b.png").write_bytes(b"b")
    (root / "live" / "b.txt").write_bytes(b"bb")
    items = (bp.Item("only_a", "live", ("*.png", "*.txt"),
                     exclude_stems=frozenset({"b"})),)
    backup = tmp_path / "backup"

    assert bp.make(str(root), str(backup), items) == 0
    out = capsys.readouterr().out
    assert (backup / "only_a" / "a.png").exists()
    assert not (backup / "only_a" / "b.png").exists()
    assert not (backup / "only_a" / "b.txt").exists()
    assert "licence exclusion: 2" in out
    assert bp.verify(str(backup)) == 0


def test_a_partial_refresh_keeps_the_whole_backup_s_exclusion_count(tmp_path, capsys):
    """`make --only <other item>` once rewrote the README's "N corpus renders
    are deliberately absent" as 0, because the count came from the items that
    run refreshed. The README describes the whole backup; the count is planned
    over every item."""
    root = tmp_path / "root"
    (root / "corpus").mkdir(parents=True)
    (root / "corpus" / "a.png").write_bytes(b"a")
    (root / "corpus" / "b.png").write_bytes(b"b")
    (root / "other").mkdir()
    (root / "other" / "x.txt").write_bytes(b"x")
    items = (bp.Item("corpus", "corpus", ("*.png",), exclude_stems=frozenset({"b"})),
             bp.Item("other", "other", ("*.txt",)))
    backup = tmp_path / "backup"
    assert bp.make(str(root), str(backup), items) == 0
    readme = (backup / bp.README_NAME).read_text(encoding="utf-8")
    assert "**1 corpus renders are deliberately absent.**" in readme
    (root / "other" / "x.txt").write_bytes(b"xx")
    assert bp.make(str(root), str(backup), items, only=["other"]) == 0
    readme = (backup / bp.README_NAME).read_text(encoding="utf-8")
    assert "**1 corpus renders are deliberately absent.**" in readme, \
        "a partial refresh must not report the whole backup's count as 0"
    capsys.readouterr()


def test_the_corpus_exclusions_come_from_the_tracked_json():
    stems = bp._corpus_exclusions()
    assert isinstance(stems, frozenset)
    assert "arial" in stems, "the proprietary Windows faces must be excluded"
    assert len(stems) >= 49
    assert bp.ITEMS[1].name == "corpus_v2"
    assert bp.ITEMS[1].exclude_stems == stems


def test_a_missing_exclusions_file_is_an_error_not_an_empty_set(tmp_path):
    """Defaulting to "exclude nothing" would upload the proprietary renders."""
    with pytest.raises(bp.BackupError, match="corpus_exclusions"):
        bp._corpus_exclusions(str(tmp_path))


# ----------------------------------------------------------- B. hash listings

def test_hash_only_files_are_listed_not_copied_and_never_restored(tmp_path, capsys):
    root = tmp_path / "root"
    (root / "pool").mkdir(parents=True)
    (root / "pool" / "keep.json").write_bytes(b"{}")
    (root / "pool" / "b.ttf").write_bytes(b"font-b")
    (root / "pool" / "a.ttf").write_bytes(b"font-a")
    items = (bp.Item("pool", "pool", ("keep.json",), hash_only=("*.ttf",)),)
    backup = tmp_path / "backup"
    bp.make(str(root), str(backup), items)

    out = capsys.readouterr().out
    assert "hash listing" in out
    out.encode("ascii")   # cp1252 console: an em-dash here prints as garbage

    lines = (backup / "pool" / bp.HASHES_NAME).read_text(
        encoding="utf-8").splitlines()
    assert [ln.split("  ", 1)[1] for ln in lines] == ["a.ttf", "b.ttf"]
    assert lines[0].split("  ", 1)[0] == bp.sha256_file(str(root / "pool" / "a.ttf"))
    assert not (backup / "pool" / "a.ttf").exists(), "the font is not uploaded"
    assert bp.verify(str(backup)) == 0, "the listing is a manifested file"
    capsys.readouterr()

    fresh = tmp_path / "fresh"
    bp.restore(str(fresh), str(backup), items)
    assert (fresh / "pool" / "keep.json").exists()
    assert not (fresh / "pool" / bp.HASHES_NAME).exists(), \
        "a hash listing describes the backup; it is never written into the tree"
    assert not (fresh / "pool" / "a.ttf").exists()


# ------------------------------------------------------- C. restore is hostile

@pytest.mark.parametrize("key", [
    "alpha/../../escape.bin",
    "../escape.bin",
    "/etc/passwd",
    "C:/Windows/system32/x.dll",
    "alpha\\sub\\one.bin",
    "alpha//one.bin",
    "",
])
def test_a_key_that_could_escape_the_root_is_refused(key):
    with pytest.raises(bp.BackupError):
        bp.check_key(key)


def test_check_key_accepts_the_shapes_the_backup_actually_uses():
    for key in ("alpha/note.txt", "adapters/glyph_r32_5000/final/x.safetensors",
                "generated/glyph_4b_r32_5000/generated/a.png",
                "logs/glyph_4b.log"):
        bp.check_key(key)


def test_restore_refuses_a_chunks_key_that_escapes_the_root(tmp_path, monkeypatch,
                                                            capsys):
    """CHUNKS.json is a file on disk, so its keys are an input, not a given."""
    root, backup, items = _dirs(tmp_path)
    bp.make(str(root), str(backup), items)
    capsys.readouterr()
    chunks = bp.read_chunks(str(backup))
    chunks["alpha/../../escape.bin"] = {"sha256": "0" * 64, "size": 1,
                                        "parts": ["alpha/x.part00"]}
    bp.write_chunks(str(backup), chunks)
    monkeypatch.setattr(bp, "verify", lambda *a, **k: 0)

    fresh = tmp_path / "fresh"
    with pytest.raises(bp.BackupError, match="relative segment"):
        bp.restore(str(fresh), str(backup), items)
    assert not fresh.exists(), "a refusal must write nothing at all"


def _junction(link, target):
    """True if an NTFS junction was created. mklink /J needs no privilege."""
    if os.name != "nt":
        return False
    proc = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                          capture_output=True, text=True)
    return proc.returncode == 0 and os.path.isdir(link)


def test_restore_refuses_a_junction_in_a_destinations_ancestry(tmp_path, capsys):
    """The incident exactly: a recursive operation followed a junction out of
    the tree it was pointed at. A restore through one writes somewhere else."""
    root, backup, items = _dirs(tmp_path)
    bp.make(str(root), str(backup), items)
    capsys.readouterr()

    fresh = tmp_path / "fresh"
    fresh.mkdir()
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    if not _junction(fresh / "live_a", elsewhere):
        pytest.skip("mklink /J is not available here")

    with pytest.raises(bp.BackupError, match="junction"):
        bp.restore(str(fresh), str(backup), items)
    assert list(elsewhere.iterdir()) == [], \
        "nothing may be written through the link"
    assert not (fresh / "live_b").exists(), \
        "no file of any item may be written when one destination is unsafe"


def test_restore_refuses_a_leftover_staging_file(tmp_path, capsys):
    root, backup, items = _dirs(tmp_path)
    bp.make(str(root), str(backup), items)
    capsys.readouterr()

    fresh = tmp_path / "fresh"
    (fresh / "live_a").mkdir(parents=True)
    stray = fresh / "live_a" / ("note.txt" + bp.STAGING_SUFFIX)
    stray.write_bytes(b"half a file from an interrupted run")

    with pytest.raises(bp.BackupError, match="interrupted restore"):
        bp.restore(str(fresh), str(backup), items)
    assert stray.exists(), "the tool never deletes, not even its own leftovers"
    assert not (fresh / "live_a" / "note.txt").exists()
    assert not (fresh / "live_b").exists()


def test_a_bad_chunk_leaves_a_staging_file_and_no_destination(tmp_path, monkeypatch,
                                                              capsys):
    """A crash or a corrupt part must never leave a half-written destination."""
    monkeypatch.setattr(bp, "CHUNK_LIMIT", 64)
    monkeypatch.setattr(bp, "PART_SIZE", 32)
    root, backup, items = _dirs(tmp_path, big=bytes(range(200)))
    bp.make(str(root), str(backup), items)
    capsys.readouterr()

    part = backup / "beta" / "big.bin.part00"
    data = bytearray(part.read_bytes())
    data[0] ^= 0xFF
    part.write_bytes(bytes(data))
    # verify would catch this; the point is what happens if it does not.
    monkeypatch.setattr(bp, "verify", lambda *a, **k: 0)

    fresh = tmp_path / "fresh"
    with pytest.raises(bp.BackupError, match="hashes"):
        bp.restore(str(fresh), str(backup), items, only=["beta"])
    assert not (fresh / "live_b" / "big.bin").exists()
    assert (fresh / "live_b" / ("big.bin" + bp.STAGING_SUFFIX)).exists()


# ------------------------------------------------------- E. the CI docs regex

def _ci_text():
    return (REPO / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")


def _ci_docs_pattern():
    m = re.search(r"^\s*docs='(.*)'\s*$", _ci_text(), re.M)
    assert m, "the 'Decide whether code changed' step no longer sets docs='...'"
    return re.compile(m.group(1))


@pytest.mark.parametrize("path", [
    "backup/holdout/manifest.json",
    "backup/adapters/x/adapter_model.safetensors.part00",
    "backup/README.md",
    "backup/MANIFEST.sha256",
    "backup/pool/HASHES.sha256",
])
def test_a_backup_refresh_is_a_docs_only_change(path):
    """Refreshing 400 MB of binaries must not run the torch test matrix."""
    assert _ci_docs_pattern().match(path), path


@pytest.mark.parametrize("path", [
    "misc/backup_private.py",
    "tests/test_backup_private.py",
    ".gitignore",
])
def test_the_backup_code_is_still_code(path):
    assert not _ci_docs_pattern().match(path), path


def test_ci_verifies_the_backup_when_the_backup_changes():
    """Docs-only must not mean unchecked: a refresh still runs verify."""
    text = _ci_text()
    assert 'echo "backup=true"' in text and 'echo "backup=false"' in text
    assert "steps.scope.outputs.backup == 'true'" in text
    assert "misc/backup_private.py verify" in text
    assert "tests/test_backup_private.py" in text


# --------------------------------------------- the layout must reach git

def test_every_item_path_survives_the_real_gitignore(tmp_path):
    """`!backup/**` must beat every unanchored rule, for every item.

    The repository ignores `dataset_*/`, `training_*/`, `eval_runs/`, `tools/`,
    `font_pool/`, `*.png`, `*.pt` and `*.safetensors`, and several item names
    and stored paths land under those rules. `git check-ignore --no-index` does
    NOT simulate directory traversal, so it answers a different question and
    would pass on a layout git actually drops. A throwaway repository with the
    real .gitignore in it is the only honest check.
    """
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    shutil.copyfile(REPO / ".gitignore", tmp_path / ".gitignore")

    expected = [f"backup/{name}" for name in bp.GENERATED]
    for item in bp.ITEMS:
        for pattern in item.include:
            concrete = pattern.replace("**", "d").replace("*", "x")
            expected.append(f"backup/{item.name}/{concrete}")
        if item.hash_only:
            expected.append(f"backup/{item.name}/{bp.HASHES_NAME}")
    for rel in expected:
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"x")

    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    staged = subprocess.run(["git", "ls-files"], cwd=tmp_path, check=True,
                            capture_output=True, text=True).stdout.split()
    missing = sorted(set(expected) - set(staged))
    assert missing == [], f"the .gitignore silently drops: {missing}"


def test_the_shipped_table_is_well_formed():
    names = [item.name for item in bp.ITEMS]
    assert len(names) == len(set(names))
    for item in bp.ITEMS:
        assert item.include, item.name
        for pattern in item.include + item.hash_only:
            assert not pattern.startswith("/") and ".." not in pattern, pattern
        # storage keys are what check_key will later have to accept
        bp.check_key(f"{item.name}/probe.bin")
