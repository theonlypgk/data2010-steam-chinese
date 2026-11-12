# Data handling: from the two input files to the two tables

Everything below is done by the notebook `steam_chinese_analysis.ipynb`, Part A.

```
input                       cleaning (Part A)                         output
games_a.csv (2026-06-20) ─┬─> clean -> select rows ──────────────────> pcd_sq1_games  (EDA, SQ1)
games_c.csv (2024-01-11) ─┴─> clean -> select rows -> join with A ───> pcd_sq2_games  (SQ2)
```

Each output table is saved whole, twice: `data/processed/csv/pcd_<table>.csv` (read it in
code with `pd.read_csv`) and `data/processed/xlsx/pcd_<table>.xlsx` (open it to look at it).
All column names are English snake_case. SQ3 needs no table of its own: it combines the
results of SQ1 and SQ2.

## 1. Cleaning (same for both input files)

1. Read 13 of the 40 columns and give them English names. The header of snapshot A merges
   two names (`DiscountDLC count`); it is split back first.
2. `app_id` to integer; drop rows without one and repeated ids.
3. `price` becomes the **list price**: snapshot A was taken during a sale, so
   `price = sale price / (1 - discount_pct / 100)`. Snapshot C prices are used as listed.
4. Parse languages, voice-over languages, tags and genres into lists; remove junk such as
   `[b]*[/b]` and HTML. Unreadable release dates become missing.
5. Add the columns used below (outcome, treatment, groups) and the filter flags.

## 2. Selecting rows

Applied in this order; the notebook (section A6) shows how many games each step removes.

| Step | Why |
|---|---|
| Drop Chinese games: Chinese without English (text or voice-over), or every developer is Chinese (name in Chinese characters, mainland-city name, or known Chinese company) | A game made in China is not a "translated into Chinese" case |
| Drop Early Access | Unfinished games; reviews behave differently |
| Keep >= 10 reviews | Below that, reach is noise |
| Keep games released >= 1 year before the snapshot | Every game had time to collect reviews |
| Keep games with a genre group, price and release year | Needed to compare similar games |
| `pcd_sq1_games` only: drop Traditional-Chinese-only games | Neither "with Simplified Chinese" nor "without Chinese" |
| `pcd_sq2_games` only: keep games with no Chinese in C, present in A, with reviews in A | Only they can "add" Chinese; 0 reviews in A means delisted |

## 3. `pcd_sq1_games`: one game in snapshot A (EDA, SQ1)

44,765 games, 14,078 with Simplified Chinese.

| Column | Meaning |
|---|---|
| `app_id`, `name` | Steam id and title |
| `release_year`, `year_band` | release year; band `<=2017`, `2018-2019`, `2020-2021`, `2022+` |
| `price`, `discount_pct`, `price_tier` | list price in USD; sale discount on the snapshot day; `free`, `lt5`, `5to10`, `10to20`, `gt20` |
| `genre_group` | Visual Novel, RPG, Strategy, Action, Puzzle or Casual (first matching user tag) |
| `n_other_langs`, `n_other_langs_bin` | languages other than English and Chinese; `0`, `1-4`, `5+` |
| `has_zh` | **treatment**: 1 = supports Simplified Chinese, 0 = no Chinese at all |
| `positive`, `negative`, `total_reviews`, `log_total_reviews` | **outcome**: reach = all reviews |
| `group_id` | group of similar games: `genre_group | year_band | price_tier | n_other_langs_bin` |

How SQ1 uses it (notebook B2): compare `total_reviews` of `has_zh = 1` and `has_zh = 0`
games inside each `group_id` (medians; groups with >= 10 games on each side), then average
over groups, overall and per `genre_group`.

## 4. `pcd_sq2_games`: one game in both snapshots, no Chinese in January 2024 (SQ2)

21,555 games: 509 added Chinese (`treated`), 20,805 did not (`control`), 241 `excluded`.

| Column | Meaning |
|---|---|
| `app_id`, `name` | Steam id and title |
| `genre_group`, `release_year`, `year_band`, `price_c`, `price_tier`, `n_other_langs_bin` | game characteristics in January 2024 (snapshot C) |
| `reviews_c`, `reviews_a` | reviews in January 2024 and in June 2026 |
| `growth` | **outcome**: `(reviews_a - reviews_c) / reviews_c` |
| `initial_reach_bin` | starting reach: `small`, `medium`, `large` (thirds of `reviews_c`) |
| `added_zh`, `added_only_zh` | added Simplified Chinese; Chinese was the only language added |
| `added_other_major_lang`, `n_langs_added` | added a major language (German, French, ...); number of languages added |
| `arm` | **treatment**: `treated` (added Chinese), `control` (added neither Chinese nor a major language), `excluded` (added another major language only) |
| `group_id_sq2` | group of similar games: `genre_group | initial_reach_bin` |

How SQ2 uses it (notebook B3): compare median `growth` of `treated` and `control` games
inside each `group_id_sq2` (groups with >= 10 games on each side), then average, overall
and per genre. The group is only genre x starting reach: about 500 games added Chinese,
too few to also split by year, price and other languages (a limitation, see README).

## Checks to run by hand after running the notebook

1. The funnel (section A6): no single step should remove most games.
2. `xlsx/pcd_sq1_games.xlsx`: pick 20 random rows and compare `has_zh`, `genre_group`,
   `price_tier` with the game's Steam page.
3. `xlsx/pcd_sq2_games.xlsx`: check 10 `treated` games really have Simplified Chinese today.
4. The removed Chinese games (section A6, biggest first): a Western game in the list means
   a rule is too broad (add an exception in the Settings cell).
