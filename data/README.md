# Data

## Source

Steam Games Dataset by FronkonGames, taken from its Hugging Face repository
(`FronkonGames/steam-games-dataset`). Each row is one game on Steam.

| | Snapshot A ("current") | Snapshot C (January 2024) |
|---|---|---|
| Commit hash | `52ba62abfa707a2fa31f4d147c2777a9d9fbd2da` | `aefdeb1ff1a739b92ac5338682cc2610a0328505` |
| Commit date | 2026-06-20 (last commit that updated `games.csv`) | 2024-01-11 |
| Rows x columns (raw) | _T1_ | _T1_ |
| Used for | SQ1, SQ2 | SQ2 |

Licence: _T1: copy the licence stated on the dataset page and confirm it allows
redistributing derived tables._

Backup of the raw files: GitHub release `raw-snapshots-v1` of this repo (made by the
`archive-raw` workflow) holds `games_a.csv.gz`, `games_c.csv.gz` and their SHA-256 checksums.

## Files

| Folder | File | Committed | Made by |
|---|---|---|---|
| `raw/` | `games_a.csv`, `games_c.csv` (the two inputs) | no (too large for GitHub) | notebook, section A1 |
| `processed/csv/` | `pcd_sq1_games.csv`, `pcd_sq2_games.csv`: for code (`pandas.read_csv`) | yes | notebook, section A7 |
| `processed/xlsx/` | `pcd_sq1_games.xlsx`, `pcd_sq2_games.xlsx`: to open and look at | yes | notebook, section A7 |

## Columns read from the raw data

| Column | Raw name | Meaning |
|---|---|---|
| `app_id` | AppID | Steam application id |
| `name` | Name | Game title |
| `release_date` | Release date | Release date |
| `price` | Price | Price in USD on the snapshot day (sale price in A) |
| `discount_pct` | Discount | Discount running on the snapshot day; only in A (0 in C) |
| `supported_languages` | Supported languages | Interface / subtitle languages |
| `full_audio_languages` | Full audio languages | Voiced languages |
| `positive`, `negative` | Positive, Negative | Review counts |
| `developers`, `publishers` | Developers, Publishers | Studio names (used to identify Chinese games) |
| `genres` | Genres | Steam genres (includes "Early Access") |
| `tags` | Tags | User tags, ordered by votes |

The full description of both tables and every column is in `../docs/data_spec.md`.

## Known limitations

- Review counts cover all languages; reviews by Chinese-speaking players cannot be separated.
- The exact date a game added a language is unknown, only that it changed between C and A.
- Chinese games are identified by four rules (no country field exists); the notebook lists the removed ones.
- Snapshot A was taken during a sale; list prices are recovered from the discount column.
- In snapshot A the header merges "Discount" and "DLC count" into one name; the notebook splits it (`read_header()`).
