# Simplified Chinese support and reach on Steam

DATA2010 Data Science Programming, final project.

**Main question.** Should a Steam game support Simplified Chinese, for which genres, and when?

| | Question | Data |
|---|---|---|
| SQ1 | How much larger is the reach of games that support Simplified Chinese, and in which genres? | snapshot A |
| SQ2 | Does adding Simplified Chinese after launch still increase reach, and in which genres? | snapshots A + C |
| SQ3 | For each genre: translate at launch, translate later, or not a priority? | results of SQ1 + SQ2 |

Reach = number of reviews (`positive + negative`). Every comparison is made inside a group
of similar games (Step 5), so that a gap is not simply "bigger games get translated more".

This README follows the work in order, from the two input files to the answers; each step
names the notebook section that does it and explains why each choice was made.

```
steam_chinese_analysis.ipynb   ALL the code, from the two input files to the analysis
requirements.txt               exact package versions (Python 3.12)
data/raw/                      the two input files (downloaded by the notebook, not committed)
data/processed/csv/            the six output tables (Steps 4 and 6), for code (pandas.read_csv)
data/processed/xlsx/           the same six tables, to open and look at
report/                        report, figures, reflections, slides
.github/, .devcontainer/       automatic re-runs on GitHub; Codespaces environment
```

---

## Step 0. Reproducing the results

```bash
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute steam_chinese_analysis.ipynb --output executed.ipynb
```

or open the notebook and choose *Run All*. It needs nothing but internet access: it downloads
the two input files itself. Two runs give byte-identical CSV files (exact package versions,
rounded floats, fixed xlsx dates). On GitHub, the `pipeline` workflow (Actions tab) runs the
notebook on a clean machine after every change and commits the tables if they changed.

In the notebook, the first line of every code cell says what kind of step it is (LOAD DATA,
DATA CLEANING, SELECT ROWS, AGGREGATE, SAVE OUTPUTS, CHECKS), and problems found in the real
data are marked `DATA ISSUE`. Every fixed choice is in the **Settings and decisions** cell
with its reason; all of them were set before any result was looked at.

## Step 1. The two input files (notebook: Settings, A1)

Steam Games Dataset by FronkonGames, Hugging Face repository `FronkonGames/steam-games-dataset`.
One row is one game on Steam. Both versions are pinned to a commit so the data never changes.

| | Snapshot A ("now") | Snapshot C (January 2024) |
|---|---|---|
| Commit | `52ba62abfa707a2fa31f4d147c2777a9d9fbd2da` | `aefdeb1ff1a739b92ac5338682cc2610a0328505` |
| Date | 2026-06-20, the last version of `games.csv` (later commits update only `games.json`) | 2024-01-11 |
| Raw rows | 125,855 | 85,103 |
| Used for | SQ1, SQ2 | SQ2 |

Backup: the release [raw-snapshots-v1](../../releases/tag/raw-snapshots-v1) of this repo holds
both files (gzip) with SHA-256 checksums, in case Hugging Face history becomes unavailable.

The notebook reads 13 of the 40 columns and gives them English names: `app_id`, `name`,
`release_date`, `price`, `discount_pct`, `supported_languages`, `full_audio_languages`,
`positive`, `negative`, `developers`, `publishers`, `genres`, `tags`.

**Data issue.** The header of snapshot A merges two names (`DiscountDLC count`) while the rows
hold two values, which would shift every later column. `read_header()` splits it.

## Step 2. Cleaning (notebook: A2)

Same for both files:

1. `app_id` to integer; drop rows without one and repeated ids.
2. **Data issue: sale prices.** Snapshot A was taken during a sale (Hades listed at 7.49 =
   24.99 at -70%). `price` becomes the list price: `sale price / (1 - discount_pct / 100)`.
   Snapshot C has no discount column; its prices are used as listed.
3. **Data issue: junk in list cells** (`[b]*[/b]`, HTML). Languages, voice-over languages,
   tags and genres are parsed into clean lists. Unreadable release dates become missing.
