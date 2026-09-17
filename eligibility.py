# ============================================================
# PROP-FIRM GIVEAWAY DETECTOR
# ELIGIBILITY / RULES ENGINE
# ============================================================

import re
from dataclasses import dataclass
from enum import Enum


# ------------------------------------------------------------
# DECISIONS
# ------------------------------------------------------------

class Decision(Enum):
    ELIGIBLE = "ELIGIBLE"
    REJECT = "REJECT"
    UNCERTAIN = "UNCERTAIN"


@dataclass
class GiveawayResult:
    decision: Decision
    reason: str
    entry_method: str = ""


# ------------------------------------------------------------
# PROP-FIRM / GIVEAWAY TERMS
# ------------------------------------------------------------

GIVEAWAY_TERMS = [
    "giveaway",
    "contest",
    "competition",
    "free funded",
    "win a funded",
    "win funded",
    "free challenge",
    "free prop challenge",
]

PROP_TERMS = [
    "prop firm",
    "propfirm",
    "prop trading",
    "proprietary trading",
    "funded account",
    "funded trader",
    "funded challenge",
    "trading challenge",
    "funded account challenge",
    "evaluation account",
    "trader funding",
]


# ------------------------------------------------------------
# ENGAGEMENT ACTIONS
# ------------------------------------------------------------

ENGAGEMENT_ACTIONS = [
    "like",
    "likes",
    "liked",
    "share",
    "shares",
    "shared",
    "repost",
    "repost this",
    "retweet",
    "follow",
    "follow us",
    "follow me",
    "tag",
    "tag friends",
    "tag a friend",
    "comment",
    "comment below",
    "subscribe",
]


# ------------------------------------------------------------
# PHRASES THAT STRONGLY INDICATE REQUIREMENT
# ------------------------------------------------------------

MANDATORY_PATTERNS = [
    # Like
    r"\blike\b.{0,100}\bto enter\b",
    r"\blike\b.{0,100}\bto win\b",
    r"\blike\b.{0,100}\bfor a chance\b",

    # Share / repost
    r"\bshare\b.{0,100}\bto enter\b",
    r"\bshare\b.{0,100}\bto win\b",
    r"\brepost\b.{0,100}\bto enter\b",
    r"\brepost\b.{0,100}\bto win\b",
    r"\bretweet\b.{0,100}\bto enter\b",
    r"\bretweet\b.{0,100}\bto win\b",

    # Follow
    r"\bfollow\b.{0,100}\bto enter\b",
    r"\bfollow\b.{0,100}\bto win\b",
    r"\bfollow us\b.{0,100}\bto enter\b",
    r"\bfollow us\b.{0,100}\bto win\b",

    # Tag
    r"\btag\b.{0,100}\bto enter\b",
    r"\btag\b.{0,100}\bto win\b",
    r"\btag friends\b.{0,100}\bto enter\b",
    r"\btag a friend\b.{0,100}\bto enter\b",

    # Comment
    r"\bcomment\b.{0,100}\bto enter\b",
    r"\bcomment below\b.{0,100}\bto enter\b",
    r"\bcomment\b.{0,100}\bto win\b",

    # Subscribe
    r"\bsubscribe\b.{0,100}\bto enter\b",
    r"\bsubscribe\b.{0,100}\bto win\b",

    # Direct requirement wording
    r"\bmust\b.{0,100}\blike\b",
    r"\bmust\b.{0,100}\bshare\b",
    r"\bmust\b.{0,100}\brepost\b",
    r"\bmust\b.{0,100}\bfollow\b",
    r"\bmust\b.{0,100}\btag\b",
    r"\bmust\b.{0,100}\bcomment\b",
    r"\brequired\b.{0,100}\blike\b",
    r"\brequired\b.{0,100}\bshare\b",
    r"\brequired\b.{0,100}\brepost\b",
    r"\brequired\b.{0,100}\bfollow\b",
    r"\brequired\b.{0,100}\btag\b",
    r"\brequired\b.{0,100}\bcomment\b",

    # Entry instructions
    r"\bto enter\b.{0,100}\blike\b",
    r"\bto enter\b.{0,100}\bshare\b",
    r"\bto enter\b.{0,100}\brepost\b",
    r"\bto enter\b.{0,100}\bfollow\b",
    r"\bto enter\b.{0,100}\btag\b",
    r"\bto enter\b.{0,100}\bcomment\b",

    r"\bentry\b.{0,100}\blike\b",
    r"\bentry\b.{0,100}\bshare\b",
    r"\bentry\b.{0,100}\brepost\b",
    r"\bentry\b.{0,100}\bfollow\b",
    r"\bentry\b.{0,100}\btag\b",
    r"\bentry\b.{0,100}\bcomment\b",

    # Winner selection
    r"\bwinner\b.{0,100}\bselected\b.{0,100}\bcomment\b",
    r"\bwinners?\b.{0,100}\bfrom\b.{0,100}\bcomments?\b",
]


# ------------------------------------------------------------
# CLEARLY OPTIONAL ENGAGEMENT
# ------------------------------------------------------------

OPTIONAL_PATTERNS = [
    r"\boptional\b",
    r"\bnot required\b",
    r"\bnot mandatory\b",
    r"\bno need to\b",
    r"\byou don't have to\b",
    r"\byou do not have to\b",
    r"\bif you want to support us\b",
    r"\bif you'd like to support us\b",
    r"\bif you want to help\b",
    r"\bfeel free to like\b",
    r"\bfeel free to share\b",
    r"\bfeel free to follow\b",
    r"\bfeel free to repost\b",
]


