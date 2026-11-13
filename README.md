# Simplified Chinese support and reach on Steam

DATA2010 Data Science Programming, final project.

---

# I. How to use and rerun the project

**Repository**

```
steam_chinese_analysis.ipynb   all the code, from the two input files to the analysis
requirements.txt               exact package versions (Python 3.12)
data/raw/                      the two input files games_a.csv, games_c.csv (Git LFS)
data/processed/csv/            output tables, for code (pandas.read_csv)
data/processed/xlsx/           the same tables, to open and look at
report/                        report, figures, reflections, slides
.github/, .devcontainer/       automatic re-runs on GitHub; Codespaces environment
```

**Reproducibility settings**

Every file that decides whether a rerun gives the same output. Their locations are fixed:
Git and GitHub only read them there.

| File | What it fixes |
|---|---|
| `requirements.txt` | exact package versions (Python 3.12) |
| `steam_chinese_analysis.ipynb`, cell *Settings and decisions* | pinned dataset commits of snapshots A and C, every cleaning and filter choice |
| `.gitattributes` | `data/raw/*.csv filter=lfs diff=lfs merge=lfs -text`: the two input files are over GitHub's 100 MB file limit, so they are stored with Git LFS; a normal `git clone` downloads them |
| `.gitignore` | keeps temporary files (`executed.ipynb`, caches) out of the repo; `data/raw/` is not ignored, so the input files are committed |
| `.github/workflows/pipeline.yml` | reruns the notebook on a clean machine after every change; `lfs: true` in the checkout step gives it the real input files |
| `.github/workflows/archive-raw.yml` | backup of the input files as the release [raw-snapshots-v1](../../releases/tag/raw-snapshots-v1) (gzip + SHA-256) |
| `.devcontainer/devcontainer.json` | the same environment in GitHub Codespaces |

**Rerun everything from scratch**
- `pip install -r requirements.txt` (Python 3.12), or open the repo in GitHub Codespaces.
- Open `steam_chinese_analysis.ipynb` and choose *Run All*, or run
  `jupyter nbconvert --to notebook --execute steam_chinese_analysis.ipynb --output executed.ipynb`.
- The notebook reads the two input files from `data/raw/` and rewrites every output table.
- Two runs give byte-identical CSV files.
- On GitHub, the `pipeline` workflow reruns the notebook after every change and commits the
  tables if they changed.

**Use the outputs**
- To look at a table: open `data/processed/xlsx/pcd_<table>.xlsx`.
- To use a table in code: `pd.read_csv("data/processed/csv/pcd_<table>.csv")`.
- Each table and its columns are described in II.3 below.

---

# II. Data science life cycle

## 1. Business understanding

- **Context:** Chinese-speaking players are one of the largest player groups on Steam, but a
  translation costs money and time, so studios need to know when it pays off.
- **Main question:** should a Steam game support Simplified Chinese, for which genres, and when?
- **Reach** = number of reviews (`positive + negative`): Steam does not publish sales.

| | Question |
|---|---|
| SQ1 | How much larger is the reach of games that support Simplified Chinese, and in which genres? |
| SQ2 | Does adding Simplified Chinese after launch still increase reach, and in which genres? |
| SQ3 | For each genre: translate at launch, translate later, or not a priority? |

## 2. Data collection

- **Source:** Steam Games Dataset by FronkonGames (Hugging Face
  `FronkonGames/steam-games-dataset`), one row per game.
- **Two snapshots** of the same file, to see which games added Chinese over time (SQ2).
- **Pinned by commit hash**, so the data never changes even though the dataset is updated.
- **Backup:** release [raw-snapshots-v1](../../releases/tag/raw-snapshots-v1) (gzip + SHA-256).

| | Snapshot A ("now") | Snapshot C ("before") |
|---|---|---|
| Commit | `52ba62abfa707a2fa31f4d147c2777a9d9fbd2da` | `aefdeb1ff1a739b92ac5338682cc2610a0328505` |
| Date | 2026-06-20 (last version of `games.csv`) | 2024-01-11 |
| Raw rows | 125,855 | 85,103 |
| Used for | SQ1, SQ2 | SQ2 |