4. Derived columns:
   - `has_zh`: supports Simplified Chinese (Traditional-only games are marked separately).
   - `genre_group`: the first of the game's user tags (ordered by votes) found in
     `TAG_TO_GENRE`: Visual Novel, RPG, Strategy, Action, Puzzle or Casual.
   - `price_tier`: free, lt5, 5to10, 10to20, gt20 (USD, list price).
   - `n_other_langs`: languages other than English and Chinese; bins 0, 1-4, 5+.
   - `year_band`: <=2017, 2018-2019, 2020-2021, 2022+.
   - `is_chinese_game`: see Step 3.

## Step 3. Selecting rows (notebook: A3-A5, removed rows shown in A6)

Applied in this order:

| Step | Why |
|---|---|
| Drop Chinese games, large or small (rules below) | A game made in China is not a case of "translating into Chinese" |
| Drop Early Access | Unfinished games; reviews behave differently |
| Keep >= 10 reviews | Below that, reach is noise |
| Keep games released >= 365 days before the snapshot | Every game had time to collect reviews |
| Keep games with a genre group, price and release year | Needed to compare similar games |
| SQ1 table only: drop Traditional-Chinese-only games | Neither "with Simplified Chinese" nor "without Chinese" |
| SQ2 table only: keep games with no Chinese in C, present in A, with > 0 reviews in A | Only they can "add" Chinese; 0 reviews in A means delisted (growth -100% is not real) |

**Chinese games.** The dataset has no country field, so a game is removed if any rule matches:

1. Chinese without English, in the text or in the voice-over.
2. Every developer's name is in Chinese characters.
3. Every developer's name contains a mainland Chinese city.
4. Every developer is a known Chinese company (`CN_COMPANIES`, e.g. Game Science, so Black
   Myth: Wukong is removed although it ships English).

Why these rules and not simpler ones: Chinese voice-over alone is not a sign of a Chinese
game, since it would remove 4,233 Western games (Cyberpunk 2077, The Witcher 3, Hollow
Knight, ...). Rules 2-4 look at developers only, and all developers must match, because
publishers are often regional partners (bilibili publishes the Swedish Core Keeper in China)
and large Western games list Chinese support studios (Ubisoft Shanghai for Far Cry,
Activision Shanghai for Call of Duty). Result: 2,862 games with >= 10 reviews removed;
section A6 lists them, biggest first.

## Step 4. Cleaned data, one row per game (notebook: A4, A5)

The notebook saves six tables: the two game-level tables below, and four comparison tables
ready to plot (Step 6). Each is saved whole, as `data/processed/csv/pcd_<table>.csv` (for
code) and `data/processed/xlsx/pcd_<table>.xlsx` (to look at). Section A10 stops with an
error if anything is wrong (unique ids, English column names, csv = xlsx, known games kept or
removed, every game in exactly one group, intervals around their averages).

```python
import pandas as pd
games_clean = pd.read_csv("data/processed/csv/pcd_games_clean.csv")
```

### `pcd_games_clean`: one game in snapshot A (EDA, input of SQ1). 44,765 games, 14,078 with Simplified Chinese

| Column | Meaning |
|---|---|
| `app_id`, `name` | Steam id and title |
| `genre_group` | genre group |
| `release_year`, `year_band` | release year; band code 1-4 |
| `price`, `price_tier` | list price (USD); tier code 1-5 |
| `n_other_langs`, `n_other_langs_bin` | number of other languages; bin code 1-3 |
| `has_zh` | **treatment**: 1 = supports Simplified Chinese, 0 = no Chinese at all |
| `total_reviews`, `log_total_reviews` | **outcome**: reach |
| `group_id` | comparison group (Step 5): `genre_group | year_band | price_tier | n_other_langs_bin` |

### `pcd_sq2_panel`: one game in both snapshots, no Chinese in January 2024 (input of SQ2). 21,555 games

