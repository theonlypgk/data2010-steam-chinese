# Simplified Chinese support and reach on Steam

DATA2010 Data Science Programming, final project.

---

# I. How to use and rerun the project

**Repository**

```
steam_chinese_analysis.ipynb   all the code, from the two input files to the analysis
requirements.txt               exact package versions (Python 3.12)
data/raw/                      the two input files (downloaded by the notebook, not committed)
data/processed/csv/            output tables, for code (pandas.read_csv)
data/processed/xlsx/           the same tables, to open and look at
report/                        report, figures, reflections, slides
.github/, .devcontainer/       automatic re-runs on GitHub; Codespaces environment
```

**Rerun everything from scratch**
- `pip install -r requirements.txt` (Python 3.12), or open the repo in GitHub Codespaces.
- Open `steam_chinese_analysis.ipynb` and choose *Run All*, or run
  `jupyter nbconvert --to notebook --execute steam_chinese_analysis.ipynb --output executed.ipynb`.
- The notebook downloads the two input files itself and rewrites every output table.
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
- Read only 13 of the 40 columns, with English names: the rest is not needed.
- Clean A and C in exactly the same way, so a game looks the same in both snapshots.
- Repair the header of A (`DiscountDLC count` is one name for two columns): otherwise every
  later column is shifted by one.
- Use the list price, `sale price / (1 - discount / 100)`: A was taken during a Steam sale.
- Remove store-page junk (`[b]*[/b]`, HTML) from language and tag cells before parsing them.
- Drop rows without an id or with a repeated id; unreadable dates become missing.
- Genre = first user tag found in the genre map: Steam orders tags by votes.
- Remove all Chinese games, large or small: they are made for China, not translated into Chinese.
- Chinese game = Chinese without English (text or voice-over), or every developer is Chinese
  (Chinese-character name, mainland city in the name, or known Chinese company).
- Chinese voice-over alone is not a rule: it would remove 4,233 Western games (Cyberpunk 2077).
- Developers only, all of them: publishers are often regional partners (bilibili for Core
  Keeper), and Western games list Chinese support studios (Ubisoft Shanghai on Far Cry).
- Drop Early Access: unfinished games, their reviews behave differently.
- Keep >= 10 reviews: below that, reach is noise.
- Keep games released >= 1 year before the snapshot: every game had time to collect reviews.
- Keep games with a genre, price and year: needed to form comparison groups.
- Drop Traditional-Chinese-only games: neither "with Simplified Chinese" nor "without Chinese".
- Encode price tier, year band and other-language bin as ranks 1, 2, 3, ...: as text they sort
  in the wrong order ("10to20" before "5to10").
- Codes are ranks, not amounts: never averaged. Genre is not encoded: it has no order.

**In code** (notebook Step 1)
- 1.1 `download_snapshots`, `read_header`, `load_snapshot`: download, repair the header, read.
- 1.2 `parse_list`, `first_genre`, `split_developers`, `add_features`: clean and add columns.
- 1.3 `apply_filters`, `base_filters`: the filters, logged in a funnel.
- 1.4 `build_games_clean`: final rows and columns.
- 1.5: shows the funnel and the removed Chinese games (2,862 with >= 10 reviews), for checking.

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

### b. SQ1: groups of similar games, with vs without Chinese

**Strategy**
- Compare games with and without Chinese only inside groups of similar games: otherwise the
  gap would partly come from other differences (bigger games are translated more).
- Group = genre x price tier x year band x number of other languages: each of these affects
  reach and differs between the two sides.
- Genre: genres differ in audience size and amount of text.
- Price tier: stands in for budget and studio size.
- Year band: older games had more time to collect reviews; bands, because single years leave
  only 44% of games in usable groups (76% with bands).
- Other languages: the strongest; games with Chinese have a median of 7 other languages,
  games without it 0.
- Medians, not means: review counts are very skewed.
- Gap = median with Chinese / median without - 1.
- A group is eligible only with >= 10 games on each side: a median of fewer moves too much.

**In code** (notebook Step 2)
- `add_sq1_group`: gives every game its readable group name.
- `build_sq1_groups`: counts, medians, gap and eligibility per group.

**Final output table:** `pcd_sq1_groups` (360 groups, 178 eligible, 76% of games)

**Data dictionary**

| Column | Description |
|---|---|
| `group_id` | group name, e.g. `Action | <=2017 | lt5 | 5+` |
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

### c. SQ2: groups of similar games, added Chinese after launch vs did not

**Strategy**
- Follow the same games over time: games with no Chinese in C that are still in A.
- Filter C exactly as in a.: the starting point is measured the same way.
- Take game characteristics from C: what the game looked like before adding Chinese.
- Drop games with 0 reviews in A: delisted, a growth of -100% is not real.
- Growth = (reviews in A - reviews in C) / reviews in C.
- Treated = added Simplified Chinese; control = added neither Chinese nor a major language.
- Major language added = own localisation push, so not a clean "did nothing": excluded.
- A control arm is needed: every game gains reviews over time anyway.
- Group = genre x year band: only 509 games added Chinese, so only the strongest confounders.
- Year band is in: control games from <=2017 grow +12%, from 2022+ +77%, and treated games
  are about 2 years newer.
- Price tier is out: little effect on growth once the year is fixed; with it, only 3 genres
  keep usable groups.
- Other languages are out: treated and control have almost the same mix.
- Uplift = median growth treated - median growth control; same >= 10 per side rule.

**In code** (notebook Step 3)
- `build_sq2_panel`: joins C and A, computes growth and the arm (one row per game, not saved).
- `add_sq2_group`, `build_sq2_groups`: group name, counts, medians, uplift and eligibility.

**Final output table:** `pcd_sq2_groups` (24 groups, 16 eligible, 90% of treated games)

**Data dictionary**

| Column | Description |
|---|---|
| `group_id_sq2` | group name, e.g. `Action | <=2017` |
| `genre_group` | genre of the group |
| `year_band` | year-band code of the group (as in `pcd_games_clean`) |
| `n_treated` | number of games that added Simplified Chinese (509 in total) |
| `n_control` | number of games that added neither Chinese nor a major language |
| `median_growth_treated` | median review growth of the treated games |
| `median_growth_control` | median review growth of the control games |
| `uplift_pts` | `median_growth_treated - median_growth_control` (0.1 = +10 points) |
| `eligible` | True if the group has >= 10 games on each side |

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
