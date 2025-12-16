"""Unit tests for src/generator.py."""

import json

import pytest

from src.generator import generate_did_document, write_output_files


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


@pytest.mark.asyncio
class TestWriteOutputFiles:
    """Tests for write_output_files function."""

    async def test_write_output_files_creates_directories(self, sample_posts, temp_output_dir):
        """Test that output directories are created."""
        await write_output_files(sample_posts, temp_output_dir)

        assert (temp_output_dir / ".well-known").is_dir()
        assert (temp_output_dir / "data").is_dir()

    async def test_write_output_files_creates_did_json(self, sample_posts, temp_output_dir):
        """Test DID document is written correctly."""
        await write_output_files(sample_posts, temp_output_dir)

        did_path = temp_output_dir / ".well-known" / "did.json"
        assert did_path.exists()

        with open(did_path) as f:
            did_doc = json.load(f)

        assert did_doc == generate_did_document()

    async def test_write_output_files_creates_feed_data(self, sample_posts, temp_output_dir):
        """Test feed data is written correctly for Cloudflare Function."""
        await write_output_files(sample_posts, temp_output_dir)

        feed_path = temp_output_dir / "data" / "feed.json"
        assert feed_path.exists()

        with open(feed_path) as f:
            feed_data = json.load(f)

        assert feed_data == sample_posts
        assert len(feed_data) == 3

    async def test_write_output_files_valid_json(self, sample_posts, temp_output_dir):
        """Test that output files contain valid JSON."""
        await write_output_files(sample_posts, temp_output_dir)

        # Should not raise json.JSONDecodeError
        with open(temp_output_dir / ".well-known" / "did.json") as f:
            json.load(f)

        with open(temp_output_dir / "data" / "feed.json") as f:
            json.load(f)

    async def test_write_output_files_empty_posts(self, temp_output_dir):
        """Test writing output with empty posts list."""
        await write_output_files([], temp_output_dir)

        feed_path = temp_output_dir / "data" / "feed.json"
        with open(feed_path) as f:
            feed_data = json.load(f)

        assert feed_data == []

    async def test_write_output_files_creates_headers(self, sample_posts, temp_output_dir):
        """Test _headers file is created with correct content."""
        await write_output_files(sample_posts, temp_output_dir)

        headers_path = temp_output_dir / "_headers"
        assert headers_path.exists()

        content = headers_path.read_text()
        assert "Access-Control-Allow-Origin: *" in content
        assert "Cache-Control:" in content
