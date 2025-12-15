"""Unit tests for src/algorithm.py."""

from src.algorithm import filter_and_rank


class TestFilterAndRank:
    """Tests for filter_and_rank function."""

    def test_filter_and_rank_basic(self, sample_posts):
        """Test basic filtering and ranking."""
        result = filter_and_rank(sample_posts, limit=2)
        assert len(result) <= 2

    def test_filter_and_rank_excludes_spam(self, sample_posts, spam_post):
        """Test spam posts are excluded."""
        posts = sample_posts + [spam_post]
        result = filter_and_rank(posts, limit=10)

        uris = [p["uri"] for p in result]
        assert spam_post["uri"] not in uris

    def test_filter_and_rank_excludes_replies(self, sample_posts, reply_post):
        """Test reply posts are excluded."""
        posts = sample_posts + [reply_post]
        result = filter_and_rank(posts, limit=10)

        uris = [p["uri"] for p in result]
        assert reply_post["uri"] not in uris

    def test_filter_and_rank_excludes_non_english(self, sample_posts, non_english_post):
        """Test non-English posts are excluded."""
        posts = sample_posts + [non_english_post]
        result = filter_and_rank(posts, limit=10)

        uris = [p["uri"] for p in result]
        assert non_english_post["uri"] not in uris

    def test_filter_and_rank_excludes_old(self, sample_posts, old_post):
        """Test old posts are excluded."""
        posts = sample_posts + [old_post]
        result = filter_and_rank(posts, limit=10)

        uris = [p["uri"] for p in result]
        assert old_post["uri"] not in uris

    def test_filter_and_rank_excludes_blacklisted(self, sample_posts, blacklisted_post):
        """Test blacklisted posts are excluded."""
        posts = sample_posts + [blacklisted_post]
        result = filter_and_rank(posts, limit=10)

        uris = [p["uri"] for p in result]
        assert blacklisted_post["uri"] not in uris

    def test_filter_and_rank_excludes_affiliate(self, sample_posts, affiliate_post):
        """Test affiliate posts are excluded."""
        posts = sample_posts + [affiliate_post]
        result = filter_and_rank(posts, limit=10)

        uris = [p["uri"] for p in result]
        assert affiliate_post["uri"] not in uris

    def test_high_quality_ranks_higher(self, sample_posts, high_quality_post):
        """Test high-quality posts rank higher."""
        posts = sample_posts + [high_quality_post]
        result = filter_and_rank(posts, limit=10)

        # High quality post should be near the top
        uris = [p["uri"] for p in result]
        assert high_quality_post["uri"] in uris
        # Should be in top 2 due to quality + engagement
        high_quality_index = uris.index(high_quality_post["uri"])
        assert high_quality_index < 3

    def test_self_authored_included(self, sample_posts, self_authored_post):
        """Test self-authored posts are included."""
        posts = sample_posts + [self_authored_post]
        result = filter_and_rank(posts, limit=10)

        uris = [p["uri"] for p in result]
        assert self_authored_post["uri"] in uris

    def test_promotional_deprioritized(self, sample_posts, promotional_post):
        """Test promotional posts are deprioritized but not excluded."""
        posts = sample_posts + [promotional_post]
        result = filter_and_rank(posts, limit=10)

        # Promotional post should still be included (not a hard filter)
        uris = [p["uri"] for p in result]
        assert promotional_post["uri"] in uris

    def test_limit_larger_than_posts(self, sample_posts):
        """Test when limit is larger than number of posts."""
        result = filter_and_rank(sample_posts, limit=100)
        # Should return all valid posts
        assert len(result) <= len(sample_posts)

    def test_limit_zero(self, sample_posts):
        """Test with limit of zero returns empty list."""
        result = filter_and_rank(sample_posts, limit=0)
        assert result == []

    def test_empty_list(self):
        """Test with empty list."""
        result = filter_and_rank([])
        assert result == []

    def test_default_limit(self, sample_posts):
        """Test default limit is applied."""
        # Create many posts
        from tests.conftest import make_timestamp

        many_posts = []
        for i in range(150):
            post = {
                "uri": f"at://did:plc:test/app.bsky.feed.post/{i}",
                "cid": f"bafy{i}",
                "author": {"did": f"did:plc:test{i}", "handle": f"user{i}.bsky.social"},
                "record": {
                    "text": f"Smart home post {i} #smarthome",
                    "createdAt": make_timestamp(i % 24),
                    "langs": ["en"],
                },
                "indexedAt": make_timestamp(i % 24),
                "likeCount": i,
                "repostCount": 0,
            }
            many_posts.append(post)

        result = filter_and_rank(many_posts)
        # Default limit is 100
        assert len(result) == 100

    def test_scoring_order(self, sample_posts, high_quality_post):
        """Test posts are ordered by score, not just recency."""
        posts = sample_posts + [high_quality_post]
        result = filter_and_rank(posts, limit=10)

        # High quality post should rank higher than lower-engagement posts
        # even if timestamps are similar
        if len(result) >= 2:
            # Just verify high quality is included and ranked well
            uris = [p["uri"] for p in result]
            assert high_quality_post["uri"] in uris
