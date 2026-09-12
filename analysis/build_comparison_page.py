"""Assemble the comparison artifact, injecting real numbers and the specimen."""
import base64
import json
import os

SCRATCH = os.path.dirname(os.path.abspath(__file__))
# Derive the repo root; do not hardcode an absolute path. The original
# hardcoded one leaked a username and broke on every other machine.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

data = json.load(open(os.path.join(SCRATCH, "page_data.json")))
b64 = open(os.path.join(SCRATCH, "specimen_b64.txt")).read().strip()

PER_FONT = [
    {"font": "Bitcount Grid", "kind": "dot-grid", "u": 0.074, "r": 0.074, "w": 0.191, "n": 0.138},
    {"font": "Fascinate Inline", "kind": "inline stroke", "u": 0.191, "r": 0.255, "w": 0.287, "n": 0.489},
    {"font": "Bitcount Prop", "kind": "dot-grid", "u": 0.181, "r": 0.213, "w": 0.181, "n": 0.266},
    {"font": "Dangrek", "kind": "rounded bold", "u": 0.511, "r": 0.585, "w": 0.649, "n": 0.691},
    {"font": "Nova Square", "kind": "geometric", "u": 0.532, "r": 0.489, "w": 0.585, "n": 0.617},
    {"font": "Rubik Distressed", "kind": "distress", "u": 0.234, "r": 0.191, "w": 0.234, "n": 0.266},
    {"font": "Averia Serif", "kind": "serif", "u": 0.745, "r": 0.702, "w": 0.755, "n": 0.830},
    {"font": "Wonky", "kind": "control", "u": 0.872, "r": 0.798, "w": 0.830, "n": 0.840},
]

REDIST = [
    {"mech": "rank 64", "metric": "char_acc", "rho": -0.491, "p": "0.0003", "hard": 0.0298, "easy": -0.0289},
    {"mech": "rank 64", "metric": "dinov2", "rho": -0.683, "p": "<0.0001", "hard": 0.0301, "easy": -0.0191},
    {"mech": "weighted", "metric": "char_acc", "rho": -0.468, "p": "0.0006", "hard": 0.0221, "easy": -0.0357},
    {"mech": "weighted", "metric": "dinov2", "rho": -0.456, "p": "0.0009", "hard": 0.0077, "easy": -0.0234},
]

