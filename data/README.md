# Data

## Source

- **Dataset:** Steam Games Dataset by FronkonGames, one row per game on Steam.
- **Link:** https://huggingface.co/datasets/FronkonGames/steam-games-dataset (file `games.csv`)
- **License:** MIT (as stated on the dataset page).
- **Two snapshots** of the same file because: SQ2 needs to see which games added Chinese over time.

| File | Snapshot | Dataset commit | Rows | Columns | Size |
|---|---|---|---:|---:|---:|
| `raw/games_a.csv` | A, 2026-06-20 ("now") | `52ba62abfa707a2fa31f4d147c2777a9d9fbd2da` | 125,855 | 40 | 401 MB |
| `raw/games_c.csv` | C, 2024-01-11 ("before") | `aefdeb1ff1a739b92ac5338682cc2610a0328505` | 85,103 | 39 | 257 MB |

- The files are larger than GitHub's 100 MB limit → stored with Git LFS (`git lfs pull` downloads them).
- Snapshot C has no `Discount` column.

## Variables

The 13 columns the project reads (the other 27 are not used):

| Raw column | Name in the code | Meaning |
|---|---|---|
| `AppID` | `app_id` | Steam id of the game |
| `Name` | `name` | title |
| `Release date` | `release_date` | release date |
| `Price` | `price` | price in USD at the snapshot |
| `Discount` | `discount_pct` | sale discount in % (snapshot A only) |
| `Supported languages` | `supported_languages` | languages with text |
| `Full audio languages` | `full_audio_languages` | languages with voice-over |
| `Positive` | `positive` | number of positive reviews |
| `Negative` | `negative` | number of negative reviews |
| `Developers` | `developers` | developer names |
| `Publishers` | `publishers` | publisher names |
| `Genres` | `genres` | Steam genres |
| `Tags` | `tags` | user tags, ordered by votes |

Not used: Estimated owners, Peak CCU, Required age, DLC count, About the game, Reviews, Header
image, Website, Support url, Support email, Windows, Mac, Linux, Metacritic score, Metacritic
url, User score, Score rank, Achievements, Recommendations, Notes, Average playtime forever,
Average playtime two weeks, Median playtime forever, Median playtime two weeks, Categories,
Screenshots, Movies.

## Known problems in the raw files

- Header of snapshot A merges two names (`DiscountDLC count`) → the notebook splits it back.
- Prices in snapshot A are sale prices → the notebook recovers the list price.
- Language and tag cells contain store-page junk (`[b]*[/b]`, HTML) → removed.

## Output tables (`processed/`)

Written by `scripts/steam_chinese_analysis.ipynb` as `csv/pcd_<table>.csv`; never edited by hand.
`xlsx/pcd_<table>.xlsx` is a copy of the same tables, only to open and look at.

| Table | One row per | Rows |
|---|---|---:|
| `pcd_games_clean` | game of snapshot A after cleaning | 45,445 |
| `pcd_sq1_groups` | SQ1 group of similar games | 360 |
| `pcd_sq2_groups` | SQ2 group of similar games | 24 |

Columns of each table: see the main [README](../README.md), section II.3.
