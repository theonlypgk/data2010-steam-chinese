# Overnight run, 12 Nov 2026: what was done and what to check

Work done by Claude (AI agent) on request of the team leader (kp). Nothing that existed
before was deleted. Everything below is in the git history of this repo.

## Results

Data handling (task T3) is done. All tables are built by code from two pinned snapshots
of the Steam Games Dataset; every table is in `data/processed/` as `pcd_<table>.xlsx`
(to open) and `pcd_<table>.csv` (for code).

| Table | Rows | Serves |
|---|---|---|
| `pcd_games_clean` | 45,307 games (14,535 with Simplified Chinese) | EDA, SQ1 |
| `pcd_sq1_groups` | 360 groups, 191 eligible (cover 36,858 games) | SQ1 |
| `pcd_panel_ac` | 21,623 games: 511 treated, 20,870 control, 242 excluded | SQ2 |
| `pcd_sq2_groups` | 18 groups, 14 eligible (cover 480 treated games) | SQ2 |
| `pcd_funnel` | 18 filter steps | data cleaning section of the report |
| `pcd_data_dictionary` | 38 column descriptions | reference |

Reproducibility check: GitHub Actions (clean machine) and a separate local rebuild produce
byte-identical CSV files.

## Data source

| | Snapshot A | Snapshot C |
|---|---|---|
| Hugging Face commit | `52ba62ab` (2026-06-20) | `aefdeb1f` (2024-01-11) |
| Raw rows | 125,855 | 85,103 |

Snapshot A is the last commit that updated `games.csv`. Later commits (up to 2026-11-08)
only update `games.json` (1 GB); see "To decide" below.

## Problems found in the real data, and fixes

1. **Merged header in snapshot A.** The header says `DiscountDLC count` while rows hold two
   values; every later column would be shifted. `scripts/01_trim.py` splits the name and
   checks that `Supported languages` looks like a list.
2. **Sale prices.** Snapshot A was taken during a sale (Hades 7.49 = 24.99 at -70%).
   `price` is now the list price, recovered from the `Discount` column (kept as `discount_pct`).
3. **Chinese-publisher proxy removed Western games.** "Chinese voice-over" alone removed
   4,233 games with >= 10 reviews such as Cyberpunk 2077, The Witcher 3, Hollow Knight,
   Dota 2. New rule: Chinese without English, in the text or in the voice-over.
4. **Groups too small.** SQ1 with single years: eligible groups covered 47% of games -> year
   bands (81%). SQ2 with five dimensions: 7 eligible groups, 2 genres -> genre x initial
   reach: 14 eligible groups, 6 genres.
5. **Delisted games.** 40 games had 0 reviews in A (growth -100%): dropped from the SQ2 panel.
6. **Reproducibility.** A codespace on Python 3.14 gave last-digit float differences.
   Fixed with exact package versions (Python 3.12), rounded float columns, gzip files without
   a timestamp and fixed xlsx metadata dates.

All analysis decisions are in `docs/decisions.md` (change log at the bottom).

## To check or decide (team leader)

- [ ] Confirm the three decisions marked "to be confirmed by kp" in `docs/decisions.md`
      (publisher proxy, SQ1 year bands, SQ2 genre x reach).
- [ ] Publisher proxy now keeps big Chinese games that also ship English (e.g. Black Myth:
      Wukong). Keep, or add a manual exclusion list?
- [ ] Snapshot A is June 2026. Keep it, or switch to `games.json` (Nov 2026, 1 GB, slower)?
- [ ] Review the tag -> genre map in `src/steamcn/config.py` (`TAG_TO_GENRE`, draft).
- [ ] Review the "major languages" list for the SQ2 control group (`MAJOR_LANGS`).
- [ ] Spot-check 20 rows of `pcd_games_clean.xlsx` against Steam (T3 Human QC).
- [ ] Invite the 4 members as collaborators (Settings -> Collaborators).
- [ ] SQ2 does not hold year, price or other languages fixed: state as a limitation.

## What was created or changed outside the code

- GitHub repo `theonlypgk/data2010-steam-chinese` (public), created in kp's browser.
- Claude GitHub app installed on this repo only (needed to push from the agent session).
- A GitHub Codespace on this repo, used to run the pipeline once; it stops by itself when
  idle and uses the free monthly quota.
- Google Doc master plan: task tabs grouped into 6.1 Before code, 6.2 Data handling,
  6.3 Analysis, 6.4 After code; references to CLAUDE.md removed; outputs renamed to `pcd_`.

## Update, 12 Nov 2026 morning (after kp's review)

- **All Chinese games removed, large or small** (kp's decision). Four rules in
  `config.py` ("CHINESE GAMES"): Chinese without English; or every developer is Chinese by
  name in Chinese characters, mainland-city name, or known company. Removed games, with the
  rule that matched, are in `pcd_cn_excluded` (2,862 games with >= 10 reviews in A).
  A first version also looked at publishers and at any single developer; it removed Far Cry,
  Call of Duty, Core Keeper and Sekiro by mistake, so it was narrowed.
- **Outputs split**: `data/processed/xlsx/` to view, `data/processed/csv/` for code (moved
  with `git mv`, nothing deleted).
- **Raw snapshots archived** as release `raw-snapshots-v1` (made by the `archive-raw`
  workflow, with SHA-256 checksums).
- **README**: where to find the data, where each decision is in the code, Limitations.
- **Comments**: every fixed choice in `config.py` has its reason; real-data problems are
  marked `DATA ISSUE` in the code.
- Snapshot A stays at 2026-06-20 (kp's decision).
