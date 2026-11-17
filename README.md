# Simplified Chinese support and reach on Steam

DATA2010 Data Science Programming, final project.

The notebook `scripts/steam_chinese_analysis.ipynb` has the same sections as this file.

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

**Needed:** Git, [Git LFS](https://git-lfs.com) (the two raw files are large), Python 3.12 or 3.13.

**Steps**
1. `git lfs install`
2. `git clone https://github.com/theonlypgk/data2010-steam-chinese.git`
3. `cd data2010-steam-chinese` then `pip install -r requirements.txt`
4. Open `scripts/steam_chinese_analysis.ipynb` and choose *Run All*.
   Or in one command: `jupyter nbconvert --to notebook --execute --inplace scripts/steam_chinese_analysis.ipynb`

**On Google Colab:** open the notebook and choose *Run All* — cell I.0 clones the repo, pulls the data and moves into `scripts/`.

**If step 4 fails**
- The raw files look tiny (a few lines of text)? → run `git lfs pull` in the project folder.

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
- No id or repeated id → row dropped (first kept). Unreadable date → missing.

**Columns added**
- Outcome: `total_reviews = positive + negative`.
- Treatment: `has_zh` (supports Simplified Chinese).
- Confounders: genre group, price tier, year band, number of other languages.
- Bins saved as ranks 1, 2, 3, ... because: text labels sort wrongly ("10to20" before "5to10").

**Games removed**

| Rule | Reason |
|---|---|
| drop Chinese-first games | original language is Chinese → not a translation |
| drop Early Access | unfinished game |
| keep >= 10 reviews | below that, reach is noise |
| keep released >= 1 year before the snapshot | time to collect reviews |
| keep games with genre, price and year | needed to form groups; not imputed because: an invented value → wrong group |
| drop Traditional-Chinese-only | neither "with" nor "without" Simplified Chinese |

**Chinese-first games**
- **Rules:** a game is flagged if
  1. it has Chinese text without English text, or
  2. every developer's name is in Chinese characters, without kana.
- **Not used:**
  - hand-made lists of cities or companies because: dataset too large → cannot check row by row.
  - voice-over languages because: Japanese games are dubbed in Chinese too → right only 1 of 9 times.
  - names with kana because: kana = Japanese.
- **Checked by:**
  - tests on known games;
  - a random sample of 50 games checked by hand → the two rules are right for 36 of 37 (notebook 3.1n);
  - SQ1 run again under other filters → same result (notebook 5.1b).

**Not changed**
- Very large review counts are kept because: they are real; comparisons use medians.

**Output:** `pcd_games_clean` (45,445 games, 14,701 with Simplified Chinese)

**Data dictionary**

| Column | Description |
|---|---|
| `app_id` | Steam application id |
| `name` | game title |
| `genre_group` | Visual Novel, RPG, Strategy, Action, Puzzle or Casual |
| `release_year` | year of release |
| `year_band` | 1 = <=2017, 2 = 2018-2019, 3 = 2020-2021, 4 = 2022+ |
| `price` | list price in USD |
| `price_tier` | 1 = free, 2 = < $5, 3 = $5-10, 4 = $10-20, 5 = > $20 |
| `n_other_langs` | number of supported languages other than English and Chinese |
| `n_other_langs_bin` | 1 = 0 other languages, 2 = 1-4, 3 = 5+ |
| `has_zh` | 1 = supports Simplified Chinese, 0 = no Chinese at all (treatment) |
| `total_reviews` | positive + negative reviews (outcome: reach) |
| `log_total_reviews` | log10 of `total_reviews`, for figures (counts are very skewed) |

**First 3 rows**

| app_id | name | genre_group | release_year | year_band | price | price_tier | n_other_langs | n_other_langs_bin | has_zh | total_reviews | log_total_reviews |
|---:|:---|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | Counter-Strike | Action | 2000 | 1 | 9.95 | 3 | 5 | 3 | 1 | 250245 | 5.39837 |
| 20 | Team Fortress Classic | Action | 1999 | 1 | 4.96 | 2 | 6 | 3 | 1 | 8738 | 3.94141 |
| 30 | Day of Defeat | Action | 2003 | 1 | 4.96 | 2 | 4 | 2 | 0 | 7102 | 3.85138 |

### 3.2 SQ1 groups: similar games, with vs without Chinese

- **Rule:** compare games with and without Chinese only inside groups of similar games.
- **Reason:** bigger games are both translated more and reviewed more.
- **Group** = genre x price tier x year band x other languages.
  - Genre: audience size and amount of text differ.
  - Price tier: stands in for budget and studio size.
  - Year band: older games had more time to collect reviews. Bands, not single years because: single years → only 47% of games in usable groups (bands: 79%).
  - Other languages: games with Chinese have a median of 7 other languages; without: 0.
- **Per side:** number of games and median reviews. Medians because: review counts are very skewed.
- **Eligible group** = >= 10 games per side because: fewer → one game moves the median.
- The two sides are compared in section 5.1.

**Output:** `pcd_sq1_groups` (360 groups, 190 eligible, 79% of games)

**Data dictionary**

| Column | Description |
|---|---|
| `group_id` | group name: genre \| year band \| price tier \| other languages |
| `genre_group` | genre of the group |
| `year_band` | year-band code of the group (as in `pcd_games_clean`) |
| `price_tier` | price-tier code of the group |
| `n_other_langs_bin` | other-languages code of the group |
| `n_zh` | number of games with Simplified Chinese |
| `n_no_zh` | number of games without Chinese |
| `median_reviews_zh` | median reviews of games with Chinese |
| `median_reviews_no_zh` | median reviews of games without Chinese |
| `eligible` | True if the group has >= 10 games on each side |

**First 3 rows**

| group_id | genre_group | year_band | price_tier | n_other_langs_bin | n_zh | n_no_zh | median_reviews_zh | median_reviews_no_zh | eligible |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|:---|
| Action \| <=2017 \| free \| 0 | Action | 1 | 1 | 1 | 9 | 350 | 65 | 103.5 | False |
| Action \| <=2017 \| free \| 1-4 | Action | 1 | 1 | 2 | 12 | 99 | 49 | 310 | True |
| Action \| <=2017 \| free \| 5+ | Action | 1 | 1 | 3 | 77 | 52 | 8617 | 1328 | True |

### 3.3 SQ2 groups: similar games, added Chinese after launch vs did not

- **Rule:** follow games with no Chinese in C to A; compare those that added Chinese (treated) with similar games that did not (control).
- **Reason for a control:** every game gains reviews over time anyway.
- **Games:** C filtered as in 3.1, no Chinese in C, still in A. Characteristics from C because: the state before adding Chinese.
- **Dropped:** 0 reviews in A because: delisted → -100% growth is not real.
- **Growth** = (reviews in A - reviews in C) / reviews in C.
- **Control** = added no Chinese and no major language. Games that added another major language are excluded because: own localisation push.
- **Group** = genre x year band because: only 510 games added Chinese → only the strongest confounders fit.
  - Year band in: control games grow +12% (<=2017) vs +77% (2022+); treated games are ~2 years newer.
  - Price tier out: little effect once the year is fixed; with it only 3 genres keep usable groups.
  - Other languages out: same mix in both arms.
- **Per arm:** number of games and median growth. Eligible = >= 10 games per side.
- The two arms are compared in section 5.2.

**Output:** `pcd_sq2_groups` (24 groups, 16 eligible, 90% of treated games)

**Data dictionary**

| Column | Description |
|---|---|
| `group_id_sq2` | group name: genre \| year band |
| `genre_group` | genre of the group |
| `year_band` | year-band code of the group (as in `pcd_games_clean`) |
| `n_treated` | number of games that added Simplified Chinese (510 in total) |
| `n_control` | number of games that added neither Chinese nor a major language |
| `median_growth_treated` | median review growth of the treated games |
| `median_growth_control` | median review growth of the control games |
| `eligible` | True if the group has >= 10 games on each side |

**First 3 rows**

| group_id_sq2 | genre_group | year_band | n_treated | n_control | median_growth_treated | median_growth_control | eligible |
|:---|:---|---:|---:|---:|---:|---:|:---|
| Action \| <=2017 | Action | 1 | 41 | 3897 | 0.171821 | 0.105263 | True |
| Action \| 2018-2019 | Action | 2 | 31 | 1971 | 0.175252 | 0.148148 | True |
| Action \| 2020-2021 | Action | 3 | 49 | 1800 | 0.285714 | 0.255479 | True |

### 3.4 Save the tables and check them

- Save: the three output tables are written to `data/processed/csv/`.
- Check: automatic tests on the tables; if a table is wrong or a number differs from the ones reported here, the notebook stops.

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
  studio with an English name and an English release (Black Myth: Wukong) is missed. Effect
  on the result is small: SQ1 gap +125% with no filter, +120% with it, +112% without the top 1% games (notebook 5.1b).
- Genre comes from user tags; snapshot A is from 2026-06-20, not today.

## Team and contributions

| Member | Role | Main contributions |
|---|---|---|
| Khanh Phung | Leader | |
| Hưng | Tech lead | |
| Phú | Data & EDA | |
| Chí Minh | SQ1 & testing | |
| Khúc | Bonus app & slides | |

## Use of AI tools
