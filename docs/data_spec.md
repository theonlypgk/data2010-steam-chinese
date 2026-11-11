# Data handling spec: which table serves which question

Everything below is produced by `python run.py tables` (`scripts/02_build_tables.py`,
functions in `src/steamcn/clean.py`). Each table is saved twice in `data/processed/`,
with the prefix `pcd_` (processed):

- `pcd_<table>.csv`: what every later step reads with `pandas.read_csv`;
- `pcd_<table>.xlsx`: the same data, for people to open and check.

All column names are English snake_case.

## At a glance

| Table | One row is | Built from | Serves |
|---|---|---|---|
| `games_clean` | one game in snapshot A | A | EDA, SQ1 |
| `sq1_groups` | one group of similar games | `games_clean` | SQ1 (main result, by genre, by price) |
| `panel_ac` | one game present in both A and C, with no Chinese in C | A + C | SQ2 |
| `sq2_groups` | one SQ2 group of similar games | `panel_ac` | SQ2 (main result, by genre, by price) |
| `funnel` | one filter step | A, C | Data cleaning section of the report |
| `data_dictionary` | one column | | Reference |

SQ3 needs no table from this step. It combines the by-genre results of SQ1 and SQ2.

```
a_trim ──┬─> games_clean ──> sq1_groups          (SQ1)
         │
c_trim ──┴─> panel_ac ─────> sq2_groups          (SQ2)
                                   sq1 by genre + sq2 by genre ──> sq3_summary   (SQ3)
```

## Step 1. Clean each snapshot (same code for A and C)

1. `app_id` to integer; drop rows without one; drop duplicate `app_id`.
2. `positive`, `negative` to integers; `price` to float; `release_date` to a date.
3. Parse `supported_languages`, `full_audio_languages`, `tags`, `genres` into lists.
   Remove junk such as `[b]*[/b]`, HTML tags and line breaks.
4. Add the derived columns:

| Column | Rule |
|---|---|
| `total_reviews` | `positive + negative` |
| `has_zh_simplified`, `has_zh_traditional`, `has_english` | language is in `supported_languages` |
| `n_other_langs` | number of supported languages other than English and the two Chinese variants |
| `n_other_langs_bin` | `0`, `1-4`, `5+` |
| `is_cn_publisher_proxy` | Chinese full audio, or Chinese supported without English |
| `is_early_access` | "Early Access" in `genres` |
| `is_traditional_only` | Traditional Chinese without Simplified |
| `genre_group` | first tag (tags are ordered by votes) found in `config.TAG_TO_GENRE` |
| `price_tier` | `free`, `lt5`, `5to10`, `10to20`, `gt20` |
| `release_year`, `year_band` | year; band `<=2017`, `2018-2019`, `2020-2021`, `2022+` |
| `days_since_release` | snapshot date minus release date |

## Step 2. `games_clean` (EDA and SQ1)

Filters on snapshot A, in this order (each one is logged in `funnel`):

1. drop Chinese-publisher proxy;
2. drop Early Access;
3. keep `total_reviews >= 10`;
4. keep games released at least one year before the snapshot;
5. keep games that have a genre group, a price and a release year;
6. drop Traditional-Chinese-only games.

| Column | Meaning |
|---|---|
| `app_id`, `name` | key and title |
| `release_year`, `price`, `price_tier`, `genre_group` | group variables |
| `n_other_langs`, `n_other_langs_bin` | group variable |
| `has_zh` | **treatment**: 1 = supports Simplified Chinese, 0 = no Chinese at all |
| `positive`, `negative`, `total_reviews`, `log_total_reviews` | **outcome**: reach |
| `group_id` | `genre_group | release_year | price_tier | n_other_langs_bin` |

Used by:
- **EDA**: histogram of `total_reviews` / `log_total_reviews`; share of `has_zh` by
  `release_year`, `price_tier`, `n_other_langs_bin`; boxplot of `log_total_reviews` by `has_zh`.
- **SQ1**: raw gap (all games, by `has_zh`); bootstrap resamples games inside each `group_id`.

## Step 3. `sq1_groups` (SQ1)

Group `games_clean` by `group_id`.

| Column | Meaning |
|---|---|
| `group_id`, `genre_group`, `release_year`, `price_tier`, `n_other_langs_bin` | the group |
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
then keep games with no Chinese at all in C, then keep games that also exist in A.
Join to A on `app_id`.

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
| `group_id_sq2` | `genre_group | year_band | price_tier | n_other_langs_bin | initial_reach_bin` |

Used by:
- **SQ2**: boxplot of `growth` by `arm`; bootstrap inside each `group_id_sq2`;
  robustness check on `added_only_zh == 1` treated games only.
- **T2 feasibility**: count `arm` by `genre_group`.

## Step 5. `sq2_groups` (SQ2)

Group the `treated` and `control` rows of `panel_ac` by `group_id_sq2`.

| Column | Meaning |
|---|---|
| `group_id_sq2` and its five parts | the group |
| `n_treated`, `n_control` | games in each arm |
| `median_growth_treated`, `median_growth_control` | median `growth` in each arm |
| `uplift_pts` | `median_growth_treated - median_growth_control` |
| `eligible` | both arms have at least 10 games |

How SQ2 uses it (keep only `eligible` rows):
- **Main result**: mean of `uplift_pts` weighted by `n_treated`.
- **By genre** (report body) and **by price** (appendix): the same per `genre_group` / `price_tier`.

If too few groups are eligible, coarsen the groups in this order and note it in
`docs/decisions.md`: drop `n_other_langs_bin` from the group, then merge genres into
text-heavy (Visual Novel, RPG, Strategy) and text-light (Action, Puzzle, Casual).

## SQ3 (no new table here)

SQ1 writes `sq1_by_genre.csv` and SQ2 writes `sq2_by_genre.csv` (one row per genre, with
the estimate and its interval). SQ3 reads both and writes `sq3_summary.csv`:

| SQ1 | SQ2 | Advice |
|---|---|---|
| large | large | can translate after launch |
| large | not large | translate at launch |
| not large | any | not a priority |

## Checks to run by hand after `python run.py tables`

1. Open `pcd_funnel.xlsx`: no single filter should remove most games.
2. `pcd_games_clean.xlsx`: pick 20 random rows and compare `has_zh`, `genre_group`,
   `price_tier` with the game's Steam page.
3. `pcd_panel_ac.xlsx`: check 10 `treated` games really have Simplified Chinese today, and
   count `arm` by `genre_group` (need roughly 20+ treated games per genre).
4. `pcd_sq1_groups.xlsx` and `pcd_sq2_groups.xlsx`: count the `eligible` rows.