HTML = """<title>Font model comparison &#8212; 4B vs 9B</title>
<style>
:root{
  color-scheme:light;
  --surface:#fcfcfb; --raised:#f4f3f0; --line:#e2e0da;
  --ink:#0b0b0b; --muted:#52514e; --faint:#7d7a74;
  --nine:#2a78d6; --four:#eb6834;
  --good:#0ca30c; --crit:#d03b3b; --mid:#f0efec;
  --sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
}
@media (prefers-color-scheme:dark){
  :root:where(:not([data-theme="light"])){
    color-scheme:dark;
    --surface:#1a1a19; --raised:#232322; --line:#35342f;
    --ink:#ffffff; --muted:#c3c2b7; --faint:#8f8d84;
    --nine:#3987e5; --four:#d95926; --mid:#383835;
  }
}
:root[data-theme="dark"]{
  color-scheme:dark;
  --surface:#1a1a19; --raised:#232322; --line:#35342f;
  --ink:#ffffff; --muted:#c3c2b7; --faint:#8f8d84;
  --nine:#3987e5; --four:#d95926; --mid:#383835;
}
*{box-sizing:border-box}
body{margin:0;background:var(--surface);color:var(--ink);font-family:var(--sans);
  font-size:16px;line-height:1.55;-webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:56px 24px 96px;
  display:flex;flex-direction:column;gap:56px}
h1{font-size:clamp(28px,4vw,40px);line-height:1.1;letter-spacing:-.022em;margin:0;text-wrap:balance}
h2{font-size:20px;letter-spacing:-.012em;margin:0 0 4px;text-wrap:balance}
h3{font-size:14px;letter-spacing:.07em;text-transform:uppercase;color:var(--faint);margin:0 0 12px;font-weight:600}
p{margin:0;max-width:68ch;color:var(--muted)}
p.lede{color:var(--ink)}
section{display:flex;flex-direction:column;gap:16px}
.eyebrow{font-family:var(--mono);font-size:12.5px;letter-spacing:.08em;
  text-transform:uppercase;color:var(--faint)}
.num{font-family:var(--mono);font-variant-numeric:tabular-nums}

/* hero */
.hero{background:var(--raised);border:1px solid var(--line);border-radius:10px;
  padding:28px 30px;display:flex;flex-direction:column;gap:14px}
.hero .big{font-family:var(--mono);font-variant-numeric:tabular-nums;
  font-size:clamp(30px,5vw,46px);letter-spacing:-.03em;line-height:1;color:var(--ink)}
.hero .big em{font-style:normal;color:var(--good)}
.badge{display:inline-flex;align-items:center;gap:7px;font-size:13px;font-weight:600;
  padding:3px 10px;border-radius:999px;border:1px solid currentColor;width:fit-content}
.badge.good{color:var(--good)} .badge.warn{color:var(--crit)}

/* table */
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--raised)}
table{border-collapse:collapse;width:100%;min-width:760px;font-size:14px}
th,td{padding:9px 13px;text-align:right;border-bottom:1px solid var(--line);white-space:nowrap}
th{font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--faint);
  font-weight:600;background:var(--surface);position:sticky;top:0}
th:first-child,td:first-child{text-align:left}
tbody tr:last-child td{border-bottom:none}
td.v{font-family:var(--mono);font-variant-numeric:tabular-nums}
.name{display:flex;align-items:baseline;gap:8px}
.dot{display:inline-block;width:8px;height:8px;border-radius:2px;flex:none;transform:translateY(-1px)}
.dot.nine{background:var(--nine)} .dot.four{background:var(--four)}
.sub{color:var(--faint);font-size:12.5px}
.best{font-weight:700}
tr.hl{background:color-mix(in srgb,var(--good) 9%,transparent)}

/* bar in cell */
.bar{position:relative;height:6px;border-radius:3px;background:var(--mid);
  min-width:70px;overflow:hidden}
.bar>i{position:absolute;inset:0 auto 0 0;border-radius:3px;display:block}
.bar>i.nine{background:var(--nine)} .bar>i.four{background:var(--four)}

/* diverging */
.div{display:grid;grid-template-columns:104px 1fr 168px;gap:12px 14px;align-items:center;
  font-size:13.5px}
.stat{font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:12px;color:var(--faint);
  white-space:nowrap}
.divbar{position:relative;height:22px;background:linear-gradient(90deg,
  transparent 0 calc(50% - 1px),var(--line) calc(50% - 1px) calc(50% + 1px),transparent calc(50% + 1px));}
.divbar>span{position:absolute;top:4px;height:14px;border-radius:3px}
.divbar>span.pos{background:var(--nine)} .divbar>span.neg{background:var(--crit)}
.divbar>b{position:absolute;top:2px;font-family:var(--mono);font-size:11.5px;
  font-variant-numeric:tabular-nums;font-weight:500;color:var(--muted)}
figure{margin:0;display:flex;flex-direction:column;gap:10px}
figure img{width:100%;max-width:391px;height:auto;border-radius:8px;
  border:1px solid var(--line);background:#fff;display:block;margin:0 auto}
figcaption{font-size:13px;color:var(--faint);max-width:68ch}
.cols{display:grid;gap:18px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.card{border:1px solid var(--line);border-radius:10px;padding:18px 20px;background:var(--raised);
  display:flex;flex-direction:column;gap:8px}
.card h4{margin:0;font-size:15px;letter-spacing:-.005em}
.card p{font-size:14px}
.rule{height:1px;background:var(--line);border:0;margin:0}
.foot{font-size:13px;color:var(--faint)}
code{font-family:var(--mono);font-size:.9em;background:var(--mid);padding:1px 5px;border-radius:4px}
.legend{display:flex;gap:18px;flex-wrap:wrap;font-size:13px;color:var(--muted)}
.legend span{display:inline-flex;align-items:center;gap:7px}
</style>

<div class="wrap">

<header>
  <div class="eyebrow">Glyph-conditioned font generation &#183; evaluated 2026-08-02</div>
  <h1>What the Apache-2.0 path costs, and what two capacity experiments bought</h1>
  <p class="lede" style="margin-top:14px">Seven trained variants on one 50-font holdout, all
  prompt-matched, all scored with the same harness. The headline is not in the
  aggregates &#8212; it is in <em>which</em> fonts moved.</p>
</header>

<section class="hero">
  <div class="badge good">&#9650; first time the free path beat the licensed one</div>
  <div class="big">Bitcount Grid&nbsp; 0.074 &#8594; <em>0.191</em></div>
  <p>Distinctiveness-weighted sampling lifts the Apache-2.0 4B past the
  non-commercial 9B on this dot-grid face &#8212; the 9B scores <span class="num">0.138</span>.
  It is one font out of fifty, and the same change costs the easy half of the
  holdout. Both facts matter.</p>
</section>

__FRONTIER__

<section>
  <h3>The mechanism</h3>
  <h2>Neither experiment added capacity &#8212; both moved it</h2>
  <p>Rank 64 and weighted sampling are independent interventions, and the formal gate
  says <strong>no difference</strong> for both. But correlating each font's delta against its
  baseline shows something the aggregate hides: quality is being reallocated from easy
  fonts to hard ones. Negative &rho; means exactly that.</p>
  __REDIST__
  <p class="foot">Spearman &rho; between per-font delta and the uniform-run baseline, n=50.
  Both mechanisms significant; neither raises the mean.</p>
</section>

<section>
  <h3>Per font</h3>
  <h2>The gains are concentrated in structurally unusual faces</h2>
  __PERFONT__
  <p class="foot">char_acc, 94 cells per font. <strong>Bold</strong> marks the best of the three
  4B variants. The control is where all methods should agree &#8212; and does.</p>
</section>

<section>
  <h3>Specimen</h3>
  <h2>What the numbers look like</h2>
  <figure>
    <img alt="Ground truth, 9B, 4B uniform and 4B weighted rendering the word Hamburg in four typefaces" src="data:image/png;base64,__B64__">
    <figcaption>Rows: ground truth, shipped 9B, 4B uniform, 4B weighted. Bitcount's dot
    structure and Fascinate's inline stroke visibly recover under weighting; the Wonky
    control is indistinguishable across all four, as its numbers predict.</figcaption>
  </figure>
</section>

<section>
  <h3>Reading this honestly</h3>
  <h2>Three things this does not show</h2>
  <div class="cols">
    <div class="card">
      <h4>The holdout is now the limiting instrument</h4>
      <p>Fifty fonts, mostly ordinary. A change that helps distinctive faces scores as
      &#8220;no difference&#8221;. That has now happened twice with two different mechanisms.
      Further work on this axis needs a distinctiveness-stratified split.</p>
    </div>
    <div class="card">
      <h4>Redistribution is not creation</h4>
      <p>Every 4B gain on hard fonts is paid for on easy ones. The base model's
      capacity is unchanged. Nothing here closes the remaining
      <span class="num">+0.20</span> gap to the 9B on Fascinate Inline.</p>
    </div>
    <div class="card">
      <h4>The 9B is a licensing wall, not a hardware one</h4>
      <p>The 9B trains fine on the same 24 GB card at <span class="num">15.6 GB</span> peak.
      What blocks it is the FLUX Non-Commercial licence &#8212; so no amount of local
      compute changes the outcome.</p>
    </div>
  </div>
</section>

<section>
  <h3>Paths forward</h3>
  <h2>Ranked by what they actually deliver</h2>
  <div class="cols">
    <div class="card">
      <h4>1 &#183; Token-concat retrain, served on fal</h4>
      <p>Real 9B quality, commercially, at roughly <span class="num">$0.04</span> per font with
      no licence negotiation. Blocked today because our conditioning uses a runtime hook a
      managed endpoint cannot run. Costs a retrain at ~2&#215; sequence length.</p>
    </div>
    <div class="card">
      <h4>2 &#183; BFL Platform licence</h4>
      <p>9B quality with the current architecture intact, self-hosted. <code>klein Base 9B</code>
      sits only in the Platform tier &#8212; contact sales, no public pricing.</p>
    </div>
    <div class="card">
      <h4>3 &#183; Combine the two 4B mechanisms</h4>
      <p>Untested and cheap. Their per-font gains do not overlap &#8212; rank 64 helped Bitcount
      Prop, weighting helped Bitcount Grid &#8212; so they may compound.</p>
    </div>
  </div>
</section>

<hr class="rule">
<p class="foot">All figures from <code>eval_runs/*/scores.json</code>, 50-font holdout, 94 cells per font,
each model evaluated on the prompt it was trained with. Significance by paired Wilcoxon on
per-font means, gate p&lt;0.05 &and; r&ge;0.3. char_acc is a DINOv2 template match &#8212; style
fidelity, not letter correctness; identity is the font-invariant classifier.</p>

</div>
"""


