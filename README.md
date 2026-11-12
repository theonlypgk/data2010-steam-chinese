# Simplified Chinese support and reach on Steam

DATA2010 Data Science Programming, final project.

**Main question.** Should a Steam game support Simplified Chinese, for which genres, and when?

| | Question | Data |
|---|---|---|
| SQ1 | How much larger is the reach of games that support Simplified Chinese, and in which genres? | snapshot A |
| SQ2 | Does adding Simplified Chinese after launch still increase reach, and in which genres? | snapshots A + C |
| SQ3 | For each genre: translate at launch, translate later, or not a priority? | results of SQ1 + SQ2 |

Reach = number of reviews (`positive + negative`).

The whole project is one notebook, `steam_chinese_analysis.ipynb`, in three steps that
produce six tables, followed by the analysis. This README summarises each step; the
notebook explains the strategy at the top of each step and the code in comments.

| Step | What | Output tables |
|---|---|---|
| 1 | clean the data and encode it | `pcd_games_clean` |
| 2 | SQ1: games with vs without Chinese, inside groups of similar games | `pcd_sq1_groups`, `pcd_sq1_summary` |
| 3 | SQ2: games that added Chinese vs similar games that did not | `pcd_sq2_panel`, `pcd_sq2_groups`, `pcd_sq2_summary` |
| Part B | figures and insights (EDA, SQ1, SQ2, SQ3) | `report/figures/` |

```
steam_chinese_analysis.ipynb   all the code, from the two input files to the analysis
requirements.txt               exact package versions (Python 3.12)
data/raw/                      the two input files (downloaded by the notebook, not committed)
data/processed/csv/            the six tables, for code (pandas.read_csv)
data/processed/xlsx/           the same six tables, to open and look at
report/                        report, figures, reflections, slides
.github/, .devcontainer/       automatic re-runs on GitHub; Codespaces environment
```

## Reproducing the results

```bash
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute steam_chinese_analysis.ipynb --output executed.ipynb
```

or open the notebook and choose *Run All*. It downloads the two input files itself. Two runs
give byte-identical CSV files (exact package versions, rounded floats, fixed seed, fixed
xlsx dates). On GitHub, the `pipeline` workflow runs the notebook on a clean machine after
every change and commits the tables if they changed.

```python
import pandas as pd
games_clean = pd.read_csv("data/processed/csv/pcd_games_clean.csv")
```

## Input data

Steam Games Dataset by FronkonGames (Hugging Face `FronkonGames/steam-games-dataset`), one
row per game, two versions pinned by commit so the data never changes:

| | Snapshot A ("now") | Snapshot C (January 2024) |
|---|---|---|
| Commit | `52ba62abfa707a2fa31f4d147c2777a9d9fbd2da` | `aefdeb1ff1a739b92ac5338682cc2610a0328505` |
| Date | 2026-06-20, the last version of `games.csv` | 2024-01-11 |
| Raw rows | 125,855 | 85,103 |
| Used for | Steps 1-3 | Step 3 |

Backup: release [raw-snapshots-v1](../../releases/tag/raw-snapshots-v1) of this repo (gzip,
with SHA-256 checksums).

---

## Step 1. Clean the data and encode it → `pcd_games_clean`

Both snapshots are cleaned in exactly the same way, so a game looks the same in both.

**Data issues fixed**
- The header of snapshot A merges two names (`DiscountDLC count`) while rows hold two
  values, which shifts every later column; it is split back before reading.
- Snapshot A was taken during a sale (Hades: 7.49 = 24.99 at -70%); `price` is the list
  price `sale price / (1 - discount / 100)`, so the price tier describes the game.
- Language and tag cells contain store-page junk (`[b]*[/b]`, HTML); removed before parsing.
- Rows without an id or with a repeated id are dropped; unreadable dates become missing.

