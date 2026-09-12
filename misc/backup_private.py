"""Back up the non-available data into `backup/` in the private repository,
verify it, and restore it -- never deleting anything.

WHY THIS EXISTS. On 2026-09-11 `git worktree remove --force` followed NTFS
junctions and emptied `dataset_v2`, `font_pool`, `eval_holdout`, `google-fonts`,
a checkpoint and a probe's references. Everything came back from surviving
copies, which was luck rather than design
(`research/2026-09-11-the-junction-incident-and-what-came-back.md`). The private
repository is already the one place that holds the whole record, so it also
holds the data that cannot be re-downloaded or re-derived exactly: the rendered
corpus and holdout, the two shipped adapters, the glyph classifier, the
generated atlases and eval records behind the published tables and figures, the
product track's reference candidates, the training and eval logs, and the font
pool's provenance manifest. What IS re-derivable is deliberately absent -- the
1.8 GB latent cache is one `cache_latents.py` run away, `dataset_v3` rebuilds
from the tracked expansion set, and the holdout's 50 TTFs are a pinned
google/fonts commit.

WHAT IS NEVER BACKED UP, AND WHY IT IS A LICENCE QUESTION RATHER THAN A SIZE
ONE. The fonts themselves are not here, and neither are the corpus renders of
the 87 stems in `research/corpus_exclusions.json`. 49 of those are
vendor-supplied Windows faces whose terms permit rendering but not conversion,
and this repository's own audit reads a 95-glyph atlas as exactly the
conversion those terms withhold
(`research/2026-08-08-the-corpus-is-not-97-percent-ofl.md`); the other 38 carry
no permissive licence at all. GitHub's terms require the right to upload even
to a private repository, so they stay off it. Those renders regenerate locally
from fonts that never left this machine, so nothing irreplaceable is lost.
`backup/` is withheld from the public export by `misc/export_public.py` and
scanned selectively by `analysis/sanitize_for_publish.py` either way.

THE THREE RULES THIS TOOL IS BUILT AROUND.

  * NOTHING OUTSIDE `backup/` IS EVER WRITTEN except by `restore`, and `restore`
    only ever CREATES files. A destination that already exists with different
    content stops the whole run, before any file of any item is written; an
    identical one is skipped. There is no overwrite path and no delete path.
    Every destination is checked for containment under the root and for a
    symlink or NTFS junction anywhere in its existing ancestry -- the exact
    failure class of the incident -- and every file is written to a
    `.restoring` sibling, hashed there, and moved into place only once it
    matches, so a crash never leaves a half-written file behind.
  * A DEAD INCLUDE PATTERN IS A BUG. Every pattern must match at least one file
    at `make` time or `make` refuses, naming the pattern, having written
    nothing. Deadness is judged BEFORE the licence exclusion, because a pattern
    whose every match is licence-excluded is doing its job, not rotting.
  * WHAT THE BACKUP CLAIMS IS CHECKABLE. `MANIFEST.sha256` carries one sha256
    line per physical file, `verify` re-hashes all of them, and `restore` runs
    `verify` first and re-hashes every file it writes.

CHUNKING. GitHub refuses a blob of 100 MiB or more, so any file at or above
`CHUNK_LIMIT` is stored as consecutive `<name>.part00`, `<name>.part01`, ...
of `PART_SIZE` bytes. `CHUNKS.json` carries the WHOLE file's sha256 and size,
so a reassembled file is checked against the original, not against its parts.

HASH LISTINGS. Some things are too large to store and too important to lose
track of. An item's `hash_only` patterns are not copied; their sha256s go into
`backup/<item>/HASHES.sha256` so a future re-fetch can be verified file by
file. `restore` never writes one back.

  python misc/backup_private.py make       # refresh backup/ from the live data
  python misc/backup_private.py verify     # re-hash every file against the manifest
  python misc/backup_private.py restore    # write back only what is missing
  python misc/backup_private.py restore --only classifier pool
"""

# repo root on sys.path so `python misc/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import glob
import hashlib
import json
import ntpath
import os
import shutil
import stat
from dataclasses import dataclass

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP_DIRNAME = "backup"

MANIFEST_NAME = "MANIFEST.sha256"
CHUNKS_NAME = "CHUNKS.json"
README_NAME = "README.md"
HASHES_NAME = "HASHES.sha256"
GENERATED = (MANIFEST_NAME, CHUNKS_NAME, README_NAME)

# A half-written destination is indistinguishable from a corrupt one, so every
# restored file lands here first and is moved into place only once it hashes.
STAGING_SUFFIX = ".restoring"

# GitHub refuses a blob of 100 MiB or more. Store anything at or above the
# limit in parts comfortably under it, so a future limit change has room.
CHUNK_LIMIT = 95 * 2 ** 20
PART_SIZE = 90 * 2 ** 20
READ_BLOCK = 1 << 20

