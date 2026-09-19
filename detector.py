# ============================================================
# PROP-FIRM GIVEAWAY DETECTOR
# APIFY COLLECTORS
# ============================================================

import os
from apify_client import ApifyClient


APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")


ACTORS = {
    "web": "apify/google-search-scraper",
    "x": "apidojo/tweet-scraper",
    "youtube": "apigeek/youtube-scraper",
    "reddit": "scrapersdelight/reddit-search-scraper",
    "instagram": "apify/instagram-search-scraper",
    "facebook": "simpleapi/facebook-posts-search-scraper",
    "tiktok": "logical_scrapers/tiktok-search-scraper",
    "linkedin": "harvestapi/linkedin-post-search",
}


def build_input(platform, queries):

    if platform == "web":
        return {
            "queries": "\n".join(queries),
            "maxPagesPerQuery": 2,
        }

    if platform == "x":
        return {
            "searchTerms": queries,
            "maxItems": 50,
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
            "maxResultsPerQuery": 20,
            "sort": "new",
        }

    if platform == "instagram":
        return {
            "search": " OR ".join(queries),
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
            "maxItems": 50,
        }

    if platform == "linkedin":
        return {
            "searchQueries": queries,
            "maxPosts": 50,
            "postedLimit": "week",
        }

    return {}


def first_value(item, keys, default=""):

    for key in keys:

        value = item.get(key)

        if value is not None and value != "":
            return value

    return default


def normalize_item(item, platform):

    if not isinstance(item, dict):

        return {
            "platform": platform,
            "post_url": "",
            "author": "",
            "published_at": "",
            "text": str(item),
            "title": "",
            "description": "",
            "media": "",
            "transcript": "",
            "engagement_data": {},
        }

    return {
        "platform": platform,

        "post_url": first_value(
            item,
            [
                "url",
                "postUrl",
                "post_url",
                "tweetUrl",
                "webUrl",
                "link",
                "canonicalUrl",
            ],
        ),

        "author": first_value(
            item,
            [
                "author",
                "authorName",
                "username",
                "userName",
                "ownerUsername",
                "channelName",
            ],
        ),

        "published_at": first_value(
            item,
            [
                "publishedAt",
                "published_at",
                "createdAt",
                "created_at",
                "date",
                "timestamp",
            ],
        ),

        "text": first_value(
            item,
            [
                "text",
                "fullText",
                "content",
                "caption",
                "tweetText",
                "snippet",
            ],
        ),

        "title": first_value(
            item,
            [
                "title",
                "videoTitle",
                "name",
            ],
        ),

        "description": first_value(
            item,
            [
                "description",
                "desc",
                "snippet",
            ],
        ),

        "media": first_value(
            item,
            [
                "videoUrl",
                "imageUrl",
                "mediaUrl",
            ],
        ),

        "transcript": first_value(
            item,
            [
                "transcript",
                "transcription",
            ],
        ),

        "engagement_data": {},
    }


def run_actor(platform, queries):

    if not APIFY_API_TOKEN:
        raise RuntimeError(
            "APIFY_API_TOKEN is not configured."
        )

    if platform not in ACTORS:

        print(
            f"No Actor configured for platform: {platform}"
        )

        return []

    actor_id = ACTORS[platform]

    actor_input = build_input(
        platform,
        queries,
    )

    print(
        f"Starting Apify Actor: {actor_id}"
    )

    client = ApifyClient(
        APIFY_API_TOKEN
    )

    run = client.actor(
        actor_id
    ).call(
        run_input=actor_input
    )

    dataset_id = run.default_dataset_id

    if not dataset_id:

        print(
            f"No dataset returned for {platform}."
        )

        return []

    items = []

    for item in client.dataset(
        dataset_id
    ).iterate_items():

        # ----------------------------------------------------
        # GOOGLE SEARCH SCRAPER
        #
        # The current Apify Google Search Scraper can return
        # one search-page record containing:
        #
        # organicResults = [
        #     {
        #         title,
        #         url,
        #         description,
        #         ...
        #     }
        # ]
        #
        # We must flatten those into individual posts.
        # ----------------------------------------------------

        if (
            platform == "web"
            and isinstance(
                item.get("organicResults"),
                list,
            )
        ):

            organic_results = item.get(
                "organicResults",
                [],
            )

            query_info = item.get(
                "searchQuery",
                "",
            )

            if isinstance(
                query_info,
                dict,
            ):

                query_info = (
                    query_info.get("term")
                    or query_info.get("query")
                    or ""
                )

            for result in organic_results:

                if not isinstance(
                    result,
                    dict,
                ):
                    continue

                result_url = first_value(
                    result,
                    [
                        "url",
                        "link",
                        "resultUrl",
                    ],
                )

                # Never treat Google's own search page
                # as a giveaway post.
                if (
                    not result_url
                    or "google.com/search" in result_url.lower()
                    or "google.com/url" in result_url.lower()
                ):
                    continue

                result_copy = dict(result)

                if query_info:
                    result_copy["search_query"] = query_info

                normalized = normalize_item(
                    result_copy,
                    platform,
                )

                items.append(
                    normalized
                )

        else:

            # ------------------------------------------------
            # Other actors may already return one post per
            # dataset item.
            # ------------------------------------------------

            normalized = normalize_item(
                item,
                platform,
            )

            result_url = normalized.get(
                "post_url",
                "",
            )

            if (
                platform == "web"
                and (
                    not result_url
                    or "google.com/search"
                    in result_url.lower()
                    or "google.com/url"
                    in result_url.lower()
                )
            ):
                continue

            items.append(
                normalized
            )

    print(
        f"{platform}: {len(items)} individual results collected."
    )

    return items


def collect_everything(
    search_queries,
    platforms,
):

    all_posts = []

    for platform in platforms:

        print("")
        print("--------------------------------------------")
        print(
            f"Collecting platform: {platform}"
        )
        print("--------------------------------------------")

        try:

            posts = run_actor(
                platform,
                search_queries,
            )

            all_posts.extend(
                posts
            )

        except Exception as error:

            print(
                f"Apify error on {platform}: {error}"
            )

    print("")
    print(
        f"Total individual results collected across platforms: "
        f"{len(all_posts)}"
    )

    return all_posts