**Columns.** Outcome `total_reviews`; treatment `has_zh` (1 = Simplified Chinese, 0 = no
Chinese at all); confounders `genre_group` (first user tag found in the genre map: Visual
Novel, RPG, Strategy, Action, Puzzle, Casual), `price_tier`, `year_band`, `n_other_langs`
(languages other than English and Chinese).

**Chinese games are removed, large or small.** A game made in China has Chinese and Chinese
players by default, so keeping it would mix "made for China" with "translated into Chinese".
With no country column, a game is Chinese if any rule matches: (1) Chinese without English,
in the text or voice-over; or every developer is Chinese by (2) a name in Chinese
characters, (3) a mainland city in the name, or (4) a known Chinese company. Chinese
voice-over alone is not a rule (it would remove 4,233 Western games such as Cyberpunk 2077);
rules 2-4 use developers only and need all of them, because publishers are often regional
partners (bilibili for Core Keeper) and Western games list Chinese support studios (Ubisoft
Shanghai on Far Cry). 2,862 games with >= 10 reviews are removed.

**Other filters**, in order: drop Early Access (unfinished games); keep >= 10 reviews (below
that, reach is noise; not higher, to avoid filtering on the outcome); keep games released
>= 1 year before the snapshot (time to collect reviews); keep games with a genre, price and
year (needed for the groups); drop Traditional-Chinese-only games (neither side).

**Encoding.** The three binned columns are saved as ordinal codes:

| Column | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| `price_tier` | free | < $5 | $5-10 | $10-20 | > $20 |
| `year_band` | <=2017 | 2018-2019 | 2020-2021 | 2022+ | |
| `n_other_langs_bin` | 0 | 1-4 | 5+ | | |

As text the labels sort in the wrong order ("10to20" before "5to10"); codes sort correctly
and can be used where an order matters. They are ranks, not amounts, so they are not
averaged or used as a plain number in a regression. Genre is not encoded: it has no order.

### `pcd_games_clean`: 44,765 games, 14,078 with Simplified Chinese

| Column | Meaning |
|---|---|
| `app_id`, `name` | Steam id and title |
| `genre_group` | genre group |
| `release_year`, `year_band` | release year; band code 1-4 |
| `price`, `price_tier` | list price (USD); tier code 1-5 |
| `n_other_langs`, `n_other_langs_bin` | number of other languages; bin code 1-3 |
| `has_zh` | **treatment**: 1 = Simplified Chinese, 0 = no Chinese at all |
| `total_reviews`, `log_total_reviews` | **outcome**: reach (log10 for figures, because counts are very skewed) |

## Step 2. SQ1 tables → `pcd_sq1_groups`, `pcd_sq1_summary`

**Strategy: compare only similar games.** A confounder affects reach and also differs
between games with and without Chinese (bigger-budget games are both more often translated
and more reviewed). Each game is put in a group of similar games and the two sides are
compared only inside the same group, where the confounders are the same on both sides.

**SQ1 group = genre x price tier x release-year band x number of other languages**

| Confounder | Why it is in the group |
|---|---|
| Genre | genres differ in audience size and in how much text a game has |
| Price tier | budget and studio size drive both translation and reach |
| Release-year band | older games have had more time to collect reviews; bands, because single years leave only 44% of games in usable groups (76% with bands) |
| Other languages | the strongest: games with Chinese have a median of 7 other languages, games without it 0 (69% vs 9% have 5+); without it SQ1 would compare "localised" with "not localised" |

**Method**
- Per group: number of games and **median** reviews on each side (medians, because review
  counts are very skewed), gap `pct_diff = median with / median without - 1`. A group is used
  (`eligible`) only with >= 10 games per side. Result: 360 groups, 178 eligible, covering 76%
  of games (87% of games with Chinese).
- Per reporting level (overall, each genre, each price tier): the **average gap over its
  eligible groups**, each group counting once. "Per genre" only says which groups are
  averaged; every gap is measured inside one group.
- **95% interval** by bootstrap: games of each side are resampled within their group 2,000
  times (seed 2010), the average is recomputed, and the middle 95% is kept. A gap is a
  function of two medians, which has no simple formula for its uncertainty.
