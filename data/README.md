# Data

## Source

Steam Games Dataset by FronkonGames, taken from its Hugging Face repository
(`FronkonGames/steam-games-dataset`). Each row is one game on Steam.

| | Snapshot A ("current") | Snapshot C (January 2024) |
|---|---|---|
| Commit hash | `52ba62abfa707a2fa31f4d147c2777a9d9fbd2da` | `aefdeb1ff1a739b92ac5338682cc2610a0328505` |
| Commit date | 2026-06-20 (last commit that updated `games.csv`) | 2024-01-11 |
| Rows x columns (raw) | _T1_ | _T1_ |
| Rows x columns (trimmed) | _T1_ | _T1_ |
| Used for | SQ1, SQ2 | SQ2 |

Licence: _T1: copy the licence stated on the dataset page and confirm it allows
redistributing the trimmed files._

## Files

| Folder | File | Committed | Made by |
|---|---|---|---|
| `raw/` | `games_a.csv`, `games_c.csv` | no (too large for GitHub) | `scripts/00_download.py` |
| `interim/` | `a_trim.csv.gz`, `c_trim.csv.gz` | yes | `scripts/01_trim.py` |
| `processed/` | `pcd_games_clean`, `pcd_sq1_groups`, `pcd_panel_ac`, `pcd_sq2_groups`, `pcd_funnel`, `pcd_data_dictionary` (each as `.csv` and `.xlsx`) | yes | `scripts/02_build_tables.py` |

## Columns kept from the raw data

| Column | Raw name | Meaning |
|---|---|---|
| `app_id` | AppID | Steam application id |
| `name` | Name | Game title |
| `release_date` | Release date | Release date |
| `price` | Price | Price in USD |
| `supported_languages` | Supported languages | Interface / subtitle languages |
| `full_audio_languages` | Full audio languages | Voiced languages |
| `positive`, `negative` | Positive, Negative | Review counts |
| `genres` | Genres | Steam genres (includes "Early Access") |
| `tags` | Tags | User tags, ordered by votes |

The full description of every processed table and column is in `../docs/data_spec.md`
and in `processed/data_dictionary.csv`.

## Known limitations

- Review counts cover all languages; reviews by Chinese-speaking players cannot be separated.
- The exact date a game added a language is unknown, only that it changed between C and A.
- Games by Chinese publishers are identified by a proxy (Chinese audio, or Chinese without English).
