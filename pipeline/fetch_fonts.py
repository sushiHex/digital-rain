"""
fetch_fonts.py — Font pool builder with multiple source adapters.

Adapters:
  directory     Copy fonts from a local directory.
  google-fonts  Copy fonts from a local google-fonts repo clone.
  github        Shallow-clone a GitHub repo and collect fonts.
  velvetyne     Collect fonts from all public Velvetyne org repos.
  fontlibrary   Scrape OFL fonts from fontlibrary.org.
"""

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


def _rmtree_force(path):
    """Remove a directory tree, handling read-only files (e.g., .git objects on Windows)."""
    def _on_error(fn, fpath, _exc):
        os.chmod(fpath, stat.S_IWRITE)
        fn(fpath)

    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_on_error)
    else:
        shutil.rmtree(path, onerror=_on_error)


# ---------------------------------------------------------------------------
# Manifest helpers
# ---------------------------------------------------------------------------

MANIFEST_FILENAME = "source_manifest.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_manifest(pool_dir: Path) -> list:
    path = pool_dir / MANIFEST_FILENAME
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _save_manifest(pool_dir: Path, manifest: list) -> None:
    pool_dir.mkdir(parents=True, exist_ok=True)
    path = pool_dir / MANIFEST_FILENAME
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def _manifest_filenames(manifest: list) -> set:
    return {entry["filename"] for entry in manifest}


# ---------------------------------------------------------------------------
# License detection
# ---------------------------------------------------------------------------

_LICENSE_KEYWORDS = {
    "OFL-1.1": ["SIL OPEN FONT LICENSE", "OFL"],
    "Apache-2.0": ["APACHE LICENSE", "APACHE-2.0"],
    "MIT": ["MIT LICENSE", "MIT"],
    "CC0/Public-Domain": ["CC0", "PUBLIC DOMAIN", "CREATIVE COMMONS ZERO"],
    "GPL": ["GNU GENERAL PUBLIC LICENSE", "GPL"],
}


# Matched against the lowercased filename, any extension. A fixed list of exact
# names misses real cases: theleagueof/chunk ships its terms as
# "Open Font License.markdown", which no LICENSE/OFL.txt list would catch.
_LICENSE_NAME_HINTS = ("license", "licence", "copying", "ofl")
# ...but "Open Font License FAQ.markdown" sits beside it and is explanatory
# text, not a grant. Exclude the obvious non-grants.
_LICENSE_NAME_EXCLUDE = ("faq", "readme", "changelog")


def _embedded_license(font_path: Path) -> str:
    """Classify from the font's OWN name ID 13, which is authoritative.

    Added 2026-08-08. Many repos ship no licence file next to the binaries but
    every well-formed font states its terms internally, and reading them is how
    the corpus audit resolved 27 fonts the manifest had lost.
    """
    try:
        from fontTools.ttLib import TTFont
        desc = (TTFont(font_path, lazy=True, fontNumber=0)["name"]
                .getDebugName(13) or "").upper()
    except Exception:
        return "unknown"
    for spdx, keywords in _LICENSE_KEYWORDS.items():
        if any(kw in desc for kw in keywords):
            return spdx
    return "unknown"


def _detect_license(font_path: Path, root: Path = None) -> str:
    """Classify the licence covering `font_path`.

    Walks UP from the font to `root` looking for a licence file, then falls back
    to the font's embedded licence field.

    Until 2026-08-08 this looked only in the font's own directory and its
    parent. Repositories conventionally put LICENSE at the ROOT while fonts live
    in `fonts/ttf/` or similar, three or more levels down, so the search missed
    it and recorded "unknown" -- which is why 1,596 of the 6,141 manifest
    entries carry no licence despite their repos being explicit about it.
    """
    here = font_path.parent
    stop = root.parent if root else None
    seen = 0
    while here and seen < 8:
        try:
            entries = sorted(here.iterdir())
        except OSError:
            entries = []
        for candidate in entries:
            low = candidate.name.lower()
            if not candidate.is_file():
                continue
            if not any(h in low for h in _LICENSE_NAME_HINTS):
                continue
            if any(x in low for x in _LICENSE_NAME_EXCLUDE):
                continue
            try:
                text = candidate.read_text(encoding="utf-8",
                                           errors="ignore").upper()
            except OSError:
                continue
            for spdx, keywords in _LICENSE_KEYWORDS.items():
                if any(kw in text for kw in keywords):
                    return spdx
        if here == stop or here == here.parent:
            break
        here = here.parent
        seen += 1
    return _embedded_license(font_path)


