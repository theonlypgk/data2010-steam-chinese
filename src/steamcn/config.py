"""Every fixed choice of the project, in one place, each with the reason for it.

This file mirrors docs/decisions.md: change both together, only with the team leader's
sign-off, and add a dated line to the change log in docs/decisions.md.
"""

# Seed for every random step (bootstrap), so results are identical on every run.
SEED = 2010

# =============================================================================
# DATA SOURCE
# =============================================================================
# Steam Games Dataset by FronkonGames on Hugging Face. We read two versions of the same
# file from the repository history, pinned by commit hash, so the downloaded bytes never
# change even when the author keeps updating the dataset.
HF_DATASET = "FronkonGames/steam-games-dataset"
HF_FILENAME = "games.csv"

# Snapshot A ("current"): the latest commit that updated games.csv (2026-06-20).
# Later commits (up to 2026-11-08) only update games.json (about 1 GB); kept on the CSV
# so that the pipeline stays fast and simple. Decision: team leader, 2026-11-12.
REVISION_A = "52ba62abfa707a2fa31f4d147c2777a9d9fbd2da"
SNAPSHOT_DATE_A = "2026-06-20"

# Snapshot C ("before"): commit "Update 12-01-2024." of 2024-01-11, the January 2024
# version of the catalogue. Used only by SQ2, to see which games added Chinese later.
REVISION_C = "aefdeb1ff1a739b92ac5338682cc2610a0328505"
SNAPSHOT_DATE_C = "2024-01-11"

# Raw column name -> English snake_case name used everywhere in this repo.
# DATA ISSUE handled in scripts/01_trim.py: in snapshot A the header merges two names into
# "DiscountDLC count" while every row holds two values, which shifts all later columns.
RAW_TO_CLEAN = {
    "AppID": "app_id",
    "Name": "name",
    "Release date": "release_date",
    "Price": "price",
    "Supported languages": "supported_languages",
    "Full audio languages": "full_audio_languages",
    "Positive": "positive",
    "Negative": "negative",
    "Developers": "developers",
    "Publishers": "publishers",
    "Genres": "genres",
    "Tags": "tags",
}
# Columns that exist in only some snapshots; filled with "0" where missing.
# DATA ISSUE: snapshot A was taken during a Steam sale, so "Price" is the sale price that
# day (Hades: 7.49 = 24.99 at -70%). "Discount" lets us recover the list price. Snapshot C
# has no "Discount" column; its prices are used as listed.
OPTIONAL_RAW_TO_CLEAN = {
    "Discount": "discount_pct",
}

# =============================================================================
# LANGUAGES
# =============================================================================
ZH_SIMPLIFIED = "Simplified Chinese"
ZH_TRADITIONAL = "Traditional Chinese"
ENGLISH = "English"

# "Major" languages. In SQ2 a CONTROL game must not have added Chinese AND must not have
# added any of these either: a game that added German and French in the same period got
# a localisation push of its own, so it is not a clean "did nothing" comparison.
# Chosen as the most common non-English Steam languages other than Chinese.
MAJOR_LANGS = [
    "German", "French", "Spanish - Spain", "Japanese", "Russian",
    "Korean", "Portuguese - Brazil",
]

