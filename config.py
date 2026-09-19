# ============================================================
# PROP-FIRM GIVEAWAY DETECTOR — CONFIGURATION
# ============================================================

# ------------------------------------------------------------
# Discord
# ------------------------------------------------------------
# IMPORTANT:
# Do NOT put your real Discord webhook directly in this file.
# GitHub Actions will load it from GitHub Secrets.

DISCORD_WEBHOOK_URL = None


# ------------------------------------------------------------
# Search queries
# ------------------------------------------------------------
# These are concept-based, NOT firm-name based.
# This allows completely new prop firms to be discovered.

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


# ------------------------------------------------------------
# Platforms
# ------------------------------------------------------------
# The detector is designed to search broadly across public
# internet/social content.

PLATFORMS = [
    "web",
"youtube”,
”reddit",]
# ------------------------------------------------------------
# Detector behavior
# ------------------------------------------------------------

# Only clearly eligible giveaways are sent to Discord.
SEND_UNCERTAIN = False

# Reject posts where engagement is clearly mandatory.
REJECT_MANDATORY_ENGAGEMENT = True

# Avoid sending the same post repeatedly.
DEDUPLICATE_RESULTS = True


# ------------------------------------------------------------
# Search limits
# ------------------------------------------------------------

# Number of results requested per search query/platform.
RESULTS_PER_QUERY = 20

# Maximum number of posts processed during one run.
MAX_POSTS_PER_RUN = 500


# ------------------------------------------------------------
# Giveaway requirements
# ------------------------------------------------------------

# A post must contain enough evidence that it is actually
# related to a prop-firm/funded-account giveaway.

MINIMUM_CONFIDENCE = 0.70


# ------------------------------------------------------------
# Debugging
# ------------------------------------------------------------

DEBUG = True
