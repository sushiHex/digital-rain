import string

import fal_client

from src.svg_parser import extract_paths_from_svg

UPPERCASE = string.ascii_uppercase
LOWERCASE = string.ascii_lowercase
NUMERALS = string.digits


def build_sep_prompt(chars: str) -> str:
    return "<|SEP|>".join(chars)


def _call_vecglypher(prompt: str, style: str) -> str:
    result = fal_client.run(
        "fal-ai/vecglypher",
        arguments={
            "prompt": prompt,
            "style_description": style,
            "temperature": 0.1,
            "output_size": 512,
            "max_tokens": 8192,
        },
    )
    return result.get("svg_content", "")


def generate_glyphs(
    style: str = "geometric sans-serif, 400 weight, clean, uniform stroke width",
) -> dict[str, str]:
    glyphs = {}
    batches = [
        (UPPERCASE, "uppercase"),
        (LOWERCASE, "lowercase"),
        (NUMERALS, "numerals"),
    ]
    for chars, _label in batches:
        prompt = build_sep_prompt(chars)
        svg_content = _call_vecglypher(prompt, style)
        paths = extract_paths_from_svg(svg_content)
        for i, char in enumerate(chars):
            if i < len(paths):
                glyphs[char] = paths[i]
    return glyphs
