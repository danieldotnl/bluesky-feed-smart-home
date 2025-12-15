"""Unit tests for src/generator.py."""

import json
from pathlib import Path

import pytest

from src.generator import generate_did_document, generate_feed_skeleton, write_output_files


class TestGenerateDidDocument:
    """Tests for generate_did_document function."""

    def test_generate_did_document_structure(self):
        """Test DID document has correct structure."""
        doc = generate_did_document()

        assert "@context" in doc
        assert doc["@context"] == ["https://www.w3.org/ns/did/v1"]
        assert "id" in doc
        assert doc["id"].startswith("did:web:")
        assert "service" in doc
        assert len(doc["service"]) == 1

    def test_generate_did_document_service(self):
        """Test service configuration in DID document."""
        doc = generate_did_document()
        service = doc["service"][0]

        assert service["id"] == "#bsky_fg"
        assert service["type"] == "BskyFeedGenerator"
        assert "serviceEndpoint" in service
        assert service["serviceEndpoint"].startswith("https://")


class TestGenerateFeedSkeleton:
    """Tests for generate_feed_skeleton function."""

    def test_generate_feed_skeleton_basic(self, sample_posts):
        """Test basic feed skeleton generation."""
        skeleton = generate_feed_skeleton(sample_posts)

        assert "feed" in skeleton
        assert len(skeleton["feed"]) == 3
        assert skeleton["feed"][0] == {"post": sample_posts[0]["uri"]}
        assert skeleton["feed"][1] == {"post": sample_posts[1]["uri"]}
        assert skeleton["feed"][2] == {"post": sample_posts[2]["uri"]}

    def test_generate_feed_skeleton_with_cursor(self, sample_posts):
        """Test cursor is set from last post."""
        skeleton = generate_feed_skeleton(sample_posts)

        assert "cursor" in skeleton
        assert skeleton["cursor"] == sample_posts[-1]["indexedAt"]

    def test_generate_feed_skeleton_empty_list(self):
        """Test with empty post list."""
        skeleton = generate_feed_skeleton([])

        assert skeleton["feed"] == []
        assert "cursor" not in skeleton

    def test_generate_feed_skeleton_filters_posts_without_uri(self):
        """Test posts without URI are filtered out."""
        posts = [
            {"uri": "at://valid/post/1", "indexedAt": "2025-12-15T12:00:00.000Z"},
            {"cid": "no_uri_post"},  # No URI
            {"uri": "at://valid/post/2", "indexedAt": "2025-12-15T11:00:00.000Z"},
        ]

        skeleton = generate_feed_skeleton(posts)

        assert len(skeleton["feed"]) == 2
        assert skeleton["feed"][0]["post"] == "at://valid/post/1"
        assert skeleton["feed"][1]["post"] == "at://valid/post/2"


@pytest.mark.asyncio
class TestWriteOutputFiles:
    """Tests for write_output_files function."""

    async def test_write_output_files_creates_directories(self, sample_posts, temp_output_dir):
        """Test that output directories are created."""
        await write_output_files(sample_posts, temp_output_dir)

        assert (temp_output_dir / ".well-known").is_dir()
        assert (temp_output_dir / "xrpc").is_dir()

    async def test_write_output_files_creates_did_json(self, sample_posts, temp_output_dir):
        """Test DID document is written correctly."""
        await write_output_files(sample_posts, temp_output_dir)

        did_path = temp_output_dir / ".well-known" / "did.json"
        assert did_path.exists()

        with open(did_path) as f:
            did_doc = json.load(f)

        assert did_doc == generate_did_document()

    async def test_write_output_files_creates_feed_skeleton(self, sample_posts, temp_output_dir):
        """Test feed skeleton is written correctly."""
        await write_output_files(sample_posts, temp_output_dir)

        feed_path = temp_output_dir / "xrpc" / "app.bsky.feed.getFeedSkeleton"
        assert feed_path.exists()

        with open(feed_path) as f:
            skeleton = json.load(f)

        assert skeleton == generate_feed_skeleton(sample_posts)
        assert len(skeleton["feed"]) == 3

    async def test_write_output_files_valid_json(self, sample_posts, temp_output_dir):
        """Test that output files contain valid JSON."""
        await write_output_files(sample_posts, temp_output_dir)

        # Should not raise json.JSONDecodeError
        with open(temp_output_dir / ".well-known" / "did.json") as f:
            json.load(f)

        with open(temp_output_dir / "xrpc" / "app.bsky.feed.getFeedSkeleton") as f:
            json.load(f)

    async def test_write_output_files_empty_posts(self, temp_output_dir):
        """Test writing output with empty posts list."""
        await write_output_files([], temp_output_dir)

        feed_path = temp_output_dir / "xrpc" / "app.bsky.feed.getFeedSkeleton"
        with open(feed_path) as f:
            skeleton = json.load(f)

        assert skeleton["feed"] == []
        assert "cursor" not in skeleton
