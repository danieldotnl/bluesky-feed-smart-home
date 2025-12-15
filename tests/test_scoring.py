"""Unit tests for src/scoring.py."""

from src.scoring import (
    calculate_engagement_bonus,
    calculate_final_score,
    calculate_quality_score,
    calculate_time_decay,
    extract_features,
    load_promotional_domains,
)


class TestLoadPromotionalDomains:
    """Tests for load_promotional_domains function."""

    def test_loads_domains(self):
        """Test loading promotional domains from file."""
        domains = load_promotional_domains()
        assert "howtogeek.com" in domains
        assert "theverge.com" in domains

    def test_domains_are_lowercase(self):
        """Test domains are lowercased."""
        domains = load_promotional_domains()
        for domain in domains:
            assert domain == domain.lower()


class TestExtractFeatures:
    """Tests for extract_features function."""

    def test_core_topic_detection(self, sample_posts):
        """Test detecting core topics."""
        features = extract_features(sample_posts[0])
        # "Home Assistant" and "#smarthome" in text
        assert features["core_matches"] >= 0
        assert features["secondary_matches"] >= 0

    def test_code_detection(self, high_quality_post):
        """Test detecting code blocks."""
        features = extract_features(high_quality_post)
        assert features["has_code"]

    def test_image_detection(self, high_quality_post):
        """Test detecting images."""
        features = extract_features(high_quality_post)
        assert features["has_images"]

    def test_doc_link_detection(self, high_quality_post):
        """Test detecting documentation links."""
        features = extract_features(high_quality_post)
        assert features["has_doc_link"]

    def test_text_length(self, sample_posts):
        """Test text length extraction."""
        features = extract_features(sample_posts[0])
        assert features["text_length"] > 0

    def test_hype_detection(self):
        """Test detecting hype words."""
        post = {"record": {"text": "This is insane! Game changer!"}}
        features = extract_features(post)
        assert features["hype_count"] >= 2

    def test_meme_detection(self):
        """Test detecting meme patterns."""
        post = {"record": {"text": "POV: you just automated your home"}}
        features = extract_features(post)
        assert features["is_meme"]

    def test_all_caps_detection(self):
        """Test detecting ALL CAPS text."""
        post = {"record": {"text": "THIS IS AMAZING NEWS"}}
        features = extract_features(post)
        assert features["has_all_caps"]


class TestCalculateQualityScore:
    """Tests for calculate_quality_score function."""

    def test_high_quality_post(self, high_quality_post):
        """Test high-quality post gets high score."""
        features = extract_features(high_quality_post)
        promo_domains = set()
        score = calculate_quality_score(high_quality_post, features, promo_domains)
        # Should get bonuses for: core topic, code, images, doc link, medium length
        assert score >= 40

    def test_low_quality_post(self):
        """Test low-quality post gets low score."""
        post = {"record": {"text": "wow"}, "author": {"handle": "test.bsky.social"}}
        features = extract_features(post)
        promo_domains = set()
        score = calculate_quality_score(post, features, promo_domains)
        # Very short, no topic matches
        assert score < 20

    def test_hype_penalty(self):
        """Test hype words reduce score."""
        clean_post = {
            "record": {"text": "Great Home Assistant setup"},
            "author": {"handle": "test.bsky.social"},
        }
        hype_post = {
            "record": {"text": "INSANE Home Assistant setup! Game changer!"},
            "author": {"handle": "test.bsky.social"},
        }
        promo_domains = set()

        clean_features = extract_features(clean_post)
        hype_features = extract_features(hype_post)

        clean_score = calculate_quality_score(clean_post, clean_features, promo_domains)
        hype_score = calculate_quality_score(hype_post, hype_features, promo_domains)

        assert hype_score < clean_score

    def test_promotional_domain_penalty(self, promotional_post):
        """Test promotional domains reduce score."""
        features = extract_features(promotional_post)
        promo_domains = {"howtogeek.com"}
        score = calculate_quality_score(promotional_post, features, promo_domains)
        # Score should be reduced by promotional penalty
        assert score < 30

    def test_self_promo_penalty(self):
        """Test self-promotional posts (handle matches domain) get penalty."""
        post = {
            "record": {"text": "Check our article https://mysite.com/post #smarthome"},
            "author": {"handle": "mysite.bsky.social"},
        }
        features = extract_features(post)
        promo_domains = set()
        score = calculate_quality_score(post, features, promo_domains)
        # Should have self-promo penalty
        assert score < 30

    def test_score_bounds(self, high_quality_post):
        """Test score stays within 0-100 bounds."""
        features = extract_features(high_quality_post)
        promo_domains = set()
        score = calculate_quality_score(high_quality_post, features, promo_domains)
        assert 0 <= score <= 100