| Column | Meaning |
|---|---|
| `app_id`, `name` | Steam id and title |
| `genre_group`, `release_year`, `year_band`, `price_c`, `price_tier` | the game in January 2024 (snapshot C); `year_band` and `price_tier` as codes |
| `reviews_c`, `reviews_a` | reviews in January 2024 and in June 2026 |
| `growth` | **outcome**: `(reviews_a - reviews_c) / reviews_c` |
| `arm` | **treatment**: `treated` = added Simplified Chinese (509); `control` = added neither Chinese nor a major language (20,805); `excluded` = added another major language only (241) |
| `group_id_sq2` | comparison group (Step 5): `genre_group | year_band` |

**Codes of the binned columns.** The three binned columns have a natural order, so each
label is saved as its rank:

| Column | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| `price_tier` | free | < $5 | $5-10 | $10-20 | > $20 |
| `year_band` | <=2017 | 2018-2019 | 2020-2021 | 2022+ | |
| `n_other_langs_bin` | 0 | 1-4 | 5+ | | |

As text the labels sort in the wrong order ("10to20" before "5to10", "<=2017" after
"2022+"), which breaks tables and figure axes; the codes sort correctly and can be used in
calculations that need an order, such as a trend over price tiers. They are ranks, not
amounts (tier 4 is not twice tier 2), so they are not averaged or used as a plain number in
a regression. `genre_group` is not encoded: genres have no order, so a number would invent
one. The comparison groups (`group_id`, `group_id_sq2`) keep the readable labels.

Major languages: German, French, Spanish - Spain, Japanese, Russian, Korean, Portuguese - Brazil.

## Step 5. Comparison groups: holding confounders fixed (notebook: A4, A5)

A **confounder** is a characteristic that affects reach on its own and also differs between
games with and without Chinese. Comparing all games directly would mix the effect of Chinese
with the effect of these characteristics (for example, bigger-budget games are both more
often translated and more reviewed). So each game is put in a **group of similar games**,
and games with and without Chinese are compared **only inside the same group**: within a
group the confounders are the same on both sides, and the remaining gap is not explained by
them. Because of this, the confounders need no separate treatment in the analysis; their raw
columns are kept only to check that the two sides are still alike inside each group.

A group is used only if it has **at least 10 games on each side**; a median of fewer games
moves too much with a single game.

### SQ1 group = genre x price tier x release-year band x number of other languages

| Confounder | Why it matters |
|---|---|
| Genre | Genres differ in audience size and in how much text a game has |
| Price tier | Stands in for budget and studio size, which drive both translation and reach |
| Release-year band | Older games have had more time to collect reviews |
| Other languages (0, 1-4, 5+) | The strongest one: games with Chinese have a median of 7 other languages, games without it 0 (69% vs 9% have 5+). Without it, SQ1 would compare "localised in many languages" with "not localised" rather than measure Chinese itself |

Result: 360 groups, **178 usable, covering 76% of games (87% of games with Chinese)**, all
6 genres. Years are grouped into bands because single years left only 44% of games in usable
groups.

### SQ2 group = genre x release-year band

Only 509 games added Chinese between the two snapshots, so the group can hold only the
confounders that matter most for **growth**:

| Variable | In the group? | Why |
|---|---|---|
| Genre | yes | Needed to answer per genre |
| Release-year band | yes | The strongest one: among control games, median growth is +12% for games from <=2017 and +77% for 2022+, and games that added Chinese are about 2 years newer. Without it the effect of Chinese would be overstated |
| Price tier | no | Once the year band is fixed, growth is about the same in every tier except gt20; and genre x price x year leaves only 17 usable groups, 54% of treated games and 3 genres (no RPG, Strategy or Visual Novel), too few to answer per genre |
| Other languages | no | Treated and control games have almost the same mix (0 / 1-4 / 5+: 62/25/13% vs 64/26/10%) |

Result: 24 groups, **16 usable, covering 90% of treated games**, all 6 genres.

## Step 6. Comparison tables, ready to plot (notebook: A7, A8)

All the data wrangling and the comparisons are done in Part A; these four tables are what
the analysis reads.

### `pcd_sq1_groups` and `pcd_sq2_groups`: one row per comparison group

