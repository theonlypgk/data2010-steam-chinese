"""Cleaning and table building (task T3).

Input : data/interim/a_trim.csv.gz, data/interim/c_trim.csv.gz  (from task T1)
Output: four analysis tables, saved by scripts/02_build_tables.py as
        data/processed/pcd_<table>.csv and pcd_<table>.xlsx (see docs/data_spec.md)

    games_clean  one row per game in snapshot A      -> EDA, SQ1
    sq1_groups   one row per comparison group        -> SQ1
    panel_ac     one row per game in both A and C    -> SQ2
    sq2_groups   one row per SQ2 comparison group    -> SQ2

SQ3 builds no table of its own: it combines the by-genre results of SQ1 and SQ2.
"""
from __future__ import annotations

import ast
import re

import numpy as np
import pandas as pd

from . import config as cfg

_TAG_JUNK = re.compile(r"\[/?[a-zA-Z]+\]|<[^>]+>|&amp;|&lt;|&gt;|\*|\r|\n|#lang_\w+")


# --------------------------------------------------------------------------- parsing
def parse_list(value) -> list[str]:
    """Turn a list-like cell into a clean list of strings.

    Handles "['English', 'French']", "English,French", stray BBCode such as
    [b]*[/b], HTML leftovers and missing values.
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return []
    text = _TAG_JUNK.sub("", str(value)).strip()
    if not text or text in {"[]", "nan"}:
        return []
    items = None
    if text.startswith("["):
        try:
            items = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            text = text.strip("[]")
    if items is None:
        items = text.split(",")
    cleaned = [str(i).strip().strip("'\"").strip() for i in items]
    seen, out = set(), []
    for item in cleaned:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def first_genre(tags: list[str]) -> str | None:
    """First tag (Steam orders tags by votes) that belongs to one of the genre groups."""
    for tag in tags:
        if tag in cfg.TAG_TO_GENRE:
            return cfg.TAG_TO_GENRE[tag]
    return None


# --------------------------------------------------------------------------- per-game features
def add_features(trim: pd.DataFrame, snapshot_date: str) -> pd.DataFrame:
    """Add every derived column to one trimmed snapshot. No row is dropped here
    except rows without a usable app_id."""
    df = trim.copy()

    # --- 1. types: ids and counts to integers, price to float, release date to a date
    df["app_id"] = pd.to_numeric(df["app_id"], errors="coerce")
    df = df.dropna(subset=["app_id"]).drop_duplicates("app_id")
    df["app_id"] = df["app_id"].astype("int64")

    for col in ("positive", "negative"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype("int64")
    # Prices in snapshot A are sale prices on the snapshot day (e.g. Hades 7.49 at -70%).
    # Recover the list price so that price tiers describe the game, not the sale.
    df["price_at_snapshot"] = pd.to_numeric(df["price"], errors="coerce")
    discount = df["discount_pct"] if "discount_pct" in df else pd.Series(0, index=df.index)
    df["discount_pct"] = pd.to_numeric(discount, errors="coerce").fillna(0).clip(0, 99)
    df["price"] = (df["price_at_snapshot"] / (1 - df["discount_pct"] / 100)).round(2)
    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce", format="mixed")
    df["release_year"] = df["release_date"].dt.year.astype("Int64")
    df["days_since_release"] = (pd.Timestamp(snapshot_date) - df["release_date"]).dt.days

    # --- 2. parse the list-like text columns into Python lists
    langs = df["supported_languages"].map(parse_list)
    audio = df["full_audio_languages"].map(parse_list)
    tags = df["tags"].map(parse_list)
    genres = df["genres"].map(parse_list)

    # --- 3. outcome: reach = all reviews, positive or negative
    df["total_reviews"] = df["positive"] + df["negative"]

    # --- 4. language columns: treatment and the "other languages" confounder
    df["has_zh_simplified"] = langs.map(lambda x: cfg.ZH_SIMPLIFIED in x)
    df["has_zh_traditional"] = langs.map(lambda x: cfg.ZH_TRADITIONAL in x)
    df["has_english"] = langs.map(lambda x: cfg.ENGLISH in x)
    chinese = {cfg.ZH_SIMPLIFIED, cfg.ZH_TRADITIONAL}
    df["n_other_langs"] = langs.map(lambda x: len(set(x) - chinese - {cfg.ENGLISH}))
    df["n_other_langs_bin"] = pd.cut(
        df["n_other_langs"], cfg.OTHER_LANG_BINS, labels=cfg.OTHER_LANG_LABELS
    ).astype(str)
    df["major_langs"] = langs.map(lambda x: "|".join(sorted(set(x) & set(cfg.MAJOR_LANGS))))
    df["all_langs"] = langs.map(lambda x: "|".join(sorted(x)))

    # --- 5. flags used by the filters (Chinese-publisher proxy, Early Access, Traditional only)
    has_zh_audio = audio.map(lambda x: bool(set(x) & chinese))
    has_en_audio = audio.map(lambda x: cfg.ENGLISH in x)
    any_zh = df["has_zh_simplified"] | df["has_zh_traditional"]
    # A game made by a Chinese publisher for the Chinese market: Chinese without English,
    # in the text or in the voice-over. (Chinese voice-over alone is NOT used: many Western
    # games such as Cyberpunk 2077 or The Witcher 3 have it. See docs/decisions.md.)
    df["is_cn_publisher_proxy"] = (any_zh & ~df["has_english"]) | (has_zh_audio & ~has_en_audio)
    df["has_zh_audio"] = has_zh_audio
    df["has_english_audio"] = has_en_audio
    df["is_early_access"] = genres.map(lambda x: "Early Access" in x)
    df["is_traditional_only"] = df["has_zh_traditional"] & ~df["has_zh_simplified"]

    # --- 6. grouping variables: genre group, price tier, year band
    df["genre_group"] = tags.map(first_genre)
    df["price_tier"] = pd.cut(df["price"], cfg.PRICE_BINS, labels=cfg.PRICE_LABELS).astype(str)
    df["year_band"] = pd.cut(
        df["release_year"].astype("float"), cfg.YEAR_BAND_BINS, labels=cfg.YEAR_BAND_LABELS
    ).astype(str)
    return df


def apply_filters(df: pd.DataFrame, steps: list[tuple[str, pd.Series]], table: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply named filters in order and record how many games survive each one."""
    rows = [{"table": table, "step": "start", "games_left": len(df)}]
    keep = pd.Series(True, index=df.index)
    for name, mask in steps:
        keep &= mask.reindex(df.index).fillna(False)
        rows.append({"table": table, "step": name, "games_left": int(keep.sum())})
    return df[keep].copy(), pd.DataFrame(rows)


