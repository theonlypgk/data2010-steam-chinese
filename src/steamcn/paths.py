"""All paths are built from the repo root, so nothing depends on the machine."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
RAW = DATA / "raw"
INTERIM = DATA / "interim"
PROCESSED = DATA / "processed"
FIGURES = ROOT / "report" / "figures"

A_TRIM = INTERIM / "a_trim.csv.gz"
C_TRIM = INTERIM / "c_trim.csv.gz"

# Every processed table is saved twice, with the prefix "pcd_" (processed):
#   pcd_<table>.xlsx  for people to open and check
#   pcd_<table>.csv   for code: every later step reads it with pandas.read_csv
PREFIX = "pcd_"


def table_csv(name: str) -> Path:
    return PROCESSED / f"{PREFIX}{name}.csv"


def table_xlsx(name: str) -> Path:
    return PROCESSED / f"{PREFIX}{name}.xlsx"


GAMES_CLEAN = table_csv("games_clean")
SQ1_GROUPS = table_csv("sq1_groups")
PANEL_AC = table_csv("panel_ac")
SQ2_GROUPS = table_csv("sq2_groups")
FUNNEL = table_csv("funnel")
DATA_DICTIONARY = table_csv("data_dictionary")
