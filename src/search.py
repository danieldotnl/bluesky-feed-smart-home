import httpx

from src.config import LANGUAGE, SEARCH_KEYWORDS

BSKY_PUBLIC_API = "https://public.api.bsky.app"


async def search_posts(keyword: str, limit: int = 100) -> list[dict]:
    """Search Bluesky for posts matching a keyword."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BSKY_PUBLIC_API}/xrpc/app.bsky.feed.searchPosts",
            params={
                "q": keyword,
                "lang": LANGUAGE,
                "limit": limit,
                "sort": "latest",
            },
        )
        response.raise_for_status()
        return response.json().get("posts", [])


async def fetch_all_posts() -> list[dict]:
    """Fetch posts for all configured keywords and deduplicate."""
    all_posts: dict[str, dict] = {}

    for keyword in SEARCH_KEYWORDS:
        try:
            posts = await search_posts(keyword)
            for post in posts:
                uri = post.get("uri")
                if uri and uri not in all_posts:
                    all_posts[uri] = post
        except httpx.HTTPError as e:
            print(f"Error searching for '{keyword}': {e}")

    return list(all_posts.values())