| Column | Meaning |
|---|---|
| `group_id` / `group_id_sq2` and its parts | the group (Step 5); parts as codes |
| `n_zh`, `n_no_zh` (SQ1) / `n_treated`, `n_control` (SQ2) | number of games on each side |
| `median_reviews_zh`, `median_reviews_no_zh` (SQ1) | median reviews on each side |
| `median_growth_treated`, `median_growth_control` (SQ2) | median growth on each side |
| `pct_diff` (SQ1) | gap: `median with / median without - 1` (0.5 = +50% reviews) |
| `uplift_pts` (SQ2) | uplift: `median growth treated - median growth control` (0.1 = +10 points) |
| `eligible` | the group has >= 10 games on each side and is used |

Medians, not means: review counts are very skewed (a few hits have millions of reviews).

### `pcd_sq1_summary` and `pcd_sq2_summary`: the answers, one row per reporting level

| Column | Meaning |
|---|---|
| `level`, `value`, `order` | `overall`/`all`, `genre`/a genre, or (SQ1 only) `price_tier`/a code; `order` sorts the rows |
| `n_groups`, game counts | eligible groups and games behind the row |
| `avg_pct_diff` (SQ1) / `avg_uplift_pts` (SQ2) | average gap / uplift over the eligible groups of that level |
| `ci_low`, `ci_high` | 95% bootstrap interval |
| `large_enough` | the average reaches the threshold (SQ1 +20%, SQ2 +10 points) and `ci_low > 0` |

How a row is computed: each eligible group gives one gap; a row averages the gaps of its
groups, each group counting once (so one huge group cannot dominate). "Per genre" is only
which groups are averaged: every gap is still measured inside one comparison group.

Interval: a gap is a function of two medians, which has no simple formula for its
uncertainty, so it is bootstrapped. The games of each side are resampled with replacement
within their group, 2,000 times (seed 2010, so every run gives the same numbers), the
average is recomputed each time, and the middle 95% of the results is the interval.

The thresholds (+20% for SQ1, +10 points for SQ2) were fixed before any result was seen:
below them, a gap is too small to justify the cost of a translation.

## Step 7. Analysis: figures and insights (notebook: Part B)

| Section | Reads | What |
|---|---|---|
| B1 EDA | `pcd_games_clean` | describe the data |
| B2 SQ1 | `pcd_sq1_groups`, `pcd_sq1_summary` | gap overall and per genre (price tier in the appendix) |
| B3 SQ2 | `pcd_sq2_panel`, `pcd_sq2_groups`, `pcd_sq2_summary` | uplift overall and per genre |
| B4 SQ3 | both summaries, per genre | translate at launch, later, or not a priority |

## Limitations

- **Reach is measured by review counts.** Steam does not publish sales. Reviews from all
  languages are counted together, so Chinese-speaking players cannot be separated.
- **SQ1 shows an association, not a cause.** Unmeasured differences remain between games
  with and without Chinese: marketing, studio size (only partly captured by price), quality.
- **SQ2 holds fewer things fixed than SQ1.** About 500 games added Chinese, too few to also
  group by price tier; within the gt20 tier growth is higher, so part of a difference could
  come from price.
- **The date a language was added is unknown**, only that it happened between January 2024
  and June 2026. A big update or sale at the same time could also raise reviews.
- **Chinese games are found by rules.** A Chinese studio with an English name, not on the
  company list, that ships English can be missed.
- **Genre comes from user tags**, which may not match how the studio describes the game.
- **Snapshot A is from 2026-06-20**, not today. Snapshot C has no discount information.

## Team and contributions

| Member | Role | Main contributions |
|---|---|---|
| Khanh Phung | Leader | |
| Hưng | Tech lead | |
| Phú | Data & EDA | |
| Chí Minh | SQ1 & testing | |
| Khúc | Bonus app & slides | |

## Use of AI tools

This project was built with AI coding agents (Claude) under human direction. Agents wrote
most of the code and first drafts; team members defined the questions and the analysis
design, checked every output against the data, and made all decisions. Individual
reflections were written by the members themselves.