def _base_filters(df: pd.DataFrame) -> list[tuple[str, pd.Series]]:
    return [
        ("drop Chinese-publisher proxy", ~df["is_cn_publisher_proxy"]),
        ("drop Early Access", ~df["is_early_access"]),
        (f"keep >= {cfg.MIN_REVIEWS} reviews", df["total_reviews"] >= cfg.MIN_REVIEWS),
        ("keep released >= 1 year before snapshot", df["days_since_release"] >= cfg.MIN_AGE_DAYS),
        ("keep games with a genre group, price and year",
         df["genre_group"].notna() & df["price"].notna() & df["release_year"].notna()),
    ]


# --------------------------------------------------------------------------- table 1: games_clean
def build_games_clean(feat_a: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """One row per game in snapshot A after all filters. Serves EDA and SQ1."""
    steps = _base_filters(feat_a) + [("drop Traditional-Chinese-only", ~feat_a["is_traditional_only"])]
    df, funnel = apply_filters(feat_a, steps, "games_clean")
    df["has_zh"] = df["has_zh_simplified"].astype(int)
    # Round derived floats so that outputs do not depend on the last bits of a library.
    df["log_total_reviews"] = np.log10(df["total_reviews"]).round(6)
    # Comparison group for SQ1. Release years are merged into bands (allowed by the
    # framework): single years left most groups with < 10 games on one side.
    df["group_id"] = (
        df["genre_group"] + " | " + df["year_band"] + " | "
        + df["price_tier"] + " | " + df["n_other_langs_bin"]
    )
    cols = [
        "app_id", "name", "release_year", "year_band", "price", "discount_pct", "price_tier", "genre_group",
        "n_other_langs", "n_other_langs_bin", "has_zh", "positive", "negative",
        "total_reviews", "log_total_reviews", "group_id",
    ]
    return df[cols].sort_values("app_id").reset_index(drop=True), funnel


# --------------------------------------------------------------------------- table 2: sq1_groups
def build_sq1_groups(games_clean: pd.DataFrame) -> pd.DataFrame:
    """One row per group: median reviews with vs without Simplified Chinese."""
    keys = ["group_id", "genre_group", "year_band", "price_tier", "n_other_langs_bin"]
    wide = (
        games_clean.groupby(keys + ["has_zh"])["total_reviews"]
        .agg(n="size", median="median")
        .unstack("has_zh")
    )
    out = pd.DataFrame({
        "n_zh": wide[("n", 1)] if ("n", 1) in wide else 0,
        "n_no_zh": wide[("n", 0)] if ("n", 0) in wide else 0,
        "median_reviews_zh": wide[("median", 1)] if ("median", 1) in wide else np.nan,
        "median_reviews_no_zh": wide[("median", 0)] if ("median", 0) in wide else np.nan,
    }).reset_index()
    out[["n_zh", "n_no_zh"]] = out[["n_zh", "n_no_zh"]].fillna(0).astype(int)
    out["pct_diff"] = (out["median_reviews_zh"] / out["median_reviews_no_zh"] - 1).round(6)
    out["extra_reviews"] = ((out["median_reviews_zh"] - out["median_reviews_no_zh"]) * out["n_zh"]).round(2)
    out["eligible"] = (out["n_zh"] >= cfg.MIN_GAMES_PER_SIDE) & (out["n_no_zh"] >= cfg.MIN_GAMES_PER_SIDE)
    return out.sort_values("group_id").reset_index(drop=True)


# --------------------------------------------------------------------------- table 3: panel_ac
def build_panel_ac(feat_a: pd.DataFrame, feat_c: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """One row per game present in both snapshots that had no Chinese in C. Serves SQ2.

    Group variables (genre, price, year, other languages) come from C, the starting point.
    """
    steps = _base_filters(feat_c) + [
        ("keep games with no Chinese (Simplified or Traditional) in C",
         ~(feat_c["has_zh_simplified"] | feat_c["has_zh_traditional"])),
        ("keep games also present in A", feat_c["app_id"].isin(feat_a["app_id"])),
    ]
    c, funnel = apply_filters(feat_c, steps, "panel_ac")
    a = feat_a.set_index("app_id")
    c = c.set_index("app_id")
    a = a.loc[c.index]

    p = pd.DataFrame(index=c.index)
    p["name"] = c["name"]
    p["genre_group"] = c["genre_group"]
    p["release_year"] = c["release_year"]
    p["year_band"] = c["year_band"]
    p["price_c"] = c["price"]  # snapshot C has no discount column: price as listed in C
    p["price_tier"] = c["price_tier"]
    p["n_other_langs_bin"] = c["n_other_langs_bin"]
    p["reviews_c"] = c["total_reviews"]
    p["reviews_a"] = a["total_reviews"]
    # A game with 0 reviews in A had >= 10 in C: it was delisted or its reviews are
    # missing in the data. Its "growth" of -100% is not real, so it is dropped (logged below).
    p = p[p["reviews_a"] > 0].copy()
    a = a.loc[p.index]
    c = c.loc[p.index]
    p["growth"] = ((p["reviews_a"] - p["reviews_c"]) / p["reviews_c"]).round(6)
    p["initial_reach_bin"] = pd.qcut(
        p["reviews_c"].rank(method="first"), 3, labels=cfg.REACH_LABELS
    ).astype(str)

    new_langs = [
        set(la.split("|")) - set(lc.split("|")) - {""}
        for la, lc in zip(a["all_langs"], c["all_langs"])
    ]
    p["added_zh"] = a["has_zh_simplified"].astype(int).to_numpy()
    p["added_only_zh"] = [int(n == {cfg.ZH_SIMPLIFIED}) for n in new_langs]
    p["added_other_major_lang"] = [int(bool(n & set(cfg.MAJOR_LANGS))) for n in new_langs]
    p["n_langs_added"] = [len(n) for n in new_langs]
    p["arm"] = np.select(
        [p["added_zh"] == 1, (p["added_zh"] == 0) & (p["added_other_major_lang"] == 0)],
        ["treated", "control"],
        default="excluded",
    )
    # Comparison group for SQ2: genre x initial reach. Only ~500 games added Chinese, so the
    # five-way group of the framework left 7 eligible groups; this one keeps ~95% of them
    # and all 6 genres. Year, price and other languages stay in the table for checks.
    p["group_id_sq2"] = p["genre_group"] + " | " + p["initial_reach_bin"]
    funnel = pd.concat([funnel, pd.DataFrame([
        {"table": "panel_ac", "step": "keep games with reviews in A (not delisted)", "games_left": len(p)},
        {"table": "panel_ac", "step": "arm = treated", "games_left": int((p["arm"] == "treated").sum())},
        {"table": "panel_ac", "step": "arm = control", "games_left": int((p["arm"] == "control").sum())},
    ])], ignore_index=True)
    return p.reset_index().sort_values("app_id").reset_index(drop=True), funnel


# --------------------------------------------------------------------------- table 4: sq2_groups
def build_sq2_groups(panel: pd.DataFrame) -> pd.DataFrame:
    """One row per SQ2 group: median growth of treated vs control games."""
    keys = ["group_id_sq2", "genre_group", "initial_reach_bin"]
    used = panel[panel["arm"].isin(["treated", "control"])]
    wide = used.groupby(keys + ["arm"])["growth"].agg(n="size", median="median").unstack("arm")

    def col(stat, arm, default):
        return wide[(stat, arm)] if (stat, arm) in wide else default

    out = pd.DataFrame({
        "n_treated": col("n", "treated", 0),
        "n_control": col("n", "control", 0),
        "median_growth_treated": col("median", "treated", np.nan),
        "median_growth_control": col("median", "control", np.nan),
    }).reset_index()
    out[["n_treated", "n_control"]] = out[["n_treated", "n_control"]].fillna(0).astype(int)
    out[["median_growth_treated", "median_growth_control"]] = out[
        ["median_growth_treated", "median_growth_control"]
    ].round(6)
    out["uplift_pts"] = (out["median_growth_treated"] - out["median_growth_control"]).round(6)
    out["eligible"] = (out["n_treated"] >= cfg.MIN_GAMES_PER_SIDE) & (out["n_control"] >= cfg.MIN_GAMES_PER_SIDE)
    return out.sort_values("group_id_sq2").reset_index(drop=True)


# --------------------------------------------------------------------------- data dictionary
DATA_DICTIONARY = [
    # table, column, meaning
    ("games_clean", "app_id", "Steam application id (key)"),
    ("games_clean", "name", "Game title (for checking only)"),
    ("games_clean", "release_year", "Year of release"),
    ("games_clean", "year_band", "<=2017 / 2018-2019 / 2020-2021 / 2022+"),
    ("games_clean", "price", "List price in USD (snapshot price undone for the discount)"),
    ("games_clean", "discount_pct", "Discount (%) running on the snapshot day"),
    ("games_clean", "price_tier", "free / lt5 / 5to10 / 10to20 / gt20"),
    ("games_clean", "genre_group", "One of 6 groups, from the first matching tag"),
    ("games_clean", "n_other_langs", "Supported languages other than English and Chinese"),
    ("games_clean", "n_other_langs_bin", "0 / 1-4 / 5+"),
    ("games_clean", "has_zh", "1 = supports Simplified Chinese, 0 = no Chinese at all"),
    ("games_clean", "positive", "Positive reviews"),
    ("games_clean", "negative", "Negative reviews"),
    ("games_clean", "total_reviews", "Reach = positive + negative"),
    ("games_clean", "log_total_reviews", "log10 of total_reviews"),
    ("games_clean", "group_id", "genre_group | year_band | price_tier | n_other_langs_bin"),
    ("sq1_groups", "group_id", "Comparison group (key)"),
    ("sq1_groups", "n_zh / n_no_zh", "Games with / without Simplified Chinese in the group"),
    ("sq1_groups", "median_reviews_zh / median_reviews_no_zh", "Median total_reviews on each side"),
    ("sq1_groups", "pct_diff", "median_reviews_zh / median_reviews_no_zh - 1"),
    ("sq1_groups", "extra_reviews", "(median_reviews_zh - median_reviews_no_zh) * n_zh"),
    ("sq1_groups", "eligible", "True when both sides have at least 10 games"),
    ("panel_ac", "app_id", "Steam application id (key); game is in both A and C, no Chinese in C, has reviews in A"),
    ("panel_ac", "genre_group, release_year, year_band, price_c, price_tier, n_other_langs_bin", "Group variables, all taken from snapshot C"),
    ("panel_ac", "reviews_c / reviews_a", "total_reviews in January 2024 / in snapshot A"),
    ("panel_ac", "growth", "(reviews_a - reviews_c) / reviews_c"),
    ("panel_ac", "initial_reach_bin", "small / medium / large: terciles of reviews_c"),
    ("panel_ac", "added_zh", "1 = has Simplified Chinese in A"),
    ("panel_ac", "added_only_zh", "1 = Simplified Chinese is the only language added"),
    ("panel_ac", "added_other_major_lang", "1 = added at least one major language (see config.MAJOR_LANGS)"),
    ("panel_ac", "n_langs_added", "Number of languages in A that were not in C"),
    ("panel_ac", "arm", "treated (added_zh=1) / control (no Chinese, no major language added) / excluded"),
    ("panel_ac", "group_id_sq2", "genre_group | initial_reach_bin"),
    ("sq2_groups", "group_id_sq2", "Comparison group (key)"),
    ("sq2_groups", "n_treated / n_control", "Games in each arm"),
    ("sq2_groups", "median_growth_treated / median_growth_control", "Median growth in each arm"),
    ("sq2_groups", "uplift_pts", "median_growth_treated - median_growth_control"),
    ("sq2_groups", "eligible", "True when both arms have at least 10 games"),
]


def build_all(trim_a: pd.DataFrame, trim_c: pd.DataFrame, date_a: str, date_c: str) -> dict[str, pd.DataFrame]:
    """Run the whole of T3 in memory and return every output table."""
    feat_a = add_features(trim_a, date_a)
    feat_c = add_features(trim_c, date_c)
    games_clean, funnel_1 = build_games_clean(feat_a)
    panel_ac, funnel_2 = build_panel_ac(feat_a, feat_c)
    return {
        "games_clean": games_clean,
        "sq1_groups": build_sq1_groups(games_clean),
        "panel_ac": panel_ac,
        "sq2_groups": build_sq2_groups(panel_ac),
        "funnel": pd.concat([funnel_1, funnel_2], ignore_index=True),
        "data_dictionary": pd.DataFrame(DATA_DICTIONARY, columns=["table", "column", "meaning"]),
    }
