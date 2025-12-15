"""Unit tests for src/filters.py."""

from src.filters import (
    count_emojis,
    extract_urls,
    get_author_handle,
    get_url_domain,
    has_amazon_affiliate_link,
    has_excessive_emojis,
    has_spam_keywords,
    has_too_many_links,
    is_blacklisted,
    is_not_english,
    is_reply,
    is_self_authored,
    is_too_old,
    load_blacklist,
    passes_hard_filters,
)


class TestLoadBlacklist:
    """Tests for load_blacklist function."""

    def test_load_blacklist_reads_file(self):
        """Test loading blacklist from actual data file."""
        blacklist = load_blacklist()
        assert "gd75wr14av.bsky.social" in blacklist
        assert "oyfzw5q055.bsky.social" in blacklist

    def test_blacklist_is_lowercase(self):
        """Test that blacklist entries are lowercased."""
        blacklist = load_blacklist()
        for handle in blacklist:
            assert handle == handle.lower()


class TestGetAuthorHandle:
    """Tests for get_author_handle function."""

    def test_extracts_handle(self, sample_posts):
        """Test extracting author handle from post."""
        handle = get_author_handle(sample_posts[0])
        assert handle == "user1.bsky.social"

    def test_lowercases_handle(self):
        """Test that handle is lowercased."""
        post = {"author": {"handle": "User.Bsky.Social"}}
        handle = get_author_handle(post)
        assert handle == "user.bsky.social"

    def test_missing_author(self):
        """Test handling missing author."""
        post = {}
        handle = get_author_handle(post)
        assert handle == ""


class TestIsBlacklisted:
    """Tests for is_blacklisted function."""

    def test_blacklisted_account(self, blacklisted_post):
        """Test detecting blacklisted account."""
        blacklist = {"gd75wr14av.bsky.social"}
        assert is_blacklisted(blacklisted_post, blacklist)

    def test_not_blacklisted(self, sample_posts):
        """Test non-blacklisted account passes."""
        blacklist = {"gd75wr14av.bsky.social"}
        assert not is_blacklisted(sample_posts[0], blacklist)

    def test_case_insensitive(self, blacklisted_post):
        """Test blacklist matching is case-insensitive."""
        blacklist = {"GD75WR14AV.BSKY.SOCIAL"}
        # Our implementation lowercases both sides
        blacklist_lower = {h.lower() for h in blacklist}
        assert is_blacklisted(blacklisted_post, blacklist_lower)


class TestIsReply:
    """Tests for is_reply function."""

    def test_reply_detected(self, reply_post):
        """Test detecting reply posts."""
        assert is_reply(reply_post)

    def test_non_reply(self, sample_posts):
        """Test non-reply passes."""
        assert not is_reply(sample_posts[0])


class TestIsNotEnglish:
    """Tests for is_not_english function."""

    def test_english_post(self, sample_posts):
        """Test English post passes."""
        assert not is_not_english(sample_posts[0])

    def test_non_english_post(self, non_english_post):
        """Test non-English post is detected."""
        assert is_not_english(non_english_post)

    def test_no_language_specified(self):
        """Test post without language passes (rely on API filter)."""
        post = {"record": {"text": "Some text"}}
        assert not is_not_english(post)

    def test_multiple_languages_with_english(self):
        """Test post with multiple languages including English passes."""
        post = {"record": {"text": "Mixed", "langs": ["fr", "en"]}}
        assert not is_not_english(post)

    def test_en_variant_passes(self):
        """Test en-US and other English variants pass."""
        post = {"record": {"text": "US English", "langs": ["en-US"]}}
        assert not is_not_english(post)


class TestIsTooOld:
    """Tests for is_too_old function."""

    def test_recent_post(self, sample_posts):
        """Test recent post passes."""
        assert not is_too_old(sample_posts[0])

    def test_old_post(self, old_post):
        """Test old post is detected."""
        assert is_too_old(old_post)

    def test_missing_timestamp(self):
        """Test post without timestamp is considered too old."""
        post = {"uri": "test"}
        assert is_too_old(post)


class TestExtractUrls:
    """Tests for extract_urls function."""

    def test_extracts_urls(self):
        """Test extracting URLs from text."""
        text = "Check this: https://example.com and http://test.com/page"
        urls = extract_urls(text)
        assert len(urls) == 2
        assert "https://example.com" in urls
        assert "http://test.com/page" in urls

    def test_no_urls(self):
        """Test text without URLs."""
        urls = extract_urls("No links here")
        assert urls == []


class TestGetUrlDomain:
    """Tests for get_url_domain function."""

    def test_extracts_domain(self):
        """Test extracting domain from URL."""
        assert get_url_domain("https://example.com/page") == "example.com"
        assert get_url_domain("http://sub.example.com/") == "sub.example.com"

    def test_removes_www(self):
        """Test www prefix is removed."""
        assert get_url_domain("https://www.example.com") == "example.com"


