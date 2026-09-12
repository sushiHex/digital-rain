from src.vecglypher import build_sep_prompt


def test_build_sep_prompt_uppercase():
    prompt = build_sep_prompt("ABCDE")
    assert prompt == "A<|SEP|>B<|SEP|>C<|SEP|>D<|SEP|>E"


def test_build_sep_prompt_single():
    assert build_sep_prompt("A") == "A"


def test_build_sep_prompt_numerals():
    prompt = build_sep_prompt("0123456789")
    assert prompt.count("<|SEP|>") == 9
