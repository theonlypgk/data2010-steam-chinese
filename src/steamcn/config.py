"""Frozen definitions. Mirror of docs/decisions.md: change both together, and only
with the team leader's sign-off (date + reason in docs/decisions.md)."""

SEED = 2010

# ---- data source (task T1 fills these in and never changes them afterwards) ----
HF_DATASET = "FronkonGames/steam-games-dataset"
HF_FILENAME = "games.csv"
# Snapshot A: latest commit that updated games.csv ("Update games.csv", 2026-06-20).
# Later commits only update games.json. Re-pin (and update docs) before gate G3 if needed.
REVISION_A = "52ba62abfa707a2fa31f4d147c2777a9d9fbd2da"
SNAPSHOT_DATE_A = "2026-06-20"
# Snapshot C: "Update 12-01-2024." (2024-01-11), the January 2024 version of the catalogue.
REVISION_C = "aefdeb1ff1a739b92ac5338682cc2610a0328505"
SNAPSHOT_DATE_C = "2024-01-11"

# Raw column name -> English snake_case name used everywhere in this repo.
# Note: in snapshot A the header merges two columns into "DiscountDLC count" while the
# rows hold two values; scripts/01_trim.py splits the header back before reading.
RAW_TO_CLEAN = {
    "AppID": "app_id",
    "Name": "name",
    "Release date": "release_date",
    "Price": "price",
    "Supported languages": "supported_languages",
    "Full audio languages": "full_audio_languages",
    "Positive": "positive",
    "Negative": "negative",
    "Genres": "genres",
    "Tags": "tags",
}

# ---- language definitions ----
ZH_SIMPLIFIED = "Simplified Chinese"
ZH_TRADITIONAL = "Traditional Chinese"
ENGLISH = "English"
# "Major" languages: a control game in SQ2 must not have added any of these either.
MAJOR_LANGS = [
    "German", "French", "Spanish - Spain", "Japanese", "Russian",
    "Korean", "Portuguese - Brazil",
]

# ---- genre groups: first tag (Steam orders tags by votes) found in this map wins ----
# DRAFT: the team leader confirms this list in docs/decisions.md before SQ1 is run.
TAG_TO_GENRE = {
    "Visual Novel": "Visual Novel",
    "RPG": "RPG", "JRPG": "RPG", "CRPG": "RPG", "Action RPG": "RPG", "Party-Based RPG": "RPG",
    "Strategy": "Strategy", "Turn-Based Strategy": "Strategy", "RTS": "Strategy",
    "Grand Strategy": "Strategy", "4X": "Strategy", "Tower Defense": "Strategy",
    "Action": "Action", "Shooter": "Action", "FPS": "Action", "Platformer": "Action",
    "Hack and Slash": "Action", "Fighting": "Action",
    "Puzzle": "Puzzle", "Hidden Object": "Puzzle",
    "Casual": "Casual",
}

# ---- bins ----
PRICE_BINS = [-0.001, 0.0, 4.999, 9.999, 19.999, float("inf")]
PRICE_LABELS = ["free", "lt5", "5to10", "10to20", "gt20"]
OTHER_LANG_BINS = [-1, 0, 4, 10_000]
OTHER_LANG_LABELS = ["0", "1-4", "5+"]
# SQ2 uses year bands instead of single years because the sample is much smaller.
YEAR_BAND_BINS = [0, 2017, 2019, 2021, 2100]
YEAR_BAND_LABELS = ["<=2017", "2018-2019", "2020-2021", "2022+"]
REACH_LABELS = ["small", "medium", "large"]   # terciles of reviews_c

# ---- filters and thresholds ----
MIN_REVIEWS = 10            # keep games with at least this many reviews
MIN_AGE_DAYS = 365          # released at least one year before the snapshot
MIN_GAMES_PER_SIDE = 10     # a group is "eligible" only with >= 10 games on each side
SQ1_THRESHOLD_PCT = 0.20    # "large enough" for SQ1
SQ2_THRESHOLD_PTS = 0.10    # "large enough" for SQ2 (growth difference, in points)
N_BOOTSTRAP = 2000
