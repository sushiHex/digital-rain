# Identifying the undocumented 13% of the training corpus

2026-08-08. Follow-up to
`research/2026-08-08-the-corpus-is-not-97-percent-ofl.md`, which established
that 121 of the 925 training fonts were absent from the fetch manifest.
All 121 are now identified.

## Sourcing documentation does exist — it just stops short

| artifact | covers |
|---|---|
| `pipeline/fetch_fonts.py` | five adapters (directory, google-fonts, github, velvetyne, fontlibrary), records provenance per file |
| `font_pool/source_manifest.json` | 6,141 entries: filename, source, licence, `origin_path`, `fetched_at`. **Gitignored** |
| `research/2026-04-09-legal-font-sources.md` | where OFL fonts can be found — *intent*, not provenance |

The manifest's only sources are `google-fonts` (3,853) and `github` (2,288). It
covers **804 of the 925**.

**The tooling was never the problem.** `fetch_fonts.py` has a `directory`
adapter that would have recorded exactly these files — and the manifest contains
**zero** `directory` entries. The remaining 121 were copied straight into the
scanned folder, bypassing the only thing that writes provenance. Everything that
went through the tool has a licence recorded; only what bypassed it does not.
The undocumented 13% is undocumented *because* it skipped the tool.

## What the 121 are

| origin | n | outcome |
|---|---|---|
| `C:\Windows\Fonts` | 51 | 49 restricted vendor terms, 2 OFL (Inter, Lato) |
| `extra-fonts/fontshare` | 63 | 25 declare OFL in-file; **36 presumed ITF-FFL** |
| `extra-fonts/league` | 5 | 3 OFL upstream, 2 need confirmation |
| `extra-fonts/fontsquirrel` | 1 | needs review |
| not on disk | 1 | `unispace_bd`, unrecoverable |

Of the 45 that carry **no licence field at all**
(`analysis/identify_unlicensed_corpus_fonts.py` →
`research/unlicensed_corpus_fonts.json`):

| verdict | n | meaning |
|---|---|---|
| `ITF_FFL_PRESUMED` | **36** | Indian Type Foundry, no licence field |
| `OFL_UPSTREAM` | 4 | same family ships OFL in `google-fonts/ofl` — re-source and it closes |
| `VENDOR_REVIEW` | 4 | identifiable foundry, needs a human decision |
| `UNKNOWN` | 1 | file absent from disk |

## The fontshare 36 are the serious finding

**Fontshare publishes under two different licences**, and this is the fact the
corpus assembly missed. Its open-source faces are SIL OFL; its closed-source
ones are the proprietary **ITF Free Font License**. Our fontshare files split
exactly along that line — 25 carry OFL text in name ID 13, and 36 carry no
licence field at all.

Per [Fontshare's own licence page](https://www.fontshare.com/licenses/itf-ffl),
closed-source fonts are *"proprietary freeware designed, produced, and owned by
the Indian Type Foundry (ITF) ... they cannot be modified or redistributed"*,
and on derivative works: *"Any derivative works are the exclusive property of
the Licensor ... Derivative works may not be sub-licensed, sold, leased,
rented, loaned, or given away without the express written permission of the
Licensor."*

That is **squarely incompatible** with this project: a generative model trained
on them, distributing output fonts, is producing exactly the derivative works
ITF reserves. It is a stronger claim than the Windows fonts' terms — those
merely fail to grant conversion rights; ITF affirmatively claims ownership of
whatever comes out.

### Where this came from

The historical justification is a **single row in a market-share table**:
`research/2026-03-26-oracle-round3-report.md:4004` —
*"| **Fontshare** | Free tier | Professional-grade, free personal & commercial use |"*,
sourced to one research scout in a survey of the font market.

That row is not wrong about Fontshare's marketing. It is simply not a licence
review, and it does not distinguish the two licences Fontshare uses. A one-line
market-survey entry became the basis for putting 63 fonts into a training corpus.
**"Free for personal and commercial use" is a statement about using a font to
set type. It says nothing about training on it or redistributing derivatives.**

## Corpus status

| | n | share |
|---|---|---|
| OFL-1.1 | 805 | 87.03% |
| **ITF-FFL presumed (fontshare closed-source)** | **36** | 3.89% |
| **vendor-supplied, non-redistributable (Windows)** | **49** | 5.30% |
| Apache-2.0 | 23 | 2.49% |
| UFL | 3 | 0.32% |
| unresolved after all evidence | 9 | 0.97% |

**Clean: 89.8%. Known-problematic: 85 fonts (9.2%).** Nine remain genuinely
unknown, down from 121 undocumented.

## What to do

1. **Re-source the free wins first** — 4 `OFL_UPSTREAM` fonts (Fira Sans,
   Knewave, Prociono, Sniglet) plus Cascadia Code from the Windows set. Five
   faces move to clean with a file swap and no corpus loss.
2. **Drop the 36 ITF-FFL and 48 remaining Windows fonts and retrain.** That is
   84 fonts, ~9.1% of the corpus. The corpus-expansion work already showed
   composition changes of this size are survivable, and this is a removal from a
   corpus that is 87% one licence — far less disruptive than the 925→1,113
   expansion that regressed.
3. **Confirm the 4 `VENDOR_REVIEW`.** Two are League of Movable Type (`chunk`,
   `junction`) whose foundry policy is OFL but whose files do not say so; one is
   Fontstore Pte Ltd; one is Jovanny Lemonad. Cheap to resolve, and may recover
   all four.
4. **Backfill `extra-fonts/` through `fetch_fonts.py --adapter directory`** so
   the pool gets manifest entries, and make the corpus build refuse any font
   without a manifest entry. The defect was never the licences — it was that a
   path existed to add fonts without recording where they came from.

## Caveat

Verdicts here are research aids, not legal conclusions. The ITF classification
is **presumed** from the absence of a licence field plus Fontshare's published
two-licence structure; the per-font open/closed split lives on their website,
not in the file. Confirm each of the 36 against Fontshare before acting, and get
counsel before publishing anything trained on them.
