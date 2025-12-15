"""Unit tests for src/algorithm.py."""

from datetime import datetime

import pytest

from src.algorithm import filter_and_rank, sort_by_date


class TestSortByDate:
    """Tests for sort_by_date function."""

    def test_sort_by_date_newest_first(self, sample_posts):
        """Test that posts are sorted with newest first."""
        # Posts are already in descending order by indexedAt
        sorted_posts = sort_by_date(sample_posts)

        assert len(sorted_posts) == 3
        assert sorted_posts[0]["indexedAt"] == "2025-12-15T12:00:00.000Z"
        assert sorted_posts[1]["indexedAt"] == "2025-12-15T11:00:00.000Z"
        assert sorted_posts[2]["indexedAt"] == "2025-12-15T10:00:00.000Z"

    def test_sort_by_date_reverse_order(self, sample_posts):
        """Test sorting posts that are in reverse chronological order."""
        reversed_posts = list(reversed(sample_posts))
        sorted_posts = sort_by_date(reversed_posts)

        assert sorted_posts[0]["indexedAt"] == "2025-12-15T12:00:00.000Z"
        assert sorted_posts[2]["indexedAt"] == "2025-12-15T10:00:00.000Z"

    def test_sort_by_date_with_missing_timestamp(self):
        """Test sorting handles posts with missing or invalid timestamps."""
        posts = [
            {"uri": "post1", "indexedAt": "2025-12-15T12:00:00.000Z"},
            {"uri": "post2"},  # Missing indexedAt
            {"uri": "post3", "indexedAt": "invalid-date"},
            {"uri": "post4", "indexedAt": "2025-12-15T11:00:00.000Z"},
        ]

        sorted_posts = sort_by_date(posts)

        # Valid timestamps should come first, invalid ones last
        assert sorted_posts[0]["uri"] == "post1"
        assert sorted_posts[1]["uri"] == "post4"
        # Invalid timestamps should be at the end (in original order)
        assert sorted_posts[2]["uri"] in ["post2", "post3"]
        assert sorted_posts[3]["uri"] in ["post2", "post3"]

    def test_sort_by_date_empty_list(self):
        """Test sorting an empty list returns empty list."""
        result = sort_by_date([])
        assert result == []


class TestFilterAndRank:
    """Tests for filter_and_rank function."""

    def test_filter_and_rank_basic(self, sample_posts):
        """Test basic filtering and ranking."""
        result = filter_and_rank(sample_posts, limit=2)

        assert len(result) == 2
        assert result[0]["indexedAt"] == "2025-12-15T12:00:00.000Z"
        assert result[1]["indexedAt"] == "2025-12-15T11:00:00.000Z"

    def test_filter_and_rank_limit_larger_than_posts(self, sample_posts):
        """Test when limit is larger than number of posts."""
        result = filter_and_rank(sample_posts, limit=100)

        assert len(result) == 3
        assert result == sort_by_date(sample_posts)

    def test_filter_and_rank_limit_zero(self, sample_posts):
        """Test with limit of zero returns empty list."""
        result = filter_and_rank(sample_posts, limit=0)

        assert result == []

    def test_filter_and_rank_default_limit(self, sample_posts):
        """Test default limit of 50."""
        # Create 60 posts
        many_posts = []
        for i in range(60):
            post = sample_posts[0].copy()
            post["uri"] = f"at://did:plc:test/app.bsky.feed.post/{i}"
            post["indexedAt"] = f"2025-12-15T{i:02d}:00:00.000Z"
            many_posts.append(post)

        result = filter_and_rank(many_posts)

        assert len(result) == 50

    def test_filter_and_rank_empty_list(self):
        """Test with empty list."""
        result = filter_and_rank([])

        assert result == []