## 3. Data processing

### a. Clean data

**Strategy**

*1. Data assessment / profiling*
- Raw size: A has 125,855 rows, C has 85,103 rows, 40 columns each.
- Header of A: `DiscountDLC count` is one name over two value columns, so every later column
  is shifted; found by checking that language cells look like lists.
- Prices of A are sale prices (Hades 7.49 = 24.99 at -70%): A was taken during a Steam sale.
- Language and tag cells contain store-page junk (`[b]*[/b]`, HTML).

*2. Deduplication*
- Repeated `app_id`: only the first row is kept, so each game appears once.

*3. Structural error correction*
- Split the merged header back into `Discount` and `DLC count`.
- Rename columns to English snake_case; ids and review counts to integers, prices to numbers.
- Dates come as "Aug 1, 2023" or "Aug 2023": all converted to one date type.
- Price: list price recovered as `sale price / (1 - discount / 100)`, so tiers describe the
  game, not the sale.
- Junk removed from list cells, then cells parsed into clean lists of languages and tags.
- Tags standardised into 6 genre groups: the first matching tag wins (Steam orders by votes).
- Price, year and other languages encoded as ranks 1, 2, 3, ...: as text they sort in the
  wrong order ("10to20" before "5to10"); codes are never averaged; genre has no order, so it
  is not encoded.

*4. Handling missing values*
- No `app_id`: row dropped (the game cannot be identified).
- Missing review count or discount: set to 0 (Steam shows nothing when there is none).
- Unreadable date, no price, or no matching genre tag: game dropped, not imputed, because an
  invented value would put the game in a wrong comparison group.

*5. Outliers*
- Review counts are very skewed (a few hits have millions): kept, because they are real;
  later comparisons use medians, which they do not distort.
- Discount capped at 0-99%: a 100% discount would make the list price infinite.

*6. Irrelevant data*
- Only 13 of the 40 columns are read: the rest does not serve the questions.
- Chinese games removed, large or small: made for China, not translated into Chinese.
  - Chinese = Chinese without English (text or voice-over), or every developer is Chinese
    (Chinese-character name, mainland city in the name, known Chinese company).
  - Not "Chinese voice-over" alone: it would remove 4,233 Western games (Cyberpunk 2077).
  - Developers only, and all of them: publishers are often regional partners (bilibili for
    Core Keeper), and Western games list Chinese support studios (Ubisoft Shanghai, Far Cry).
- Early Access removed: unfinished games, their reviews behave differently.
- Fewer than 10 reviews removed: below that, reach is noise.
- Released less than 1 year before the snapshot removed: no time to collect reviews.
- Traditional-Chinese-only games removed: neither "with" nor "without" Simplified Chinese.

**Final output table:** `pcd_games_clean` (44,765 games, 14,078 with Simplified Chinese)

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

### b. SQ1: groups of similar games, with vs without Chinese

**Strategy**

*Why groups*
- Compare games with and without Chinese only inside groups of similar games: otherwise
  the gap partly comes from other differences (bigger games are translated more).

*Which variables form a group: genre x price tier x year band x other languages*
- Each affects reach and differs between games with and without Chinese (a confounder).
- Genre: audience size and amount of text differ by genre.
- Price tier: stands in for budget and studio size.
- Year band: older games had more time to collect reviews; bands, because single years leave
  only 44% of games in usable groups (76% with bands).
- Other languages: the strongest; games with Chinese have a median of 7 other languages,
  games without it 0.

*How each group is compared*
- Medians, not means: review counts are very skewed.
- Gap = median with Chinese / median without - 1.
- Eligible only with >= 10 games on each side: a median of fewer games moves too much.