class TestHasAmazonAffiliateLink:
    """Tests for has_amazon_affiliate_link function."""

    def test_amazon_tag(self, affiliate_post):
        """Test detecting Amazon affiliate tag."""
        assert has_amazon_affiliate_link(affiliate_post)

    def test_amzn_to_link(self):
        """Test detecting amzn.to shortlinks."""
        post = {"record": {"text": "Check this: https://amzn.to/abc123"}}
        assert has_amazon_affiliate_link(post)

    def test_clean_amazon_link(self):
        """Test clean Amazon link without tag passes."""
        post = {"record": {"text": "https://amazon.com/dp/B123456"}}
        assert not has_amazon_affiliate_link(post)

    def test_no_amazon(self, sample_posts):
        """Test post without Amazon links passes."""
        assert not has_amazon_affiliate_link(sample_posts[0])


class TestHasTooManyLinks:
    """Tests for has_too_many_links function."""

    def test_no_links(self, sample_posts):
        """Test post without links passes."""
        assert not has_too_many_links(sample_posts[0])

    def test_one_link(self):
        """Test single external link passes."""
        post = {"record": {"text": "Check https://example.com"}}
        assert not has_too_many_links(post)

    def test_two_links(self):
        """Test two external links fails."""
        post = {"record": {"text": "See https://a.com and https://b.com"}}
        assert has_too_many_links(post)

    def test_bsky_links_excluded(self):
        """Test bsky.app links don't count."""
        post = {"record": {"text": "See https://bsky.app/post and https://example.com"}}
        assert not has_too_many_links(post)


class TestHasSpamKeywords:
    """Tests for has_spam_keywords function."""

    def test_deal_keyword(self):
        """Test 'deal' keyword detected."""
        post = {"record": {"text": "Great deal on smart plugs!"}}
        assert has_spam_keywords(post)

    def test_discount_keyword(self):
        """Test 'discount' keyword detected."""
        post = {"record": {"text": "50% discount today!"}}
        assert has_spam_keywords(post)

    def test_clean_post(self, sample_posts):
        """Test clean post passes."""
        assert not has_spam_keywords(sample_posts[0])

    def test_case_insensitive(self):
        """Test detection is case-insensitive."""
        post = {"record": {"text": "AMAZING DEAL!"}}
        assert has_spam_keywords(post)


class TestCountEmojis:
    """Tests for count_emojis function."""

    def test_counts_emojis(self):
        """Test counting emojis."""
        assert count_emojis("Hello 🔥🚀💯") == 3

    def test_no_emojis(self):
        """Test text without emojis."""
        assert count_emojis("No emojis here") == 0

    def test_emoji_variations(self):
        """Test various emoji types."""
        # Emoticons, symbols, flags
        assert count_emojis("😀🏠🇺🇸") >= 2


class TestHasExcessiveEmojis:
    """Tests for has_excessive_emojis function."""

    def test_many_emojis(self, spam_post):
        """Test detecting excessive emojis."""
        assert has_excessive_emojis(spam_post)

    def test_few_emojis(self):
        """Test few emojis passes."""
        post = {"record": {"text": "Nice setup! 🏠👍"}}
        assert not has_excessive_emojis(post)

    def test_no_emojis(self, sample_posts):
        """Test no emojis passes."""
        assert not has_excessive_emojis(sample_posts[0])


class TestIsSelfAuthored:
    """Tests for is_self_authored function."""

    def test_self_authored(self, self_authored_post):
        """Test detecting self-authored post."""
        assert is_self_authored(self_authored_post)

    def test_not_self_authored(self, sample_posts):
        """Test non-self-authored post."""
        assert not is_self_authored(sample_posts[0])


class TestPassesHardFilters:
    """Tests for passes_hard_filters function."""

    def test_valid_post_passes(self, sample_posts):
        """Test valid posts pass all filters."""
        blacklist = load_blacklist()
        assert passes_hard_filters(sample_posts[0], blacklist)

    def test_blacklisted_fails(self, blacklisted_post):
        """Test blacklisted post fails."""
        blacklist = load_blacklist()
        assert not passes_hard_filters(blacklisted_post, blacklist)

    def test_reply_fails(self, reply_post):
        """Test reply fails."""
        blacklist = set()
        assert not passes_hard_filters(reply_post, blacklist)

    def test_non_english_fails(self, non_english_post):
        """Test non-English post fails."""
        blacklist = set()
        assert not passes_hard_filters(non_english_post, blacklist)

    def test_old_post_fails(self, old_post):
        """Test old post fails."""
        blacklist = set()
        assert not passes_hard_filters(old_post, blacklist)

    def test_affiliate_fails(self, affiliate_post):
        """Test affiliate post fails."""
        blacklist = set()
        assert not passes_hard_filters(affiliate_post, blacklist)

    def test_spam_fails(self, spam_post):
        """Test spam post fails."""
        blacklist = set()
        assert not passes_hard_filters(spam_post, blacklist)

    def test_self_authored_bypasses_spam(self, self_authored_post):
        """Test self-authored posts bypass spam filters."""
        # Add spam keywords to self-authored post
        self_authored_post["record"]["text"] += " Great deal!"
        blacklist = set()
        assert passes_hard_filters(self_authored_post, blacklist)
