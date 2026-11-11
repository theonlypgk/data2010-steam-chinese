# Decisions (frozen before results are seen)

Only the team leader edits this file. Every change gets a date and a reason at the bottom.
`src/steamcn/config.py` mirrors these values.

## Scope (12 Nov 2026)

- Three questions: SQ1, SQ2, SQ3 (see README).
- SQ1 and SQ2: main result + breakdown by genre in the report body; breakdown by price
  tier as one appendix figure each. No separate analysis by number of other languages or
  by initial reach; both are still used to form comparison groups.
- SQ3: advice per genre only.

## Definitions

| Item | Value |
|---|---|
| Reach | `total_reviews = positive + negative` |
| Treatment (SQ1) | `has_zh = 1` if Simplified Chinese is supported; `0` if no Chinese at all. Traditional-only games are dropped. |
| Chinese-publisher proxy | Chinese (text) without English text, or Chinese voice-over without English voice-over. Dropped. **Changed 2026-11-12, see log.** |
| Minimum reviews | 10 |
| Minimum age | released at least 365 days before the snapshot |
| Genre group | first tag found in `TAG_TO_GENRE` (6 groups: Visual Novel, RPG, Strategy, Action, Puzzle, Casual). **Draft list, to be confirmed.** |
| Price | list price: snapshot price / (1 - discount). Snapshot A was taken during a sale. |
| Price tiers | free, lt5, 5to10, 10to20, gt20 (USD, list price) |
| Other languages | count excluding English and Chinese; bins 0, 1-4, 5+ |
| Year bands (SQ2) | <=2017, 2018-2019, 2020-2021, 2022+ |
| Initial reach (SQ2) | terciles of `reviews_c`: small, medium, large |
| Major languages (SQ2 control) | German, French, Spanish - Spain, Japanese, Russian, Korean, Portuguese - Brazil |
| Eligible group | at least 10 games on each side |
| "Large enough" | SQ1: +20% or more; SQ2: +10 points or more; interval must not include 0 |
| Bootstrap | 2000 resamples, seed 2010 |

## Report page budget (10 pages)

Introduction 1.5 · SQ1 2.5 · SQ2 2.5 · SQ3 1.5 · Conclusion 1 · Lifecycle reflection 1.
Two figures per question in the body.

## Change log

- 2026-11-12: file created.
- 2026-11-12 (Claude, overnight run, **to be confirmed by kp**): Chinese-publisher proxy
  narrowed. The original rule ("Chinese voice-over, or Chinese without English") removed
  4,233 Western games with >= 10 reviews that simply ship Chinese voice-over (Cyberpunk 2077,
  The Witcher 3, Hollow Knight, Dota 2, HELLDIVERS 2 ...). Those are the best-localised games,
  so dropping them biases SQ1 downwards. New rule: Chinese without English, in the text or in
  the voice-over.
- 2026-11-12 (Claude, overnight run): price tiers use the list price. Snapshot A (2026-06-20)
  was taken during a sale (e.g. Hades listed at 7.49 = 24.99 at -70%), so the raw price put
  many games in the wrong tier.
