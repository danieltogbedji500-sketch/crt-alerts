# eligibility.py

import re
from dataclasses import dataclass
from enum import Enum


class Decision(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    REJECT = "REJECT"
    UNCERTAIN = "UNCERTAIN"


@dataclass
class GiveawayResult:
    decision: Decision
    reason: str
    confidence: float


# Words that indicate a giveaway/contest
GIVEAWAY_TERMS = [
    "giveaway",
    "give away",
    "contest",
    "competition",
    "win",
    "winner",
    "winners",
    "free account",
    "free challenge",
]


# Words indicating a prop/funded trading prize
PROP_TERMS = [
    "prop firm",
    "propfirm",
    "prop trading",
    "proprietary trading",
    "funded account",
    "funded challenge",
    "funding challenge",
    "trading challenge",
    "funded trader",
]


# Engagement actions that are NOT allowed when mandatory
ENGAGEMENT_ACTIONS = [
    "like",
    "likes",
    "liking",
    "share",
    "shares",
    "sharing",
    "repost",
    "repost this",
    "retweet",
    "retweet this",
    "follow",
    "follow us",
    "follow me",
    "tag",
    "tag friends",
    "tag 3 friends",
    "tag 5 friends",
    "comment",
    "comment below",
]


# Phrases that strongly indicate the action is mandatory
MANDATORY_PATTERNS = [
    r"\bmust\s+(like|share|repost|retweet|follow|tag|comment)\b",
    r"\bto\s+enter\b.*\b(like|share|repost|retweet|follow|tag|comment)\b",
    r"\bto\s+win\b.*\b(like|share|repost|retweet|follow|tag|comment)\b",
    r"\bentry\s+requirement\b.*\b(like|share|repost|retweet|follow|tag|comment)\b",
    r"\brequired\b.*\b(like|share|repost|retweet|follow|tag|comment)\b",
    r"\b(like|share|repost|retweet|follow|tag|comment)\b.*\bto enter\b",
    r"\b(like|share|repost|retweet|follow|tag|comment)\b.*\bto win\b",
    r"\b(like|share|repost|retweet|follow|tag|comment)\b.*\bmandatory\b",
    r"\b(like|share|repost|retweet|follow|tag|comment)\b.*\brequired\b",
]


# Phrases showing that engagement is optional/supportive
OPTIONAL_PATTERNS = [
    r"\bif you want\b",
    r"\boptional\b",
    r"\bfeel free to\b",
    r"\byou can\b",
    r"\bif you wish\b",
    r"\bnot required\b",
    r"\bnot mandatory\b",
    r"\bno need to\b",
]


def normalize(text: str) -> str:
    """Normalize post text for analysis."""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def is_prop_giveaway(text: str) -> bool:
    """
    Determine whether the post appears to be about
    a prop-firm/funded-account giveaway.
    """

    giveaway_found = contains_any(text, GIVEAWAY_TERMS)
    prop_found = contains_any(text, PROP_TERMS)

    return giveaway_found and prop_found


def mandatory_engagement_detected(text: str) -> bool:
    """Detect explicit mandatory engagement requirements."""

    for pattern in MANDATORY_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False


def optional_engagement_detected(text: str) -> bool:
    """Detect language suggesting engagement is optional."""

    for pattern in OPTIONAL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False


def analyze_entry_requirements(text: str) -> Decision:
    """
    Apply the user's strict entry rule.

    Mandatory engagement = REJECT
    Clearly optional engagement = continue
    Ambiguous engagement requirement = UNCERTAIN
    """

    mandatory = mandatory_engagement_detected(text)

    if mandatory:
        return Decision.REJECT

    # Look for engagement terms in the post.
    engagement_present = contains_any(text, ENGAGEMENT_ACTIONS)

    if not engagement_present:
        return Decision.ELIGIBLE

    # Engagement exists but is explicitly optional.
    if optional_engagement_detected(text):
        return Decision.ELIGIBLE

    # Engagement is mentioned but we cannot prove whether
    # it is mandatory or optional.
    return Decision.UNCERTAIN


def evaluate_giveaway(text: str) -> GiveawayResult:
    """
    Main eligibility engine.
    """

    text = normalize(text)

    # First determine whether this is even a prop giveaway.
    if not is_prop_giveaway(text):
        return GiveawayResult(
            decision=Decision.REJECT,
            reason="Not clearly a prop-firm giveaway",
            confidence=0.95,
        )

    # Apply the entry requirement rule.
    entry_decision = analyze_entry_requirements(text)

    if entry_decision == Decision.REJECT:
        return GiveawayResult(
            decision=Decision.REJECT,
            reason="Mandatory engagement requirement detected",
            confidence=0.98,
        )

    if entry_decision == Decision.UNCERTAIN:
        return GiveawayResult(
            decision=Decision.UNCERTAIN,
            reason="Engagement requirement is ambiguous",
            confidence=0.50,
        )

    return GiveawayResult(
        decision=Decision.ELIGIBLE,
        reason="Prop-firm giveaway with no mandatory engagement requirement detected",
        confidence=0.90,
)
