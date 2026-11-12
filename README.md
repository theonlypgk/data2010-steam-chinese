# Simplified Chinese support and reach on Steam

DATA2010 Data Science Programming, final project.

**Main question.** Should a Steam game support Simplified Chinese, for which genres, and when?

| | Question | Data |
|---|---|---|
| SQ1 | How much larger is the reach of games that support Simplified Chinese, and in which genres? | snapshot A |
| SQ2 | Does adding Simplified Chinese after launch still increase reach, and in which genres? | snapshots A + C |
| SQ3 | For each genre: translate at launch, translate later, or not a priority? | results of SQ1 + SQ2 |

Reach = number of reviews (`positive + negative`). Every comparison is made inside a group
of similar games, so that a gap is not simply "bigger games get translated more".

This README is the only document of the project. It follows the work in order, from the two
input files to the answers; each step names the notebook section that does it.

```
steam_chinese_analysis.ipynb   ALL the code, from the two input files to the analysis
requirements.txt               exact package versions (Python 3.12)
data/raw/                      the two input files (downloaded by the notebook, not committed)
data/processed/csv/            the two cleaned tables, for code (pandas.read_csv)
data/processed/xlsx/           the same two tables, to open and look at
report/                        report, figures, reflections, slides
.github/, .devcontainer/       automatic re-runs on GitHub; Codespaces environment
```

---

## Step 0. Run it

```bash
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute steam_chinese_analysis.ipynb --output executed.ipynb
```

or open the notebook and choose *Run All*. It needs nothing but internet access: it downloads
the two input files itself. Two runs give byte-identical CSV files (exact package versions,
rounded floats, fixed xlsx dates). On GitHub, the `pipeline` workflow (Actions tab) runs the
notebook on a clean machine after every change and commits the tables if they changed.

To work on the project: edit the notebook, run it from the top, commit the notebook (and the
tables if they changed). The first line of every code cell says what kind of step it is
(LOAD DATA, DATA CLEANING, SELECT ROWS, AGGREGATE, SAVE OUTPUTS, CHECKS); problems found in
the real data are marked `DATA ISSUE`. Every fixed choice is in the **Settings and
decisions** cell, with its reason; a change there gets a dated line in the change log below.

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

Rules 2-4 look at developers only, and all developers must match. Earlier versions went
wrong: "Chinese voice-over" alone removed 4,233 Western games (Cyberpunk 2077, The Witcher 3,
Hollow Knight, ...); looking at publishers or at any one developer removed Core Keeper
(publisher bilibili), Far Cry (Ubisoft Shanghai), Call of Duty (Activision Shanghai) and
Sekiro. Result: 2,862 games with >= 10 reviews removed. Section A6 lists them, biggest first,
so a wrongly removed game can be spotted and added as an exception in Settings.

## Step 4. The two output tables (notebook: A7 saves, A8 checks)

Each table is saved whole, as `data/processed/csv/pcd_<table>.csv` (for code) and
`data/processed/xlsx/pcd_<table>.xlsx` (to look at). Section A8 stops with an error if
anything is wrong (unique ids, English column names, csv = xlsx, known games kept or removed).

```python
import pandas as pd
sq1_games = pd.read_csv("data/processed/csv/pcd_sq1_games.csv")
sq2_games = pd.read_csv("data/processed/csv/pcd_sq2_games.csv")
```

### `pcd_sq1_games`: one game in snapshot A (EDA, SQ1). 44,765 games, 14,078 with Simplified Chinese

| Column | Meaning |
|---|---|
| `app_id`, `name` | Steam id and title |
| `release_year`, `year_band` | release year and its band |
| `price`, `discount_pct`, `price_tier` | list price (USD); sale discount on the snapshot day; tier |
| `genre_group` | genre group |
| `n_other_langs`, `n_other_langs_bin` | number of other languages and its bin |
| `has_zh` | **treatment**: 1 = supports Simplified Chinese, 0 = no Chinese at all |
| `positive`, `negative`, `total_reviews`, `log_total_reviews` | **outcome**: reach |
| `group_id` | group of similar games: `genre_group | year_band | price_tier | n_other_langs_bin` |

### `pcd_sq2_games`: one game in both snapshots, no Chinese in January 2024 (SQ2). 21,555 games

