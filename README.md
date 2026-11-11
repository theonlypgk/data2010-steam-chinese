# Simplified Chinese support and reach on Steam

DATA2010 Data Science Programming, final project.

**Main question.** Should a Steam game support Simplified Chinese, for which genres, and when?

| | Question | Data |
|---|---|---|
| SQ1 | How much larger is the reach of games that support Simplified Chinese, and in which genres? | snapshot A |
| SQ2 | Does adding Simplified Chinese after launch still increase reach, and in which genres? | snapshots A + C |
| SQ3 | For each genre: translate at launch, translate later, or not a priority? | results of SQ1 + SQ2 |

Reach = number of reviews (`positive + negative`). Every comparison is made inside a group
of similar games (same genre, release year, price tier and number of other languages).

## Reproduce everything

```bash
pip install -r requirements.txt
python run.py all        # or: make all
```

| Step | Command | Reads | Writes |
|---|---|---|---|
| Download + trim | `python run.py data` | Hugging Face (pinned commits) | `data/raw/`, `data/interim/*_trim.csv.gz` |
| Clean + build tables | `python run.py tables` | `data/interim/` | `data/processed/pcd_<table>.csv` and `.xlsx` |
| EDA, SQ1, SQ2, SQ3 | `python run.py eda` / `sq1` / `sq2` / `sq3` | `data/processed/*.csv` | `report/figures/`, result tables |
| Report | `python run.py report` | everything above | `report/report.md`, `report/report.pdf` |
| Tests | `python run.py test` | | |

Every processed table is saved twice in `data/processed/` with the prefix `pcd_`:
`pcd_<table>.xlsx` to open and check, `pcd_<table>.csv` for code. Later steps only ever
read the CSV files with `pandas.read_csv`.

The GitHub Actions workflow `pipeline` runs `test`, `data` and `tables` on a clean
machine and commits the outputs, so the tables in the repo are always produced by code.

## Repository layout

```
data/        raw/ (downloaded, not committed) · interim/ (trimmed snapshots) · processed/ (analysis tables) · README.md
scripts/     numbered pipeline steps, run in order by run.py
src/steamcn/ shared functions: paths, config, cleaning
notebooks/   exploratory notebooks, one per step
report/      report source, figures, individual reflections
app/         interactive dashboard (bonus)
slides/      presentation
docs/        data_spec.md (which table serves which question), decisions.md, QC logs
tests/       pytest tests for src/steamcn
```

All column names, file names and code are in English. No absolute paths: everything is
resolved from the repo root in `src/steamcn/paths.py`.

## Team and contributions

| Member | Role | Main contributions |
|---|---|---|
| | | |

## Use of AI tools

This project was built with AI coding agents (Claude) under human direction. Agents wrote
most of the code and first drafts; team members defined the questions and the analysis
design, checked every output against the data, and made all decisions. Quality-check logs
are in `docs/qc/`. Individual reflections were written by the members themselves.