# ---------------------------------------------------------------------------
# Font collection
# ---------------------------------------------------------------------------

def _collect_fonts(source_dir: Path) -> list:
    """Recursively find all *.ttf and *.otf files under source_dir."""
    fonts = []
    for ext in ("*.ttf", "*.otf", "*.TTF", "*.OTF"):
        fonts.extend(source_dir.rglob(ext))
    # Deduplicate by resolved path
    seen = set()
    unique = []
    for f in fonts:
        r = f.resolve()
        if r not in seen:
            seen.add(r)
            unique.append(f)
    return unique


# ---------------------------------------------------------------------------
# Adapters
# ---------------------------------------------------------------------------

def fetch_directory(pool_dir: Path, path: str = None, **kwargs) -> None:
    """Copy fonts from a local directory into the pool."""
    if not path:
        raise ValueError("--path is required for the 'directory' adapter")
    source_dir = Path(path)
    if not source_dir.exists():
        raise FileNotFoundError(f"Directory not found: {source_dir}")

    pool_dir.mkdir(parents=True, exist_ok=True)
    manifest = _load_manifest(pool_dir)
    existing = _manifest_filenames(manifest)

    fonts = _collect_fonts(source_dir)
    added = 0
    for font_path in fonts:
        filename = font_path.name
        if filename in existing:
            continue
        dest = pool_dir / filename
        shutil.copy2(font_path, dest)
        manifest.append({
            "filename": filename,
            "source": "directory",
            "license": _detect_license(font_path),
            "origin_path": str(font_path.resolve()),
            "fetched_at": _now_iso(),
        })
        existing.add(filename)
        added += 1

    _save_manifest(pool_dir, manifest)
    print(f"[directory] Added {added} fonts (skipped {len(fonts) - added} already present).")


def fetch_google_fonts(pool_dir: Path, path: str = None, **kwargs) -> None:
    """Copy fonts from a local google-fonts repository clone."""
    if not path:
        # Try common default location
        default = Path(__file__).parent / "google-fonts"
        if default.exists():
            path = str(default)
        else:
            raise ValueError(
                "--path is required for the 'google-fonts' adapter "
                "(point it at your google/fonts repo clone)"
            )
    source_dir = Path(path)
    if not source_dir.exists():
        raise FileNotFoundError(f"Directory not found: {source_dir}")

    pool_dir.mkdir(parents=True, exist_ok=True)
    manifest = _load_manifest(pool_dir)
    existing = _manifest_filenames(manifest)

    def _license_from_path(font_path: Path) -> str:
        parts = [p.lower() for p in font_path.parts]
        if "ofl" in parts:
            return "OFL-1.1"
        if "apache" in parts:
            return "Apache-2.0"
        if "ufl" in parts:
            return "UFL"
        return _detect_license(font_path)

    fonts = _collect_fonts(source_dir)
    added = 0
    for font_path in fonts:
        # Prefix with family dir name to prevent cross-family collision
        try:
            rel = font_path.relative_to(source_dir)
            family = rel.parts[1] if len(rel.parts) >= 2 else "unknown"
        except (ValueError, IndexError):
            family = "unknown"
        filename = f"{family}_{font_path.name}"
        if filename in existing:
            continue
        dest = pool_dir / filename
        shutil.copy2(font_path, dest)
        manifest.append({
            "filename": filename,
            "source": "google-fonts",
            "license": _license_from_path(font_path),
            "origin_path": str(font_path.resolve()),
            "fetched_at": _now_iso(),
        })
        existing.add(filename)
        added += 1

    _save_manifest(pool_dir, manifest)
    print(f"[google-fonts] Added {added} fonts (skipped {len(fonts) - added} already present).")