| Column | Meaning |
|---|---|
| `app_id`, `name` | Steam id and title |
| `genre_group`, `release_year`, `year_band`, `price_c`, `price_tier`, `n_other_langs_bin` | the game in January 2024 (snapshot C) |
| `reviews_c`, `reviews_a` | reviews in January 2024 and in June 2026 |
| `growth` | **outcome**: `(reviews_a - reviews_c) / reviews_c` |
| `initial_reach_bin` | starting reach: small, medium, large (thirds of `reviews_c`) |
| `added_zh`, `added_only_zh` | added Simplified Chinese; Chinese was the only language added |
| `added_other_major_lang`, `n_langs_added` | added a major language; number of languages added |
| `arm` | **treatment**: `treated` = added Chinese (509); `control` = added neither Chinese nor a major language (20,805); `excluded` = added another major language only (241) |
| `group_id_sq2` | group of similar games: `genre_group | initial_reach_bin` |

Major languages: German, French, Spanish - Spain, Japanese, Russian, Korean, Portuguese - Brazil.

## Step 5. Analysis (notebook: Part B)

| Section | What | Rule |
|---|---|---|
| B1 EDA | describe both tables | |
| B2 SQ1 | inside each `group_id`, compare median `total_reviews` of `has_zh` 1 vs 0; average over groups, overall and per genre (price tier in the appendix) | a group counts if it has >= 10 games on each side: 178 of 360 groups |
| B3 SQ2 | inside each `group_id_sq2`, compare median `growth` of treated vs control; average, overall and per genre | same rule: 14 of 18 groups |
| B4 SQ3 | per genre: translate at launch, later, or not a priority, from B2 and B3 | |

Uncertainty: bootstrap, 2,000 resamples, seed 2010. A gap is "large enough" when SQ1 >= +20%
or SQ2 >= +10 points, and its interval does not include 0.

Why these groups: with single release years, SQ1 groups big enough covered only 47% of games;
year bands raise this to 81%. For SQ2 the five-way group left 7 usable groups in 2 genres;
genre x starting reach gives 14 groups in all 6 genres.

Report (10 pages): Introduction 1.5, SQ1 2.5, SQ2 2.5, SQ3 1.5, Conclusion 1, Lifecycle
reflection 1; two figures per question in the body.

## Limitations

- **Reach is measured by review counts.** Steam does not publish sales. Reviews from all
  languages are counted together, so Chinese-speaking players cannot be separated.
- **SQ1 shows an association, not a cause.** Unmeasured differences remain between games
  with and without Chinese: marketing, studio size (only partly captured by price), quality.
- **SQ2 holds fewer things fixed than SQ1.** About 500 games added Chinese, too few to split
  by five characteristics; release year, price and number of other languages are not held
  fixed, so part of a difference could come from them.
- **The date a language was added is unknown**, only that it happened between January 2024
  and June 2026. A big update or sale at the same time could also raise reviews.
- **Chinese games are found by rules.** A Chinese studio with an English name, not on the
  company list, that ships English can be missed.
- **Genre comes from user tags**, which may not match how the studio describes the game.
- **Snapshot A is from 2026-06-20**, not today. Snapshot C has no discount information.

## Still to do (team leader)

- [ ] Review `TAG_TO_GENRE` (genre map, draft) and `MAJOR_LANGS` in the Settings cell.
- [ ] Spot-check 20 rows of `pcd_sq1_games.xlsx` and 10 `treated` rows of `pcd_sq2_games.xlsx` against Steam.
- [ ] Check the removed Chinese games in section A6 for Western games.
- [ ] Copy the dataset licence from its page and confirm it allows sharing derived tables.
- [ ] Invite the 4 members as collaborators (Settings -> Collaborators).
- [ ] Fill in the team table below.

## Change log

Decisions were fixed before any result was looked at; each later change is dated.

- 2026-11-12: scope fixed: SQ1, SQ2 (main result + per genre; price tier in the appendix), SQ3 per genre.
- 2026-11-12: prices use the list price (snapshot A taken during a sale).
- 2026-11-12: SQ1 groups use year bands; SQ2 groups are genre x starting reach (to be confirmed by kp).
- 2026-11-12: SQ2 drops 40 games with 0 reviews in A (delisted).
- 2026-11-12 (kp): all Chinese games removed, large or small; rules 2-4 use developers only, all must match.
- 2026-11-12 (kp): snapshot A stays at 2026-06-20.
- 2026-11-12 (kp): the whole project is one notebook; outputs are only the two cleaned tables; all
  documentation is in this README.

## Team and contributions

| Member | Role | Main contributions |
|---|---|---|
| kp | Leader | |
| Hưng | Tech lead | |
| Phú | Data & EDA | |
| Chí Minh | SQ1 & testing | |
| Khúc | Bonus app & slides | |

## Use of AI tools

This project was built with AI coding agents (Claude) under human direction. Agents wrote
most of the code and first drafts; team members defined the questions and the analysis
design, checked every output against the data, and made all decisions. Individual
reflections were written by the members themselves.
