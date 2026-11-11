import numpy as np
import pandas as pd

from steamcn import clean
from steamcn import config as cfg


def test_parse_list_handles_messy_cells():
    assert clean.parse_list("['English', 'Simplified Chinese']") == ["English", "Simplified Chinese"]
    assert clean.parse_list("['English[b]*[/b]', 'French']") == ["English", "French"]
    assert clean.parse_list("Indie,Casual, RPG") == ["Indie", "Casual", "RPG"]
    assert clean.parse_list(np.nan) == []
    assert clean.parse_list("[]") == []


def test_first_genre_takes_first_matching_tag():
    assert clean.first_genre(["Indie", "RPG", "Action"]) == "RPG"
    assert clean.first_genre(["Indie", "Simulation"]) is None


def _row(app_id, langs, pos, neg=0, tags="RPG,Indie", price=14.99, date="Mar 5, 2021",
         audio="[]", genres="Indie,RPG", name=None):
    return {
        "app_id": app_id, "name": name or f"game {app_id}", "release_date": date, "price": price,
        "supported_languages": str(langs), "full_audio_languages": audio,
        "positive": pos, "negative": neg, "genres": genres, "tags": tags,
    }


def _snapshots():
    en, zh, tw, fr = "English", cfg.ZH_SIMPLIFIED, cfg.ZH_TRADITIONAL, "French"
    c = pd.DataFrame([
        _row(1, [en], 100),                 # adds only zh later  -> treated
        _row(2, [en], 200),                 # adds nothing        -> control
        _row(3, [en], 300),                 # adds French (major) -> excluded
        _row(4, [en, zh], 400),             # already has zh in C -> not in panel
        _row(5, [en], 5),                   # too few reviews
        _row(6, [en], 50, genres="Indie,Early Access"),
        _row(7, [zh], 500),                 # Chinese-publisher proxy (zh, no English)
        _row(8, [en], 80, tags="Simulation,Indie"),   # no genre group
        _row(11, [en, zh], 90, audio="['English', 'Simplified Chinese']"),  # Western game with zh voice
        _row(13, [en], 50),                 # 0 reviews in A (delisted) -> dropped from panel
    ])
    a = pd.DataFrame([
        _row(1, [en, zh], 300),
        _row(2, [en], 240),
        _row(3, [en, fr], 600),
        _row(4, [en, zh], 800),
        _row(5, [en], 6),
        _row(6, [en], 90, genres="Indie,Early Access"),
        _row(7, [zh], 900),
        _row(8, [en], 100, tags="Simulation,Indie"),
        _row(9, [en, tw], 700),             # Traditional only -> dropped from games_clean
        _row(10, [en, zh, fr], 60, price=0.0, tags="Puzzle"),
        _row(11, [en, zh], 90, audio="['English', 'Simplified Chinese']"),
        _row(12, [zh], 80, audio="['Simplified Chinese']"),  # Chinese-only -> proxy
        _row(13, [en], 0),
    ])
    a["discount_pct"] = "0"
    a.loc[a["app_id"] == 2, ["price", "discount_pct"]] = [4.49, "70"]   # sale price
    return a, c


def test_games_clean_filters_and_columns():
    a, c = _snapshots()
    t = clean.build_all(a, c, "2025-11-01", "2024-01-31")
    g = t["games_clean"]
    assert sorted(g["app_id"]) == [1, 2, 3, 4, 10, 11]     # 11 kept: English + zh voice
    assert g.set_index("app_id").loc[2, "price"] == 14.97   # 4.49 at -70%
    assert g.set_index("app_id").loc[2, "price_tier"] == "10to20"
    assert g.set_index("app_id").loc[1, "has_zh"] == 1
    assert g.set_index("app_id").loc[2, "has_zh"] == 0
    assert g.set_index("app_id").loc[10, "price_tier"] == "free"
    assert g.set_index("app_id").loc[10, "n_other_langs_bin"] == "1-4"
    assert g.set_index("app_id").loc[1, "group_id"] == "RPG | 2020-2021 | 10to20 | 0"
    assert all(col == col.lower() for col in g.columns)


def test_panel_arms_and_growth():
    a, c = _snapshots()
    p = clean.build_all(a, c, "2025-11-01", "2024-01-31")["panel_ac"].set_index("app_id")
    assert sorted(p.index) == [1, 2, 3]     # 4 and 11 already had zh in C
    assert p.loc[1, "arm"] == "treated" and p.loc[1, "added_only_zh"] == 1
    assert p.loc[2, "arm"] == "control"
    assert p.loc[3, "arm"] == "excluded"
    assert p.loc[1, "growth"] == 2.0          # 100 -> 300
    assert abs(p.loc[2, "growth"] - 0.2) < 1e-9


def test_group_tables_compute_differences():
    en, zh = "English", cfg.ZH_SIMPLIFIED
    a = pd.DataFrame(
        [_row(i, [en, zh], 200) for i in range(1, 13)] + [_row(i, [en], 100) for i in range(13, 25)]
    )
    g, _ = clean.build_games_clean(clean.add_features(a, "2025-11-01"))
    s = clean.build_sq1_groups(g)
    assert len(s) == 1
    row = s.iloc[0]
    assert (row["n_zh"], row["n_no_zh"]) == (12, 12)
    assert row["pct_diff"] == 1.0
    assert row["extra_reviews"] == 1200
    assert bool(row["eligible"])
