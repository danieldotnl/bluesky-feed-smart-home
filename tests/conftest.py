"""Pytest configuration and shared fixtures."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def sample_posts():
    """Sample posts data for testing."""
    return [
        {
            "uri": "at://did:plc:test1/app.bsky.feed.post/abc123",
            "cid": "bafytest1",
            "author": {
                "did": "did:plc:test1",
                "handle": "user1.bsky.social",
            },
            "record": {
                "text": "Testing smart home automation #smarthome",
                "createdAt": "2025-12-15T12:00:00.000Z",
            },
            "indexedAt": "2025-12-15T12:00:00.000Z",
        },
        {
            "uri": "at://did:plc:test2/app.bsky.feed.post/def456",
            "cid": "bafytest2",
            "author": {
                "did": "did:plc:test2",
                "handle": "user2.bsky.social",
            },
            "record": {
                "text": "Home Assistant is amazing! #homeassistant",
                "createdAt": "2025-12-15T11:00:00.000Z",
            },
            "indexedAt": "2025-12-15T11:00:00.000Z",
        },
        {
            "uri": "at://did:plc:test3/app.bsky.feed.post/ghi789",
            "cid": "bafytest3",
            "author": {
                "did": "did:plc:test3",
                "handle": "user3.bsky.social",
            },
            "record": {
                "text": "IoT devices everywhere #iot",
                "createdAt": "2025-12-15T10:00:00.000Z",
            },
            "indexedAt": "2025-12-15T10:00:00.000Z",
        },
    ]


@pytest.fixture
def sample_post_with_duplicate(sample_posts):
    """Sample posts with a duplicate URI for deduplication testing."""
    duplicate = sample_posts[0].copy()
    duplicate["cid"] = "bafytest1duplicate"
    return sample_posts + [duplicate]


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary output directory for file generation tests."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
