"""Step 2 (task T1): keep only the columns the project uses and give them English
snake_case names.

Input : data/raw/games_a.csv, data/raw/games_c.csv
Output: data/interim/a_trim.csv.gz, data/interim/c_trim.csv.gz (committed, small enough)
"""
import csv

import pandas as pd

import _bootstrap  # noqa: F401  (adds src/ to the import path)
from steamcn import config as cfg
from steamcn import paths


def read_header(raw_path) -> list[str]:
    """Read the header row and repair a known defect of this dataset.

    Some versions write "DiscountDLC count" as ONE header name while every data row
    holds TWO values (discount, DLC count). Without the fix every column after it is
    shifted by one, e.g. "Supported languages" would hold the game description.
    """
    with open(raw_path, newline="", encoding="utf-8") as f:
        header = next(csv.reader(f))
    fixed = []
    for name in header:
        if name == "DiscountDLC count":
            fixed += ["Discount", "DLC count"]
        else:
            fixed.append(name)
    return fixed


def trim(raw_path, out_path) -> None:
    names = read_header(raw_path)
    missing = [c for c in cfg.RAW_TO_CLEAN if c not in names]
    if missing:
        raise SystemExit(f"{raw_path.name}: columns not found: {missing}\nHeader: {names}")

    # Read with the repaired header (skip the original header row) and only the
    # columns we need, everything as text first; types are set during cleaning.
    optional = [c for c in cfg.OPTIONAL_RAW_TO_CLEAN if c in names]
    raw = pd.read_csv(
        raw_path,
        names=names,
        header=None,
        skiprows=1,
        usecols=list(cfg.RAW_TO_CLEAN) + optional,
        dtype=str,
        keep_default_na=False,
        na_values=[""],
        engine="c",
    )

    # Sanity check that the header repair worked: languages must look like lists.
    langs = raw["Supported languages"].dropna()
    share_list_like = langs.str.startswith("[").mean() if len(langs) else 0
    if share_list_like < 0.9:
        raise SystemExit(
            f"{raw_path.name}: only {share_list_like:.0%} of 'Supported languages' look like "
            "lists; the columns are probably shifted. Check read_header()."
        )

    out = raw[list(cfg.RAW_TO_CLEAN)].rename(columns=cfg.RAW_TO_CLEAN)
    # Optional columns: copy when the snapshot has them, otherwise fill with 0.
    for raw_name, clean_name in cfg.OPTIONAL_RAW_TO_CLEAN.items():
        out[clean_name] = raw[raw_name] if raw_name in raw.columns else "0"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # mtime=0 keeps the gzip header free of the run time, so re-runs give identical bytes.
    out.to_csv(out_path, index=False, compression={"method": "gzip", "mtime": 0})
    print(f"{out_path.name}: {len(out):,} rows x {out.shape[1]} columns")


if __name__ == "__main__":
    trim(paths.RAW / "games_a.csv", paths.A_TRIM)
    trim(paths.RAW / "games_c.csv", paths.C_TRIM)