def fetch_github(pool_dir: Path, repo: str = None, **kwargs) -> None:
    """Shallow-clone a GitHub repo and collect fonts into the pool."""
    if not repo:
        raise ValueError("--repo is required for the 'github' adapter (e.g. owner/name)")

    pool_dir.mkdir(parents=True, exist_ok=True)
    manifest = _load_manifest(pool_dir)
    existing = _manifest_filenames(manifest)

    repo_url = repo if repo.startswith("http") else f"https://github.com/{repo}.git"

    tmpdir = tempfile.mkdtemp()
    try:
        clone_dir = Path(tmpdir) / "repo"
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--quiet", repo_url, str(clone_dir)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"[github] Clone failed for {repo_url}: {result.stderr.strip()}")
            return

        fonts = _collect_fonts(clone_dir)
        added = 0
        for font_path in fonts:
            repo_slug = repo.replace("/", "_")
            filename = f"{repo_slug}_{font_path.name}"
            if filename in existing:
                continue
            dest = pool_dir / filename
            shutil.copy2(font_path, dest)
            manifest.append({
                "filename": filename,
                "source": "github",
                "license": _detect_license(font_path, root=clone_dir),
                "origin_url": repo_url,
                "fetched_at": _now_iso(),
            })
            existing.add(filename)
            added += 1

        _save_manifest(pool_dir, manifest)
        print(f"[github] {repo}: Added {added} fonts (skipped {len(fonts) - added} already present).")
    finally:
        _rmtree_force(tmpdir)


_VELVETYNE_FALLBACK_REPOS = [
    "velvetyne/Ouroboros",
    "velvetyne/Compagnon",
    "velvetyne/Basteleur",
    "velvetyne/ClimateCrisis",
    "velvetyne/Facade",
    "velvetyne/Galmuri",
    "velvetyne/Grotesk",
    "velvetyne/Lack",
    "velvetyne/LinLibertine",
    "velvetyne/Syne",
    "velvetyne/Velvetyne",
]


def fetch_velvetyne(pool_dir: Path, **kwargs) -> None:
    """Collect fonts from all public Velvetyne org repos via GitHub API."""
    try:
        import requests
        api_url = "https://api.github.com/orgs/velvetyne/repos?per_page=100&type=public"
        headers = {"Accept": "application/vnd.github+json"}
        resp = requests.get(api_url, headers=headers, timeout=30)
        resp.raise_for_status()
        repos = [
            f"velvetyne/{r['name']}"
            for r in resp.json()
            if not r.get("archived", False)
        ]
        print(f"[velvetyne] Found {len(repos)} repos via API.")
    except Exception as exc:
        print(f"[velvetyne] API failed ({exc}), using fallback list.")
        repos = _VELVETYNE_FALLBACK_REPOS

    for repo in repos:
        fetch_github(pool_dir, repo=repo)


