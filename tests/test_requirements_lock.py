"""Pin the lock to the requirements it is supposed to constrain.

WHY THE LOCK EXISTS. CI installed `>=` floors from the live index, so a
dependency release could change the result with nothing changed in the tree --
the reason a regenerated artefact was never byte-exact, and issue #16. The fix
is `requirements.lock`, a pip CONSTRAINTS file: it pins the version of whatever
gets installed and never adds a package.

WHY IT IS NOT A REQUIREMENTS FILE. A universal resolution of `torch` lists the
Linux `nvidia-*` CUDA wheels as dependencies. Installed with `-r` that is 2 GB
of CUDA libraries in a GPU-free runner -- the exact thing CI's CPU-torch step
exists to avoid. With `-c` those rows are inert unless something asks for them,
and nothing does.

WHAT DRIFTS, all silently: a new package added to `requirements.txt` and not
locked, so the constraint does nothing for it; a floor raised past the pin,
which fails in CI rather than here; a row that stops being an exact `==` and
constrains nothing; a pin carrying a marker that is false on Linux, which
leaves CI unpinned while every test here still passes; and a regeneration
without `--universal`.

THE CUDA ROWS ARE A CANARY, NOT A HAZARD IN THEMSELVES. An unmarked
`nvidia-*` constraint still installs nothing on its own -- a constraint only
applies to a package something else requests. What an unmarked row means is
that the lock was regenerated for one platform instead of universally, and
that same regeneration is what would leave the other platforms wrong. So the
check is on the markers, and the reason is provenance.
"""
import os
import re

import pytest
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCK = os.path.join(REPO, "requirements.lock")
SOURCES = ("requirements.txt", "requirements-dev.txt")
EDITABLE = re.compile(r"^(-e\b|--editable\b)")
# Every GPU-shaped distribution the resolution can carry, not just `nvidia-*`:
# `cuda-bindings` and `cuda-toolkit` are direct torch dependencies under those
# names, and `triton` is Linux-only.
CUDA_PREFIXES = ("nvidia-", "cuda-", "triton")
# The two interpreters CI runs, on the platform it runs them on.
CI_ENVIRONMENTS = tuple(
    {"sys_platform": "linux", "platform_system": "Linux", "os_name": "posix",
     "platform_machine": "x86_64", "platform_python_implementation": "CPython",
     "implementation_name": "cpython", "python_version": v,
     "python_full_version": f"{v}.0", "implementation_version": f"{v}.0",
     "extra": ""}
    for v in ("3.12", "3.14"))


def _lines(path):
    """Requirement lines only: no blanks, no comments, no trailing annotations.

    `requirements.txt` annotates most rows (`peft>=0.14.0  # rank-32 LoRA ...`),
    and pip's own rule is that a `#` preceded by whitespace starts a comment.
    """
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = re.split(r"\s+#", raw.strip(), maxsplit=1)[0].strip()
            if line and not line.startswith("#"):
                yield line


def _declared():
    """Every requirement declared across the source files, by canonical name."""
    out = {}
    for name in SOURCES:
        for line in _lines(os.path.join(REPO, name)):
            req = Requirement(line)
            out[canonicalize_name(req.name)] = (req, name)
    return out


def _lock_rows():
    """Every row of the lock, in file order, as (canonical name, req, line).

    A list, not a dict: a duplicate name would otherwise overwrite the first
    and hide whatever was wrong with it.
    """
    rows = []
    for line in _lines(LOCK):
        req = Requirement(line)
        rows.append((canonicalize_name(req.name), req, line))
    return rows


def _pinned():
    """Every row of the lock, by canonical name."""
    return {name: (req, line) for name, req, line in _lock_rows()}


def _exact_version(req):
    """The version of an exact `==` pin, or None if the row is not one."""
    specs = list(req.specifier)
    if len(specs) == 1 and specs[0].operator == "==":
        return specs[0].version
    return None


def test_the_lock_is_not_empty():
    assert len(_pinned()) > 50, "requirements.lock did not parse as pins"


def test_no_name_appears_twice_in_the_lock():
    """Two rows for one name make every other check here read only one."""
    seen, dupes = set(), []
    for name, _, line in _lock_rows():
        if name in seen:
            dupes.append(line)
        seen.add(name)
    assert dupes == [], f"pinned more than once: {dupes}"


def test_every_row_of_the_lock_is_an_exact_pin():
    """Not just the declared ones. A transitive row that regresses to `>=`
    constrains nothing, and uv never emits one -- so it means a hand edit."""
    loose = [line for _, req, line in _lock_rows() if _exact_version(req) is None]
    assert loose == [], f"not an exact `==` pin: {loose}"


@pytest.mark.parametrize("name", sorted(_declared()))
def test_every_declared_requirement_is_pinned(name):
    req, source = _declared()[name]
    pinned = _pinned().get(name)
    assert pinned is not None, (
        f"{req.name} is required by {source} and absent from requirements.lock -- "
        "regenerate it (the command is in the lock's header)")
    assert _exact_version(pinned[0]) is not None, (
        f"{req.name} is not pinned exactly in requirements.lock: {pinned[1]!r}")


@pytest.mark.parametrize("name", sorted(_declared()))
def test_every_pin_satisfies_its_declared_floor(name):
    req, source = _declared()[name]
    pinned = _pinned()[name]
    version = _exact_version(pinned[0])
    assert req.specifier.contains(version), (
        f"requirements.lock pins {req.name}=={version}, which does not satisfy "
        f"`{req}` in {source}")


@pytest.mark.parametrize("name", sorted(_declared()))
def test_every_pin_actually_applies_on_the_python_ci_runs(name):
    """A marker is what makes a pin silently absent.

    `pytest==9.1.1 ; sys_platform == "win32"` is an exact pin satisfying its
    floor, and pins nothing at all on the Ubuntu runner. Nothing else here
    would notice.
    """
    req, _ = _declared()[name]
    marker = _pinned()[name][0].marker
    if marker is None:
        return
    dead = [env["python_version"] for env in CI_ENVIRONMENTS
            if not marker.evaluate(env)]
    assert dead == [], (
        f"{req.name}'s pin does not apply on CI's Python {dead}: {marker}")


def test_the_lock_has_no_editable_or_url_requirements():
    """pip rejects both in a constraints file, and a URL pins nothing.

    The URL half is read off the parsed requirement rather than matched as
    text: `pkg @ https://x/y.whl` and `pkg@https://x/y.whl` are both legal and
    only one of them has spaces around the `@`.
    """
    bad = [line for _, req, line in _lock_rows()
           if req.url is not None or EDITABLE.match(line)]
    assert bad == [], f"not usable as constraints: {bad}"


def test_every_cuda_row_keeps_its_environment_marker():
    """Unmarked GPU rows mean the lock was resolved for one platform.

    Not that the constraint would install CUDA by itself -- it would not, a
    constraint only applies to a package something else asks for. It is the
    visible signature of a regeneration without `--universal`, and that same
    regeneration is what leaves the other platforms wrong.
    """
    unmarked = [line for name, req, line in _lock_rows()
                if name.startswith(CUDA_PREFIXES) and req.marker is None]
    assert unmarked == [], f"GPU wheels pinned for every platform: {unmarked}"
