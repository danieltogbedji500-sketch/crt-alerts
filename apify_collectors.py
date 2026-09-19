import requests


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


def first_value(item, keys, default=""):
    for key in keys:
        value = item.get(key)

        if value is not None and value != "":
            return value

    return default


def build_input(platform, query):
    if platform == "web":
        return {
            "queries": query,
            "maxPagesPerQuery": 1,
            "resultsPerPage": 20,
            "languageCode": "en",
            "countryCode": "us",
        }

    if platform == "x":
        return {
            "searchTerms": [query],
            "maxItems": 20,
        }

    if platform == "youtube":
        return {
            "searchQueries": [query],
            "maxResults": 20,
        }

    if platform == "reddit":
        return {
            "searches": [query],
            "maxItems": 20,
        }

    if platform == "instagram":
        return {
            "search": query,
            "resultsLimit": 20,
        }

    if platform == "facebook":
        return {
            "searchQueries": [query],
            "maxItems": 20,
        }

    if platform == "tiktok":
        return {
            "searchQueries": [query],
            "maxItems": 20,
        }

    if platform == "linkedin":
        return {
            "searchQueries": [query],
            "maxResults": 20,
        }

    return {
        "query": query,
    }


def normalize_item(item, platform):
    if not isinstance(item, dict):
        return None

    url = first_value(
        item,
        [
            "url",
            "link",
            "postUrl",
            "postURL",
            "webpageUrl",
            "pageUrl",
            "canonicalUrl",
            "videoUrl",
            "video_url",
        ],
    )

    title = first_value(
        item,
        [
            "title",
            "name",
            "headline",
            "videoTitle",
        ],
    )

    text = first_value(
        item,
        [
            "text",
            "content",
            "postText",
            "caption",
            "body",
            "tweetText",
            "description",
        ],
    )

    description = first_value(
        item,
        [
            "description",
            "snippet",
            "summary",
        ],
    )

    author = first_value(
        item,
        [
            "author",
            "authorName",
            "username",
            "userName",
            "channelName",
            "ownerUsername",
        ],
    )

    published_at = first_value(
        item,
        [
            "publishedAt",
            "publishDate",
            "date",
            "createdAt",
            "timestamp",
        ],
    )

    # Build useful searchable text.
    combined_text = "\n".join(
        str(value)
        for value in [
            title,
            text,
            description,
        ]
        if value
    )

    if not url and not combined_text:
        return None

    return {
        "platform": platform,
        "post_url": str(url or ""),
        "author": str(author or ""),
        "published_at": str(published_at or ""),
        "text": str(combined_text),
        "title": str(title or ""),
        "description": str(description or ""),
        "media": "",
    }


def run_actor(api_token, actor_id, actor_input, platform):
    print(
        f"Running Apify actor: {actor_id} "
        f"for platform: {platform}"
    )

    url = (
        "https://api.apify.com/v2/acts/"
        f"{actor_id.replace('/', '~')}/runs"
    )

    response = requests.post(
        url,
        params={
            "token": api_token,
        },
        json=actor_input,
        timeout=60,
    )

    response.raise_for_status()

    run = response.json().get("data", {})

    run_id = run.get("id")
    dataset_id = run.get("defaultDatasetId")

    if not run_id:
        raise RuntimeError(
            f"Apify did not return a run ID for {actor_id}"
        )

    if not dataset_id:
        raise RuntimeError(
            f"Apify did not return a dataset ID for {actor_id}"
        )

    print(
        f"Apify run started: {run_id}"
    )

    # Wait for the actor to finish.
    status_url = (
        f"https://api.apify.com/v2/actor-runs/"
        f"{run_id}"
    )

    for attempt in range(60):
        status_response = requests.get(
            status_url,
            params={
                "token": api_token,
            },
            timeout=60,
        )

        status_response.raise_for_status()

        status_data = status_response.json().get(
            "data",
            {}
        )

        status = status_data.get("status")

        print(
            f"Apify status: {status}"
        )

        if status in {
            "SUCCEEDED",
            "FAILED",
            "ABORTED",
            "TIMED-OUT",
        }:
            break

        import time

        time.sleep(2)

    if status != "SUCCEEDED":
        raise RuntimeError(
            f"Apify actor {actor_id} ended with "
            f"status: {status}"
        )

    dataset_url = (
        f"https://api.apify.com/v2/datasets/"
        f"{dataset_id}/items"
    )

    dataset_response = requests.get(
        dataset_url,
        params={
            "token": api_token,
            "clean": "true",
        },
        timeout=60,
    )

    dataset_response.raise_for_status()

    items = dataset_response.json()

    if not isinstance(items, list):
        return []

    normalized = []

    for item in items:

        # Google Search actor can return one object
        # containing all organic results.
        if platform == "web":

            organic_results = item.get(
                "organicResults"
            )

            if isinstance(
                organic_results,
                list
            ):
                for result in organic_results:

                    normalized_item = normalize_item(
                        result,
                        platform
                    )

                    if normalized_item:
                        normalized.append(
                            normalized_item
                        )

                continue

        normalized_item = normalize_item(
            item,
            platform
        )

        if normalized_item:
            normalized.append(
                normalized_item
            )

    return normalized


def collect_everything(api_token, platforms):
    all_posts = []

    for platform in platforms:

        actor_id = ACTORS.get(platform)

        if not actor_id:
            print(
                f"No Apify actor configured for "
                f"platform: {platform}"
            )
            continue

        for query in SEARCH_QUERIES:

            print()
            print(
                f"Searching {platform}: {query}"
            )

            try:
                actor_input = build_input(
                    platform,
                    query
                )

                results = run_actor(
                    api_token,
                    actor_id,
                    actor_input,
                    platform
                )

                print(
                    f"Found {len(results)} results "
                    f"for this search."
                )

                all_posts.extend(results)

            except Exception as e:
                print(
                    f"ERROR for {platform} / "
                    f"{query}: {e}"
                )

    return all_posts
