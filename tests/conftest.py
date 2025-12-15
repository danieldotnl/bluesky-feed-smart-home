"""Pytest configuration and shared fixtures."""

from datetime import UTC, datetime, timedelta

import pytest


def make_timestamp(hours_ago: float = 0) -> str:
    """Create ISO timestamp for hours ago from now."""
    dt = datetime.now(UTC) - timedelta(hours=hours_ago)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")


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
                "text": "Testing smart home automation with Home Assistant #smarthome",
                "createdAt": make_timestamp(1),
                "langs": ["en"],
            },
            "indexedAt": make_timestamp(1),
            "likeCount": 5,
            "repostCount": 2,
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
                "createdAt": make_timestamp(2),
                "langs": ["en"],
            },
            "indexedAt": make_timestamp(2),
            "likeCount": 10,
            "repostCount": 3,
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
                "createdAt": make_timestamp(3),
                "langs": ["en"],
            },
            "indexedAt": make_timestamp(3),
            "likeCount": 2,
            "repostCount": 0,
        },
    ]


@pytest.fixture
def sample_post_with_duplicate(sample_posts):
    """Sample posts with a duplicate URI for deduplication testing."""
    duplicate = sample_posts[0].copy()
    duplicate["cid"] = "bafytest1duplicate"
    return sample_posts + [duplicate]


@pytest.fixture
def spam_post():
    """A post that should be filtered as spam."""
    return {
        "uri": "at://did:plc:spam/app.bsky.feed.post/spam123",
        "cid": "bafyspam",
        "author": {
            "did": "did:plc:spam",
            "handle": "spammer.bsky.social",
        },
        "record": {
            "text": "Amazing deal on smart home devices! 50% discount! Buy now! 🔥🔥🔥🔥",
            "createdAt": make_timestamp(1),
            "langs": ["en"],
        },
        "indexedAt": make_timestamp(1),
        "likeCount": 0,
        "repostCount": 0,
    }


@pytest.fixture
def reply_post():
    """A post that is a reply."""
    return {
        "uri": "at://did:plc:reply/app.bsky.feed.post/reply123",
        "cid": "bafyreply",
        "author": {
            "did": "did:plc:reply",
            "handle": "replier.bsky.social",
        },
        "record": {
            "text": "Great setup! #homeassistant",
            "createdAt": make_timestamp(1),
            "langs": ["en"],
            "reply": {
                "parent": {"uri": "at://did:plc:other/app.bsky.feed.post/parent"},
                "root": {"uri": "at://did:plc:other/app.bsky.feed.post/root"},
            },
        },
        "indexedAt": make_timestamp(1),
        "likeCount": 1,
        "repostCount": 0,
    }


@pytest.fixture
def non_english_post():
    """A post in a non-English language."""
    return {
        "uri": "at://did:plc:foreign/app.bsky.feed.post/foreign123",
        "cid": "bafyforeign",
        "author": {
            "did": "did:plc:foreign",
            "handle": "foreign.bsky.social",
        },
        "record": {
            "text": "Domotique maison intelligente #smarthome",
            "createdAt": make_timestamp(1),
            "langs": ["fr"],
        },
        "indexedAt": make_timestamp(1),
        "likeCount": 5,
        "repostCount": 1,
    }


@pytest.fixture
def affiliate_post():
    """A post with Amazon affiliate links."""
    return {
        "uri": "at://did:plc:aff/app.bsky.feed.post/aff123",
        "cid": "bafyaff",
        "author": {
            "did": "did:plc:aff",
            "handle": "affiliate.bsky.social",
        },
        "record": {
            "text": (
                "Check out this smart plug! "
                "https://amazon.com/dp/B123?tag=myaffiliate-20 #smarthome"
            ),
            "createdAt": make_timestamp(1),
            "langs": ["en"],
        },
        "indexedAt": make_timestamp(1),
        "likeCount": 0,
        "repostCount": 0,
    }


