# Simplified Chinese support and reach on Steam

DATA2010 Data Science Programming, final project.

**Main question.** Should a Steam game support Simplified Chinese, for which genres, and when?

| | Question | Data |
|---|---|---|
| SQ1 | How much larger is the reach of games that support Simplified Chinese, and in which genres? | snapshot A |
| SQ2 | Does adding Simplified Chinese after launch still increase reach, and in which genres? | snapshots A + C |
| SQ3 | For each genre: translate at launch, translate later, or not a priority? | results of SQ1 + SQ2 |

Reach = number of reviews (`positive + negative`). Every comparison is made inside a group
of similar games, so that the gap is not simply "bigger games get translated more".

## Where to find the data

| I want to... | Go to |
|---|---|
| **look at** a table (Excel, Google Sheets) | `data/processed/xlsx/pcd_<table>.xlsx` |
| **read** a table **in code** | `data/processed/csv/pcd_<table>.csv` |
| know what each table and column means | `docs/data_spec.md`, or `pcd_data_dictionary` |
| get the original input files | `python run.py data`, or the release [raw-snapshots-v1](../../releases) |

The `.xlsx` and `.csv` files with the same name hold exactly the same data. Code always
reads the CSV version, for example:

```python
import pandas as pd
games = pd.read_csv("data/processed/csv/pcd_games_clean.csv")
```

| Table | One row is | Used for |
|---|---|---|
| `pcd_games_clean` | one game in snapshot A, after cleaning | EDA, SQ1 |
| `pcd_sq1_groups` | one group of similar games | SQ1 |
| `pcd_panel_ac` | one game present in both snapshots, with no Chinese in January 2024 | SQ2 |
| `pcd_sq2_groups` | one SQ2 group (genre x starting reach) | SQ2 |
| `pcd_cn_excluded` | one Chinese game that was removed, with the rule that matched | checking |
| `pcd_funnel` | one cleaning step, with the number of games left | report |
| `pcd_data_dictionary` | one column of the tables above | reference |

## Reproduce everything

```bash
pip install -r requirements.txt   # Python 3.12, exact versions
python run.py all                 # or: make all
```

| Step | Command | Script | Reads | Writes |
|---|---|---|---|---|
| Download | `python run.py data` | `scripts/00_download.py` | Hugging Face, pinned commits | `data/raw/` |
| Trim | (same command) | `scripts/01_trim.py` | `data/raw/` | `data/interim/*_trim.csv.gz` |
| Clean + build tables | `python run.py tables` | `scripts/02_build_tables.py` (logic in `src/steamcn/clean.py`) | `data/interim/` | `data/processed/csv/`, `data/processed/xlsx/` |
| EDA, SQ1, SQ2, SQ3 | `python run.py eda` / `sq1` / `sq2` / `sq3` | to be written | `data/processed/csv/` | `report/figures/`, results |
| Report | `python run.py report` | to be written | everything above | `report/report.pdf` |
| Tests | `python run.py test` | `tests/` | | |

Two independent re-runs give byte-identical CSV files. The GitHub Actions workflow
`pipeline` re-runs `test`, `data` and `tables` on a clean machine after every code change
and commits the outputs. Opening the repo in GitHub Codespaces uses `.devcontainer/`,
the same environment.

## Where each decision is in the code

Every fixed choice is in `src/steamcn/config.py`, next to a comment giving the reason;
`docs/decisions.md` lists them with a dated change log. Problems found in the real data are
marked `DATA ISSUE` in the code.

| Decision or data issue | Code |
|---|---|
| Which snapshots (pinned commits) | `config.py`, "DATA SOURCE" |
| Header of snapshot A merges two columns (`DiscountDLC count`) | `scripts/01_trim.py`, `read_header()` |
| Snapshot A prices are sale prices: use the list price | `config.py` `OPTIONAL_RAW_TO_CLEAN`; `clean.py` `add_features()` step 1 |
| Junk in language and tag cells (`[b]*[/b]`, HTML) | `clean.py` `_TAG_JUNK`, `parse_list()` |
| All Chinese games removed (4 rules) | `config.py` "CHINESE GAMES"; `clean.py` `add_features()` step 5 |
| Genre = first matching user tag | `config.py` `TAG_TO_GENRE`; `clean.py` `first_genre()` |
| Filters: Early Access, >= 10 reviews, >= 1 year old, Traditional-only | `config.py` "FILTERS"; `clean.py` `_base_filters()`, `build_games_clean()` |
| SQ1 groups use year bands | `config.py` `YEAR_BAND_BINS`; `clean.py` `build_games_clean()` |
| SQ2 treated / control / excluded | `config.py` `MAJOR_LANGS`; `clean.py` `build_panel_ac()` |
| SQ2 drops delisted games (0 reviews in A) | `clean.py` `build_panel_ac()` |
| SQ2 groups = genre x starting reach | `clean.py` `build_panel_ac()` |
| Byte-identical re-runs (versions, rounding, gzip, xlsx dates) | `requirements.txt`; `clean.py`; `01_trim.py`; `02_build_tables.py` |

## Limitations

- **Reach is measured by review counts.** Steam does not publish sales. Reviews from all
  languages are counted together, so Chinese-speaking players cannot be separated.
- **SQ1 shows an association, not a cause.** Games with Chinese are compared with similar
  games without it, but unmeasured differences remain: marketing, studio size (only partly
  captured by price), game quality.
- **SQ2 holds fewer things fixed than SQ1.** About 500 games added Chinese between the two
  snapshots, too few to split by five characteristics. SQ2 compares games of the same genre
  and the same starting reach only; release year, price and number of other languages are
  not held fixed, so part of a difference could come from them.
- **Exact date of a language addition is unknown.** We only know it happened between January
  2024 and June 2026. A big update or sale at the same time could also raise reviews.
- **Chinese games are identified by rules, not by a country field.** The dataset has no
  country of origin. Four rules (language pattern, Chinese characters, Chinese city, known
  company) catch most Chinese games, but some may be missed or wrongly caught;
  `pcd_cn_excluded` lists every removed game so this can be checked.
- **Genre comes from user tags.** A game's genre group is its most-voted matching tag, which
  may not match how the studio describes it.
- **Snapshot dates.** Snapshot A is from 2026-06-20 (the last CSV version of the dataset),
  not from today. Snapshot C prices have no discount information.

## Repository layout

```
data/        raw/ (downloaded, not committed) · interim/ (trimmed snapshots) ·
             processed/csv/ (for code) · processed/xlsx/ (to view) · README.md
scripts/     numbered pipeline steps, run in order by run.py
src/steamcn/ shared code: paths, config (all decisions), cleaning
notebooks/   exploratory notebooks
report/      report source, figures, individual reflections
app/         interactive dashboard (bonus)
slides/      presentation
docs/        data_spec.md, decisions.md, QC logs (docs/qc/)
tests/       pytest tests
```

All column names, file names and code are in English.

## Team and contributions

| Member | Role | Main contributions |
|---|---|---|
| | | |

## Use of AI tools

This project was built with AI coding agents (Claude) under human direction. Agents wrote
most of the code and first drafts; team members defined the questions and the analysis
design, checked every output against the data, and made all decisions. Quality-check logs
are in `docs/qc/`. Individual reflections were written by the members themselves.
