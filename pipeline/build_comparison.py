"""Build model_comparison.html with all font test results embedded as base64 WOFF2."""
import base64

def load_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

vec_repo = load_b64("vec_repo.woff2")
vec_greedy = load_b64("vec_greedy.woff2")
vec_orig = load_b64("vecglypher_result.woff2")
sonnet = load_b64("sonnet_result.woff2")
opus = load_b64("opus_result.woff2")
haiku = load_b64("haiku_result.woff2")

models = [
    ("VecRepo", vec_repo, "VecGlypher — Repo Recommended", "NEW BEST",
     "badge-blue", "model new",
     "410s (cold) / ~57s warm", "$0.05", "10/10", "tag good",
     "Boldest, most professional. Clean I. Best weight consistency.",
     "temp=0.7, top_p=0.8, top_k=20, rep_penalty=1.05. Style: sans-serif, geometric, no serifs, monolinear. "
     "Uses the VecGlypher repo's own recommended Qwen sampling parameters."),

    ("VecGreedy", vec_greedy, "VecGlypher — Greedy Decoding", "",
     "", "model",
     "410s (cold) / ~57s warm", "$0.05", "10/10", "tag good",
     "Clean but thin. Subtle serifs on F. Lighter weight than Repo.",
     "temp=0, top_k=1 (greedy, matches paper eval conditions). Same improved style description."),

    ("VecOriginal", vec_orig, "VecGlypher — Original (fal-ai defaults)", "",
     "", "model",
     "61s (warm)", "$0.05", "10/10", "tag mid",
     "Good overall but I has serif artifact. Inconsistent weight.",
     "temp=0.1, top_k=5 (fal-ai defaults). Style: geometric sans-serif, 400 weight, clean."),

    ("SonnetFont", sonnet, "Claude Sonnet 4.6", "",
     "", "model",
     "864s (14.4 min)", "~$0.15", "8/10", "tag mid",
     "A missing crossbar, G has unwanted spur.",
     "Default Claude API settings. SVG generated via JSON prompt."),

    ("OpusFont", opus, "Claude Opus 4.6", "",
     "", "model",
     "907s (15.1 min)", "~$0.50", "6/10", "tag bad",
     "A inverted, F/G/J wrong. Worse than Sonnet despite higher cost.",
     "Default Claude API settings."),

    ("HaikuFont", haiku, "Claude Haiku 4.5", "",
     "", "model",
     "24s", "~$0.01", "2/10", "tag bad",
     "Filled rectangles and blobs. Unusable.",
     "Default Claude API settings."),
]

font_faces = "\n".join(
    f"    @font-face {{ font-family: '{m[0]}'; src: url(data:font/woff2;base64,{m[1]}) format('woff2'); }}"
    for m in models
)

def model_card(m):
    font_id, _, title, badge_text, badge_class, card_class, time_str, cost, score, score_tag, quality, note = m
    badge_html = f' <span class="{badge_class}">{badge_text}</span>' if badge_text else ""
    return f"""
<div class="{card_class}">
    <h2>{title}{badge_html}</h2>
    <div class="meta">
        <span>&#9201; {time_str}</span>
        <span>&#128176; {cost}</span>
        <span class="{score_tag}">{score} recognizable</span>
    </div>
    <div class="note"><strong>Quality:</strong> {quality}<br><strong>Settings:</strong> {note}</div>
    <div class="samples">
        <div class="sample lg" style="font-family: '{font_id}', monospace;">ABCDEFGHIJ</div>
        <div class="sample md" style="font-family: '{font_id}', monospace;">ABCDEFGHIJ</div>
        <div class="sample sm" style="font-family: '{font_id}', monospace;">ABCDEFGHIJ — The quick brown fox jumps over the lazy dog</div>
    </div>
</div>"""

cards = "\n".join(model_card(m) for m in models)

# Build summary table rows
rows = ""
for m in models:
    font_id, _, title, _, _, _, time_str, cost, score, score_tag, quality_short, _ = m
    time_color = "c-green" if "57s" in time_str or "61s" in time_str else ("c-yellow" if "864" in time_str else ("c-red" if "907" in time_str else "c-dim"))
    score_color = "c-green" if "10/10" in score else ("c-yellow" if "8/10" in score else "c-red")
    rows += f"""
        <tr>
            <td>{'<strong>' + title.split(' — ')[-1] + '</strong>' if 'Repo' in title else title.split(' — ')[-1] if ' — ' in title else title}</td>
            <td>{time_str}</td>
            <td>{cost}</td>
            <td class="{score_color} score">{score}</td>
            <td>{quality_short[:50]}</td>
        </tr>"""

