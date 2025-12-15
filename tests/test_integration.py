"""Integration tests that call the real Bluesky API.

These tests require BSKY_HANDLE and BSKY_PASSWORD environment variables.
They will be skipped if credentials are not available.
"""

import os

import pytest
from dotenv import load_dotenv

from src.search import fetch_all_posts, get_authenticated_client, search_posts

# Load .env file for local testing
load_dotenv()

# Skip all tests in this module if credentials are not available
pytestmark = pytest.mark.skipif(
    not os.environ.get("BSKY_HANDLE") or not os.environ.get("BSKY_PASSWORD"),
    reason="BSKY_HANDLE and BSKY_PASSWORD environment variables required for integration tests",
)


@pytest.mark.asyncio
@pytest.mark.integration
class TestRealAPIIntegration:
    """Integration tests with real Bluesky API calls."""

    async def test_authenticate_with_real_credentials(self):
        """Test authentication with real API credentials."""
        client = await get_authenticated_client()

        assert client is not None
        # If authentication succeeded, client should be usable
        assert hasattr(client, "app")

    async def test_search_posts_real_api(self):
        """Test searching posts with real API."""
        client = await get_authenticated_client()

        # Search for a common hashtag with small limit to keep test fast
        posts = await search_posts(client, "#smarthome", limit=5)

        # Should get some results
        assert isinstance(posts, list)
        # Posts might be empty, but if not, should have correct structure
        if posts:
            assert "uri" in posts[0]
            assert "indexedAt" in posts[0] or "indexed_at" in posts[0]

    async def test_fetch_all_posts_real_api(self):
        """Test fetching posts from all keywords with real API.

        This test uses a small subset of keywords to keep it fast.
        """
        # Temporarily override SEARCH_KEYWORDS for faster test
        import src.config

        original_keywords = src.config.SEARCH_KEYWORDS
        try:
            # Use only 2 keywords for faster test
            src.config.SEARCH_KEYWORDS = ["#smarthome", "#homeassistant"]

            posts = await fetch_all_posts()

            # Should return a list
            assert isinstance(posts, list)

            # If we got posts, verify structure
            if posts:
                assert "uri" in posts[0]
                # Check deduplication worked (no duplicate URIs)
                uris = [p.get("uri") for p in posts]
                assert len(uris) == len(set(uris)), "Duplicate URIs found"

        finally:
            # Restore original keywords
            src.config.SEARCH_KEYWORDS = original_keywords

    async def test_api_returns_recent_posts(self):
        """Test that API returns recent posts (from last 24 hours ideally)."""
        from datetime import datetime, timedelta

        client = await get_authenticated_client()
        posts = await search_posts(client, "#smarthome", limit=10)

        if posts:
            # Check that at least some posts are recent
            now = datetime.now()
            recent_posts = 0

            for post in posts:
                indexed_at = post.get("indexedAt") or post.get("indexed_at")
                if indexed_at:
                    try:
                        post_time = datetime.fromisoformat(indexed_at.replace("Z", "+00:00"))
                        if (now - post_time.replace(tzinfo=None)) < timedelta(days=7):
                            recent_posts += 1
                    except (ValueError, AttributeError):
                        pass

            # At least some posts should be from the last week
            assert recent_posts > 0, "No recent posts found"