def fetch_fontlibrary(pool_dir: Path, **kwargs) -> None:
    """Scrape OFL fonts from fontlibrary.org and download TTFs."""
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError as exc:
        raise RuntimeError(
            "requests and beautifulsoup4 are required for the 'fontlibrary' adapter"
        ) from exc

    pool_dir.mkdir(parents=True, exist_ok=True)
    manifest = _load_manifest(pool_dir)
    existing = _manifest_filenames(manifest)

    base_url = "https://fontlibrary.org"
    search_url = (
        "https://fontlibrary.org/en/search"
        "?license=OFL+%28SIL+Open+Font+License%29&page={page}"
    )
    headers = {"User-Agent": "fetch_fonts/1.0 (font dataset builder)"}

    added = 0
    errors = 0
    error_threshold = 20
    page = 1
    max_pages = 200  # safety limit

    while page <= max_pages:
        url = search_url.format(page=page)
        try:
            time.sleep(1)
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
        except Exception as exc:
            print(f"[fontlibrary] Failed to fetch page {page}: {exc}")
            errors += 1
            if errors >= error_threshold:
                print("[fontlibrary] Error threshold reached, stopping.")
                break
            page += 1
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        # Find links to individual font pages
        font_links = []
        for a in soup.select("a[href]"):
            href = a["href"]
            if "/en/font/" in href:
                full = href if href.startswith("http") else base_url + href
                if full not in font_links:
                    font_links.append(full)

        if not font_links:
            print(f"[fontlibrary] No font links on page {page}, stopping pagination.")
            break

        print(f"[fontlibrary] Page {page}: {len(font_links)} font pages found.")

        for font_page_url in font_links:
            try:
                time.sleep(1)
                fp_resp = requests.get(font_page_url, headers=headers, timeout=30)
                fp_resp.raise_for_status()
                fp_soup = BeautifulSoup(fp_resp.text, "html.parser")

                # Find TTF download links
                ttf_links = []
                for a in fp_soup.select("a[href]"):
                    href = a["href"]
                    if href.lower().endswith(".ttf"):
                        full = href if href.startswith("http") else base_url + href
                        ttf_links.append(full)

                for ttf_url in ttf_links:
                    raw_filename = Path(ttf_url.split("/")[-1].split("?")[0]).name
                    if not raw_filename:
                        continue
                    filename = f"fl_{raw_filename}"
                    if filename in existing:
                        continue
                    try:
                        time.sleep(1)
                        dl = requests.get(ttf_url, headers=headers, timeout=60)
                        dl.raise_for_status()
                        dest = pool_dir / filename
                        dest.write_bytes(dl.content)
                        manifest.append({
                            "filename": filename,
                            "source": "fontlibrary",
                            "license": "OFL-1.1",
                            "origin_url": ttf_url,
                            "fetched_at": _now_iso(),
                        })
                        existing.add(filename)
                        added += 1

                        if added % 50 == 0:
                            _save_manifest(pool_dir, manifest)
                            print(f"[fontlibrary] Checkpoint: {added} fonts saved.")

                    except Exception as exc:
                        print(f"[fontlibrary] Failed to download {ttf_url}: {exc}")
                        errors += 1
                        if errors >= error_threshold:
                            break

            except Exception as exc:
                print(f"[fontlibrary] Failed to fetch font page {font_page_url}: {exc}")
                errors += 1

            if errors >= error_threshold:
                print("[fontlibrary] Error threshold reached, stopping.")
                break

        if errors >= error_threshold:
            break

        page += 1

    if page > max_pages:
        print(f"  [fontlibrary] Reached max_pages limit ({max_pages}), stopping pagination")

    _save_manifest(pool_dir, manifest)
    print(f"[fontlibrary] Done. Added {added} fonts total.")


# ---------------------------------------------------------------------------
# Adapter registry
# ---------------------------------------------------------------------------

ADAPTERS = {
    "directory": fetch_directory,
    "google-fonts": fetch_google_fonts,
    "github": fetch_github,
    "velvetyne": fetch_velvetyne,
    "fontlibrary": fetch_fontlibrary,
}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Fetch fonts from various sources into a local pool directory.",
    )
    parser.add_argument(
        "--source",
        required=True,
        choices=list(ADAPTERS.keys()),
        help="Font source adapter to use.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Directory where fonts and the manifest will be written.",
    )
    parser.add_argument(
        "--path",
        default=None,
        help="Local directory path (used by 'directory' and 'google-fonts' adapters).",
    )
    parser.add_argument(
        "--repo",
        default=None,
        help="GitHub repo (owner/name) for the 'github' adapter.",
    )

    args = parser.parse_args()
    pool_dir = Path(args.output)

    adapter_fn = ADAPTERS[args.source]
    adapter_fn(pool_dir, path=args.path, repo=args.repo)


if __name__ == "__main__":
    main()
