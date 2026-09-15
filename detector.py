# ============================================================
# PROP-FIRM GIVEAWAY DETECTOR
# Main detection engine
# ============================================================

import os
import hashlib
import requests

from config import (
    SEARCH_QUERIES,
    SEND_UNCERTAIN,
    DEDUPLICATE_RESULTS,
    MAX_POSTS_PER_RUN,
    DEBUG,
)

from eligibility import (
    Decision,
    evaluate_giveaway,
)


# ------------------------------------------------------------
# Environment variables
# ------------------------------------------------------------

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


# ------------------------------------------------------------
# Logging
# ------------------------------------------------------------

def log(message):
    if DEBUG:
        print(message)


# ------------------------------------------------------------
# Normalize a collected post
# ------------------------------------------------------------

def normalize_post(item):
    """
    Convert different platform/Apify formats into one
    common structure.
    """

    text_parts = [
        item.get("text"),
        item.get("caption"),
        item.get("description"),
        item.get("title"),
        item.get("content"),
    ]

    text = " ".join(
        str(x).strip()
        for x in text_parts
        if x
    )

    return {
        "id": item.get("id"),
        "platform": item.get("platform", "unknown"),
        "post_url": (
            item.get("post_url")
            or item.get("url")
            or item.get("webUrl")
            or item.get("link")
        ),
        "author": (
            item.get("author")
            or item.get("authorName")
            or item.get("username")
            or ""
        ),
        "published_at": (
            item.get("published_at")
            or item.get("timestamp")
            or item.get("date")
        ),
        "text": text,
        "title": item.get("title", ""),
        "description": item.get("description", ""),
        "media": item.get("media"),
        "transcript": item.get("transcript"),
        "engagement_data": item.get("engagement_data"),
    }


# ------------------------------------------------------------
# Deduplication
# ------------------------------------------------------------

def make_fingerprint(post):
    """
    Creates a stable fingerprint so the same giveaway isn't
    sent repeatedly.
    """

    url = (post.get("post_url") or "").strip().lower()

    if url:
        return hashlib.sha256(
            url.encode("utf-8")
        ).hexdigest()

    content = (
        post.get("text", "")
        + "|"
        + post.get("author", "")
    ).strip().lower()

    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


def deduplicate_posts(posts):
    seen = set()
    unique = []

    for post in posts:
        fingerprint = make_fingerprint(post)

        if fingerprint in seen:
            continue

        seen.add(fingerprint)
        unique.append(post)

    return unique


# ------------------------------------------------------------
# Apify collector
# ------------------------------------------------------------

def collect_from_apify(): from apify_collectors import collect_everything 
    return collect_everything( SEARCH_QUERIES, PLATFORMS, )
    """
    Collection layer.

    The actual Apify actor(s) will be configured here.

    We intentionally keep this separate from the eligibility
    engine so platform-specific scraping cannot change the
    giveaway rules.
    """

    if not APIFY_API_TOKEN:
        log("WARNING: APIFY_API_TOKEN is not configured.")
        return []

    log("Starting Apify collection...")

    # Actor configuration will be added once the exact Apify
    # actor(s) and input schema are selected.
    #
    # For now, return an empty list instead of pretending that
    # collection has succeeded.

    return []


# ------------------------------------------------------------
# Eligibility processing
# ------------------------------------------------------------

def process_posts(posts):
    results = []

    for raw_post in posts:

        post = normalize_post(raw_post)

        text = post.get("text", "").strip()

        if not text:
            continue

        result = evaluate_giveaway(text)

        result_data = {
            "post": post,
            "decision": result.decision,
            "reason": result.reason,
            "prize": getattr(result, "prize", None),
            "firm": getattr(result, "firm", None),
        }

        results.append(result_data)

        log(
            f"[{result.decision.value}] "
            f"{post.get('platform')} | "
            f"{post.get('post_url')}"
        )

    return results


# ------------------------------------------------------------
# Discord notification
# ------------------------------------------------------------

def send_discord_alert(result):
    if not DISCORD_WEBHOOK_URL:
        log("WARNING: DISCORD_WEBHOOK_URL is not configured.")
        return False

    post = result["post"]

    message = (
        "🎯 **ELIGIBLE PROP-FIRM GIVEAWAY**\n\n"
        f"**Prop Firm:** "
        f"{result.get('firm') or 'Not stated'}\n"
        f"**Prize:** "
        f"{result.get('prize') or 'Not stated'}\n"
        f"**Platform:** "
        f"{post.get('platform', 'Unknown')}\n"
        f"**Author:** "
        f"{post.get('author') or 'Unknown'}\n\n"
        f"**Post:** {post.get('post_url')}\n\n"
        f"**Entry:** Clearly eligible under detector rules."
    )

    response = requests.post(
        DISCORD_WEBHOOK_URL,
        json={"content": message},
        timeout=20,
    )

    if response.status_code in (200, 204):
        log("Discord alert sent.")
        return True

    log(
        f"Discord error: "
        f"{response.status_code} "
        f"{response.text[:300]}"
    )

    return False


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    print("=" * 60)
    print("PROP-FIRM GIVEAWAY DETECTOR")
    print("=" * 60)

    log(f"Search queries loaded: {len(SEARCH_QUERIES)}")
    log(f"Maximum posts per run: {MAX_POSTS_PER_RUN}")

    # 1. Collect
    raw_posts = collect_from_apify()

    log(f"Collected posts: {len(raw_posts)}")

    # 2. Normalize + deduplicate
    posts = [
        normalize_post(post)
        for post in raw_posts
    ]

    if DEDUPLICATE_RESULTS:
        posts = deduplicate_posts(posts)

    log(f"Unique posts: {len(posts)}")

    # 3. Evaluate
    results = process_posts(posts)

    eligible = [
        r for r in results
        if r["decision"] == Decision.ELIGIBLE
    ]

    uncertain = [
        r for r in results
        if r["decision"] == Decision.UNCERTAIN
    ]

    rejected = [
        r for r in results
        if r["decision"] == Decision.REJECT
    ]

    print()
    print(f"Eligible:  {len(eligible)}")
    print(f"Uncertain: {len(uncertain)}")
    print(f"Rejected:  {len(rejected)}")

    # 4. Discord
    sent = 0

    for result in eligible:

        if send_discord_alert(result):
            sent += 1

    # SEND_UNCERTAIN remains False by default.
    if SEND_UNCERTAIN:
        log(
            "WARNING: SEND_UNCERTAIN is enabled. "
            "This is not recommended."
        )

    print()
    print(f"Discord alerts sent: {sent}")
    print("Detector run complete.")


if __name__ == "__main__":
    main()