def frontier(rows):
    mx = max(r["char_acc"] for r in rows)
    out = ['<section><h3>The frontier</h3>',
           '<h2>Seven variants, one holdout</h2>',
           '<p>Sorted by inference cost. The two 9B rows cannot ship commercially; '
           'every 4B row can.</p>',
           '<div class="legend">'
           '<span><i class="dot nine"></i>9B — non-commercial</span>'
           '<span><i class="dot four"></i>4B — Apache-2.0</span></div>',
           '<div class="scroll"><table><thead><tr>'
           '<th>Variant</th><th>char_acc</th><th></th><th>identity</th><th>DINOv2</th>'
           '<th>R-ACC</th><th>LPIPS</th><th>s/atlas</th></tr></thead><tbody>']
    for r in sorted(rows, key=lambda x: -x["sec"]):
        cls = "nine" if r["nc"] else "four"
        pct = 100 * r["char_acc"] / mx
        hl = ' class="hl"' if r["name"] == "4B weighted" else ""
        out.append(
            f'<tr{hl}><td><div class="name"><i class="dot {cls}"></i>'
            f'<div><div>{r["name"]}</div><div class="sub">{r["note"]}</div></div></div></td>'
            f'<td class="v">{r["char_acc"]:.4f}</td>'
            f'<td style="width:110px"><div class="bar"><i class="{cls}" style="width:{pct:.1f}%"></i></div></td>'
            f'<td class="v">{r["identity"]:.4f}</td><td class="v">{r["dinov2"]:.4f}</td>'
            f'<td class="v">{r["racc"]:.4f}</td><td class="v">{r["lpips"]:.4f}</td>'
            f'<td class="v">{r["sec"]:.1f}</td></tr>')
    out.append('</tbody></table></div>'
               '<p class="foot">LPIPS is lower-better. The 4-step distilled row is 9× faster '
               'than the 4B baseline and 17× faster than the 9B, at 0.946 identity.</p></section>')
    return "\n".join(out)


