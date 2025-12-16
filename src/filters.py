"""Hard filters for the feed algorithm - binary pass/fail checks."""

import re
from datetime import UTC, datetime

from src.config import DATA_DIR, SEARCH_TIME_WINDOW_DAYS, SELF_AUTHOR_HANDLE

# Spam keywords that indicate promotional/deal content
SPAM_KEYWORDS = {
    "deal",
    "deals",
    "discount",
    "promo",
    "promocode",
    "coupon",
    "buy now",
    "aff link",
    "affiliate",
    "limited time",
    "sale",
    "% off",
    "save $",
}

# Amazon affiliate link patterns
AMAZON_AFFILIATE_PATTERNS = [
    re.compile(r"amazon\.[a-z.]+/.*[?&]tag=", re.IGNORECASE),
    re.compile(r"amzn\.to/", re.IGNORECASE),
]

# URL pattern for extracting links from text
URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)

# Hashtag pattern for counting hashtags
HASHTAG_PATTERN = re.compile(r"#\w+", re.UNICODE)

# Bluesky internal domains to exclude from link counting
BSKY_DOMAINS = {"bsky.app", "bsky.social"}

# Common non-English words that indicate language mismatch when post is tagged as English
# These are high-frequency words unlikely to appear in English text
NON_ENGLISH_MARKERS = {
    # Italian
    "della",
    "delle",
    "degli",
    "nella",
    "nelle",
    "questo",
    "questa",
    "questi",
    "anche",
    "sono",
    "essere",
    "stato",
    "molto",
    "tutto",
    "tutti",
    "sempre",
    "ancora",
    "quando",
    "dove",
    "perché",
    "quindi",
    "però",
    "nuovo",
    "nuova",
    "rivela",
    "prossime",
    "uscite",
    # German
    "nicht",
    "sich",
    "auch",
    "werden",
    "nach",
    "noch",
    "jetzt",
    "können",
    "diese",
    "dieser",
    "dieses",
    "unter",
    "durch",
    "gegen",
    "während",
    # French
    "dans",
    "pour",
    "avec",
    "cette",
    "sont",
    "mais",
    "nous",
    "vous",
    "leur",
    "leurs",
    "être",
    "avoir",
    "faire",
    "tout",
    "tous",
    "très",
    # Spanish
    "para",
    "pero",
    "como",
    "está",
    "este",
    "esta",
    "esto",
    "tienen",
    "puede",
    "hacer",
    "sobre",
    "todos",
    "desde",
    "hasta",
    "entre",
    "nuevo",
    # Portuguese
    "para",
    "como",
    "está",
    "esse",
    "essa",
    "isso",
    "foram",
    "muito",
    "sobre",
    "todos",
    "desde",
    "agora",
    "ainda",
    "novo",
    "nova",
}


def load_blacklist() -> set[str]:
    """Load blacklisted account handles from data/blacklist.txt."""
    blacklist_file = DATA_DIR / "blacklist.txt"
    if not blacklist_file.exists():
        return set()
    return {
        line.strip().lower() for line in blacklist_file.read_text().splitlines() if line.strip()
    }


def get_author_handle(post: dict) -> str:
    """Extract author handle from post, normalized to lowercase."""
    author = post.get("author", {})
    handle = author.get("handle", "")
    return handle.lower()


def is_blacklisted(post: dict, blacklist: set[str]) -> bool:
    """Check if post author is in the blacklist."""
    handle = get_author_handle(post)
    return handle in blacklist


def is_reply(post: dict) -> bool:
    """Check if post is a reply to another post."""
    record = post.get("record", {})
    # The 'reply' key exists in all posts but is None for non-replies
    reply = record.get("reply")
    return reply is not None


def is_not_english(post: dict) -> bool:
    """Check if post language is not English.

    Returns True if post should be excluded (not English).
    Returns False if post is English or language is unknown (allow through).
    """
    record = post.get("record", {})
    langs = record.get("langs", [])

    # If no language specified, allow through (rely on search API filter)
    if not langs:
        return False

    # Check if any specified language is English
    for lang in langs:
        if lang.lower().startswith("en"):
            return False

    # No English language found
    return True


def is_too_old(post: dict) -> bool:
    """Check if post is older than the search time window."""
    indexed_at = post.get("indexed_at") or post.get("indexedAt", "")
    if not indexed_at:
        return True

    try:
        post_time = datetime.fromisoformat(indexed_at.replace("Z", "+00:00"))
        now = datetime.now(UTC)
        age_days = (now - post_time).total_seconds() / 86400
        return age_days > SEARCH_TIME_WINDOW_DAYS
    except (ValueError, AttributeError):
        return True


def extract_urls(text: str) -> list[str]:
    """Extract all URLs from text."""
    return URL_PATTERN.findall(text)


