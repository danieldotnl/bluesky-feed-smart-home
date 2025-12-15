"""Search module for fetching posts from Bluesky."""

import os
from datetime import UTC, datetime, timedelta

from atproto import AsyncClient
from atproto.exceptions import AtProtocolError

from src.config import LANGUAGE, SEARCH_TIME_WINDOW_DAYS, load_keywords

# Maximum pages to fetch per keyword to avoid excessive API calls
MAX_PAGES_PER_KEYWORD = 3


def parse_keywords(keywords: list[str]) -> tuple[list[str], list[str]]:
    """Separate keywords into hashtags and phrases.

    Args:
        keywords: List of search terms

    Returns:
        Tuple of (hashtags without #, phrases)
    """
    tags = []
    phrases = []
    for keyword in keywords:
        if keyword.startswith("#"):
            tags.append(keyword[1:])  # Remove # prefix
        else:
            phrases.append(keyword)
    return tags, phrases


async def get_authenticated_client() -> AsyncClient:
    """Create and authenticate an AsyncClient for API access."""
    client = AsyncClient()

    # Check if credentials are available for authenticated access
    handle = os.environ.get("BSKY_HANDLE")
    password = os.environ.get("BSKY_PASSWORD")

    if handle and password:
        await client.login(handle, password)
        print(f"Authenticated as {handle}")
    else:
        print("Warning: No credentials found. Searching may fail without authentication.")

    return client


def get_since_timestamp() -> str:
    """Get ISO timestamp for search time window start."""
    since = datetime.now(UTC) - timedelta(days=SEARCH_TIME_WINDOW_DAYS)
    return since.strftime("%Y-%m-%dT%H:%M:%SZ")


async def search_posts_paginated(
    client: AsyncClient,
    query: str | None = None,
    tag: str | None = None,
    limit_per_page: int = 100,
    max_pages: int = MAX_PAGES_PER_KEYWORD,
) -> list[dict]:
    """Search Bluesky for posts with pagination.

    Args:
        client: Authenticated AsyncClient
        query: Search query string (for phrases)
        tag: Hashtag to filter by (without # prefix)
        limit_per_page: Results per page (max 100)
        max_pages: Maximum pages to fetch

    Returns:
        List of posts as dictionaries
    """
    all_posts = []
    cursor = None
    since = get_since_timestamp()

    for page in range(max_pages):
        params = {
            "lang": LANGUAGE,
            "limit": limit_per_page,
            "sort": "latest",
            "since": since,
        }

        if query:
            params["q"] = query
        if tag:
            params["tag"] = [tag]

        if cursor:
            params["cursor"] = cursor

        response = await client.app.bsky.feed.search_posts(params=params)

        # Convert posts to dict format
        posts = [
            post.model_dump() if hasattr(post, "model_dump") else dict(post)
            for post in response.posts
        ]
        all_posts.extend(posts)

        # Check if there are more results
        cursor = response.cursor
        if not cursor or len(response.posts) < limit_per_page:
            break

    return all_posts


async def fetch_all_posts() -> list[dict]:
    """Fetch posts for all configured keywords and deduplicate.

    Uses the tag parameter for hashtag searches (more precise facet matching)
    and the q parameter for phrase searches.
    """
    all_posts: dict[str, dict] = {}
    keywords = load_keywords()

    if not keywords:
        print("Warning: No keywords found in data/keywords.txt")
        return []

    tags, phrases = parse_keywords(keywords)

    # Create a single authenticated client for all searches
    client = await get_authenticated_client()

    # Search by hashtags using tag parameter (precise facet matching)
    for tag in tags:
        try:
            posts = await search_posts_paginated(client, tag=tag)
            new_count = 0
            for post in posts:
                uri = post.get("uri")
                if uri and uri not in all_posts:
                    all_posts[uri] = post
                    new_count += 1
            print(f"  #{tag}: {len(posts)} posts ({new_count} new)")
        except AtProtocolError as e:
            print(f"Error searching for #{tag}: {e}")

    # Search by phrases using q parameter
    # Wrap multi-word phrases in quotes for exact phrase matching
    for phrase in phrases:
        try:
            query = f'"{phrase}"' if " " in phrase else phrase
            posts = await search_posts_paginated(client, query=query)
            new_count = 0
            for post in posts:
                uri = post.get("uri")
                if uri and uri not in all_posts:
                    all_posts[uri] = post
                    new_count += 1
            print(f"  '{phrase}': {len(posts)} posts ({new_count} new)")
        except AtProtocolError as e:
            print(f"Error searching for '{phrase}': {e}")

    return list(all_posts.values())
