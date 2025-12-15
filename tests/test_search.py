"""Unit tests for src/search.py."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from atproto.exceptions import AtProtocolError

from src.search import fetch_all_posts, get_authenticated_client, search_posts


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

            client = await get_authenticated_client()

            mock_client.login.assert_not_called()
            captured = capsys.readouterr()
            assert "Warning" in captured.out


@pytest.mark.asyncio
class TestSearchPosts:
    """Tests for search_posts function."""

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
        mock_client.app.bsky.feed.search_posts = AsyncMock(return_value=mock_response)

        result = await search_posts(mock_client, "#smarthome", limit=10)

        assert len(result) == 2
        assert result[0]["uri"] == "at://did:plc:test/app.bsky.feed.post/1"
        assert result[1]["uri"] == "at://did:plc:test/app.bsky.feed.post/2"

        # Verify search was called with correct parameters
        call_args = mock_client.app.bsky.feed.search_posts.call_args
        assert call_args.kwargs["params"]["q"] == "#smarthome"
        assert call_args.kwargs["params"]["limit"] == 10
        assert call_args.kwargs["params"]["lang"] == "en"
        assert call_args.kwargs["params"]["sort"] == "latest"

    async def test_search_posts_with_custom_limit(self):
        """Test search with custom limit."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.posts = []
        mock_client.app.bsky.feed.search_posts = AsyncMock(return_value=mock_response)

        await search_posts(mock_client, "test", limit=50)

        call_args = mock_client.app.bsky.feed.search_posts.call_args
        assert call_args.kwargs["params"]["limit"] == 50


@pytest.mark.asyncio
class TestFetchAllPosts:
    """Tests for fetch_all_posts function."""

    @patch("src.config.SEARCH_KEYWORDS", ["#smarthome", "#homeassistant"])
    @patch("src.search.search_posts")
    @patch("src.search.get_authenticated_client")
    async def test_fetch_all_posts_deduplicates(self, mock_get_client, mock_search):
        """Test that duplicate posts are removed."""
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

        # Use a function that returns the right posts based on keyword
        async def search_side_effect(client, keyword):
            if keyword == "#smarthome":
                return posts_1
            elif keyword == "#homeassistant":
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

    @patch("src.config.SEARCH_KEYWORDS", ["#test"])
    @patch("src.search.search_posts")
    @patch("src.search.get_authenticated_client")
    async def test_fetch_all_posts_handles_errors(self, mock_get_client, mock_search, capsys):
        """Test error handling for failed searches."""
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        mock_search.side_effect = AtProtocolError("API Error")

        result = await fetch_all_posts()

        assert result == []
        captured = capsys.readouterr()
        assert "Error searching" in captured.out

    async def test_fetch_all_posts_searches_all_keywords(self):
        """Test that all keywords are searched."""
        with patch("src.search.SEARCH_KEYWORDS", ["#keyword1", "#keyword2", "#keyword3"]):
            with patch("src.search.get_authenticated_client") as mock_get_client:
                with patch("src.search.search_posts") as mock_search:
                    mock_client = AsyncMock()
                    mock_get_client.return_value = mock_client
                    mock_search.return_value = []

                    await fetch_all_posts()

                    # Should be called once per keyword
                    assert mock_search.call_count == 3

    @patch("src.search.get_authenticated_client")
    @patch("src.search.search_posts")
    @patch("src.config.SEARCH_KEYWORDS", ["#test"])
    async def test_fetch_all_posts_filters_posts_without_uri(self, mock_search, mock_get_client):
        """Test that posts without URI are filtered out."""
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
