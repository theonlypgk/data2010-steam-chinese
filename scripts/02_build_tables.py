"""Step 3 (task T3): clean both snapshots and build the analysis tables.

Input : data/interim/a_trim.csv.gz, data/interim/c_trim.csv.gz
Output: for every table below, two files in data/processed/
          pcd_<table>.xlsx  -> for people to open and check
          pcd_<table>.csv   -> for code: later steps read it with pandas.read_csv

  table            one row is                                  used by
  games_clean      one game in snapshot A                      EDA, SQ1
  sq1_groups       one group of similar games                  SQ1
  panel_ac         one game in A and C, no Chinese in C        SQ2
  sq2_groups       one SQ2 group of similar games              SQ2
  funnel           one filter step                             report (data cleaning)
  data_dictionary  one column of the tables above              reference

See docs/data_spec.md for every column and rule.
"""
from datetime import datetime

import pandas as pd

import _bootstrap  # noqa: F401  (adds src/ to the import path)
from steamcn import clean
from steamcn import config as cfg
from steamcn import paths


FIXED_DATE = datetime(2026, 1, 1)


def main() -> None:
    # 1. Read the trimmed snapshots produced by scripts/01_trim.py.
    trim_a = pd.read_csv(paths.A_TRIM, dtype=str, keep_default_na=False, na_values=[""])
    trim_c = pd.read_csv(paths.C_TRIM, dtype=str, keep_default_na=False, na_values=[""])
    print(f"read a_trim: {len(trim_a):,} rows, c_trim: {len(trim_c):,} rows")

    # 2. Clean, derive columns, filter and aggregate (all logic is in src/steamcn/clean.py).
    tables = clean.build_all(trim_a, trim_c, cfg.SNAPSHOT_DATE_A, cfg.SNAPSHOT_DATE_C)

    # 3. Save every table as CSV (for code) and XLSX (for people), same name, prefix pcd_.
    paths.PROCESSED.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(paths.table_csv(name), index=False)
        with pd.ExcelWriter(paths.table_xlsx(name), engine="openpyxl") as writer:
            table.to_excel(writer, index=False, sheet_name=name[:31])
            # Fixed document dates: the xlsx metadata does not change between runs.
            writer.book.properties.created = FIXED_DATE
            writer.book.properties.modified = FIXED_DATE
        print(f"pcd_{name}: {len(table):,} rows x {table.shape[1]} columns (.csv + .xlsx)")

    # 4. Print the funnel so the effect of each filter is visible in the run log.
    print()
    print(tables["funnel"].to_string(index=False))


if __name__ == "__main__":
    main()
