"""Scan (and optionally fix) the tracked tree for things that must not go public.

WHY A TOOL AND NOT A ONE-OFF SWEEP. A repository is sanitised at the moment it
is published and then keeps accruing local paths, pasted tool errors and machine
names. `--check` exits non-zero when anything is found, so it can gate a release
the same way the tests do.

WHAT IT LOOKS FOR

  home paths      C:\\Users\\<name>\\ and /c/Users/<name>/ in any form. These leak
                  a username and are meaningless to a reader.
  tool noise      Blocks of pasted CLI errors -- a corrupted-config message got
                  pasted into three oracle reports, carrying paths with it. It
                  is not research content and does not belong in the record.
  secrets         API-key shapes, tokens, private keys. `.env.example` holds
                  placeholders and is expected to pass. Broadened 2026-09-11
                  (fine-grained GitHub tokens, AWS, Slack, bearer strings);
                  GitHub's own secret scanning only runs once the repository
                  is public, which is after exposure, so this is the gate.
  machine names   Hostnames picked up from perf-counter output.
  blocked files   Fonts, weights and archives may not be tracked at all.

WHAT IT DELIBERATELY DOES NOT TOUCH

  Co-Authored-By trailers in git history. The work was done with an AI assistant
  and this repository's whole subject is honest reporting; concealing that would
  contradict it. Session URLs in commit messages are a separate question -- they
  are dead links for any reader, but removing them means rewriting history.

  python analysis/sanitize_for_publish.py --check   # gate, exits 1 on findings
  python analysis/sanitize_for_publish.py --fix
"""

# repo root on sys.path so `python analysis/x.py` works as well as `-m`
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import re
import subprocess

HOME = [
    # `{1,2}` because a path inside a JSON string carries DOUBLED backslashes
    # between the drive letter, `Users` and the name. With a single `[\\/]`
    # this pattern missed three tracked JSON result files for a month while
    # the gate reported "clean" -- the exact failure a gate exists to prevent.
    # The drive may also be a UNC host: two backslashes, a hostname, then the
    # same Users segment. (Not spelled out here: this file is scanned too.)
    (re.compile(r"(?:[A-Za-z]:|\\\\[A-Za-z0-9._-]+)[\\/]{1,2}Users[\\/]{1,2}"
                r"[A-Za-z0-9._-]+", re.I), "<HOME>"),
    (re.compile(r"/c/Users/[A-Za-z0-9._-]+", re.I), "<HOME>"),
    # Linux and macOS homes. The lookbehind keeps `example.edu/home/x` (a URL
    # path segment) out; a real path is preceded by a quote, a space, `=`,
    # `:` or the start of the line.
    (re.compile(r"(?<![\w./])/home/[A-Za-z0-9._-]+"), "<HOME>"),
    (re.compile(r"(?<![\w./:])/Users/[A-Za-z0-9._-]+"), "<HOME>"),
]

# Whole lines that are pasted tool failure output, not content.
NOISE_LINE = re.compile(
    r"^(Claude configuration file at .*is corrupted"
    r"|The corrupted file has been backed up to:"
    r"|A backup file exists at:"
    r"|You can manually restore it by running:"
    r"|Configuration error in .*\.claude\.json"
    r"|Fatal error in message reader:"
    r"|Error output: Check stderr output for details).*$")

SECRET = [
    (re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"), "openai-style key"),
    (re.compile(r"\bhf_[A-Za-z0-9]{20,}"), "huggingface token"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"), "github token"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"), "github fine-grained token"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "aws access key"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"), "slack token"),
    (re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{20,}"), "bearer credential"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key"),
]
MACHINE = re.compile(r"\bdesktop-[a-z0-9]{6,}\b", re.I)

# Images are figures and are not scanned. Everything else in this tuple must
# NOT be tracked at all: fonts and weights are the two licensing blockers, and
# an archive can carry anything. `--check` fails on their presence; `--fix`
# does not delete them, because that is a decision, not a redaction.
SKIP_SUFFIX = (".png", ".jpg", ".jpeg", ".gif", ".ico")
BLOCKED_SUFFIX = (".ttf", ".otf", ".woff", ".woff2", ".pt", ".pth", ".ckpt",
                  ".safetensors", ".npz", ".bin", ".pkl", ".zip", ".gz",
                  ".tgz", ".7z", ".tar", ".rar")


def all_tracked():
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True)
    return [f for f in out.stdout.splitlines() if f]


