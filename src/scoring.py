"""Quality scoring module for the feed algorithm."""

import re
from datetime import UTC, datetime

from src.config import DATA_DIR, DECAY_HALF_LIFE_HOURS, SELF_AUTHOR_HANDLE
from src.filters import extract_urls, get_author_handle, get_url_domain

# Core topics - strong relevance signal
CORE_TOPICS = {
    "home assistant",
    "homeassistant",
    "#homeassistant",
    "matter",
    "#matter",
    "thread",
    "#thread",
    "zigbee",
    "#zigbee",
    "zwave",
    "z-wave",
    "#zwave",
    "esphome",
    "#esphome",
}

# Secondary topics - moderate relevance signal
SECONDARY_TOPICS = {
    "shelly",
    "aqara",
    "hue",
    "philips hue",
    "tasmota",
    "#tasmota",
    "mqtt",
    "#mqtt",
    "smart home",
    "#smarthome",
    "home automation",
    "#homeautomation",
    "iot",
    "#iot",
    "sonoff",
    "tuya",
    "zigbee2mqtt",
    "zha",
    "deconz",
    "homekit",
    "alexa",
    "google home",
    "smartthings",
    "hubitat",
    "openhab",
    "node-red",
    "nodered",
}

# Hype words - negative signal
HYPE_WORDS = {
    "insane",
    "game changer",
    "game-changer",
    "mind blown",
    "mind-blown",
    "mindblown",
    "holy shit",
    "amazing",
    "incredible",
    "unbelievable",
    "best ever",
    "must have",
    "must-have",
    "life changing",
    "life-changing",
    "🔥",
    "🚀",
    "💯",
    "🤯",
}

# Meme patterns - negative signal
MEME_PATTERNS = [
    re.compile(r"^pov:", re.IGNORECASE),
    re.compile(r"^nobody:", re.IGNORECASE),
    re.compile(r"^me when", re.IGNORECASE),
    re.compile(r"^when you", re.IGNORECASE),
]

# Code/config patterns - positive signal
CODE_PATTERNS = [
    re.compile(r"```"),  # Code blocks
    re.compile(r"yaml:", re.IGNORECASE),
    re.compile(r"automation:", re.IGNORECASE),
    re.compile(r"sensor:", re.IGNORECASE),
    re.compile(r"service:", re.IGNORECASE),
    re.compile(r"trigger:", re.IGNORECASE),
    re.compile(r"action:", re.IGNORECASE),
    re.compile(r"condition:", re.IGNORECASE),
]

# Documentation/quality domains - positive signal
DOC_DOMAINS = {
    "github.com",
    "home-assistant.io",
    "esphome.io",
    "zigbee2mqtt.io",
    "community.home-assistant.io",
}


def load_promotional_domains() -> set[str]:
    """Load promotional domains from data/promotional_domains.txt."""
    promo_file = DATA_DIR / "promotional_domains.txt"
    if not promo_file.exists():
        return set()
    return {line.strip().lower() for line in promo_file.read_text().splitlines() if line.strip()}


def extract_features(post: dict) -> dict:
    """Extract features from a post for scoring."""
    record = post.get("record", {})
    text = record.get("text", "")
    text_lower = text.lower()

    # Topic matching
    core_matches = sum(1 for topic in CORE_TOPICS if topic in text_lower)
    secondary_matches = sum(1 for topic in SECONDARY_TOPICS if topic in text_lower)

    # Code/config detection
    has_code = any(pattern.search(text) for pattern in CODE_PATTERNS)

    # Image detection
    embed = post.get("embed", {})
    has_images = False
    if embed:
        # Check for image embeds
        embed_type = embed.get("$type", "")
        if "images" in embed_type.lower():
            has_images = True
        # Check for images array
        if embed.get("images"):
            has_images = True

    # Link analysis
    urls = extract_urls(text)
    link_domains = [get_url_domain(url) for url in urls]

    has_doc_link = any(domain in DOC_DOMAINS for domain in link_domains)

    # Text length
    text_length = len(text)

    # Hype detection
    hype_count = sum(1 for word in HYPE_WORDS if word in text_lower)

    # Meme detection
    is_meme = any(pattern.search(text) for pattern in MEME_PATTERNS)

    # ALL CAPS detection (3+ consecutive uppercase words)
    all_caps_pattern = re.compile(r"\b[A-Z]{2,}\s+[A-Z]{2,}\s+[A-Z]{2,}\b")
    has_all_caps = bool(all_caps_pattern.search(text))

    return {
        "core_matches": core_matches,
        "secondary_matches": secondary_matches,
        "has_code": has_code,
        "has_images": has_images,
        "has_doc_link": has_doc_link,
        "link_domains": link_domains,
        "text_length": text_length,
        "hype_count": hype_count,
        "is_meme": is_meme,
        "has_all_caps": has_all_caps,
    }


