# Data handling spec: which table serves which question

Everything below is produced by the notebook `steam_chinese_analysis.ipynb`, Part A. Each table is saved twice in `data/processed/`,
with the prefix `pcd_` (processed):

- `data/processed/csv/pcd_<table>.csv`: what every later step reads with `pandas.read_csv`;
- `data/processed/xlsx/pcd_<table>.xlsx`: the same data, for people to open and check.

All column names are English snake_case.

## At a glance

| Table | One row is | Built from | Serves |
|---|---|---|---|
| `games_clean` | one game in snapshot A | A | EDA, SQ1 |
| `sq1_groups` | one group of similar games | `games_clean` | SQ1 (main result, by genre, by price) |
| `panel_ac` | one game present in both A and C, with no Chinese in C | A + C | SQ2 |
| `sq2_groups` | one SQ2 group of similar games | `panel_ac` | SQ2 (main result, by genre, by price) |
| `cn_excluded` | one Chinese game removed | A | Manual check of the Chinese-game rules |
| `funnel` | one filter step | A, C | Data cleaning section of the report |
| `data_dictionary` | one column | | Reference |

SQ3 needs no table from this step. It combines the by-genre results of SQ1 and SQ2.

```
raw A ───┬─> games_clean ──> sq1_groups          (SQ1)
         │
raw C ───┴─> panel_ac ─────> sq2_groups          (SQ2)
                                   sq1 by genre + sq2 by genre ──> sq3_summary   (SQ3)
```

## Step 1. Clean each snapshot (same code for A and C; notebook A1-A2)

1. `app_id` to integer; drop rows without one; drop duplicate `app_id`.
2. `positive`, `negative` to integers; `release_date` to a date. `price` becomes the
   **list price**: snapshot A was taken during a sale, so `price = price_at_snapshot /
   (1 - discount_pct / 100)` (snapshot C has no discount column, its price is used as is).
3. Parse `supported_languages`, `full_audio_languages`, `tags`, `genres` into lists.
   Remove junk such as `[b]*[/b]`, HTML tags and line breaks.
4. Add the derived columns:

| Column | Rule |
|---|---|
| `total_reviews` | `positive + negative` |
| `has_zh_simplified`, `has_zh_traditional`, `has_english` | language is in `supported_languages` |
| `n_other_langs` | number of supported languages other than English and the two Chinese variants |
| `n_other_langs_bin` | `0`, `1-4`, `5+` |
| `is_cn_game` | Chinese game, by any of 4 rules: (1) Chinese without English, in text or voice-over; or every developer is Chinese: (2) name in Chinese characters, (3) name contains a mainland Chinese city, (4) known Chinese company. `cn_rules` says which matched |
| `is_early_access` | "Early Access" in `genres` |
| `is_traditional_only` | Traditional Chinese without Simplified |
| `genre_group` | first tag (tags are ordered by votes) found in `config.TAG_TO_GENRE` |
| `price_tier` | `free`, `lt5`, `5to10`, `10to20`, `gt20` |
| `release_year`, `year_band` | year; band `<=2017`, `2018-2019`, `2020-2021`, `2022+` |
| `days_since_release` | snapshot date minus release date |

## Step 2. `games_clean` (EDA and SQ1)

Filters on snapshot A, in this order (each one is logged in `funnel`):

1. drop Chinese games (any of the 4 rules);
2. drop Early Access;
3. keep `total_reviews >= 10`;
4. keep games released at least one year before the snapshot;
5. keep games that have a genre group, a price and a release year;
6. drop Traditional-Chinese-only games.

| Column | Meaning |
|---|---|
| `app_id`, `name` | key and title |
| `release_year`, `year_band`, `price` (list price), `discount_pct`, `price_tier`, `genre_group` | group variables |
| `n_other_langs`, `n_other_langs_bin` | group variable |
| `has_zh` | **treatment**: 1 = supports Simplified Chinese, 0 = no Chinese at all |
| `positive`, `negative`, `total_reviews`, `log_total_reviews` | **outcome**: reach |
| `group_id` | `genre_group | year_band | price_tier | n_other_langs_bin` (year bands, not single years: single years left 53% of games in groups with < 10 games on one side) |

Used by:
- **EDA**: histogram of `total_reviews` / `log_total_reviews`; share of `has_zh` by
  `release_year`, `price_tier`, `n_other_langs_bin`; boxplot of `log_total_reviews` by `has_zh`.
- **SQ1**: raw gap (all games, by `has_zh`); bootstrap resamples games inside each `group_id`.

## Step 3. `sq1_groups` (SQ1)

Group `games_clean` by `group_id`.