def redist(rows):
    scale = 0.04  # deltas run to ~+/-0.036
    out = ['<div class="div">']
    for r in rows:
        hw, ew = abs(r["hard"]) / scale * 50, abs(r["easy"]) / scale * 50
        tip = (f'{r["mech"]} {r["metric"]}: harder half {r["hard"]:+.4f}, '
               f'easier half {r["easy"]:+.4f}, rho={r["rho"]}, p={r["p"]}')
        out.append(
            f'<div><strong>{r["mech"]}</strong><br><span class="sub num">{r["metric"]}</span></div>'
            f'<div class="divbar" title="{tip}">'
            f'<span class="neg" style="right:50%;width:{ew:.1f}%"></span>'
            f'<span class="pos" style="left:50%;width:{hw:.1f}%"></span>'
            f'<b style="right:calc(50% + {ew:.1f}% + 8px)">{r["easy"]:+.4f}</b>'
            f'<b style="left:calc(50% + {hw:.1f}% + 8px)">{r["hard"]:+.4f}</b>'
            f'</div>'
            f'<div class="stat">rho {r["rho"]} &nbsp;p {r["p"]}</div>')
    out.append('</div>'
               '<div class="legend" style="margin-top:6px">'
               '<span><i class="dot" style="background:var(--crit)"></i>easier half of the holdout</span>'
               '<span><i class="dot" style="background:var(--nine)"></i>harder half</span></div>')
    return "\n".join(out)


def perfont(rows):
    out = ['<div class="scroll"><table><thead><tr><th>Font</th><th>Type</th>'
           '<th>4B uniform</th><th>4B rank 64</th><th>4B weighted</th><th>9B</th>'
           '<th>gap left</th></tr></thead><tbody>']
    for r in rows:
        best = max(r["u"], r["r"], r["w"])
        cells = []
        for key in ("u", "r", "w"):
            b = ' best' if r[key] == best else ''
            cells.append(f'<td class="v{b}">{r[key]:.3f}</td>')
        # Gap is weighted-vs-9B: the weighted model is what this page evaluates.
        # Measuring best-of-three instead made the control read as a win.
        gap = r["n"] - r["w"]
        beat = gap < 0
        gtxt = (f'<span style="color:var(--good);font-weight:700">−{abs(gap):.3f} ▲</span>'
                if beat else f'{gap:+.3f}')
        hl = ' class="hl"' if beat else ''
        out.append(f'<tr{hl}><td>{r["font"]}</td><td class="sub">{r["kind"]}</td>'
                   + "".join(cells) +
                   f'<td class="v">{r["n"]:.3f}</td><td class="v">{gtxt}</td></tr>')
    out.append('</tbody></table></div>')
    return "\n".join(out)


html = (HTML.replace("__FRONTIER__", frontier(data))
            .replace("__REDIST__", redist(REDIST))
            .replace("__PERFONT__", perfont(PER_FONT))
            .replace("__B64__", b64))
# Escape EVERY non-ASCII char in the final document, generated tables included,
# so the page is byte-identical under any charset the host serves.
html = "".join(c if ord(c) < 128 else f"&#{ord(c)};" for c in html)
out_path = os.path.join(SCRATCH, "model_comparison.html")
open(out_path, "w", encoding="utf-8").write(html)
print(f"wrote {out_path}  {len(html)//1024} KB")
