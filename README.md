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

The cleaned data is two tables, each saved whole in two formats:

| I want to... | Go to |
|---|---|
| **look at** a table (Excel, Google Sheets) | `data/processed/xlsx/pcd_<table>.xlsx` |
| **read** a table **in code** | `data/processed/csv/pcd_<table>.csv` |
| know what each column means | `docs/data_spec.md` |
| get the two original input files | notebook section A1, or the release [raw-snapshots-v1](../../releases/tag/raw-snapshots-v1) |

| Table | One row is | Used for |
|---|---|---|
| `pcd_sq1_games` | one game in snapshot A (2026), after cleaning: 44,765 games | EDA, SQ1 |
| `pcd_sq2_games` | one game present in both snapshots, with no Chinese in January 2024: 21,555 games | SQ2 |

```python
import pandas as pd
sq1_games = pd.read_csv("data/processed/csv/pcd_sq1_games.csv")
sq2_games = pd.read_csv("data/processed/csv/pcd_sq2_games.csv")
```

## Reproduce the project

The whole project is **one notebook**, `steam_chinese_analysis.ipynb`. It runs from scratch:
its only input is the two original CSV files (snapshots A and C), which it downloads at
pinned versions; every cleaning step, filter and table is done in code.

```bash
pip install -r requirements.txt     # Python 3.12, exact package versions
jupyter nbconvert --to notebook --execute steam_chinese_analysis.ipynb --output executed.ipynb
```

or open the notebook and choose *Run All*. Two runs give byte-identical CSV files. On
GitHub, the `pipeline` workflow (Actions tab) runs the notebook on a clean machine after
every change and commits the tables; GitHub Codespaces opens the repo with the same
environment (`.devcontainer/`). If the Hugging Face history is ever unavailable, the input
files are kept in the release [raw-snapshots-v1](../../releases/tag/raw-snapshots-v1).

| Notebook section | What it does | Output |
|---|---|---|
| Settings and decisions | every fixed choice, with its reason | |
| A1 Load | download the two input files, repair the header, keep 13 columns | `data/raw/` |
| A2 Clean | fix types, parse lists, add derived columns | |
| A3-A5 Select rows | filters; table for SQ1; table for SQ2 (join A and C) | |
| A6 What was removed | funnel and removed Chinese games, shown for checking | |
| A7 Save | write the two tables as csv and xlsx | `data/processed/` |
| A8 Checks | stop with an error if anything is wrong | |
| B1-B4 Analysis | EDA, SQ1, SQ2, SQ3 (B2 and B3 start with the group comparison) | `report/figures/` |

## Where each decision is in the notebook

Every fixed choice is in the **Settings and decisions** cell, next to a comment giving the
reason; `docs/decisions.md` lists them with a dated change log. The first line of every
code cell says what kind of step it is (LOAD DATA, DATA CLEANING, SELECT ROWS, AGGREGATE,
SAVE OUTPUTS, CHECKS), and problems found in the real data are marked `DATA ISSUE`.

| Decision or data issue | Notebook |
|---|---|
| Which snapshots (pinned commits) | Settings, "DATA SOURCE" |
| Header of snapshot A merges two columns (`DiscountDLC count`) | A1, `read_header()` |
| Snapshot A prices are sale prices: use the list price | Settings `OPTIONAL_RAW_TO_CLEAN`; A2 `add_features()` step 1 |
| Junk in language and tag cells (`[b]*[/b]`, HTML) | A2, `_TAG_JUNK`, `parse_list()` |
| All Chinese games removed (4 rules) | Settings "CHINESE GAMES"; A2 `add_features()` step 5 |
| Genre = first matching user tag | Settings `TAG_TO_GENRE`; A2 `first_genre()` |
| Filters: Early Access, >= 10 reviews, >= 1 year old, Traditional-only | Settings "FILTERS"; A3 `_base_filters()`; A4 |
| SQ1 groups use year bands | Settings `YEAR_BAND_BINS`; A4 `build_games_clean()`; B2 |
| SQ2 treated / control / excluded | Settings `MAJOR_LANGS`; A5 `build_panel_ac()` |
| SQ2 drops delisted games (0 reviews in A) | A5 `build_panel_ac()` |
| SQ2 groups = genre x starting reach | A5 `build_panel_ac()`; B3 |
| Byte-identical re-runs (versions, rounding, xlsx dates) | `requirements.txt`; rounding in A4-A5; A7 |

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
  country of origin. Four rules (language pattern; developers with Chinese-character names,
  Chinese-city names or known Chinese companies) catch most Chinese games, but a Chinese
  studio with an English name that is not on the list and ships English can be missed;
  section A6 of the notebook lists every removed game so this can be checked.
- **Genre comes from user tags.** A game's genre group is its most-voted matching tag, which
  may not match how the studio describes it.
- **Snapshot dates.** Snapshot A is from 2026-06-20 (the last CSV version of the dataset),
  not from today. Snapshot C prices have no discount information.

## Repository layout

```
steam_chinese_analysis.ipynb   THE project: all code, from the two input files to the analysis
requirements.txt               exact package versions
data/
  raw/              the two input CSV files (downloaded by the notebook, not committed)
  processed/csv/    the two cleaned tables, for code (pandas.read_csv)
  processed/xlsx/   the same two tables, to open and look at
  README.md         source, versions, columns, licence
docs/               data_spec.md (cleaning steps and columns), decisions.md (all choices), qc/ (check logs)
report/             report, figures, reflections, slides
```

`.github/` (automatic re-runs on GitHub) and `.devcontainer/` (Codespaces environment) are
configuration folders that GitHub requires at the top level.

## Team and contributions

| Member | Role | Main contributions |
|---|---|---|
| | | |

## Use of AI tools

This project was built with AI coding agents (Claude) under human direction. Agents wrote
most of the code and first drafts; team members defined the questions and the analysis
design, checked every output against the data, and made all decisions. Quality-check logs
are in `docs/qc/`. Individual reflections were written by the members themselves.
