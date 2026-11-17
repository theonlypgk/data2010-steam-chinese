# Simplified Chinese support and reach on Steam

DATA2010 Data Science Programming, final project.

- **Question:** should a Steam game support Simplified Chinese, for which genres, and when?
- **Data:** two snapshots of the Steam catalogue (2024-01-11 and 2026-06-20).
- **Approach:** reach = number of reviews. SQ1 compares games with and without Simplified Chinese inside groups of similar games; SQ2 compares games that added Simplified Chinese after launch with similar games that did not.

The notebook `scripts/steam_chinese_analysis.ipynb` has the same sections as this file.

**Contents**
- [I. Setup and how to reproduce](#i-setup-and-how-to-reproduce)
- [II. Data science life cycle](#ii-data-science-life-cycle)
  - [1. Business understanding](#1-business-understanding)
  - [2. Data collection](#2-data-collection)
  - [3. Data processing](#3-data-processing)
  - [4. Data analysis / EDA](#4-data-analysis--eda)
  - [5. Data modelling](#5-data-modelling)
  - [6. Model deployment](#6-model-deployment)
- [Limitations](#limitations)
- [Team and contributions](#team-and-contributions)
- [Use of AI tools](#use-of-ai-tools)

---

# I. Setup and how to reproduce

**Files**

```
scripts/steam_chinese_analysis.ipynb   all the code
requirements.txt                       exact package versions
data/README.md                         description of the dataset
data/raw/                              the two input files (Git LFS)
data/processed/csv/                    output tables (written by the notebook)
data/processed/xlsx/                   a copy of the same tables, to open and look at
report/                                report, figures, reflections, slides
```

**Needed:** [Git](https://git-scm.com) with [Git LFS](https://git-lfs.com) (the Windows installer of Git already includes it), Python 3.12 or 3.13.

**Steps**
1. `git lfs install` (once per computer)
2. `git clone https://github.com/theonlypgk/data2010-steam-chinese.git`
3. `cd data2010-steam-chinese` then `pip install -r requirements.txt`
4. Open `scripts/steam_chinese_analysis.ipynb` and choose *Run All*.
   Or in one command: `jupyter nbconvert --to notebook --execute --inplace scripts/steam_chinese_analysis.ipynb`

- `data/raw/games_a.csv` is only a few lines of text (not ~400 MB)? → run `git lfs pull` in the project folder.

**How to read section 3 of the notebook**
- Steps are numbered 3.1.1, 3.1.2, ... Each step = a table (problem, solution, output; problems lettered a, b, c), then its code cell.
- In the code, `# 3.1.1e · ...` stands above the lines that solve problem e.
- Each step runs on both snapshots right after its functions, then prints its counts and a preview of the first 3 games of A and of C.

---

# II. Data science life cycle

## 1. Business understanding

- **Context:** Chinese-speaking players are one of the largest groups on Steam; a translation costs money and time.
- **Main question:** should a Steam game support Simplified Chinese, for which genres, and when?
- **Reach** = number of reviews because: Steam publishes no sales.

| | Question |
|---|---|
| SQ1 | How much larger is the reach of games with Simplified Chinese, and in which genres? |
| SQ2 | Does adding Simplified Chinese after launch still increase reach, and in which genres? |
| SQ3 | For each genre: translate at launch, later, or not a priority? |

## 2. Data collection

- **Source:** Steam Games Dataset by FronkonGames (Hugging Face `FronkonGames/steam-games-dataset`), one row per game.
- **License:** MIT (as given on the Hugging Face page).
- **Two snapshots** because: SQ2 needs to see which games added Chinese over time.
- **Saved in `data/raw/`** because: the dataset keeps being updated. Details: [data/README.md](data/README.md).

| | Snapshot A ("now") | Snapshot C ("before") |
|---|---|---|
| Commit | `52ba62abfa707a2fa31f4d147c2777a9d9fbd2da` | `aefdeb1ff1a739b92ac5338682cc2610a0328505` |
| Date | 2026-06-20 | 2024-01-11 |
| Raw rows | 125,855 | 85,103 |
| Used for | SQ1, SQ2 | SQ2 |

## 3. Data processing

### 3.1 Clean data

**Data issues fixed**
- Header of A merges two names (`DiscountDLC count`) → later columns shifted → split back.
- Prices in A are sale prices (Hades 7.49 = 24.99 at -70%) → list price.
- Junk in language and tag cells (`[b]*[/b]`, HTML) → removed.
- One genre label is written two ways ("Free To Play" in snapshot A, "Free to Play" in snapshot C and in the tags) → compared in lower case.
- One language renamed between the snapshots ("Portuguese" in C = "Portuguese - Portugal" in A) → the new name is used in both.
- No id or repeated id → row dropped (first kept); none in the current data. Unreadable date → missing.

**Columns added**
- Reach: `total_reviews = positive + negative`.
- Simplified Chinese support: `has_zh`.
- Confounders: genre group, price tier, year band, number of other languages.
- Genre group = the first user tag (most voted) that is a Steam genre. The genre list is taken from the data by code: Steam's genre labels on >= 2% of games, without Indie, Early Access, Free to Play (not a type of gameplay). Not a hand-made tag list because: it cannot be checked against 125k games.
- Price, release year and number of other languages are cut into ranges, each saved by its name (e.g. "<=2017", "<$5", "5+").

**Games removed**

Applied in this order (notebook 3.1.8); games left in snapshot A after each rule:

| Rule | Reason | Games left in A |
|---|---|---:|
| (start) | | 125,855 |
| drop Chinese-first games | original language is Chinese → not a translation | 121,228 |
| drop Early Access | unfinished game | 110,107 |
| keep >= 10 reviews | below that, reach is noise | 50,160 |
| keep released >= 1 year before the snapshot | time to collect reviews | 49,838 |
| keep games with genre, price and year | needed to form groups; not imputed because: an invented value → wrong group | 48,371 |
| drop Traditional-Chinese-only (A only) | neither "with" nor "without" Simplified Chinese | 47,603 |

**Chinese-first games**
- **Rules:** a game is flagged if
  1. it has Chinese text without English text, or
  2. every developer's name is in Chinese characters, without kana.
- **Not used:**
  - hand-made lists of cities or companies because: dataset too large → cannot check row by row.
  - voice-over languages because: Japanese games are dubbed in Chinese too.
  - names with kana because: kana = Japanese.

**Not changed**
- Very large review counts are kept because: they are real; comparisons use medians.

**Output:** `pcd_games_clean` (47,603 games, 15,178 with Simplified Chinese)

**Data dictionary**

| Column | Description |
|---|---|
| `app_id` | Steam application id |
| `name` | game title |
| `genre_group` | Steam genre: Action, Adventure, Casual, Massively Multiplayer, Racing, RPG, Simulation, Sports or Strategy |
| `release_year` | year of release |
| `year_band` | release-year range: <=2017, 2018-2019, 2020-2021, 2022+ |
| `price` | list price in USD |
| `price_tier` | list-price range: free, <$5, $5-10, $10-20, >$20 |
| `n_other_langs` | number of supported languages other than English and Chinese |
| `n_other_langs_bin` | range of other languages: 0, 1-4, 5+ |
| `has_zh` | 1 = supports Simplified Chinese, 0 = no Chinese at all |
| `total_reviews` | positive + negative reviews (= reach) |

**First 3 rows**

| app_id | name | genre_group | release_year | year_band | price | price_tier | n_other_langs | n_other_langs_bin | has_zh | total_reviews |
|---:|:---|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | Counter-Strike | Action | 2000 | <=2017 | 9.95 | $5-10 | 5 | 5+ | 1 | 250245 |
| 20 | Team Fortress Classic | Action | 1999 | <=2017 | 4.96 | <$5 | 6 | 5+ | 1 | 8738 |
| 30 | Day of Defeat | Action | 2003 | <=2017 | 4.96 | <$5 | 4 | 1-4 | 0 | 7102 |

### 3.2 SQ1 groups: similar games, with vs without Chinese

- **Rule:** compare games with and without Chinese only inside groups of similar games.
- **Reason:** bigger games are both translated more and reviewed more.
- **Group** = genre x price tier x year band x other languages.
  - Genre: audience size and amount of text differ.
  - Price tier: stands in for budget and studio size.
  - Year band: older games had more time to collect reviews.
  - Other languages: bigger games ship in more languages.
- **Per side:** number of games and median reviews. Medians because: review counts are very skewed.
- **Eligible group** = >= 10 games per side because: fewer → one game moves the median.
- The two sides are compared in section 5.1.

**Output:** `pcd_sq1_groups` (518 groups, 202 eligible)

**Data dictionary**

| Column | Description |
|---|---|
| `group_id` | group name: genre \| year band \| price tier \| other languages, e.g. "Action \| <=2017 \| <$5 \| 5+" |
| `genre_group` | genre of the group |
| `year_band` | year range of the group (as in `pcd_games_clean`) |
| `price_tier` | price range of the group |
| `n_other_langs_bin` | other-languages range of the group |
| `n_zh` | number of games with Simplified Chinese |
| `n_no_zh` | number of games without Chinese |
| `median_reviews_zh` | median reviews of games with Chinese |
| `median_reviews_no_zh` | median reviews of games without Chinese |
| `eligible` | True if the group has >= 10 games on each side |

**First 3 rows**

| group_id | genre_group | year_band | price_tier | n_other_langs_bin | n_zh | n_no_zh | median_reviews_zh | median_reviews_no_zh | eligible |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|:---|
| Action \| <=2017 \| free \| 0 | Action | <=2017 | free | 0 | 7 | 279 | 43 | 79 | False |
| Action \| <=2017 \| free \| 1-4 | Action | <=2017 | free | 1-4 | 8 | 82 | 186.5 | 302 | False |
| Action \| <=2017 \| free \| 5+ | Action | <=2017 | free | 5+ | 55 | 36 | 9937 | 1186.5 | True |

### 3.3 SQ2 groups: similar games, added Chinese after launch vs did not

- **Rule:** follow games with no Chinese in C to A; compare those that added Chinese (treated) with similar games that did not (control).
- **Reason for a control:** every game gains reviews over time anyway.
- **Games:** C filtered as A (3.1.8), no Chinese in C, still in A. Characteristics from C because: the state before adding Chinese.
- **Dropped:** 0 reviews in A because: delisted → -100% growth is not real.
- **Growth** = (reviews in A - reviews in C) / reviews in C.
- **Treated** = added Simplified Chinese. **Control** = language list unchanged. **Excluded** = added another language (also only Traditional Chinese) because: own localisation push → not a clean control. Not a hand-made list of "major" languages because: it cannot be justified from the data.
- **Group** = genre x year band.
- **Per side (treated / control):** number of games and median growth. Eligible = >= 10 games per side.
- The two sides are compared in section 5.2.

**Output:** `pcd_sq2_groups` (36 groups, 19 eligible)

**Data dictionary**

| Column | Description |
|---|---|
| `group_id_sq2` | group name: genre \| year band, e.g. "Action \| <=2017" |
| `genre_group` | genre of the group |
| `year_band` | year range of the group (as in `pcd_games_clean`) |
| `n_treated` | number of games that added Simplified Chinese (532 in total) |
| `n_control` | number of games whose language list did not change |
| `median_growth_treated` | median review growth of the treated games |
| `median_growth_control` | median review growth of the control games |
| `eligible` | True if the group has >= 10 games on each side |

**First 3 rows**

| group_id_sq2 | genre_group | year_band | n_treated | n_control | median_growth_treated | median_growth_control | eligible |
|:---|:---|---:|---:|---:|---:|---:|:---|
| Action \| <=2017 | Action | <=2017 | 29 | 3133 | 0.166134 | 0.104465 | True |
| Action \| 2018-2019 | Action | 2018-2019 | 21 | 1617 | 0.17931 | 0.142857 | True |
| Action \| 2020-2021 | Action | 2020-2021 | 38 | 1410 | 0.296376 | 0.25 | True |

### 3.4 Save the tables

- The three output tables are written to `data/processed/csv/`.

## 4. Data analysis / EDA

## 5. Data modelling

## 6. Model deployment

---

## Limitations

- Reach = reviews in all languages → Chinese-speaking players cannot be separated.
- SQ1 is an association, not a cause: marketing, studio size and quality are not measured.
- SQ2 does not hold price fixed.
- Single- vs multiplayer is not held fixed.
- The date a language was added is unknown (between 2024-01 and 2026-06).
- Chinese-first games: dataset too large to check row by row → found by two rules. A Chinese
  studio with an English name and an English release (Black Myth: Wukong) is missed.
- Genre = Steam's own genre list, so there is no Visual Novel or Puzzle group: those games (the most text-heavy ones)
  fall into other genres (e.g. Adventure, Casual, Simulation) → their result is mixed into those genres.
- One genre per game (the most-voted user tag that is a Steam genre) → a game that is both, e.g. Action and RPG, counts
  only in one. The 2% cut-off for a genre is a choice.
- Snapshot A is from 2026-06-20, not today.

## Team and contributions

| Member | Role | Main contributions |
|---|---|---|
| Khanh Phung | Leader | |
| Hưng | Tech lead | |
| Phú | Data & EDA | |
| Chí Minh | SQ1 & testing | |
| Khúc | Bonus app & slides | |

## Use of AI tools