def calculate_quality_score(post: dict, features: dict, promotional_domains: set[str]) -> float:
    """Calculate base quality score (0-100) for a post."""
    score = 0.0

    # Positive signals
    if features["core_matches"] > 0:
        score += 20

    if features["secondary_matches"] > 0:
        score += 10

    if features["has_code"]:
        score += 15

    if features["has_images"]:
        score += 10

    if features["has_doc_link"]:
        score += 10

    # Text length bonus (medium length is ideal)
    text_len = features["text_length"]
    if 100 <= text_len <= 500:
        score += 5
    elif text_len < 50:
        score -= 15  # Very short posts penalized

    # Negative signals
    if features["hype_count"] > 0:
        score -= min(features["hype_count"] * 5, 10)

    if features["is_meme"]:
        score -= 10

    if features["has_all_caps"]:
        score -= 5

    # Promotional domain penalty
    for domain in features["link_domains"]:
        if domain in promotional_domains:
            score -= 20
            break

    # Self-promotional penalty (author handle matches linked domain)
    author_handle = get_author_handle(post)
    for domain in features["link_domains"]:
        # Check if handle contains domain or domain contains handle
        handle_base = author_handle.split(".")[0]
        domain_base = domain.split(".")[0]
        if handle_base in domain_base or domain_base in handle_base:
            if len(handle_base) > 3:  # Avoid false positives on short handles
                score -= 15
                break

    # Ensure score is within bounds
    return max(0.0, min(100.0, score))


def calculate_engagement_bonus(post: dict) -> float:
    """Calculate engagement bonus (capped at 10)."""
    like_count = post.get("like_count") or post.get("likeCount", 0) or 0
    repost_count = post.get("repost_count") or post.get("repostCount", 0) or 0

    like_bonus = min(like_count * 0.5, 5)
    repost_bonus = min(repost_count * 1.0, 5)

    return like_bonus + repost_bonus


def calculate_time_decay(post: dict, half_life_hours: float = DECAY_HALF_LIFE_HOURS) -> float:
    """Calculate time decay factor (0-1) based on post age."""
    indexed_at = post.get("indexed_at") or post.get("indexedAt", "")
    if not indexed_at:
        return 0.1  # Very old/unknown posts get minimal visibility

    try:
        post_time = datetime.fromisoformat(indexed_at.replace("Z", "+00:00"))
        now = datetime.now(UTC)
        age_hours = (now - post_time).total_seconds() / 3600

        # Exponential decay: 0.5^(age/half_life)
        decay = 0.5 ** (age_hours / half_life_hours)
        return max(0.01, decay)  # Minimum 1% to avoid zero scores
    except (ValueError, AttributeError):
        return 0.1


def calculate_final_score(post: dict, promotional_domains: set[str]) -> float:
    """Calculate final score for a post combining all factors."""
    features = extract_features(post)
    quality_score = calculate_quality_score(post, features, promotional_domains)
    engagement_bonus = calculate_engagement_bonus(post)
    time_decay = calculate_time_decay(post)

    final_score = (quality_score * time_decay) + engagement_bonus

    # Self-authored posts get a minimum score floor
    author_handle = get_author_handle(post)
    if author_handle == SELF_AUTHOR_HANDLE.lower():
        final_score = max(final_score, 50)

    return final_score