class TestCalculateEngagementBonus:
    """Tests for calculate_engagement_bonus function."""

    def test_no_engagement(self):
        """Test post with no engagement."""
        post = {"likeCount": 0, "repostCount": 0}
        bonus = calculate_engagement_bonus(post)
        assert bonus == 0

    def test_likes_bonus(self):
        """Test likes contribute to bonus."""
        post = {"likeCount": 10, "repostCount": 0}
        bonus = calculate_engagement_bonus(post)
        assert bonus == 5  # 10 * 0.5 = 5 (capped at 5)

    def test_reposts_bonus(self):
        """Test reposts contribute to bonus."""
        post = {"likeCount": 0, "repostCount": 5}
        bonus = calculate_engagement_bonus(post)
        assert bonus == 5  # 5 * 1.0 = 5 (capped at 5)

    def test_combined_bonus(self, high_quality_post):
        """Test combined likes and reposts."""
        bonus = calculate_engagement_bonus(high_quality_post)
        # 25 likes (capped at 5) + 10 reposts (capped at 5) = 10
        assert bonus == 10

    def test_bonus_capped(self):
        """Test bonus is capped at 10."""
        post = {"likeCount": 1000, "repostCount": 1000}
        bonus = calculate_engagement_bonus(post)
        assert bonus == 10

    def test_missing_counts(self):
        """Test handling missing count fields."""
        post = {}
        bonus = calculate_engagement_bonus(post)
        assert bonus == 0


class TestCalculateTimeDecay:
    """Tests for calculate_time_decay function."""

    def test_recent_post(self, sample_posts):
        """Test recent post has high decay factor."""
        decay = calculate_time_decay(sample_posts[0])
        assert decay > 0.8

    def test_old_post(self, old_post):
        """Test old post has low decay factor."""
        decay = calculate_time_decay(old_post)
        assert decay < 0.1

    def test_missing_timestamp(self):
        """Test missing timestamp gets low decay."""
        post = {}
        decay = calculate_time_decay(post)
        assert decay == 0.1

    def test_decay_bounds(self, sample_posts):
        """Test decay stays within reasonable bounds."""
        decay = calculate_time_decay(sample_posts[0])
        assert 0 < decay <= 1


class TestCalculateFinalScore:
    """Tests for calculate_final_score function."""

    def test_high_quality_post(self, high_quality_post):
        """Test high-quality recent post gets high score."""
        promo_domains = set()
        score = calculate_final_score(high_quality_post, promo_domains)
        # Quality * decay + engagement
        assert score > 30

    def test_old_post_score(self, old_post):
        """Test old post gets low score despite high engagement."""
        promo_domains = set()
        score = calculate_final_score(old_post, promo_domains)
        # High engagement but severe time decay
        assert score < 20

    def test_self_authored_floor(self, self_authored_post):
        """Test self-authored posts have minimum score floor."""
        promo_domains = set()
        score = calculate_final_score(self_authored_post, promo_domains)
        # Should be at least 50
        assert score >= 50

    def test_low_quality_post(self):
        """Test low-quality post gets low score."""
        from tests.conftest import make_timestamp

        post = {
            "record": {"text": "meh", "langs": ["en"]},
            "author": {"handle": "test.bsky.social"},
            "indexedAt": make_timestamp(1),
            "likeCount": 0,
            "repostCount": 0,
        }
        promo_domains = set()
        score = calculate_final_score(post, promo_domains)
        assert score < 10