# The holdout's 50 TTFs are not backed up: they are google/fonts at this commit.
GOOGLE_FONTS_PIN = "85f52fd19ff9649d8d173a9401c289e0f59befab"

RESEARCH_NOTE = "research/2026-09-11-the-junction-incident-and-what-came-back.md"
LICENCE_NOTE = "research/2026-08-08-the-corpus-is-not-97-percent-ofl.md"
EXCLUSIONS_JSON = "research/corpus_exclusions.json"


class BackupError(Exception):
    """A refusal. Raised before anything is written, never during."""


def _corpus_exclusions(repo=None):
    """The 87 corpus stems that may not be uploaded, from the tracked JSON.

    Read rather than hardcoded, so the backup and `train_lora_kg.py`'s licence
    filter cannot drift apart. A missing file is an error and not an empty set:
    defaulting to "exclude nothing" would upload the proprietary renders.
    """
    path = os.path.join(repo or REPO, *EXCLUSIONS_JSON.split("/"))
    if not os.path.isfile(path):
        raise BackupError(
            f"{EXCLUSIONS_JSON} is missing, so the licence-excluded corpus "
            "stems cannot be determined. Refusing to guess -- backing up "
            "everything would upload renders of vendor-licensed faces")
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    stems = data.get("exclude_stems")
    if not stems:
        raise BackupError(f"{EXCLUSIONS_JSON} has no non-empty 'exclude_stems'")
    return frozenset(stems)


@dataclass(frozen=True)
class Item:
    """One backed-up thing.

    `live` is relative to the repo root; `include` is a tuple of glob patterns
    relative to `live`, each of which MUST match at least one file. `**` is
    supported (`plan` globs recursively), so `**/*` means "every file under
    here". Storage is `backup/<name>/<path relative to live>`.

    `exclude_stems` drops any matched file whose basename stem is in the set,
    AFTER the pattern has been proved alive -- that is how the licence-excluded
    corpus renders stay off GitHub without making their patterns read as dead.

    `hash_only` patterns are listed, not copied: their sha256s go into
    `backup/<name>/HASHES.sha256` and `restore` never writes that file back.
    """
    name: str
    live: str
    include: tuple[str, ...]
    follow_up: str | None = None
    exclude_stems: frozenset[str] = frozenset()
    hash_only: tuple[str, ...] = ()


_CORPUS_EXCLUDED = _corpus_exclusions()

