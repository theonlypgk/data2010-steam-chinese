"""The raw header of snapshot A merges two columns ("DiscountDLC count");
check that 01_trim.py splits it so later columns are not shifted."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("trim", ROOT / "scripts" / "01_trim.py")
trim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trim)

HEADER_A = ("AppID,Name,Release date,Estimated owners,Peak CCU,Required age,Price,DiscountDLC count,"
            "About the game,Supported languages,Full audio languages,Reviews,Header image,Website,"
            "Support url,Support email,Windows,Mac,Linux,Metacritic score,Metacritic url,User score,"
            "Positive,Negative,Score rank,Achievements,Recommendations,Notes,Average playtime forever,"
            "Average playtime two weeks,Median playtime forever,Median playtime two weeks,Developers,"
            "Publishers,Categories,Genres,Tags,Screenshots,Movies")
ROW_A = ('10,"Test Game","Aug 1, 2023","0 - 0",0,0,9.99,0,2,"About, with comma",'
         '"[\'English\', \'Simplified Chinese\']","[]","","img","","","",True,False,False,0,"",0,'
         '120,30,"",0,0,"",0,0,0,0,"Dev","Pub","Single-player","Indie,RPG","RPG,Indie","",""')


def test_trim_repairs_merged_header(tmp_path):
    raw = tmp_path / "raw.csv"
    raw.write_text(HEADER_A + "\n" + ROW_A + "\n", encoding="utf-8")
    out = tmp_path / "trim.csv.gz"
    trim.trim(raw, out)
    import pandas as pd
    df = pd.read_csv(out)
    row = df.iloc[0]
    assert row["supported_languages"] == "['English', 'Simplified Chinese']"
    assert (row["positive"], row["negative"]) == (120, 30)
    assert row["tags"] == "RPG,Indie"
    assert row["price"] == 9.99
    assert row["discount_pct"] == 0        # the "Discount" value of the row
