# ============================================================
# PROP-FIRM GIVEAWAY DETECTOR — CONFIGURATION
# ============================================================

DISCORD_WEBHOOK_URL = None

SEARCH_QUERIES = [
    "prop firm giveaway",
    "prop trading giveaway",
    "funded account giveaway",
    "funded trader giveaway",
    "free funded account",
    "free prop challenge",
    "win funded account",
    "win prop firm challenge",
    "win a funded account",
    "prop firm contest",
    "prop trading contest",
    "funded account contest",
    "free trading challenge",
    "100k funded account giveaway",
    "50k funded account giveaway",
    "200k funded account giveaway",
    "new prop firm giveaway",
    "prop firm launch giveaway",
    "prop firm opening giveaway",
    '"giveaway" "funded account"',
    '"giveaway" "prop firm"',
    '"win" "funded account"',
    '"free challenge" "prop firm"',
    '"winner" "funded account"',
]

PLATFORMS = [
    "web",
    "youtube",
    "reddit",
]

SEND_UNCERTAIN = False
REJECT_MANDATORY_ENGAGEMENT = True
DEDUPLICATE_RESULTS = True

RESULTS_PER_QUERY = 20
MAX_POSTS_PER_RUN = 500

MINIMUM_CONFIDENCE = 0.70

DEBUG = True