ITEMS = (
    Item("holdout", "eval_holdout",
         ("atlases/*.png", "references/*.png", "manifest.json",
          "gt_ocr_cache.json")),
    # The licence exclusion drops both the atlas and the reference of each of
    # the 87 stems, and with them all three atlas captions -- which happen to
    # belong to `arial`, `arialbi` and `ariblk`. The `atlases/*.txt` pattern
    # therefore contributes nothing today and is still alive, and kept: a
    # caption for a permissively-licensed face would be backed up tomorrow.
    Item("corpus_v2", "dataset_v2",
         ("atlases/*.png", "atlases/*.txt", "references/*.png", "manifest.txt",
          "cache/cache_meta.json", "cache/template*.pt",
          "cache/glyph_template*.png"),
         follow_up="python cache_latents.py --dataset-dir dataset_v2",
         exclude_stems=_CORPUS_EXCLUDED),
    # The run metadata of both adapters lives in `training_records`, so only
    # the weights and their config are here.
    Item("adapters/glyph_4b_r32_5000", "training_glyph_4b_r32_5000",
         ("final/adapter_model.safetensors", "final/adapter_config.json",
          "final/README.md")),
    Item("adapters/glyph_r32_5000", "training_glyph_r32_5000",
         ("final/adapter_model.safetensors", "final/adapter_config.json",
          "final/README.md")),
    Item("classifier", ".", ("glyph_classifier.pt",)),
    # Atlases only: every run's scores.json / per_cell.json /
    # identity_scorecard.json is in `eval_records`, once.
    Item("generated/glyph_r32_disambig50_mild",
         "eval_runs/glyph_r32_disambig50_mild", ("generated/*.png",)),
    Item("generated/glyph_4b_r32_5000", "eval_runs/glyph_4b_r32_5000",
         ("generated/*.png",)),
    Item("generated/glyph_4b_r32_5000_lrfix",
         "eval_runs/glyph_4b_r32_5000_lrfix", ("generated/*.png",)),
    Item("generated/prompt_trained_short", "eval_runs/prompt_trained_short",
         ("generated/*.png",)),
    Item("generated/structured_prompt_5000", "eval_runs/structured_prompt_5000",
         ("generated/*.png",)),
    # analysis/claim_ledger.py reads the scores.json of arms that are not
    # tracked, so the records of every run travel together.
    Item("eval_records", "eval_runs",
         ("*/scores.json", "*/per_cell.json", "*/identity_scorecard.json")),
    Item("product_refs", "eval_runs/_candidate_refs", ("**/*",)),
    Item("synthetic_refs", "eval_runs/_synthetic_refs", ("**/*",)),
    Item("synthetic_probe", "eval_runs/_synthetic_probe", ("**/*",)),
    Item("transfer_atlases", "eval_runs/_transfer_atlases", ("**/*",)),
    Item("attribute_atlases", "eval_runs/_attribute_atlases", ("**/*",)),
    Item("relational_refs", "eval_runs/_relational_refs", ("**/*",)),
    # The Mi pair (second registration, 2026-09-12): the run that overturned
    # the Kg failure's conditional reading.
    Item("relational_refs_mi", "eval_runs/_relational_refs_Mi", ("**/*",)),
    Item("relational_refs_mi_controls", "eval_runs/_relational_refs_Mi_controls", ("**/*",)),
    # viz/lr_horizon_bug.py parses glyph_4b.log and glyph_4b_lrfix.log as DATA:
    # the learning-rate trace of the horizon bug exists nowhere else.
    Item("logs", ".", ("*.log",)),
    Item("training_records", ".",
         ("training_*/metrics.csv", "training_*/train_config.json",
          "training_*/training.log", "training_*/conditioning.json")),
    Item("tools", "tools", ("potrace.exe",)),
    # The pool's 6,194 font files are never uploaded. Their hashes are, so a
    # re-fetch can be checked file by file against what was actually trained on.
    # The six-seed candidate sets behind the 4B-vs-9B gap (README table, the
    # multiseed note and the 2026-09-12 rescore): generated once, scored twice.
    Item("candidates/multiseed_4b", "bestofn_4b", ("candidates/**/*.png", "scores.json")),
    Item("candidates/multiseed_9b", "bestofn_9b", ("candidates/**/*.png", "scores.json")),
    Item("pool", "font_pool", ("source_manifest.json", "RESTORE_NOTE.txt"),
         hash_only=("*.ttf", "*.otf")),
)

# Named in backup/README.md so that "what is not here" is stated, not implied.
NOT_BACKED_UP = (
    ("the font binaries", "font_pool/ and google-fonts/ -- a licence "
     "constraint, not a size one; their hashes are in pool/HASHES.sha256"),
    ("dataset_v3", "the closed corpus-expansion track; rebuilds from the "
     "tracked expansion set and the pinned clone"),
    ("glyph_clf_data.npz", "279 MiB of cached classifier training data; the "
     "trained checkpoint is kept instead"),
    ("dataset_v2/cache/atlases and references",
     "the 1.8 GB latent cache -- one cache_latents.py run"),
)


# ------------------------------------------------------------------- plumbing

def _posix(path):
    return path.replace(os.sep, "/")


def _live_base(root, item):
    return root if item.live == "." else os.path.join(root, *item.live.split("/"))


def _is_generated(rel):
    """True for files the backup writes about itself, which are never restored."""
    return rel in GENERATED or rel.rsplit("/", 1)[-1] == HASHES_NAME


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(READ_BLOCK), b""):
            digest.update(block)
    return digest.hexdigest()


def physical_files(backup_dir):
    """Every file under `backup_dir`, as sorted posix relative paths."""
    out = []
    for base, _dirs, names in os.walk(backup_dir):
        for name in names:
            full = os.path.join(base, name)
            out.append(_posix(os.path.relpath(full, backup_dir)))
    return sorted(out)


def select(items, only):
    if not only:
        return list(items)
    by_name = {item.name: item for item in items}
    unknown = [n for n in only if n not in by_name]
    if unknown:
        raise BackupError(f"unknown item(s) {unknown}; known: {sorted(by_name)}")
    return [by_name[n] for n in only]


def read_chunks(backup_dir):
    path = os.path.join(backup_dir, CHUNKS_NAME)
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def read_manifest(backup_dir):
    """{posix relative path: sha256} from MANIFEST.sha256."""
    path = os.path.join(backup_dir, MANIFEST_NAME)
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line:
                continue
            digest, rel = line.split("  ", 1)
            out[rel] = digest
    return out


# --------------------------------------------------------------- safety rails

