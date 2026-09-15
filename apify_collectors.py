```python
# ============================================================
# PROP-FIRM GIVEAWAY DETECTOR
# APIFY COLLECTION LAYER
# ============================================================

import os
from apify_client import ApifyClient


APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")

if not APIFY_TOKEN:
    raise RuntimeError("APIFY_API_TOKEN is not set.")


client = ApifyClient(APIFY_TOKEN)


# ------------------------------------------------------------
# VERIFIED APIFY ACTORS
# ------------------------------------------------------------

ACTORS = {
    # Broad web discovery
    "web": "apify/google-search-scraper",

    # X / Twitter
    "x": "apidojo/tweet-scraper",

    # YouTube
    "youtube": "apigeek/youtube-scraper",

    # Reddit
    "reddit": "scrapersdelight/reddit-search-scraper",

    # Instagram
    "instagram": "apify/instagram-search-scraper",

    # Facebook
    "facebook": "simpleapi/facebook-posts-search-scraper",

    # TikTok
    "tiktok": "logical_scrapers/tiktok-search-scraper",

    # LinkedIn
    "linkedin": "harvestapi/linkedin-post-search",
}


# ------------------------------------------------------------
# PLATFORM-SPECIFIC INPUT BUILDERS
# ------------------------------------------------------------

def build_input(platform, queries):
    """
    Build the correct input format for each verified Actor.
    """

    if platform == "web":
        # Google Search Scraper accepts newline-separated queries.
        return {
            "queries": "\n".join(queries),
            "maxPagesPerQuery": 3,
        }

    if platform == "x":
        return {
            "searchTerms": queries,
            "maxItems": 100,
            "sort": "Latest",
        }

    if platform == "youtube":
        return {
            "searchQueries": queries,
            "maxResultsPerQuery": 20,
        }

    if platform == "reddit":
        return {
            "searchQueries": queries,
            "maxResultsPerQuery": 50,
            "sort": "new",
        }

    if platform == "instagram":
        # Instagram Search Scraper uses keyword search.
        return {
            "search": ", ".join(queries),
            "searchType": "popular_reels",
            "maxResults": 50,
        }

    if platform == "facebook":
        return {
            "searchQueries": queries,
            "maxPosts": 50,
            "postTimeRange": "7d",
        }

    if platform == "tiktok":
        return {
            "searchQueries": queries,
            "maxItems": 20,
        }

    if platform == "linkedin":
        return {
            "searchQueries": queries[:10],
            "maxPosts": 25,
            "postedLimit": "week",
        }

    raise ValueError(f"Unsupported platform: {platform}")


# ------------------------------------------------------------
# SAFE FIELD EXTRACTION
# ------------------------------------------------------------

def first_value(item, *keys):
    """
    Return the first useful value found among possible field names.
    Different Apify Actors use different output schemas.
    """

    for key in keys:
        value = item.get(key)

        if value is not None and value != "":
            return value

    return ""


def normalize_item(item, platform):
    """
    Convert different Apify output formats into one common post format.
    """

    text = first_value(
        item,
        "text",
        "caption",
        "description",
        "title",
        "content",
        "postText",
        "tweetText",
    )

    title = first_value(
        item,
        "title",
        "name",
        "videoTitle",
    )

    url = first_value(
        item,
        "url",
        "postUrl",
        "postURL",
        "tweetUrl",
        "videoUrl",
        "webpageUrl",
        "permalink",
        "link",
    )

    author = first_value(
        item,
        "authorName",
        "author",
        "username",
        "ownerUsername",
        "pageName",
        "channelName",
        "creator",
        "userName",
    )

    published_at = first_value(
        item,
        "publishedAt",
        "published_at",
        "createdAt",
        "created_at",
        "timestamp",
        "time",
        "date",
        "uploadDate",
    )

    return {
        "platform": platform,
        "post_url": url,
        "author": author,
        "published_at": published_at,
        "text": str(text or ""),
        "title": str(title or ""),
        "description": str(
            item.get("description")
            or item.get("caption")
            or ""
        ),
        "media": item.get("media") or [],
        "engagement_data": {
            "likes": first_value(
                item,
                "likes",
                "likeCount",
                "likesCount",
            ),
            "comments": first_value(
                item,
                "comments",
                "commentCount",
                "commentsCount",
            ),
            "shares": first_value(
                item,
                "shares",
                "shareCount",
                "sharesCount",
                "retweets",
                "retweetCount",
            ),
            "views": first_value(
                item,
                "views",
                "viewCount",
                "playCount",
            ),
        },
    }


# ------------------------------------------------------------
# RUN ONE ACTOR
# ------------------------------------------------------------

def run_actor(platform, queries):
    """
    Run one Apify Actor and return normalized posts.
    """

    actor_id = ACTORS.get(platform)

    if not actor_id:
        print(f"[SKIP] No Actor configured for {platform}")
        return []

    try:
        actor_input = build_input(platform, queries)

        print(f"[APIFY] Starting {platform}: {actor_id}")

        run = client.actor(actor_id).call(
            run_input=actor_input
        )

        dataset_id = run.get("defaultDatasetId")

        if not dataset_id:
            print(f"[APIFY] No dataset returned for {platform}")
            return []

        results = []

        for item in client.dataset(dataset_id).iterate_items():
            normalized = normalize_item(item, platform)

            # Ignore completely empty rows.
            if (
                not normalized["text"].strip()
                and not normalized["title"].strip()
            ):
                continue

            results.append(normalized)

        print(
            f"[APIFY] {platform}: "
            f"{len(results)} usable results"
        )

        return results

    except Exception as exc:
        print(
            f"[APIFY ERROR] {platform}: "
            f"{type(exc).__name__}: {exc}"
        )
        return []


# ------------------------------------------------------------
# MAIN COLLECTION FUNCTION
# ------------------------------------------------------------

def collect_everything(queries, platforms=None):
    """
    Collect giveaway candidates from all configured platforms.

    The 'web' collector is especially important because it gives
    us broader discovery across platforms that do not have a
    reliable public keyword-search Actor.
    """

    if platforms is None:
        platforms = list(ACTORS.keys())

    all_posts = []

    for platform in platforms:
        print("=" * 60)
        print(f"COLLECTING: {platform.upper()}")

        posts = run_actor(
            platform,
            queries,
        )

        all_posts.extend(posts)

    print("=" * 60)
    print(
        f"[APIFY] TOTAL RAW RESULTS: "
        f"{len(all_posts)}"
    )

    return all_posts
```



