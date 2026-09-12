# "The training corpus is 97.5% OFL" is wrong, and 51 Microsoft fonts are in it

2026-08-08. Publication-readiness audit (codex, max effort), verified locally
against the tracked artifacts. **This is a blocker for any public push**, and it
is worse for a commercial product than the OFL-derivative problem it was
supposed to characterise.

## The number counted the wrong population

`research/2026-07-27-ofl-derivative-work-constraint.md:26` derives 97.5% as
`3760 / 3858` — files in `google-fonts/ofl/` over a raw recursive scan of the
**Google Fonts checkout**. But `build_dataset.py` then filters that checkout for
charset support and removes near-duplicates, and the manifest recording what
actually survived is written *inside a gitignored directory*. A pre-filter
checkout ratio cannot establish the post-filter training ratio, and a clean
clone contains no source-to-training-item mapping at all.

## Recounted against the actual 925 fonts

Matching the real corpus (`research/font_distinctiveness.json`, 925 entries)
against `font_pool/source_manifest.json`, and — where that manifest is silent —
reading the licence out of **the font's own name ID 13**:

| licence | count | share |
|---|---|---|
| OFL-1.1 | 805 | **87.03%** |
| **vendor-supplied, non-redistributable** | **49** | **5.30%** |
| still unknown | 45 | 4.86% |
| Apache-2.0 | 23 | 2.49% |
| UFL | 3 | 0.32% |

**OFL is 87.0%, not 97.5%.** Granting every still-unknown file OFL status — the
most generous reading available — the ceiling is 91.9%, well below the
published figure.

### A first pass at this got it wrong, in the direction of alarm

The initial recount reported "84.1% OFL, 51 proprietary Microsoft fonts,"
classifying by **presence in `C:\Windows\Fonts`**. That is not evidence of
anything. Plenty of libre fonts are installed there: **Inter** and **Lato** are
both OFL and both on the list. A follow-up attempt with loose substring markers
was worse, scoring **Arial** as open because the phrase *"...as permitted by
the license terms..."* contains the substring `mit licen`.

The authoritative source is the font's own licence field. On that basis:

- **49** of the 925 carry *"Microsoft supplied font. You may use this font to
  create, display, and print content as permitted by the license terms ... of
  the Microsoft product..."* — a licence to **render content**, not to
  redistribute, convert, or train on. A 95-glyph full-coverage atlas is exactly
  the conversion those terms do not grant.
- **2** of the flagged 51 (Inter, Lato) were false positives and are cleanly OFL.
- **1** more, **Cascadia Code**, is **OFL upstream** — Microsoft released it
  under SIL OFL 1.1 — and carries restricted terms only in its Windows-bundled
  copy. Re-sourcing that file resolves it without dropping the face.

Also worth correcting: **"Microsoft fonts" was wrong as a label.** The 49 are
held by Monotype (Arial, Times, Courier, Impact, Franklin Gothic), ITC,
Bigelow & Holmes (Lucida), and Linotype/Heidelberger (Palatino) as well as
Microsoft. The obligation is the same; the attribution was sloppy.

Independently corroborated by a tracked artifact that was already in the repo:
`dataset_Kg/quarantine/report.json` records `total: 925, fonts_not_found: 117` —
the corpus has had unresolvable provenance recorded in-repo the whole time.

**Reading the embedded licences also resolved 27 fonts the fetch manifest had
lost**, which is why OFL rose from 84.1% to 87.0%. The correction cut both ways.

## Why this is worse than the problem it replaces

The OFL-derivative constraint (SIL FAQ 1.25) says generated fonts must be OFL.
That is a *distribution* constraint on outputs, and it is survivable — it pushes
toward a service-shaped product.

Proprietary fonts in the training corpus is a **right-to-train** question about
inputs. It does not go away by licensing the outputs differently, it is not
cured by the model being a derivative work, and it attaches to every checkpoint
already trained. The two are not the same kind of risk and the second was
invisible because the first had a confident number attached to it.

## Corrected everywhere the claim appeared

`README.md:241`, `CLAUDE.md:355`, `LICENSE:37`, `docs/PUSH-PREP.md:120`,
`analysis/score_pool_distinctiveness.py:21`, `analysis/select_expansion_set.py:16`,
and the source memo `research/2026-07-27-ofl-derivative-work-constraint.md`
(superseding section, not a rewrite — it is a dated record).

## What has to happen before a public push

1. **Do not publish weights or a hosted demo** until the corpus provenance is
   resolved. This is now two independent blockers, not one.
2. **Build a tracked, auditable manifest** mapping each training item to a
   source and licence, committed rather than written into a gitignored tree.
   Until that exists no licence claim about the corpus is checkable from a
   clean clone.
3. **Decide about the 49 restricted fonts.** Re-source Cascadia Code from its
   OFL upstream (free). For the other 48 the clean option is to drop them and
   retrain: losing ~5.2% of a 925-font corpus is a smaller cost than the
   exposure, and the ink-floor work already showed corpus composition changes
   are survivable. This cannot be fixed by re-labelling — the existing
   checkpoints were trained on them.
4. **Resolve the remaining 45 unknowns**, which are unknown rather than known-bad.
4. The other two audit blockers were verified and **fixed** (`b9cb9a5`):

   - **Vendored Nunchaku source with no licence.** `route_b/transformer_flux2.patched.py`
     is tracked and is a modified copy of nunchaku 1.2.1 + upstream PR #926.
     Nunchaku is Apache-2.0 (confirmed from the installed distribution's own
     `LICENCE.txt`), whose section 4 requires a copy of the licence, a
     statement that files were changed, and retained attribution. The repo had
     none of the three — `route_b/README.md` described provenance in prose,
     which documents the code but does not satisfy the licence. Added
     `route_b/LICENSE.nunchaku`, `route_b/NOTICE`, and a header on the file.
   - **The demo handed out bare font files.** `build_font` called
     `setupNameTable` with only family and style, so every generated `.otf`
     and `.woff2` shipped with name IDs 0/13/14 empty. A downloaded font does
     not travel with the README, so a licence stated only there reaches nobody.
     `build_font` now embeds OFL-1.1 terms by default, overridable.

   **Note the asymmetry.** Those two were fixable in an afternoon because they
   are about what accompanies the artifacts. The corpus-provenance blocker is
   not: it is baked into every trained checkpoint and cannot be fixed by
   attaching a file.

## Method note

The audit that surfaced this is the same one that, in an earlier round,
fabricated a research citation. Every number above was re-derived locally from
tracked artifacts before being written down; the two facts that carry the
conclusion — the 30+ system-font names in the corpus list and
`fonts_not_found: 117` — are checkable in one command each.