def check_key(key):
    """A backup key must be a plain relative posix path, or nothing is written.

    `restore` turns a key into a path under the live root. A key carrying `..`,
    a leading separator, a drive letter or a backslash would escape it, so
    every key -- including the ones CHUNKS.json supplies, which is a file on
    disk and therefore an input -- is checked before it is joined to anything.
    """
    if not key:
        raise BackupError("empty path in the backup index")
    if "\\" in key:
        raise BackupError(f"backup key {key!r} contains a backslash; keys are posix")
    if key.startswith("/"):
        raise BackupError(f"backup key {key!r} is absolute")
    # ntpath, not os.path: on Linux os.path.splitdrive is a no-op, so a key
    # such as `C:/Windows/x.dll` sailed through in CI while Windows refused it.
    # A backup made on one platform must be refused identically on the other.
    if ntpath.splitdrive(key)[0]:
        raise BackupError(f"backup key {key!r} carries a drive letter or share")
    if any(part in ("", ".", "..") for part in key.split("/")):
        raise BackupError(f"backup key {key!r} has an empty or relative segment")


def contained(root, dest):
    """True when `dest` resolves under `root`."""
    root_n = os.path.normcase(os.path.abspath(root))
    dest_n = os.path.normcase(os.path.abspath(dest))
    try:
        return os.path.commonpath([root_n, dest_n]) == root_n
    except ValueError:                       # different drives cannot be nested
        return False


def is_reparse_point(path):
    """True for a symlink or an NTFS junction. Never follows the link."""
    try:
        st = os.lstat(path)
    except OSError:
        return False
    if os.name == "nt":
        return bool(getattr(st, "st_file_attributes", 0)
                    & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    return stat.S_ISLNK(st.st_mode)


def reparse_ancestors(root, dest):
    """Existing ancestors of `dest`, from `root` down to its parent, that are links.

    This is the incident, exactly: a junction in the path made a recursive
    operation act on the target instead of the tree it was pointed at. A
    restore into a junctioned directory writes somewhere else entirely.
    """
    root_abs = os.path.abspath(root)
    chain, current = [], os.path.dirname(os.path.abspath(dest))
    while True:
        chain.append(current)
        if os.path.normcase(current) == os.path.normcase(root_abs):
            break
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return [p for p in reversed(chain)
            if os.path.lexists(p) and is_reparse_point(p)]


# ----------------------------------------------------------------------- plan

def _expand(base, item, pattern, seen):
    """(entries, n_excluded) for one pattern. Refuses if the pattern is dead."""
    hits = sorted(p for p in glob.glob(
        os.path.join(glob.escape(base), *pattern.split("/")), recursive=True)
        if os.path.isfile(p))
    if not hits:
        raise BackupError(
            f"{item.name}: include pattern {pattern!r} matches no file under "
            f"{item.live!r} -- a dead rule is a bug; fix the pattern or the "
            "source. Nothing was written")
    entries, excluded = [], 0
    for src in hits:
        rel = _posix(os.path.relpath(src, base))
        if rel in seen:
            continue
        seen.add(rel)
        if os.path.splitext(os.path.basename(src))[0] in item.exclude_stems:
            excluded += 1
            continue
        entries.append((rel, src))
    return entries, excluded


def plan(root, items):
    """(copy work, hash-listing work, {item name: n excluded}) -- or refuse.

    Every pattern of every item is expanded BEFORE anything is written, so a
    dead rule, a missing directory or a missing exclusions file costs nothing.
    """
    work, listings, dropped = [], [], {}
    for item in items:
        base = _live_base(root, item)
        if not os.path.isdir(base):
            raise BackupError(
                f"{item.name}: the live directory {item.live!r} does not exist "
                f"under {root} -- nothing was written")
        seen = set()
        for pattern in item.include:
            entries, excluded = _expand(base, item, pattern, seen)
            work += [(item, rel, src) for rel, src in entries]
            if excluded:
                dropped[item.name] = dropped.get(item.name, 0) + excluded
        seen_hash = set()
        for pattern in item.hash_only:
            entries, excluded = _expand(base, item, pattern, seen_hash)
            listings += [(item, rel, src) for rel, src in entries]
            if excluded:
                dropped[item.name] = dropped.get(item.name, 0) + excluded
    return work, listings, dropped


# ----------------------------------------------------------------------- make

def _store(src, dest, key, chunks):
    """Copy one file into the backup, in parts if it is too large for GitHub.

    Returns the physical paths written, relative to the backup directory.
    """
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.getsize(src) < CHUNK_LIMIT:
        shutil.copyfile(src, dest)
        return [key]

    digest = hashlib.sha256()
    parts, total, index = [], 0, 0
    with open(src, "rb") as fh:
        while True:
            part_rel = f"{key}.part{index:02d}"
            part_path = os.path.join(os.path.dirname(dest),
                                     os.path.basename(part_rel))
            written = 0
            with open(part_path, "wb") as out:
                while written < PART_SIZE:
                    block = fh.read(min(READ_BLOCK, PART_SIZE - written))
                    if not block:
                        break
                    out.write(block)
                    digest.update(block)
                    written += len(block)
            if written == 0:                      # an exact multiple of PART_SIZE
                os.remove(part_path)
                break
            parts.append(part_rel)
            total += written
            index += 1
            if written < PART_SIZE:
                break
    chunks[key] = {"sha256": digest.hexdigest(), "size": total, "parts": parts}
    return list(parts)


def write_hash_listing(backup_dir, item, pairs):
    """`backup/<item>/HASHES.sha256`: one `<sha256>  <basename>` line, by name."""
    rows = sorted((os.path.basename(src), sha256_file(src)) for _rel, src in pairs)
    path = os.path.join(backup_dir, *item.name.split("/"), HASHES_NAME)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(f"{digest}  {name}" for name, digest in rows) + "\n")
    return f"{item.name}/{HASHES_NAME}", len(rows)