def get_url_domain(url: str) -> str:
    """Extract domain from URL."""
    # Remove protocol
    url = re.sub(r"^https?://", "", url)
    # Get domain part
    domain = url.split("/")[0].lower()
    # Remove www prefix
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def has_amazon_affiliate_link(post: dict) -> bool:
    """Check if post contains Amazon affiliate links."""
    record = post.get("record", {})
    text = record.get("text", "")

    for pattern in AMAZON_AFFILIATE_PATTERNS:
        if pattern.search(text):
            return True

    # Also check embed if present (external links)
    embed = post.get("embed", {})
    if embed:
        external = embed.get("external", {})
        uri = external.get("uri", "")
        for pattern in AMAZON_AFFILIATE_PATTERNS:
            if pattern.search(uri):
                return True

    return False


def has_too_many_links(post: dict, max_links: int = 1) -> bool:
    """Check if post has more than max_links outbound links (excluding bsky.app)."""
    record = post.get("record", {})
    text = record.get("text", "")

    urls = extract_urls(text)
    external_count = 0

    for url in urls:
        domain = get_url_domain(url)
        if domain not in BSKY_DOMAINS:
            external_count += 1

    return external_count > max_links


def has_spam_keywords(post: dict) -> bool:
    """Check if post contains spam/deal keywords."""
    record = post.get("record", {})
    text = record.get("text", "").lower()

    for keyword in SPAM_KEYWORDS:
        if keyword in text:
            return True

    return False


def count_emojis(text: str) -> int:
    """Count emojis in text."""
    # Unicode emoji ranges
    emoji_pattern = re.compile(
        "["
        "\U0001f600-\U0001f64f"  # emoticons
        "\U0001f300-\U0001f5ff"  # symbols & pictographs
        "\U0001f680-\U0001f6ff"  # transport & map
        "\U0001f1e0-\U0001f1ff"  # flags
        "\U00002702-\U000027b0"  # dingbats
        "\U0001f900-\U0001f9ff"  # supplemental symbols
        "\U0001fa00-\U0001fa6f"  # chess symbols
        "\U0001fa70-\U0001faff"  # symbols extended
        "\U00002600-\U000026ff"  # misc symbols
        "]+",
        flags=re.UNICODE,
    )
    matches = emoji_pattern.findall(text)
    return sum(len(match) for match in matches)


def has_excessive_emojis(post: dict, max_emojis: int = 3) -> bool:
    """Check if post has more than max_emojis emojis."""
    record = post.get("record", {})
    text = record.get("text", "")
    return count_emojis(text) > max_emojis


def count_hashtags(text: str) -> int:
    """Count hashtags in text."""
    return len(HASHTAG_PATTERN.findall(text))


def has_excessive_hashtags(post: dict, max_hashtags: int = 5) -> bool:
    """Check if post has more than max_hashtags hashtags (hashtag spam)."""
    record = post.get("record", {})
    text = record.get("text", "")
    return count_hashtags(text) > max_hashtags


def has_language_mismatch(post: dict, min_markers: int = 2) -> bool:
    """Check if post claims to be English but contains non-English text.

    Returns True if post should be excluded (language mismatch detected).
    Only checks posts that claim to be English.
    """
    record = post.get("record", {})
    langs = record.get("langs", [])

    # Only check posts that claim to be English
    is_tagged_english = any(lang.lower().startswith("en") for lang in langs)
    if not is_tagged_english:
        return False

    # Check text for non-English markers
    text = record.get("text", "").lower()
    # Split on whitespace and punctuation to get words
    words = set(re.findall(r"\b\w+\b", text))

    # Count how many non-English markers are found
    markers_found = words & NON_ENGLISH_MARKERS
    return len(markers_found) >= min_markers


def is_self_authored(post: dict) -> bool:
    """Check if post is authored by the feed owner."""
    handle = get_author_handle(post)
    return handle == SELF_AUTHOR_HANDLE.lower()


def passes_hard_filters(post: dict, blacklist: set[str]) -> bool:
    """Check if post passes all hard filters.

    Returns True if post should be included, False if excluded.
    Self-authored posts bypass spam filters.
    """
    # Always exclude blacklisted accounts
    if is_blacklisted(post, blacklist):
        return False

    # Always exclude replies
    if is_reply(post):
        return False

    # Always exclude non-English posts
    if is_not_english(post):
        return False

    # Exclude posts that claim English but contain non-English text
    if has_language_mismatch(post):
        return False

    # Always exclude posts older than time window
    if is_too_old(post):
        return False

    # Self-authored posts bypass remaining spam filters
    if is_self_authored(post):
        return True

    # Spam filters for non-self-authored posts
    if has_amazon_affiliate_link(post):
        return False

    if has_too_many_links(post):
        return False

    if has_spam_keywords(post):
        return False

    if has_excessive_emojis(post):
        return False

    if has_excessive_hashtags(post):
        return False

    return True
