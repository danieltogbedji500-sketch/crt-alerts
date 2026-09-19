import os
import json
import hashlib
import time
from urllib.parse import urlsplit, urlunsplit

import requests

from eligibility import evaluate_giveaway
from apify_collectors import collect_everything
from config import PLATFORMS


APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

ALERT_STATE_FILE = "alerted_urls.json"


def canonicalize_url(url):
    if not url:
        return ""

    try:
        parts = urlsplit(url)

        clean = urlunsplit(
            (
                parts.scheme,
                parts.netloc,
                parts.path.rstrip("/"),
                "",
                "",
            )
        )

        return clean

    except Exception:
        return url.strip()


def load_alerted_urls():
    if not os.path.exists(ALERT_STATE_FILE):
        return set()

    try:
        with open(ALERT_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return set(data)

    except Exception as e:
        print(f"Could not load alert memory: {e}")

    return set()


def save_alerted_urls(alerted_urls):
    try:
        with open(ALERT_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(
                sorted(alerted_urls),
                f,
                indent=2,
                ensure_ascii=False,
            )

    except Exception as e:
        print(f"Could not save alert memory: {e}")


def normalize_post(post):
    return {
        "platform": post.get("platform", ""),
        "post_url": post.get("post_url", ""),
        "author": post.get("author", ""),
        "published_at": post.get("published_at", ""),
        "text": post.get("text", ""),
        "title": post.get("title", ""),
        "description": post.get("description", ""),
        "media": post.get("media", ""),
    }


def make_fingerprint(post):
    raw = " | ".join(
        [
            str(post.get("platform", "")),
            str(post.get("post_url", "")),
            str(post.get("author", "")),
            str(post.get("published_at", "")),
            str(post.get("text", "")),
            str(post.get("title", "")),
        ]
    )

    return hashlib.sha256(
        raw.encode("utf-8", errors="ignore")
    ).hexdigest()


def deduplicate_posts(posts):
    unique = []
    seen = set()

    for post in posts:
        fingerprint = make_fingerprint(post)

        if fingerprint in seen:
            continue

        seen.add(fingerprint)
        unique.append(post)

    return unique


def build_post_text(post):
    parts = [
        post.get("title", ""),
        post.get("text", ""),
        post.get("description", ""),
        post.get("media", ""),
    ]

    return "\n".join(
        str(part)
        for part in parts
        if part
    )


def send_discord_alert(post, result):
    if not DISCORD_WEBHOOK_URL:
        print("DISCORD_WEBHOOK_URL is missing.")
        return False

    platform = post.get("platform", "Unknown")
    url = post.get("post_url", "")

    prop_firm = getattr(result, "prop_firm", None) or "Not stated"
    prize = getattr(result, "prize", None) or "Not stated"
    winners = getattr(result, "winners", None) or "Not stated"
    entry_method = (
        getattr(result, "entry_method", None)
        or "Not clearly stated"
    )

    message = (
        "🎯 **ELIGIBLE PROP-FIRM GIVEAWAY**\n\n"
        f"**Prop Firm:** {prop_firm}\n"
        f"**Prize:** {prize}\n"
        f"**Winners:** {winners}\n"
        f"**Eligible Entry Method:** {entry_method}\n"
        f"**Platform:** {platform}\n"
        f"**Post:** {url}"
    )

    payload = {
        "content": message
    }

    for attempt in range(1, 6):
        try:
            response = requests.post(
                DISCORD_WEBHOOK_URL,
                json=payload,
                timeout=30,
            )

            if 200 <= response.status_code < 300:
                print("Discord alert sent successfully.")
                return True

            if response.status_code == 429:
                retry_after = 1

                try:
                    data = response.json()
                    retry_after = float(
                        data.get("retry_after", 1)
                    )
                except Exception:
                    pass

                retry_after = min(retry_after, 60)

                print(
                    f"Discord rate limited (429). "
                    f"Waiting {retry_after} seconds..."
                )

                time.sleep(retry_after)
                continue

            if 500 <= response.status_code < 600:
                wait_time = min(2 ** attempt, 30)

                print(
                    f"Discord server error "
                    f"({response.status_code}). "
                    f"Retrying in {wait_time}s..."
                )

                time.sleep(wait_time)
                continue

            print(
                f"Discord webhook failed: "
                f"HTTP {response.status_code}"
            )

            print(
                f"Discord response: "
                f"{response.text[:500]}"
            )

            return False

        except requests.RequestException as e:
            wait_time = min(2 ** attempt, 30)

            print(
                f"Discord request error "
                f"(attempt {attempt}/5): {e}"
            )

            if attempt < 5:
                time.sleep(wait_time)

    print("Discord alert failed after 5 attempts.")
    return False


def process_posts(posts, alerted_urls):
    eligible_count = 0
    uncertain_count = 0
    rejected_count = 0
    already_alerted_count = 0
    discord_alert_count = 0
    discord_failure_count = 0

    for index, raw_post in enumerate(posts, start=1):
        post = normalize_post(raw_post)

        url = canonicalize_url(
            post.get("post_url", "")
        )

        if not url:
            print(
                f"[{index}] Skipping post without URL."
            )
            continue

        post["post_url"] = url

        if url in alerted_urls:
            print(
                f"[{index}] ALREADY ALERTED: {url}"
            )

            already_alerted_count += 1
            continue

        text = build_post_text(post).strip()

        if not text:
            print(
                f"[{index}] Skipping empty post."
            )
            continue

        result = evaluate_giveaway(text)

        decision = getattr(result, "decision", None)

        if decision is None:
            print(
                f"[{index}] Could not determine decision: {url}"
            )
            continue

        decision_value = getattr(
            decision,
            "value",
            str(decision)
        )

        if decision_value == "ELIGIBLE":
            eligible_count += 1

            print(
                f"[{index}] ELIGIBLE: {url}"
            )

            success = send_discord_alert(
                post,
                result
            )

            if success:
                discord_alert_count += 1

                alerted_urls.add(url)
                save_alerted_urls(alerted_urls)

            else:
                discord_failure_count += 1

        elif decision_value == "UNCERTAIN":
            uncertain_count += 1

            print(
                f"[{index}] UNCERTAIN: {url}"
            )

        else:
            rejected_count += 1

            print(
                f"[{index}] REJECTED: {url}"
            )

    print()
    print("========== DETECTOR SUMMARY ==========")
    print(f"Total posts:       {len(posts)}")
    print(f"Eligible:          {eligible_count}")
    print(f"Uncertain:         {uncertain_count}")
    print(f"Rejected:          {rejected_count}")
    print(f"Already alerted:   {already_alerted_count}")
    print(f"Discord alerts:    {discord_alert_count}")
    print(f"Discord failures:  {discord_failure_count}")
    print("=======================================")


def main():
    print("🚨 PROP-FIRM GIVEAWAY DETECTOR STARTED")

    if not APIFY_API_TOKEN:
        print("ERROR: APIFY_API_TOKEN is missing.")
        return

    if not DISCORD_WEBHOOK_URL:
        print("ERROR: DISCORD_WEBHOOK_URL is missing.")
        return

    print("Loading previous alert memory...")

    alerted_urls = load_alerted_urls()

    print(
        f"Previously alerted URLs: "
        f"{len(alerted_urls)}"
    )

    print("Collecting posts from Apify...")

    try:
        posts = collect_everything(
            APIFY_API_TOKEN,
            PLATFORMS
        )

    except Exception as e:
        print(
            f"ERROR while collecting posts: {e}"
        )
        return

    print(
        f"Collected {len(posts)} raw posts."
    )

    posts = deduplicate_posts(posts)

    print(
        f"After deduplication: "
        f"{len(posts)} posts."
    )

    process_posts(
        posts,
        alerted_urls
    )


if __name__ == "__main__":
    main()