def logical_files(backup_dir, chunks):
    """{posix relative path: size} of the LOGICAL files the backup holds.

    A chunked file appears once, at its whole size; its parts do not appear.
    The files the backup writes about itself are not data and are excluded.
    """
    parts = {p for meta in chunks.values() for p in meta["parts"]}
    out = {}
    for rel in physical_files(backup_dir):
        if _is_generated(rel) or rel in parts:
            continue
        out[rel] = os.path.getsize(os.path.join(backup_dir, *rel.split("/")))
    for key, meta in chunks.items():
        out[key] = meta["size"]
    return out


def write_chunks(backup_dir, chunks):
    path = os.path.join(backup_dir, CHUNKS_NAME)
    text = json.dumps({k: chunks[k] for k in sorted(chunks)}, indent=2) + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def write_manifest(backup_dir):
    """One sha256sum line per physical file except the manifest itself."""
    lines = []
    for rel in physical_files(backup_dir):
        if rel == MANIFEST_NAME:
            continue
        digest = sha256_file(os.path.join(backup_dir, *rel.split("/")))
        lines.append(f"{digest}  {rel}")
    lines.sort(key=lambda line: line.split("  ", 1)[1])
    with open(os.path.join(backup_dir, MANIFEST_NAME), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    return len(lines)


def _mib(n):
    return f"{n / 2 ** 20:.1f}"


def inventory(backup_dir, items, chunks):
    """[(item, file count, bytes)] over what the backup ACTUALLY holds."""
    sizes = logical_files(backup_dir, chunks)
    rows = []
    for item in items:
        prefix = item.name + "/"
        owned = [rel for rel in sizes if rel.startswith(prefix)]
        if owned:
            rows.append((item, len(owned), sum(sizes[rel] for rel in owned)))
    return rows


def hash_listings(backup_dir, items):
    """[(item, line count)] for every item carrying a HASHES.sha256."""
    out = []
    for item in items:
        path = os.path.join(backup_dir, *item.name.split("/"), HASHES_NAME)
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                out.append((item, sum(1 for line in fh if line.strip())))
    return out


def render_readme(backup_dir, items, chunks, n_excluded=0):
    """The backup's own README -- deterministic, no timestamps."""
    rows = inventory(backup_dir, items, chunks)
    chunked = sorted(chunks)
    listings = hash_listings(backup_dir, items)
    follow_ups = [(item.name, item.follow_up) for item, _n, _b in rows
                  if item.follow_up]

    out = [
        "# `backup/` — the data the private repository keeps",
        "",
        "Generated by `misc/backup_private.py make`. Do not edit by hand: the",
        "next `make` rewrites this file in full.",
        "",
        "## What this is",
        "",
        "The data behind this project's results that cannot be re-downloaded or",
        "re-derived exactly. On 2026-09-11 `git worktree remove --force` followed",
        "NTFS junctions and emptied five data directories; everything came back",
        "from surviving copies, which was luck rather than design",
        f"(`{RESEARCH_NOTE}`).",
        "The private repository is the one place that already holds the whole",
        "record, so it holds this too.",
        "",
        "**This directory is never exported.** `misc/export_public.py` withholds",
        "it, and `analysis/sanitize_for_publish.py` scans it selectively: its",
        "binaries are not read as text and are exempt from the tracked-weights",
        "block, while every text file in it is still scanned for secrets.",
        "",
        "## Inventory",
        "",
        "| item | restores to | files | MiB |",
        "|---|---|---|---|",
    ]
    total_files = total_bytes = 0
    for item, count, size in rows:
        out.append(f"| `{item.name}` | `{item.live}` | {count} | {_mib(size)} |")
        total_files += count
        total_bytes += size
    out.append(f"| **total** | | **{total_files}** | **{_mib(total_bytes)}** |")

    if listings:
        out += [
            "",
            "## Hash listings",
            "",
            "Files too large to store and too important to lose track of. These",
            "are not copied; their sha256s are recorded so a future re-fetch can",
            "be verified file by file. `restore` never writes one back.",
            "",
        ]
        for item, count in listings:
            out.append(f"- `{item.name}/{HASHES_NAME}` — {count} files under "
                       f"`{item.live}`")

    out += [
        "",
        "## What is NOT here",
        "",
    ]
    for what, why in NOT_BACKED_UP:
        out.append(f"- **{what}** — {why}")
    out += [
        "",
        "The holdout's 50 TTFs are not here either: they are `google/fonts` at",
        f"commit `{GOOGLE_FONTS_PIN}`.",
        "",
        "## Restoring",
        "",
        "```bash",
        "python misc/backup_private.py verify",
        "python misc/backup_private.py restore",
        "python misc/backup_private.py restore --only pool classifier",
        "```",
        "",
        "`restore` writes only files that are absent. A destination that exists",
        "with different content stops the whole run before anything is written;",
        "an identical one is skipped. It never deletes and never overwrites. It",
        "also refuses if a destination would fall outside the repository root or",
        "if any existing directory on the way to it is a symlink or an NTFS",
        "junction — the failure that caused the incident above. Each file is",
        f"written to a `{STAGING_SUFFIX}` sibling, hashed there, and moved into",
        "place only once it matches.",
        "",
    ]
    if follow_ups:
        out += ["## After restoring", "",
                "These are the parts left out because they regenerate:", ""]
        for name, command in follow_ups:
            out.append(f"- `{name}` — `{command}`")
        out.append("")
    out += [
        "## Files stored in parts",
        "",
        "GitHub refuses a blob of 100 MiB or more, so a file at or above",
        f"{_mib(CHUNK_LIMIT)} MiB is stored as consecutive `.partNN` files of",
        f"{_mib(PART_SIZE)} MiB. `{CHUNKS_NAME}` carries the WHOLE file's sha256",
        "and size, so a reassembled file is checked against the original rather",
        "than against its parts.",
        "",
    ]
    if chunked:
        for key in chunked:
            out.append(f"- `{key}` — {len(chunks[key]['parts'])} parts, "
                       f"{_mib(chunks[key]['size'])} MiB")
    else:
        out.append("Nothing is chunked at present.")
    out += [
        "",
        "## Integrity",
        "",
        f"`{MANIFEST_NAME}` holds one sha256 line per physical file in this",
        "directory, itself excluded. `verify` re-hashes every one of them and",
        "reports anything missing, extra or mismatched.",
        "",
        "## Licence",
        "",
        f"**{n_excluded} corpus renders are deliberately absent.** Every stem in",
        f"`{EXCLUSIONS_JSON}` — 87 of them, 49 vendor-supplied Windows faces",
        "whose terms permit rendering but not conversion and 38 with no",
        "permissive licence at all — is excluded from `corpus_v2`, in the",
        "atlases, the references and the captions alike. A 95-glyph atlas of such",
        f"a face is the conversion those terms withhold (`{LICENCE_NOTE}`), and",
        "GitHub's terms require the right to upload even to a private",
        "repository. They regenerate locally from fonts that never left this",
        "machine.",
        "",
        "The adapters are a separate question and are kept. They were trained on",
        "the FULL corpus, before that filter existed, so they carry the",
        "unresolved right-to-train question that no output licence settles — "
        "which",
        "is exactly why they are here, in a private backup, and not published.",
        "See `docs/licensing.md`.",
        "",
    ]
    with open(os.path.join(backup_dir, README_NAME), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write("\n".join(out))


def make(root, backup_dir, items=ITEMS, only=None):
    """Refresh the backup from the live data. Never deletes; reports stale files."""
    chosen = select(items, only)
    work, listings, dropped = plan(root, chosen)   # refuses before anything exists

    os.makedirs(backup_dir, exist_ok=True)
    chunks = read_chunks(backup_dir)
    written = set()
    for item, rel, src in work:
        key = f"{item.name}/{rel}"
        chunks.pop(key, None)                     # this run decides afresh
        dest = os.path.join(backup_dir, *key.split("/"))
        written.update(_store(src, dest, key, chunks))

    by_item = {}
    for item, rel, src in listings:
        by_item.setdefault(item, []).append((rel, src))
    listed = []
    for item, pairs in by_item.items():
        rel, count = write_hash_listing(backup_dir, item, pairs)
        written.add(rel)
        listed.append((item, count))

    # A chunk record for an item that is no longer selected stays; one for a
    # file this run stored whole has already been dropped above.
    write_chunks(backup_dir, chunks)
    # The README describes the WHOLE backup, so its licence-exclusion count is
    # planned over every item, not the ones this run refreshed: a `--only`
    # refresh of an unrelated item once rewrote "177 corpus renders are
    # deliberately absent" as 0 (review finding, 2026-09-12). Planning is glob
    # expansion only; if some unselected item's live directory is missing
    # right now, fall back to this run's count rather than refuse the refresh.
    try:
        _, _, dropped_all = plan(root, items) if only else (None, None, dropped)
    except BackupError:
        dropped_all = dropped
    render_readme(backup_dir, items, chunks, sum(dropped_all.values()))
    n_manifest = write_manifest(backup_dir)

    stale = [rel for rel in physical_files(backup_dir)
             if not _is_generated(rel) and rel not in written
             and any(rel.startswith(item.name + "/") for item in chosen)]

    rows = inventory(backup_dir, items, chunks)
    print(f"backup: {backup_dir}")
    print(f"{'item':<36} {'restores to':<34} {'files':>6} {'MiB':>9}")
    total_files = total_bytes = 0
    for item, count, size in rows:
        print(f"{item.name:<36} {item.live:<34} {count:>6} {_mib(size):>9}")
        total_files += count
        total_bytes += size
    print(f"{'total':<36} {'':<34} {total_files:>6} {_mib(total_bytes):>9}")
    # ASCII only in console output; this runs on a cp1252 Windows terminal.
    # The generated README.md is written as UTF-8 and does use em-dashes.
    for item, count in listed:
        print(f"\nhash listing: {item.name}/{HASHES_NAME} -- {count} file(s) "
              f"under {item.live}, hashed but not copied")
    if dropped:
        print(f"\nlicence exclusion: {sum(dropped.values())} file(s) matched a "
              "pattern and were NOT backed up")
        for name in sorted(dropped):
            print(f"    {name:<36} {dropped[name]}")
    print(f"\n{n_manifest} physical file(s) hashed into {MANIFEST_NAME}; "
          f"{len(chunks)} chunked")
    if stale:
        print(f"\nSTALE -- {len(stale)} file(s) in the backup no longer have a "
              "source. Nothing was deleted; remove them by hand if they are "
              "really gone:")
        for rel in stale:
            print(f"    {rel}")
    return 0


# --------------------------------------------------------------------- verify

def verify(backup_dir, only=None):
    """Re-hash every file the manifest lists. 0 clean, 1 on any problem."""
    if only:
        raise BackupError("verify checks the whole backup; --only is for make "
                          "and restore")
    if not os.path.isfile(os.path.join(backup_dir, MANIFEST_NAME)):
        print(f"no {MANIFEST_NAME} in {backup_dir} -- run `make` first")
        return 1
    listed = read_manifest(backup_dir)
    present = set(physical_files(backup_dir)) - {MANIFEST_NAME}

    missing = sorted(set(listed) - present)
    extra = sorted(present - set(listed))
    mismatched = []
    for rel in sorted(set(listed) & present):
        if sha256_file(os.path.join(backup_dir, *rel.split("/"))) != listed[rel]:
            mismatched.append(rel)

    for rel in missing:
        print(f"    MISSING   {rel}")
    for rel in extra:
        print(f"    EXTRA     {rel}   (not in {MANIFEST_NAME})")
    for rel in mismatched:
        print(f"    MISMATCH  {rel}")
    n = len(listed)
    if missing or extra or mismatched:
        print(f"\nFAIL: {n} listed, {len(missing)} missing, {len(extra)} extra, "
              f"{len(mismatched)} mismatched.")
        return 1
    print(f"verified {n} file(s) against {MANIFEST_NAME}: all match.")
    return 0


# -------------------------------------------------------------------- restore

def _entries(backup_dir, item, chunks):
    """The keys of one item's logical files, sorted. Generated files excluded."""
    prefix = item.name + "/"
    parts = {p for meta in chunks.values() for p in meta["parts"]}
    keys = [rel for rel in physical_files(backup_dir)
            if rel.startswith(prefix) and rel not in parts
            and not _is_generated(rel)]
    keys += [key for key in chunks if key.startswith(prefix)]
    return sorted(set(keys))


def _write_staged(backup_dir, key, chunks, tmp):
    with open(tmp, "xb") as out:
        if key in chunks:
            for part in chunks[key]["parts"]:
                with open(os.path.join(backup_dir, *part.split("/")), "rb") as fh:
                    shutil.copyfileobj(fh, out, READ_BLOCK)
        else:
            with open(os.path.join(backup_dir, *key.split("/")), "rb") as fh:
                shutil.copyfileobj(fh, out, READ_BLOCK)


def restore(root, backup_dir, items=ITEMS, only=None):
    """Write back only what is absent. Refuses on ANY problem, before writing."""
    chosen = select(items, only)
    if verify(backup_dir) != 0:
        raise BackupError("the backup did not verify; nothing was restored. "
                          "Fix the backup before restoring from it")
    chunks = read_chunks(backup_dir)
    manifest = read_manifest(backup_dir)

    # CHUNKS.json is a file on disk, so its keys are an input, not a given.
    for key in sorted(set(physical_files(backup_dir)) | set(chunks)):
        check_key(key)
    for meta in chunks.values():
        for part in meta["parts"]:
            check_key(part)

    todo, skipped, conflicts, staged = [], [], [], []
    for item in chosen:
        base = _live_base(root, item)
        for key in _entries(backup_dir, item, chunks):
            rel = key[len(item.name) + 1:]
            dest = os.path.join(base, *rel.split("/"))
            if not contained(root, dest):
                raise BackupError(
                    f"{key} would write to {dest}, outside {root}. Nothing was "
                    "restored")
            want = chunks[key]["sha256"] if key in chunks else manifest.get(key)
            if want is None:
                raise BackupError(f"{key} is in the backup but not in "
                                  f"{MANIFEST_NAME}; nothing was restored")
            if not os.path.lexists(dest):
                todo.append((item, key, dest, want))
                if os.path.lexists(dest + STAGING_SUFFIX):
                    staged.append(dest + STAGING_SUFFIX)
            elif (os.path.isfile(dest) and not is_reparse_point(dest)
                    and sha256_file(dest) == want):
                skipped.append(key)
            else:
                conflicts.append((key, _posix(os.path.relpath(dest, root))))

    if conflicts:
        lines = "\n".join(f"    {live}   (backup: {key})" for key, live in conflicts)
        raise BackupError(
            f"{len(conflicts)} destination(s) exist with DIFFERENT content. "
            "Nothing was written -- this tool never overwrites. Move or delete "
            f"them by hand if the backup is the version you want:\n{lines}")
    if staged:
        lines = "\n".join(f"    {_posix(os.path.relpath(p, root))}" for p in staged)
        raise BackupError(
            f"{len(staged)} staging file(s) from an interrupted restore are in "
            "the way. Nothing was written -- this tool never deletes. Check "
            f"them and remove them by hand:\n{lines}")

    links, checked = [], set()
    for _item, _key, dest, _want in todo:
        parent = os.path.dirname(os.path.abspath(dest))
        if parent in checked:
            continue
        checked.add(parent)
        links += reparse_ancestors(root, dest)
    if is_reparse_point(backup_dir):
        links.append(os.path.abspath(backup_dir))
    if links:
        lines = "\n".join(f"    {p}" for p in sorted(set(links)))
        raise BackupError(
            f"{len(set(links))} director(y/ies) on the way to a destination "
            "are a symlink or an NTFS junction. Nothing was written: a restore "
            "through one writes into the target, not the tree you pointed at "
            f"-- which is how the data was lost in the first place:\n{lines}")

    for _item, key, dest, want in todo:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        tmp = dest + STAGING_SUFFIX
        _write_staged(backup_dir, key, chunks, tmp)
        got = sha256_file(tmp)
        if got != want:
            raise BackupError(
                f"{_posix(os.path.relpath(tmp, root))} hashes {got}, not {want}. "
                f"{_posix(os.path.relpath(dest, root))} was NOT written and no "
                "further file will be. The staged copy is left for inspection; "
                "delete it by hand")
        os.replace(tmp, dest)

    print(f"restore: wrote {len(todo)} file(s), skipped {len(skipped)} already "
          "identical, overwrote 0.")
    done = {item for item, _k, _d, _w in todo}
    follow = [item for item in chosen if item.follow_up and item in done]
    if follow:
        print("\nStill to regenerate:")
        for item in follow:
            print(f"    {item.name:<36} {item.follow_up}")
    return 0


# ------------------------------------------------------------------------ CLI

def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0].replace("\n", " "))
    ap.add_argument("action", choices=("make", "verify", "restore"))
    ap.add_argument("--only", nargs="+", metavar="NAME",
                    help="act on these items only (names are in backup/README.md)")
    ap.add_argument("--root", default=REPO,
                    help="the repository root the live data sits under")
    ap.add_argument("--backup", default=None,
                    help=f"the backup directory (default <root>/{BACKUP_DIRNAME})")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    backup_dir = os.path.abspath(args.backup or os.path.join(root, BACKUP_DIRNAME))
    try:
        if args.action == "make":
            return make(root, backup_dir, ITEMS, args.only)
        if args.action == "verify":
            return verify(backup_dir, args.only)
        return restore(root, backup_dir, ITEMS, args.only)
    except BackupError as exc:
        print(f"REFUSED: {exc}")
        return 1


if __name__ == "__main__":
    _sys.exit(main())