### Important correction

I deliberately made **Google/web discovery part of the system**, not an afterthought.

That matters because we want the detector to discover a **brand-new prop firm** without already knowing its name. Google Search can use operators such as `site:` and search multiple queries in one run.

So the architecture becomes:

**Direct social searches**
→ X
→ YouTube
→ Reddit
→ Instagram
→ Facebook
→ TikTok
→ LinkedIn

**PLUS broad web discovery**
→ Google
→ can surface Threads, Telegram, Pinterest, Twitch, Discord pages, Bluesky, Mastodon, Medium, Substack, Quora, Vimeo, Dailymotion, GitHub, etc., when publicly indexed.

This is more realistic than pretending one scraper can literally access every public post on every platform.

### Step 2 — One small change to `detector.py`

Your current `detector.py` has the placeholder:

```python
def collect_from_apify():
    return []
```

Replace that function with:

```python
def collect_from_apify():
    from apify_collectors import collect_everything

    return collect_everything(
        SEARCH_QUERIES,
        PLATFORMS,
    )
```

And make sure the imports at the top include:

```python
from config import (
    SEARCH_QUERIES,
    PLATFORMS,
)
```

**Do not put the Apify token in either file.** Your GitHub Secret handles that.

The Actors above are based on their currently documented input formats; for example, X's current Actor uses `searchTerms`, Facebook's keyword-search Actor uses `searchQueries`, and LinkedIn's post-search Actor uses `searchQueries`.

Once those two edits are committed, **don't run the workflow yet**. The next step is to tighten the search queries and make sure the eligibility engine correctly distinguishes **mandatory engagement** from merely mentioning likes/reposts/follows.
