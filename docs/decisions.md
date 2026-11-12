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
| Chinese games | ALL dropped, large or small, if any rule matches: (1) Chinese without English, in text or voice-over; or EVERY developer of the game is Chinese: (2) name in Chinese characters, (3) name contains a mainland Chinese city, (4) known Chinese company (`config.CN_COMPANIES`). Publishers are not used. |
| Minimum reviews | 10 |
| Minimum age | released at least 365 days before the snapshot |
| Genre group | first tag found in `TAG_TO_GENRE` (6 groups: Visual Novel, RPG, Strategy, Action, Puzzle, Casual). **Draft list, to be confirmed.** |
| Price | list price: snapshot price / (1 - discount). Snapshot A was taken during a sale. |
| Price tiers | free, lt5, 5to10, 10to20, gt20 (USD, list price) |
| Other languages | count excluding English and Chinese; bins 0, 1-4, 5+ |
| Year bands | <=2017, 2018-2019, 2020-2021, 2022+ (used in the SQ1 group) |
| SQ1 group | genre × year band × price tier × other languages |
| SQ2 group | genre × initial reach |
| SQ2 sample | also drops games with 0 reviews in A (delisted) |
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
- 2026-11-12 (Claude, overnight run, **to be confirmed by kp**): SQ1 groups use year bands
  instead of single years (the framework allows this): eligible groups now cover 81% of
  games instead of 47%.
- 2026-11-12 (Claude, overnight run, **to be confirmed by kp**): SQ2 groups are genre ×
  initial reach. The framework's five-way group gave 7 eligible groups (16% of treated
  games, 2 genres); genre × reach gives 14 eligible groups (about 95% of treated games,
  6 genres). Year, price and other languages are not held fixed in SQ2: state it as a limitation.
- 2026-11-12 (Claude, overnight run): SQ2 drops 40 games with 0 reviews in A (delisted or
  missing data); their growth of -100% is not real.
- 2026-11-12 (kp): ALL Chinese games are removed, large or small. Implemented with four
  rules (language pattern + developer/publisher names); removed games are listed in
  `pcd_cn_excluded` with the rule that matched.
- 2026-11-12 (kp): snapshot A stays at 2026-06-20 (last CSV version).
- 2026-11-12: processed tables split into `data/processed/csv/` (code) and `xlsx/` (viewing).
- 2026-11-12: Chinese-game rules 2-4 look at developers only, and all developers must be
  Chinese. With publishers and "any developer", Western games were removed because of a
  regional publisher (bilibili for Core Keeper) or a Chinese support studio (Ubisoft
  Shanghai for Far Cry, Activision Shanghai for Call of Duty).