def tracked():
    return [f for f in all_tracked() if not f.lower().endswith(SKIP_SUFFIX)]


def blocked():
    """Tracked fonts, weights and archives -- none may be published."""
    return [f for f in all_tracked() if f.lower().endswith(BLOCKED_SUFFIX)]


def scan_text(text):
    """(n_home, n_noise, secrets, n_machine) for one file's text."""
    n_home = sum(len(p.findall(text)) for p, _ in HOME)
    n_noise = sum(1 for ln in text.splitlines() if NOISE_LINE.match(ln))
    secrets = [name for p, name in SECRET if p.search(text)]
    n_machine = len(MACHINE.findall(text))
    return n_home, n_noise, secrets, n_machine


def clean_text(text):
    kept = [ln for ln in text.splitlines(keepends=True)
            if not NOISE_LINE.match(ln.rstrip("\r\n"))]
    text = "".join(kept)
    for pat, repl in HOME:
        text = pat.sub(repl, text)
    return MACHINE.sub("<HOST>", text)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--check", action="store_true",
                   help="report only; exit 1 on findings")
    g.add_argument("--fix", action="store_true", help="rewrite the offending files")
    args = ap.parse_args(argv)

    tot = {"home": 0, "noise": 0, "machine": 0}
    secret_hits, touched = [], []
    for f in tracked():
        try:
            text = open(f, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        h, n, sec, m = scan_text(text)
        if sec:
            secret_hits.append((f, sec))
        if not (h or n or m):
            continue
        tot["home"] += h
        tot["noise"] += n
        tot["machine"] += m
        touched.append((f, h, n, m))
        if args.fix:
            open(f, "w", encoding="utf-8", newline="").write(clean_text(text))

    CODE = (".py", ".sh", ".ps1", ".js", ".ts", ".yaml", ".yml", ".toml", ".cfg")
    code_touched = []
    for f, h, n, m in touched:
        bits = [x for x in (f"{h} home path" if h else "",
                            f"{n} noise line" if n else "",
                            f"{m} machine name" if m else "") if x]
        flag = "  <-- CODE" if f.lower().endswith(CODE) else ""
        print(f"  {f:<60} {', '.join(bits)}{flag}")
        if f.lower().endswith(CODE):
            code_touched.append(f)

    if code_touched:
        # Learned the hard way: redacting a path INSIDE code breaks the code.
        # build_comparison_page.py had REPO = "<a home path>" and the automatic
        # substitution turned it into a string that is not a path at all. A
        # redactor cannot know whether a path is prose or a value.
        print("\n!! These are CODE files. A substituted path is not a working")
        print("!! path -- fix them by DERIVING the location instead of pasting")
        print("!! a literal, then re-run. Do not ship the placeholder:")
        for f in code_touched:
            print(f"     {f}")
    print(f"\nfiles affected {len(touched)}   home paths {tot['home']}   "
          f"pasted noise lines {tot['noise']}   machine names {tot['machine']}")

    if secret_hits:
        print("\n!! POSSIBLE SECRETS -- never auto-fixed, review by hand:")
        for f, sec in secret_hits:
            print(f"   {f}: {', '.join(sec)}")

    blocked_files = blocked()
    if blocked_files:
        print("\n!! FONTS, WEIGHTS OR ARCHIVES ARE TRACKED -- none may be "
              "published (the two licensing blockers; an archive can carry "
              "anything). Untrack them; --fix will not delete them:")
        for f in blocked_files:
            print(f"   {f}")

    if args.fix:
        print("\nfiles rewritten. Re-run with --check to confirm clean.")
        return 0
    if args.check and (touched or secret_hits or blocked_files):
        print("\nFAIL: the tree is not clean for publication.")
        return 1
    if not touched and not secret_hits and not blocked_files:
        print("clean.")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