# =============================================================================
# CHINESE GAMES: ALL are removed, large or small (decision: team leader, 2026-11-12)
# =============================================================================
# Why: a game made in China has Chinese and Chinese players by default. Comparing it with
# Western games would mix "made for China" with "translated into Chinese".
# The dataset has no "country" column, so a game is treated as Chinese if ANY rule matches
# (the rule that matched is written to pcd_cn_excluded so it can be checked by hand):
#   1. Chinese text or voice-over WITHOUT English (made for the Chinese market).
#   2. Developer or publisher name written in Chinese characters.
#   3. Developer or publisher name contains a mainland Chinese city (Chinese companies are
#      registered as "Shanghai ... Network Technology Co., Ltd." and similar).
#   4. Developer or publisher is a well-known Chinese company (list below).
# Rule 1 alone is not enough: Black Myth: Wukong (Game Science) ships English, so only
# rules 2-4 catch it. Chinese voice-over alone is NOT a rule: many Western games such as
# Cyberpunk 2077 or The Witcher 3 have it (an earlier rule removed 4,233 such games).
CN_CITIES = [
    "Beijing", "Shanghai", "Shenzhen", "Guangzhou", "Hangzhou", "Chengdu", "Nanjing",
    "Wuhan", "Xiamen", "Suzhou", "Chongqing", "Tianjin", "Changsha", "Fuzhou", "Hefei",
    "Jinan", "Qingdao", "Dalian", "Zhuhai", "Dongguan", "Xi'an",
]
CN_COMPANIES = [
    "Tencent", "NetEase", "miHoYo", "HoYoverse", "Game Science", "Perfect World",
    "X.D. Network", "XD Inc", "bilibili", "Gamera Games", "Hypergryph", "Lilith Games",
    "Seasun", "Kingsoft", "Papergames", "Paper Games", "Yostar", "Pathea", "NExT Studios",
    "TiMi Studio", "Leiting", "Giant Network", "Snail Games", "Shanda", "CMGE", "Zulong",
    "Hero Games", "Youthcat",
]

# =============================================================================
# GENRE GROUPS
# =============================================================================
# Six groups, from the framework of 2026-11-03. A game gets the group of its FIRST tag that
# appears in this map. Steam lists user tags by number of votes, so the first matching tag
# is the one players use most. Tags such as "Indie" or "Simulation" are skipped: they say
# nothing about how much text a game has. Games with no matching tag are dropped.
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

# =============================================================================
# BINS
# =============================================================================
# Price tiers in USD, on the LIST price (see OPTIONAL_RAW_TO_CLEAN). Five tiers from the
# framework: price stands in for budget and studio size.
PRICE_BINS = [-0.001, 0.0, 4.999, 9.999, 19.999, float("inf")]
PRICE_LABELS = ["free", "lt5", "5to10", "10to20", "gt20"]
# Number of languages other than English and Chinese: games with Chinese are usually
# translated as a package, so this is held fixed when comparing.
OTHER_LANG_BINS = [-1, 0, 4, 10_000]
OTHER_LANG_LABELS = ["0", "1-4", "5+"]
# Release-year bands. Used in the SQ1 group instead of single years: with single years
# only 47% of games sat in groups with >= 10 games on each side; with bands, 81%.
YEAR_BAND_BINS = [0, 2017, 2019, 2021, 2100]
YEAR_BAND_LABELS = ["<=2017", "2018-2019", "2020-2021", "2022+"]
# Starting reach for SQ2 = terciles of reviews in snapshot C. Growth in % depends on the
# starting point (100 -> 200 is +100%, 50,000 -> 55,000 is +10%), so it is held fixed.
REACH_LABELS = ["small", "medium", "large"]

# =============================================================================
# FILTERS AND THRESHOLDS
# =============================================================================
# At least 10 reviews: below that, reach is noise. Not 500: filtering hard on the outcome
# itself would shrink the gap we want to measure.
MIN_REVIEWS = 10
# Released at least one year before the snapshot, so every game had time to collect reviews.
MIN_AGE_DAYS = 365
# A comparison group counts ("eligible") only with >= 10 games on each side; a median of
# fewer games moves too much with a single game.
MIN_GAMES_PER_SIDE = 10
# "Large enough" effects, fixed before looking at results (framework, section 7).
SQ1_THRESHOLD_PCT = 0.20    # SQ1: games with Chinese have >= 20% more reviews
SQ2_THRESHOLD_PTS = 0.10    # SQ2: growth is >= 10 percentage points higher
N_BOOTSTRAP = 2000