@pytest.fixture
def high_quality_post():
    """A high-quality technical post."""
    return {
        "uri": "at://did:plc:quality/app.bsky.feed.post/quality123",
        "cid": "bafyquality",
        "author": {
            "did": "did:plc:quality",
            "handle": "expert.bsky.social",
        },
        "record": {
            "text": """Here's my Home Assistant automation for energy monitoring:

```yaml
automation:
  trigger:
    - platform: numeric_state
      entity_id: sensor.power_usage
  action:
    - service: notify.mobile
```

Check the docs: https://home-assistant.io/docs/automation #homeassistant""",
            "createdAt": make_timestamp(1),
            "langs": ["en"],
        },
        "indexedAt": make_timestamp(1),
        "likeCount": 25,
        "repostCount": 10,
        "embed": {
            "$type": "app.bsky.embed.images",
            "images": [{"alt": "Dashboard screenshot"}],
        },
    }


@pytest.fixture
def old_post():
    """A post older than the time window."""
    return {
        "uri": "at://did:plc:old/app.bsky.feed.post/old123",
        "cid": "bafyold",
        "author": {
            "did": "did:plc:old",
            "handle": "olduser.bsky.social",
        },
        "record": {
            "text": "Old smart home post #smarthome",
            "createdAt": make_timestamp(200),  # ~8 days old
            "langs": ["en"],
        },
        "indexedAt": make_timestamp(200),
        "likeCount": 100,
        "repostCount": 50,
    }


@pytest.fixture
def blacklisted_post():
    """A post from a blacklisted account."""
    return {
        "uri": "at://did:plc:blacklisted/app.bsky.feed.post/bl123",
        "cid": "bafybl",
        "author": {
            "did": "did:plc:blacklisted",
            "handle": "gd75wr14av.bsky.social",  # In blacklist
        },
        "record": {
            "text": "Smart home content #smarthome",
            "createdAt": make_timestamp(1),
            "langs": ["en"],
        },
        "indexedAt": make_timestamp(1),
        "likeCount": 10,
        "repostCount": 5,
    }


@pytest.fixture
def self_authored_post():
    """A post from the feed owner."""
    return {
        "uri": "at://did:plc:self/app.bsky.feed.post/self123",
        "cid": "bafyself",
        "author": {
            "did": "did:plc:self",
            "handle": "smarthomenewsletter.bsky.social",
        },
        "record": {
            "text": "Weekly smart home roundup from the newsletter #smarthome",
            "createdAt": make_timestamp(1),
            "langs": ["en"],
        },
        "indexedAt": make_timestamp(1),
        "likeCount": 15,
        "repostCount": 5,
    }


@pytest.fixture
def promotional_post():
    """A post linking to a promotional domain."""
    return {
        "uri": "at://did:plc:promo/app.bsky.feed.post/promo123",
        "cid": "bafypromo",
        "author": {
            "did": "did:plc:promo",
            "handle": "howtogeek.bsky.social",
        },
        "record": {
            "text": (
                "Check out our latest article! https://howtogeek.com/smart-home-guide #smarthome"
            ),
            "createdAt": make_timestamp(1),
            "langs": ["en"],
        },
        "indexedAt": make_timestamp(1),
        "likeCount": 20,
        "repostCount": 8,
    }


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary output directory for file generation tests."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def temp_data_dir(tmp_path):
    """Temporary data directory with test blacklist and keywords."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create blacklist
    blacklist = data_dir / "blacklist.txt"
    blacklist.write_text("gd75wr14av.bsky.social\noyfzw5q055.bsky.social\n")

    # Create keywords
    keywords = data_dir / "keywords.txt"
    keywords.write_text("#smarthome\n#homeassistant\nhome assistant\n")

    # Create promotional domains
    promo = data_dir / "promotional_domains.txt"
    promo.write_text("howtogeek.com\ntheverge.com\n")

    return data_dir