| Column | Meaning |
|---|---|
| `group_id`, `genre_group`, `year_band`, `price_tier`, `n_other_langs_bin` | the group |
| `n_zh`, `n_no_zh` | games on each side |
| `median_reviews_zh`, `median_reviews_no_zh` | median `total_reviews` on each side |
| `pct_diff` | `median_reviews_zh / median_reviews_no_zh - 1` |
| `extra_reviews` | `(median_reviews_zh - median_reviews_no_zh) * n_zh` |
| `eligible` | both sides have at least 10 games |

How SQ1 uses it (keep only `eligible` rows):
- **Main result**: mean of `pct_diff` weighted by `n_zh + n_no_zh`; sum of `extra_reviews`.
- **By genre** (report body): the same two numbers per `genre_group`.
- **By price** (appendix): the same per `price_tier`.

## Step 4. `panel_ac` (SQ2)

Start from snapshot C. Filters, in order: the first five filters of Step 2 applied to C,
then keep games with no Chinese at all in C, then keep games that also exist in A, then
drop games with 0 reviews in A (delisted, or reviews missing in the data). Join to A on `app_id`.

| Column | Meaning |
|---|---|
| `app_id`, `name` | key and title |
| `genre_group`, `release_year`, `year_band`, `price_c`, `price_tier`, `n_other_langs_bin` | group variables, **all from C** (the starting point) |
| `reviews_c`, `reviews_a` | `total_reviews` in January 2024 and in snapshot A |
| `growth` | **outcome**: `(reviews_a - reviews_c) / reviews_c` |
| `initial_reach_bin` | `small`, `medium`, `large`: terciles of `reviews_c` |
| `added_zh` | 1 = has Simplified Chinese in A |
| `added_only_zh` | 1 = Simplified Chinese is the only language added |
| `added_other_major_lang` | 1 = added at least one major language |
| `n_langs_added` | number of languages in A that were not in C |
| `arm` | **treatment**: `treated` (`added_zh = 1`), `control` (no Chinese and no major language added), `excluded` (the rest) |
| `group_id_sq2` | `genre_group | initial_reach_bin` (see Step 5) |

Used by:
- **SQ2**: boxplot of `growth` by `arm`; bootstrap inside each `group_id_sq2`;
  robustness check on `added_only_zh == 1` treated games only.
- **T2 feasibility**: count `arm` by `genre_group`.

## Step 5. `sq2_groups` (SQ2)

Group the `treated` and `control` rows of `panel_ac` by `group_id_sq2` = genre × initial reach
(18 groups). Only about 500 games added Chinese between C and A, so the five-way group of the
framework (genre × year × price × other languages × reach) left 7 eligible groups; genre ×
reach keeps 14 eligible groups, about 95% of treated games and all 6 genres. Year, price and
other languages stay in `panel_ac` and can be used as checks.

| Column | Meaning |
|---|---|
| `group_id_sq2`, `genre_group`, `initial_reach_bin` | the group |
| `n_treated`, `n_control` | games in each arm |
| `median_growth_treated`, `median_growth_control` | median `growth` in each arm |
| `uplift_pts` | `median_growth_treated - median_growth_control` |
| `eligible` | both arms have at least 10 games |

How SQ2 uses it (keep only `eligible` rows):
- **Main result**: mean of `uplift_pts` weighted by `n_treated`.
- **By genre** (report body): the same per `genre_group`.
- **By price** (appendix): from `panel_ac`, compare median `growth` of treated vs control per `price_tier`.

Limitation to state in the report: SQ2 holds genre and starting reach fixed, but not
release year, price or number of other languages.

## SQ3 (no new table here)

SQ1 writes `sq1_by_genre.csv` and SQ2 writes `sq2_by_genre.csv` (one row per genre, with
the estimate and its interval). SQ3 reads both and writes `sq3_summary.csv`:

| SQ1 | SQ2 | Advice |
|---|---|---|
| large | large | can translate after launch |
| large | not large | translate at launch |
| not large | any | not a priority |

## Checks to run by hand after running the notebook

1. Open `xlsx/pcd_funnel.xlsx`: no single filter should remove most games.
2. `xlsx/pcd_games_clean.xlsx`: pick 20 random rows and compare `has_zh`, `genre_group`,
   `price_tier` with the game's Steam page.
3. `xlsx/pcd_panel_ac.xlsx`: check 10 `treated` games really have Simplified Chinese today, and
   count `arm` by `genre_group` (need roughly 20+ treated games per genre).
4. `xlsx/pcd_sq1_groups.xlsx` and `xlsx/pcd_sq2_groups.xlsx`: count the `eligible` rows.
5. `xlsx/pcd_cn_excluded.xlsx`: scan the biggest games and the `cn_rules` column; a Western
   game in the list means a rule is too broad (add an exception in the Settings cell).
