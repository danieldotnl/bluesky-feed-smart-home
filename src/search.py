"""Search module for fetching posts from Bluesky."""

import os
from datetime import UTC, datetime, timedelta

from atproto import AsyncClient
from atproto.exceptions import AtProtocolError

from src.config import LANGUAGE, SEARCH_TIME_WINDOW_DAYS, load_keywords

# Maximum pages to fetch per keyword to avoid excessive API calls
MAX_PAGES_PER_KEYWORD = 3


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
    keyword: str,
    limit_per_page: int = 100,
    max_pages: int = MAX_PAGES_PER_KEYWORD,
) -> list[dict]:
    """Search Bluesky for posts matching a keyword with pagination.

    Args:
        client: Authenticated AsyncClient
        keyword: Search term
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
            "q": keyword,
            "lang": LANGUAGE,
            "limit": limit_per_page,
            "sort": "latest",
            "since": since,
        }

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
    """Fetch posts for all configured keywords and deduplicate."""
    all_posts: dict[str, dict] = {}
    keywords = load_keywords()

    if not keywords:
        print("Warning: No keywords found in data/keywords.txt")
        return []

    # Create a single authenticated client for all searches
    client = await get_authenticated_client()

    for keyword in keywords:
        try:
            posts = await search_posts_paginated(client, keyword)
            new_count = 0
            for post in posts:
                uri = post.get("uri")
                if uri and uri not in all_posts:
                    all_posts[uri] = post
                    new_count += 1
            print(f"  '{keyword}': {len(posts)} posts ({new_count} new)")
        except AtProtocolError as e:
            print(f"Error searching for '{keyword}': {e}")

    return list(all_posts.values())
