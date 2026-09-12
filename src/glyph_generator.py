"""Generate font glyphs as SVG paths using Claude as a proxy.

This module replaces VecGlypher (fal-ai) with Claude Opus 4.6 for local testing.
The interface is identical: generate_glyphs(style) → dict[char, svg_path].

When ready for production, swap back to vecglypher.py (fal-ai VecGlypher).
"""
import os
import string
import subprocess
import json
import tempfile


UPPERCASE = string.ascii_uppercase
LOWERCASE = string.ascii_lowercase
NUMERALS = string.digits

SYSTEM_PROMPT = """You generate clean SVG paths for font glyphs. Output ONLY valid JSON.

Rules:
- Each glyph is a single SVG path using ONLY M (moveTo), L (lineTo), Q (quadratic Bezier), and Z (closePath) commands
- Use absolute coordinates only (uppercase commands)
- Coordinate space: 0-1000 (x) by 0-1000 (y), where y=0 is baseline and y=700 is cap height
- Snap coordinates to integers
- Outer contours must be CLOCKWISE (for TrueType y-up)
- Inner counters (holes) must be COUNTER-CLOCKWISE
- Every path must close with Z
- Glyphs should look like professional font letters, not crude shapes

Output format — a JSON object mapping each character to its SVG path d-attribute:
{"A": "M 50 0 L 300 700 L 550 0 Z M 150 250 L 400 250 L 350 300 L 200 300 Z", "B": "M ..."}
"""


def _call_claude(chars: str, style: str) -> dict[str, str]:
    """Call Claude CLI to generate SVG paths for characters.

    Uses `claude -p` (print mode) to get a single response.
    """
    user_prompt = f"""Generate SVG path d-attributes for these characters: {chars}

Style: {style}

Return ONLY a JSON object mapping each character to its SVG path d-attribute string.
No markdown, no explanation, no code fences. Just the JSON object."""

    # Write prompts to temp files to avoid shell quoting issues on Windows
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as sf:
        sf.write(SYSTEM_PROMPT)
        system_file = sf.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as uf:
        uf.write(user_prompt)
        user_file = uf.name

    try:
        # Read prompts from files and pipe to claude
        with open(user_file, 'r', encoding='utf-8') as f:
            user_text = f.read()

        with open(system_file, 'r', encoding='utf-8') as f:
            system_text = f.read()

        result = subprocess.run(
            ["claude", "-p", "--model", "claude-haiku-4-5", "--system-prompt", system_text],
            input=user_text,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"Claude CLI error: {result.stderr[:200]}")
            return {}

        # Parse JSON from response — handle markdown fences if present
        response = result.stdout.strip()
        if response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

        return json.loads(response)

    except subprocess.TimeoutExpired:
        print("Claude CLI timed out")
        return {}
    except json.JSONDecodeError as e:
        print(f"Failed to parse Claude response as JSON: {e}")
        print(f"Raw response: {result.stdout[:500]}")
        return {}
    finally:
        os.unlink(system_file)
        os.unlink(user_file)


def generate_glyphs(
    style: str = "geometric sans-serif, 400 weight, clean, uniform stroke width",
) -> dict[str, str]:
    """Generate all 62 Latin glyphs via Claude API calls.

    Makes 3 calls: uppercase A-Z, lowercase a-z, numerals 0-9.

    Args:
        style: Natural language style description.

    Returns:
        Dict mapping character → SVG path d-attribute string.
    """
    glyphs = {}

    batches = [
        (UPPERCASE, "uppercase letters A-Z"),
        (LOWERCASE, "lowercase letters a-z"),
        (NUMERALS, "numerals 0-9"),
    ]

    for chars, label in batches:
        print(f"Generating {label}...")
        result = _call_claude(chars, style)
        glyphs.update(result)
        print(f"  Got {len(result)} glyphs")

    return glyphs