**Final output table:** `pcd_sq1_groups` (360 groups, 178 eligible, 76% of games)

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
| `pct_diff` | gap: `median_reviews_zh / median_reviews_no_zh - 1` (0.5 = +50%) |
| `eligible` | True if the group has >= 10 games on each side |

**First 3 rows**

| group_id | genre_group | year_band | price_tier | n_other_langs_bin | n_zh | n_no_zh | median_reviews_zh | median_reviews_no_zh | pct_diff | eligible |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|---:|:---|
| Action \| <=2017 \| free \| 0 | Action | 1 | 1 | 1 | 6 | 348 | 54 | 103.5 | -0.478261 | False |
| Action \| <=2017 \| free \| 1-4 | Action | 1 | 1 | 2 | 11 | 99 | 45 | 310 | -0.854839 | True |
| Action \| <=2017 \| free \| 5+ | Action | 1 | 1 | 3 | 77 | 52 | 8617 | 1328 | 5.48871 | True |

### c. SQ2: groups of similar games, added Chinese after launch vs did not

**Strategy**

*Which games*
- Games with no Chinese in snapshot C that are still in snapshot A, followed over time.
- C is filtered exactly as in a.: the starting point is measured the same way.
- Game characteristics come from C: what the game looked like before adding Chinese.
- Games with 0 reviews in A are dropped: delisted, a growth of -100% is not real.

*Outcome and treatment*
- Growth = (reviews in A - reviews in C) / reviews in C.
- Treated = added Simplified Chinese; control = added neither Chinese nor a major language.
- Games that added another major language are excluded: a localisation push of their own.
- A control arm is needed: every game gains reviews over time anyway.

*Which variables form a group: genre x year band*
- Only 509 games added Chinese, so only the strongest confounders fit.
- Year band is in: control games from <=2017 grow +12%, from 2022+ +77%, and treated
  games are about 2 years newer.
- Price tier is out: little effect on growth once the year is fixed; with it, only 3 genres
  keep usable groups.
- Other languages are out: treated and control have almost the same mix.

*How each group is compared*
- Uplift = median growth treated - median growth control.
- Eligible only with >= 10 games on each side, as in SQ1.

**Final output table:** `pcd_sq2_groups` (24 groups, 16 eligible, 90% of treated games)

**Data dictionary**

| Column | Description |
|---|---|
| `group_id_sq2` | group name: genre \| year band |
| `genre_group` | genre of the group |
| `year_band` | year-band code of the group (as in `pcd_games_clean`) |
| `n_treated` | number of games that added Simplified Chinese (509 in total) |
| `n_control` | number of games that added neither Chinese nor a major language |
| `median_growth_treated` | median review growth of the treated games |
| `median_growth_control` | median review growth of the control games |
| `uplift_pts` | `median_growth_treated - median_growth_control` (0.1 = +10 points) |
| `eligible` | True if the group has >= 10 games on each side |

**First 3 rows**

| group_id_sq2 | genre_group | year_band | n_treated | n_control | median_growth_treated | median_growth_control | uplift_pts | eligible |
|:---|:---|---:|---:|---:|---:|---:|---:|:---|
| Action \| <=2017 | Action | 1 | 41 | 3891 | 0.171821 | 0.105263 | 0.066558 | True |
| Action \| 2018-2019 | Action | 2 | 31 | 1960 | 0.175252 | 0.147244 | 0.028008 | True |
| Action \| 2020-2021 | Action | 3 | 49 | 1792 | 0.285714 | 0.255392 | 0.030322 | True |

## 4. Data analysis / EDA

## 5. Data modelling

## 6. Model deployment

---

## Limitations

- Reach = reviews from all languages: Chinese-speaking players cannot be separated.
- SQ1 is an association, not a cause: marketing, studio size and quality are not measured.
- SQ2 does not hold price fixed: part of a difference could come from price.
- The date a language was added is unknown, only that it was between 2024-01 and 2026-06.
- Chinese games are found by rules: a Chinese studio with an English name can be missed.
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