- **Large enough** = average >= +20% and the whole interval above 0 (fixed beforehand).

### `pcd_sq1_groups`: one row per group (360)

| Column | Meaning |
|---|---|
| `group_id` | readable group name, e.g. `Action | <=2017 | lt5 | 5+` |
| `genre_group`, `year_band`, `price_tier`, `n_other_langs_bin` | the group's parts (codes) |
| `n_zh`, `n_no_zh` | games with / without Chinese |
| `median_reviews_zh`, `median_reviews_no_zh` | median reviews on each side |
| `pct_diff` | gap (0.5 = +50% reviews) |
| `eligible` | >= 10 games on each side |

### `pcd_sq1_summary`: one row per reporting level (12)

| Column | Meaning |
|---|---|
| `level`, `value`, `order` | `overall`/`all`, `genre`/a genre, `price_tier`/a code; `order` sorts the rows |
| `n_groups`, `n_zh`, `n_no_zh` | eligible groups and games behind the row |
| `avg_pct_diff` | average gap over those groups |
| `ci_low`, `ci_high` | 95% bootstrap interval |
| `large_enough` | `avg_pct_diff >= 0.20` and `ci_low > 0` |

## Step 3. SQ2 tables → `pcd_sq2_panel`, `pcd_sq2_groups`, `pcd_sq2_summary`

**Strategy: follow the same games over time.** Games with no Chinese in January 2024
(snapshot C) that are still on Steam in June 2026 (snapshot A): those that added Chinese
in between (**treated**) are compared with similar games that added nothing (**control**).
The control arm is needed because every game gains reviews over time anyway.

**Panel.** Snapshot C is filtered as in Step 1; game characteristics are taken from C
(what a game looked like before adding Chinese); games with 0 reviews in A are dropped
(delisted: a growth of -100% is not real). `growth = (reviews A - reviews C) / reviews C`.
`arm`: `treated` = added Simplified Chinese (509); `control` = added neither Chinese nor any
major language (German, French, Spanish, Japanese, Russian, Korean, Portuguese-Brazil),
because adding those means a localisation push of its own (20,805); `excluded` = added
another major language only (241).

**SQ2 group = genre x release-year band.** Only 509 games added Chinese, so the group holds
only the confounders that matter most for growth:

| Variable | In the group? | Why |
|---|---|---|
| Genre | yes | needed to answer per genre |
| Release-year band | yes | the strongest: control games from <=2017 grow +12% (median), from 2022+ +77%, and treated games are about 2 years newer; without it the effect would be overstated |
| Price tier | no | with the year band fixed, growth is about the same in every tier except > $20; genre x price x year leaves only 17 usable groups, 54% of treated games and 3 genres |
| Other languages | no | treated and control have almost the same mix (0 / 1-4 / 5+: 62/25/13% vs 64/26/10%) |

Result: 24 groups, 16 eligible, covering 90% of treated games and all 6 genres. Groups and
summary are built exactly as in Step 2, with `uplift_pts = median growth treated - median
growth control` (0.1 = +10 points), reported overall and per genre; **large enough** =
average >= +10 points and the whole interval above 0.

### `pcd_sq2_panel`: one row per game (21,555)

| Column | Meaning |
|---|---|
| `app_id`, `name` | Steam id and title |
| `genre_group`, `release_year`, `year_band`, `price_c`, `price_tier` | the game in January 2024 (codes as in Step 1) |
| `reviews_c`, `reviews_a` | reviews in January 2024 and June 2026 |
| `growth` | **outcome** |
| `arm` | **treatment**: treated / control / excluded |

### `pcd_sq2_groups` (24) and `pcd_sq2_summary` (7)

Same layout as the SQ1 tables, with `group_id_sq2` (e.g. `Action | <=2017`), `n_treated`,
`n_control`, `median_growth_treated`, `median_growth_control`, `uplift_pts` and, in the
summary, `avg_uplift_pts`.

## Part B. Analysis: figures and insights

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
