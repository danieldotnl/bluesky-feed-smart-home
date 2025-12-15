"""Unit tests for src/search.py."""

import os
from datetime import UTC
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from atproto.exceptions import AtProtocolError

from src.search import (
    fetch_all_posts,
    get_authenticated_client,
    get_since_timestamp,
    parse_keywords,
    search_posts_paginated,
)


@pytest.mark.asyncio
class TestGetAuthenticatedClient:
    """Tests for get_authenticated_client function."""

    @patch.dict(os.environ, {"BSKY_HANDLE": "test.bsky.social", "BSKY_PASSWORD": "testpass"})
    async def test_get_authenticated_client_with_credentials(self):
        """Test client authentication when credentials are provided."""
        with patch("src.search.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            client = await get_authenticated_client()

            mock_client.login.assert_called_once_with("test.bsky.social", "testpass")
            assert client == mock_client

    @patch.dict(os.environ, {}, clear=True)
    async def test_get_authenticated_client_without_credentials(self, capsys):
        """Test client creation when credentials are not provided."""
        with patch("src.search.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            _ = await get_authenticated_client()

            mock_client.login.assert_not_called()
            captured = capsys.readouterr()
            assert "Warning" in captured.out


class TestGetSinceTimestamp:
    """Tests for get_since_timestamp function."""

    def test_returns_iso_format(self):
        """Test timestamp is in ISO format."""
        timestamp = get_since_timestamp()
        assert "T" in timestamp
        assert timestamp.endswith("Z")

    def test_timestamp_is_in_past(self):
        """Test timestamp is in the past."""
        from datetime import datetime

        timestamp = get_since_timestamp()
        # Parse the timestamp
        dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
        dt = dt.replace(tzinfo=UTC)
        now = datetime.now(UTC)
        assert dt < now


class TestParseKeywords:
    """Tests for parse_keywords function."""

    def test_separates_hashtags_and_phrases(self):
        """Test that hashtags and phrases are separated correctly."""
        keywords = ["#smarthome", "#homeassistant", "smart home", "home automation"]
        tags, phrases = parse_keywords(keywords)

        assert tags == ["smarthome", "homeassistant"]
        assert phrases == ["smart home", "home automation"]

    def test_single_word_phrases(self):
        """Test that single-word phrases are preserved."""
        keywords = ["zigbee", "matter"]
        tags, phrases = parse_keywords(keywords)

        assert tags == []
        assert phrases == ["zigbee", "matter"]

    def test_removes_hash_prefix(self):
        """Test that # prefix is removed from hashtags."""
        keywords = ["#test", "#another"]
        tags, phrases = parse_keywords(keywords)

        assert tags == ["test", "another"]
        assert phrases == []

    def test_empty_list(self):
        """Test with empty keyword list."""
        tags, phrases = parse_keywords([])
        assert tags == []
        assert phrases == []

    def test_only_hashtags(self):
        """Test with only hashtags."""
        keywords = ["#one", "#two", "#three"]
        tags, phrases = parse_keywords(keywords)

        assert tags == ["one", "two", "three"]
        assert phrases == []

    def test_only_phrases(self):
        """Test with only phrases."""
        keywords = ["smart home", "home automation"]
        tags, phrases = parse_keywords(keywords)

        assert tags == []
        assert phrases == ["smart home", "home automation"]


@pytest.mark.asyncio
class TestSearchPostsPaginated:
    """Tests for search_posts_paginated function."""

    async def test_search_posts_basic(self):
        """Test basic post search functionality."""
        mock_client = AsyncMock()
        mock_response = MagicMock()

        # Create mock post objects with model_dump method
        mock_post1 = MagicMock()
        mock_post1.model_dump.return_value = {
            "uri": "at://did:plc:test/app.bsky.feed.post/1",
            "text": "Test post #smarthome",
        }
        mock_post2 = MagicMock()
        mock_post2.model_dump.return_value = {
            "uri": "at://did:plc:test/app.bsky.feed.post/2",
            "text": "Another test #homeassistant",
        }

        mock_response.posts = [mock_post1, mock_post2]
        mock_response.cursor = None  # No more pages
        mock_client.app.bsky.feed.search_posts = AsyncMock(return_value=mock_response)

        result = await search_posts_paginated(mock_client, "#smarthome", limit_per_page=10)

        assert len(result) == 2
        assert result[0]["uri"] == "at://did:plc:test/app.bsky.feed.post/1"
        assert result[1]["uri"] == "at://did:plc:test/app.bsky.feed.post/2"

    async def test_search_posts_pagination(self):
        """Test pagination through multiple pages."""
        mock_client = AsyncMock()

        # First page response
        mock_response1 = MagicMock()
        mock_post1 = MagicMock()
        mock_post1.model_dump.return_value = {"uri": "post1"}
        mock_response1.posts = [mock_post1]
        mock_response1.cursor = "cursor1"

        # Second page response
        mock_response2 = MagicMock()
        mock_post2 = MagicMock()
        mock_post2.model_dump.return_value = {"uri": "post2"}
        mock_response2.posts = [mock_post2]
        mock_response2.cursor = None  # No more pages

        mock_client.app.bsky.feed.search_posts = AsyncMock(
            side_effect=[mock_response1, mock_response2]
        )

        result = await search_posts_paginated(mock_client, "#test", limit_per_page=1, max_pages=3)

        assert len(result) == 2
        assert mock_client.app.bsky.feed.search_posts.call_count == 2

    async def test_search_posts_max_pages_limit(self):
        """Test max pages limit is respected."""
        mock_client = AsyncMock()

        def create_response(cursor):
            response = MagicMock()
            post = MagicMock()
            post.model_dump.return_value = {"uri": f"post-{cursor}"}
            response.posts = [post]
            response.cursor = f"cursor-{cursor}"
            return response

        mock_client.app.bsky.feed.search_posts = AsyncMock(
            side_effect=[create_response(i) for i in range(10)]
        )

        await search_posts_paginated(mock_client, "#test", limit_per_page=1, max_pages=2)

        # Should stop at 2 pages even though more are available
        assert mock_client.app.bsky.feed.search_posts.call_count == 2

    async def test_search_posts_includes_since(self):
        """Test that 'since' parameter is included."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.posts = []
        mock_response.cursor = None
        mock_client.app.bsky.feed.search_posts = AsyncMock(return_value=mock_response)

        await search_posts_paginated(mock_client, "test")

        call_args = mock_client.app.bsky.feed.search_posts.call_args
        assert "since" in call_args.kwargs["params"]


@pytest.mark.asyncio
class TestFetchAllPosts:
    """Tests for fetch_all_posts function."""

    @patch("src.search.search_posts_paginated")
    @patch("src.search.get_authenticated_client")
    @patch("src.search.load_keywords")
    async def test_fetch_all_posts_deduplicates(
        self, mock_load_keywords, mock_get_client, mock_search
    ):
        """Test that duplicate posts are removed."""
        mock_load_keywords.return_value = ["#smarthome", "#homeassistant"]
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        # Same URI in both searches
        posts_1 = [
            {"uri": "at://did:plc:test/post/1", "text": "Post 1"},
            {"uri": "at://did:plc:test/post/2", "text": "Post 2"},
        ]
        posts_2 = [
            {"uri": "at://did:plc:test/post/2", "text": "Post 2 duplicate"},
            {"uri": "at://did:plc:test/post/3", "text": "Post 3"},
        ]

        async def search_side_effect(client, query=None, tag=None, **kwargs):
            if tag == "smarthome":
                return posts_1
            elif tag == "homeassistant":
                return posts_2
            return []

        mock_search.side_effect = search_side_effect

        result = await fetch_all_posts()

        # Should have 3 unique posts
        assert len(result) == 3
        uris = [post["uri"] for post in result]
        assert "at://did:plc:test/post/1" in uris
        assert "at://did:plc:test/post/2" in uris
        assert "at://did:plc:test/post/3" in uris

    @patch("src.search.search_posts_paginated")
    @patch("src.search.get_authenticated_client")
    @patch("src.search.load_keywords")
    async def test_fetch_all_posts_handles_errors(
        self, mock_load_keywords, mock_get_client, mock_search, capsys
    ):
        """Test error handling for failed searches."""
        mock_load_keywords.return_value = ["#test"]
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        mock_search.side_effect = AtProtocolError("API Error")

        result = await fetch_all_posts()

        assert result == []
        captured = capsys.readouterr()
        assert "Error searching" in captured.out

    @patch("src.search.search_posts_paginated")
    @patch("src.search.get_authenticated_client")
    @patch("src.search.load_keywords")
    async def test_fetch_all_posts_searches_all_keywords(
        self, mock_load_keywords, mock_get_client, mock_search
    ):
        """Test that all keywords are searched."""
        mock_load_keywords.return_value = ["#keyword1", "#keyword2", "#keyword3"]
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_search.return_value = []

        await fetch_all_posts()

        # Should be called once per keyword
        assert mock_search.call_count == 3

    @patch("src.search.get_authenticated_client")
    @patch("src.search.load_keywords")
    async def test_fetch_all_posts_empty_keywords(
        self, mock_load_keywords, mock_get_client, capsys
    ):
        """Test handling empty keywords list."""
        mock_load_keywords.return_value = []

        result = await fetch_all_posts()

        assert result == []
        captured = capsys.readouterr()
        assert "No keywords found" in captured.out

    @patch("src.search.search_posts_paginated")
    @patch("src.search.get_authenticated_client")
    @patch("src.search.load_keywords")
    async def test_fetch_all_posts_filters_posts_without_uri(
        self, mock_load_keywords, mock_get_client, mock_search
    ):
        """Test that posts without URI are filtered out."""
        mock_load_keywords.return_value = ["#test"]
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        posts = [
            {"uri": "at://did:plc:test/post/1", "text": "Valid post"},
            {"text": "Invalid post without URI"},
            {"uri": "at://did:plc:test/post/2", "text": "Another valid post"},
        ]
        mock_search.return_value = posts

        result = await fetch_all_posts()

        assert len(result) == 2
        assert all("uri" in post for post in result)

    @patch("src.search.search_posts_paginated")
    @patch("src.search.get_authenticated_client")
    @patch("src.search.load_keywords")
    async def test_fetch_all_posts_quotes_multi_word_phrases(
        self, mock_load_keywords, mock_get_client, mock_search
    ):
        """Test that multi-word phrases are wrapped in quotes for exact matching."""
        mock_load_keywords.return_value = ["smart home", "google home", "zigbee"]
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_search.return_value = []

        await fetch_all_posts()

        # Check that search was called with quoted multi-word phrases
        calls = mock_search.call_args_list
        queries = [call.kwargs.get("query") for call in calls if call.kwargs.get("query")]

        assert '"smart home"' in queries
        assert '"google home"' in queries
        assert "zigbee" in queries  # Single word should NOT be quoted
        assert '"zigbee"' not in queries

    @patch("src.search.search_posts_paginated")
    @patch("src.search.get_authenticated_client")
    @patch("src.search.load_keywords")
    async def test_fetch_all_posts_does_not_quote_single_words(
        self, mock_load_keywords, mock_get_client, mock_search
    ):
        """Test that single-word phrases are not wrapped in quotes."""
        mock_load_keywords.return_value = ["matter", "thread"]
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_search.return_value = []

        await fetch_all_posts()

        calls = mock_search.call_args_list
        queries = [call.kwargs.get("query") for call in calls if call.kwargs.get("query")]

        # Single words should not have quotes
        assert "matter" in queries
        assert "thread" in queries
        assert '"matter"' not in queries
        assert '"thread"' not in queries
