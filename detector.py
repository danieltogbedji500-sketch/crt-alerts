# ============================================================
# PROP-FIRM GIVEAWAY DETECTOR
# Main detector engine
# ============================================================

import os
import hashlib
import requests

from config import SEARCH_QUERIES, PLATFORMS
from eligibility import evaluate_giveaway


APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def normalize_post(post):

    return {
        "platform": post.get("platform", "unknown"),
        "post_url": post.get("post_url") or post.get("url") or "",
        "author": post.get("author") or post.get("username") or "",
        "published_at": (
            post.get("published_at")
            or post.get("timestamp")
            or ""
        ),
        "text": post.get("text") or "",
        "title": post.get("title") or "",
        "description": post.get("description") or "",
        "media": post.get("media") or "",
        "transcript": post.get("transcript") or "",
        "engagement_data": (
            post.get("engagement_data") or {}
        ),
    }


def make_fingerprint(post):

    url = post.get(
        "post_url",
        "",
    ).strip().lower()

    if url:

        source = url

    else:

        source = (
            post.get("platform", "")
            + "|"
            + post.get("author", "")
            + "|"
            + post.get("text", "")
            + "|"
            + post.get("title", "")
        )

    return hashlib.sha256(
        source.encode("utf-8")
    ).hexdigest()


def deduplicate_posts(posts):

    seen = set()
    unique_posts = []

    for post in posts:

        fingerprint = make_fingerprint(
            post
        )

        if fingerprint in seen:
            continue

        seen.add(fingerprint)

        unique_posts.append(
            post
        )

    return unique_posts


def collect_from_apify():

    from apify_collectors import (
        collect_everything
    )

    return collect_everything(
        SEARCH_QUERIES,
        PLATFORMS,
    )


def build_post_text(post):

    parts = [
        post.get("title", ""),
        post.get("text", ""),
        post.get("description", ""),
        post.get("transcript", ""),
    ]

    return "\n".join(
        part.strip()
        for part in parts
        if part and part.strip()
    )


def send_discord_alert(
    post,
    result,
):

    if not DISCORD_WEBHOOK_URL:

        print(
            "DISCORD_WEBHOOK_URL is not configured."
        )

        return False

    entry_method = getattr(
        result,
        "entry_method",
        None,
    ) or "Clearly eligible under detector rules."

    prop_firm = getattr(
        result,
        "prop_firm",
        None,
    ) or "Not clearly stated"

    prize = getattr(
        result,
        "prize",
        None,
    ) or "Not clearly stated"

    winners = getattr(
        result,
        "winners",
        None,
    ) or "Not stated"

    message = (
        "🎯 **ELIGIBLE PROP-FIRM GIVEAWAY**\n\n"
        f"**Prop Firm:** {prop_firm}\n"
        f"**Prize:** {prize}\n"
        f"**Winners:** {winners}\n"
        f"**Platform:** "
        f"{post.get('platform', 'Unknown')}\n"
        f"**Author:** "
        f"{post.get('author', 'Unknown')}\n\n"
        f"**Post:** "
        f"{post.get('post_url', '')}\n\n"
        f"**Entry:** {entry_method}"
    )

    try:

        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json={
                "content": message,
            },
            timeout=20,
        )

        if response.status_code in (
            200,
            204,
        ):

            print(
                "Discord alert sent successfully: "
                f"{post.get('post_url', '')}"
            )

            return True

        print(
            "Discord webhook failed: "
            f"HTTP {response.status_code}"
        )

        print(
            response.text[:1000]
        )

        return False

    except Exception as error:

        print(
            f"Discord webhook error: {error}"
        )

        return False


def process_posts(posts):

    eligible_count = 0
    uncertain_count = 0
    rejected_count = 0
    alerts_sent = 0

    print(
        f"Processing {len(posts)} posts..."
    )

    print("")
    print(
        "========== SAMPLE COLLECTED POSTS =========="
    )

    for sample in posts[:5]:

        print(
            "PLATFORM:",
            sample.get(
                "platform",
                "",
            ),
        )

        print(
            "TITLE:",
            sample.get(
                "title",
                "",
            ),
        )

        print(
            "TEXT:",
            sample.get(
                "text",
                "",
            )[:500],
        )

        print(
            "DESCRIPTION:",
            sample.get(
                "description",
                "",
            )[:500],
        )

        print(
            "URL:",
            sample.get(
                "post_url",
                "",
            ),
        )

        print(
            "--------------------------------------------"
        )

    print(
        "============================================"
    )

    print("")

    for index, raw_post in enumerate(
        posts,
        start=1,
    ):

        post = normalize_post(
            raw_post
        )

        text = build_post_text(
            post
        )

        if not text.strip():

            rejected_count += 1

            continue

        try:

            result = evaluate_giveaway(
                text
            )

        except Exception as error:

            print(
                f"Eligibility error on post "
                f"{index}: {error}"
            )

            continue

        decision = getattr(
            result,
            "decision",
            None,
        )

        decision_value = getattr(
            decision,
            "value",
            str(decision),
        )

        print(
            f"Post {index}: "
            f"{decision_value} | "
            f"{post.get('platform', 'unknown')} | "
            f"{post.get('post_url', '')}"
        )

        if decision_value == "ELIGIBLE":

            eligible_count += 1

            if send_discord_alert(
                post,
                result,
            ):

                alerts_sent += 1

        elif decision_value == "UNCERTAIN":

            uncertain_count += 1

        else:

            rejected_count += 1

    print("")

    print(
        "========== DETECTOR SUMMARY =========="
    )

    print(
        f"Total posts:    {len(posts)}"
    )

    print(
        f"Eligible:       {eligible_count}"
    )

    print(
        f"Uncertain:      {uncertain_count}"
    )

    print(
        f"Rejected:       {rejected_count}"
    )

    print(
        f"Discord alerts: {alerts_sent}"
    )

    print(
        "======================================="
    )

    return {
        "total": len(posts),
        "eligible": eligible_count,
        "uncertain": uncertain_count,
        "rejected": rejected_count,
        "alerts_sent": alerts_sent,
    }


def main():

    print(
        "=============================================="
    )

    print(
        "PROP-FIRM GIVEAWAY DETECTOR"
    )

    print(
        "=============================================="
    )

    print("")

    print(
        "Detector starting..."
    )

    print(
        f"Platforms configured: {PLATFORMS}"
    )

    print(
        f"Search queries: {len(SEARCH_QUERIES)}"
    )

    if not APIFY_API_TOKEN:

        print(
            "ERROR: APIFY_API_TOKEN is not configured."
        )

        return

    if not DISCORD_WEBHOOK_URL:

        print(
            "WARNING: DISCORD_WEBHOOK_URL "
            "is not configured."
        )

    print("")

    print(
        "Starting Apify collection..."
    )

    try:

        collected_posts = (
            collect_from_apify()
        )

    except Exception as error:

        print(
            f"Apify collection failed: {error}"
        )

        return

    if not collected_posts:

        print(
            "No posts were collected."
        )

        return

    print("")

    print(
        f"Collected {len(collected_posts)} "
        "individual results."
    )

    normalized_posts = [
        normalize_post(post)
        for post in collected_posts
    ]

    unique_posts = deduplicate_posts(
        normalized_posts
    )

    print(
        f"After deduplication: "
        f"{len(unique_posts)} posts."
    )

    print("")

    process_posts(
        unique_posts
    )

    print("")

    print(
        "Detector run complete."
    )


if __name__ == "__main__":

    main()