# ------------------------------------------------------------
# CLEAR NON-ENGAGEMENT ENTRY METHODS
# ------------------------------------------------------------

ENTRY_PATTERNS = [
    r"\bregister\b",
    r"\bregistration\b",
    r"\bsign up\b",
    r"\bsignup\b",
    r"\bfill out\b",
    r"\bform\b",
    r"\bapplication\b",
    r"\bjoin\b",
    r"\bjoin our discord\b",
    r"\bjoin the discord\b",
    r"\bvisit\b",
    r"\bwebsite\b",
    r"\blink in bio\b",
    r"\benter through\b",
    r"\bentry form\b",
]


# ------------------------------------------------------------
# TEXT NORMALIZATION
# ------------------------------------------------------------

def normalize(text):
    if not text:
        return ""

    text = str(text).lower()

    # Normalize common symbols.
    text = text.replace("&", " and ")
    text = text.replace("\n", " ")
    text = text.replace("\r", " ")

    # Collapse whitespace.
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ------------------------------------------------------------
# TERM DETECTION
# ------------------------------------------------------------

def contains_any(text, terms):
    return any(term in text for term in terms)


def is_prop_giveaway(text):
    """
    Determines whether the content is sufficiently related
    to a prop-firm / funded-account giveaway.
    """

    text = normalize(text)

    has_giveaway = contains_any(text, GIVEAWAY_TERMS)
    has_prop = contains_any(text, PROP_TERMS)

    return has_giveaway and has_prop


# ------------------------------------------------------------
# MANDATORY ENGAGEMENT DETECTION
# ------------------------------------------------------------

def mandatory_engagement_detected(text):
    text = normalize(text)

    for pattern in MANDATORY_PATTERNS:
        if re.search(pattern, text):
            return True

    return False


# ------------------------------------------------------------
# OPTIONAL ENGAGEMENT DETECTION
# ------------------------------------------------------------

def optional_engagement_detected(text):
    text = normalize(text)

    for pattern in OPTIONAL_PATTERNS:
        if re.search(pattern, text):
            return True

    return False


# ------------------------------------------------------------
# ENTRY METHOD EXTRACTION
# ------------------------------------------------------------

def extract_entry_method(text):
    text = normalize(text)

    matches = []

    for pattern in ENTRY_PATTERNS:
        match = re.search(pattern, text)

        if match:
            matches.append(match.group(0))

    if not matches:
        return ""

    # Remove duplicates while preserving order.
    unique = list(dict.fromkeys(matches))

    return ", ".join(unique)


# ------------------------------------------------------------
# ENGAGEMENT MENTION
# ------------------------------------------------------------

def engagement_mentioned(text):
    text = normalize(text)

    return contains_any(text, ENGAGEMENT_ACTIONS)


# ------------------------------------------------------------
# MAIN ANALYSIS
# ------------------------------------------------------------

def analyze_entry_requirements(text):
    text = normalize(text)

    if not text:
        return GiveawayResult(
            Decision.UNCERTAIN,
            "No usable post text.",
        )

    # --------------------------------------------------------
    # 1. Explicit mandatory engagement = REJECT
    # --------------------------------------------------------

    if mandatory_engagement_detected(text):
        return GiveawayResult(
            Decision.REJECT,
            "Mandatory social-media engagement is required.",
        )

    # --------------------------------------------------------
    # 2. Explicitly optional engagement = acceptable
    # --------------------------------------------------------

    if optional_engagement_detected(text):
        entry = extract_entry_method(text)

        return GiveawayResult(
            Decision.ELIGIBLE,
            "Social-media engagement is explicitly optional.",
            entry,
        )

    # --------------------------------------------------------
    # 3. No engagement mentioned
    # --------------------------------------------------------

    if not engagement_mentioned(text):
        entry = extract_entry_method(text)

        return GiveawayResult(
            Decision.ELIGIBLE,
            "No mandatory social-media engagement detected.",
            entry,
        )

    # --------------------------------------------------------
    # 4. Engagement exists but relationship is unclear
    # --------------------------------------------------------

    return GiveawayResult(
        Decision.UNCERTAIN,
        "Social-media engagement is mentioned, but it is unclear whether it is mandatory.",
    )


# ------------------------------------------------------------
# FINAL GIVEAWAY EVALUATION
# ------------------------------------------------------------

def evaluate_giveaway(text):
    text = normalize(text)

    # Not a recognizable prop giveaway.
    if not is_prop_giveaway(text):
        return GiveawayResult(
            Decision.REJECT,
            "Content is not clearly a prop-firm giveaway.",
        )

    result = analyze_entry_requirements(text)

    return result


# ------------------------------------------------------------
# LOCAL TESTS
# ------------------------------------------------------------

if __name__ == "__main__":

    tests = [
        (
            "Like, repost and follow to enter our $100K funded "
            "account giveaway."
        ),

        (
            "Register through our website to enter the $100K "
            "funded account giveaway."
        ),

        (
            "Join our free funded account giveaway. "
            "Following us is optional."
        ),

        (
            "Like and repost if you want to support us. "
            "Enter the $100K funded account giveaway through "
            "the registration form."
        ),

        (
            "Like this post and join our $100K funded account "
            "giveaway."
        ),
    ]

    print("\nPROP-FIRM GIVEAWAY RULE TESTS\n")

    for number, test in enumerate(tests, start=1):
        result = evaluate_giveaway(test)

        print(f"TEST {number}")
        print(f"Decision: {result.decision.value}")
        print(f"Reason:   {result.reason}")
        print(f"Entry:    {result.entry_method}")
        print("-" * 60)
