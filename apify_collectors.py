# ============================================================
# APIFY COLLECTION LAYER
# ============================================================

import os
from apify_client import ApifyClient


APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")


# ------------------------------------------------------------
# Actor configuration
# ------------------------------------------------------------
#
# We keep actor IDs here instead of scattering them throughout
# detector.py.
#
# These can be changed independently as we test each collector.
#

ACTORS = {
    "instagram": os.getenv("APIFY_INSTAGRAM_ACTOR"),
    "facebook": os.getenv("APIFY_FACEBOOK_ACTOR"),
    "linkedin": os.getenv("APIFY_LINKEDIN_ACTOR"),
    "youtube": os.getenv("APIFY_YOUTUBE_ACTOR"),
    "reddit": os.getenv("APIFY_REDDIT_ACTOR"),
    "tiktok": os.getenv("APIFY_TIKTOK_ACTOR"),
    "x": os.getenv("APIFY_X_ACTOR"),
    "threads": os.getenv("APIFY_THREADS_ACTOR"),
    "telegram": os.getenv("APIFY_TELEGRAM_ACTOR"),
    "web": os.getenv("APIFY_WEB_ACTOR"),
}


# ------------------------------------------------------------
# Run one Actor
# ------------------------------------------------------------

def run_actor(actor_id, run_input):
    if not APIFY_API_TOKEN:
        print("ERROR: APIFY_API_TOKEN is missing.")
        return []

    if not actor_id:
        return []

    client = ApifyClient(APIFY_API_TOKEN)

    print(f"Running Apify Actor: {actor_id}")

    try:
        run = client.actor(actor_id).call(
            run_input=run_input
        )

        if not run:
            print("Actor returned no run.")
            return []

        dataset_id = run.default_dataset_id

        if not dataset_id:
            print("Actor returned no dataset.")
            return []

        items = client.dataset(dataset_id).list_items().items

        print(
            f"Actor completed: {actor_id} | "
            f"Results: {len(items)}"
        )

        return items

    except Exception as error:
        print(
            f"Actor failed: {actor_id} | "
            f"{error}"
        )

        return []


# ------------------------------------------------------------
# Generic keyword search
# ------------------------------------------------------------

def search_actor(
    platform,
    queries,
    results_limit=20
):
    """
    Run a configured Actor using search queries.

    Different Apify Actors have different input schemas.
    Therefore the exact input is supplied by the platform
    adapter below rather than pretending every Actor accepts
    the same parameters.
    """

    actor_id = ACTORS.get(platform)

    if not actor_id:
        print(
            f"[{platform}] Actor not configured yet."
        )
        return []

    all_results = []

    for query in queries:

        run_input = build_input(
            platform,
            query,
            results_limit
        )

        if run_input is None:
            continue

        results = run_actor(
            actor_id,
            run_input
        )

        for item in results:
            item["platform"] = platform
            all_results.append(item)

    return all_results


# ------------------------------------------------------------
# Platform-specific input builders
# ------------------------------------------------------------

def build_input(
    platform,
    query,
    results_limit
):
    """
    Build the input expected by each configured Actor.

    IMPORTANT:
    Actor schemas differ, so these mappings are kept isolated.
    """

    if platform == "instagram":
        return {
            "search": query,
            "resultsLimit": results_limit,
        }

    if platform == "youtube":
        return {
            "searchQueries": [query],
            "maxResults": results_limit,
        }

    if platform == "reddit":
        return {
            "searches": [query],
            "maxItems": results_limit,
        }

    if platform == "tiktok":
        return {
            "searchQueries": [query],
            "resultsPerPage": results_limit,
        }

    if platform == "facebook":
        return {
            "searchQueries": [query],
            "maxPosts": results_limit,
        }

    if platform == "linkedin":
        return {
            "searchQueries": [query],
            "maxResults": results_limit,
        }

    if platform == "threads":
        return {
            "searchQueries": [query],
            "maxResults": results_limit,
        }

    if platform == "x":
        return {
            "searchQueries": [query],
            "maxItems": results_limit,
        }

    if platform == "telegram":
        return {
            "searchQueries": [query],
            "maxResults": results_limit,
        }

    if platform == "web":
        return {
            "queries": [query],
            "maxResults": results_limit,
        }

    print(
        f"No input adapter configured for: {platform}"
    )

    return None


# ------------------------------------------------------------
# Collect everything
# ------------------------------------------------------------

def collect_everything(
    search_queries,
    results_per_query=20,
    max_posts=500
):

    all_posts = []

    for platform in ACTORS:

        print()
        print(
            f"========== {platform.upper()} =========="
        )

        results = search_actor(
            platform,
            search_queries,
            results_per_query
        )

        all_posts.extend(results)

        if len(all_posts) >= max_posts:
            break

    return all_posts