html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>AI Font Generation: Model Comparison</title>
<style>
{font_faces}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: system-ui, -apple-system, sans-serif; max-width: 1200px; margin: 0 auto; padding: 40px 20px; background: #0a0a0a; color: #e0e0e0; }}
    h1 {{ text-align: center; font-size: 28px; margin-bottom: 8px; color: #fff; }}
    .subtitle {{ text-align: center; color: #666; font-size: 14px; margin-bottom: 12px; }}
    .divider {{ text-align: center; color: #444; font-size: 12px; text-transform: uppercase; letter-spacing: 2px; margin: 32px 0 20px; padding-top: 32px; border-top: 1px solid #222; }}
    .model {{ background: #141414; border: 1px solid #2a2a2a; border-radius: 12px; padding: 28px; margin-bottom: 20px; }}
    .model.new {{ border: 2px solid #60a5fa; }}
    .model h2 {{ margin-bottom: 4px; color: #fff; font-size: 20px; }}
    .badge-blue {{ background: #60a5fa; color: #000; padding: 2px 10px; border-radius: 12px; font-size: 13px; margin-left: 8px; font-weight: 600; }}
    .meta {{ color: #666; font-size: 13px; margin-bottom: 12px; display: flex; flex-wrap: wrap; gap: 12px; }}
    .tag {{ background: #1e1e1e; border: 1px solid #333; padding: 2px 8px; border-radius: 6px; font-size: 12px; }}
    .tag.good {{ border-color: #4ade80; color: #4ade80; }}
    .tag.mid {{ border-color: #facc15; color: #facc15; }}
    .tag.bad {{ border-color: #f87171; color: #f87171; }}
    .samples {{ display: grid; gap: 8px; }}
    .sample {{ padding: 16px 20px; background: #1a1a1a; border-radius: 8px; word-break: break-all; color: #fff; }}
    .sample.lg {{ font-size: 72px; line-height: 1.2; }}
    .sample.md {{ font-size: 48px; line-height: 1.2; }}
    .sample.sm {{ font-size: 24px; line-height: 1.4; }}
    .note {{ background: #1a1a2e; border: 1px solid #333; border-radius: 8px; padding: 14px; margin: 8px 0 12px; font-size: 13px; color: #aaa; line-height: 1.5; }}
    .note strong {{ color: #60a5fa; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
    th, td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid #222; font-size: 14px; }}
    th {{ color: #888; font-weight: 500; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }}
    .c-green {{ color: #4ade80; }}
    .c-yellow {{ color: #facc15; }}
    .c-red {{ color: #f87171; }}
    .c-dim {{ color: #555; }}
    .score {{ font-weight: 700; font-size: 16px; }}
</style>
</head><body>

<h1>AI Font Generation: Model Comparison</h1>
<p class="subtitle">Characters: ABCDEFGHIJ — Style: geometric sans-serif, 400 weight</p>

<div class="divider">VecGlypher Settings Comparison</div>

{cards}

<div class="divider">Reference</div>

<div class="model">
    <h2>Arial (System Font)</h2>
    <div class="meta"><span class="tag">Professional baseline</span></div>
    <div class="samples">
        <div class="sample lg" style="font-family: Arial, Helvetica, sans-serif;">ABCDEFGHIJ</div>
        <div class="sample md" style="font-family: Arial, Helvetica, sans-serif;">ABCDEFGHIJ</div>
        <div class="sample sm" style="font-family: Arial, Helvetica, sans-serif;">ABCDEFGHIJ — The quick brown fox jumps over the lazy dog</div>
    </div>
</div>

<div class="model" style="background:#111118;">
    <h2>Results Summary</h2>
    <table>
        <tr><th>Model</th><th>Time</th><th>Cost</th><th>Score</th><th>Quality</th></tr>
        {rows}
    </table>
</div>

</body></html>"""

with open("model_comparison.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Updated model_comparison.html with all 7 variants")
