import pytest

# The superseded external-API path; `fal-client` is the `vecglypher` extra and
# is not installed on the CI runner. The first public CI run failed at
# collection on exactly this import.
pytest.importorskip("fal_client")

from src.vecglypher import build_sep_prompt  # noqa: E402


def test_build_sep_prompt_uppercase():
    prompt = build_sep_prompt("ABCDE")
    assert prompt == "A<|SEP|>B<|SEP|>C<|SEP|>D<|SEP|>E"


def test_build_sep_prompt_single():
    assert build_sep_prompt("A") == "A"
