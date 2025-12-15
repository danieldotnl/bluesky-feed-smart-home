import os

from atproto import AsyncClient
from atproto.exceptions import AtProtocolError

from src.config import LANGUAGE, SEARCH_KEYWORDS


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


async def search_posts(client: AsyncClient, keyword: str, limit: int = 100) -> list[dict]:
    """Search Bluesky for posts matching a keyword."""
    response = await client.app.bsky.feed.search_posts(
        params={
            "q": keyword,
            "lang": LANGUAGE,
            "limit": limit,
            "sort": "latest",
        }
    )
    # Convert posts to dict format for compatibility
    return [
        post.model_dump() if hasattr(post, "model_dump") else dict(post) for post in response.posts
    ]


async def fetch_all_posts() -> list[dict]:
    """Fetch posts for all configured keywords and deduplicate."""
    all_posts: dict[str, dict] = {}

    # Create a single authenticated client for all searches
    client = await get_authenticated_client()

    for keyword in SEARCH_KEYWORDS:
        try:
            posts = await search_posts(client, keyword)
            for post in posts:
                uri = post.get("uri")
                if uri and uri not in all_posts:
                    all_posts[uri] = post
        except AtProtocolError as e:
            print(f"Error searching for '{keyword}': {e}")

    return list(all_posts.values())
