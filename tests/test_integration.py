"""Integration tests that call the real Bluesky API.

These tests require BSKY_HANDLE and BSKY_PASSWORD environment variables.
Run with: pytest -m integration

They are skipped by default and when credentials are not available.
"""

import os

import pytest
from dotenv import load_dotenv

from src.search import fetch_all_posts, get_authenticated_client, search_posts_paginated

# Load .env file for local testing
load_dotenv()

# Skip all tests in this module if credentials are not available
pytestmark = pytest.mark.skipif(
    not os.environ.get("BSKY_HANDLE") or not os.environ.get("BSKY_PASSWORD"),
    reason="BSKY_HANDLE and BSKY_PASSWORD environment variables required",
)


@pytest.mark.asyncio
@pytest.mark.integration
class TestBlueskyAPI:
    """Smoke tests to verify the Bluesky API integration works."""

    async def test_authentication_and_search(self):
        """Test that we can authenticate and search for posts."""
        client = await get_authenticated_client()
        assert client is not None

        # Search by hashtag
        posts = await search_posts_paginated(client, tag="smarthome", limit_per_page=5, max_pages=1)
        assert isinstance(posts, list)

        if posts:
            # Verify post structure
            assert "uri" in posts[0]
            assert posts[0]["uri"].startswith("at://")

    async def test_fetch_all_posts_pipeline(self):
        """Test the full fetch pipeline with a minimal keyword set."""
        from unittest.mock import patch

        # Use minimal keywords to keep test fast
        with patch("src.search.load_keywords", return_value=["#smarthome"]):
            posts = await fetch_all_posts()

        assert isinstance(posts, list)
        # Should find some smart home posts
        assert len(posts) > 0, "Expected to find some #smarthome posts"

        # Verify no duplicate URIs (deduplication works)
        uris = [p.get("uri") for p in posts]
        assert len(uris) == len(set(uris)), "Duplicate URIs found"

    async def test_exact_phrase_search(self):
        """Test that quoted phrases return posts with the exact phrase."""
        client = await get_authenticated_client()

        posts = await search_posts_paginated(
            client, query='"smart home"', limit_per_page=5, max_pages=1
        )

        if posts:
            # Verify posts contain the exact phrase (in text or alt text)
            for post in posts:
                text = post.get("record", {}).get("text", "").lower()
                assert "smart home" in text, f"Post missing exact phrase: {text[:100]}"
