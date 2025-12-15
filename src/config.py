from pathlib import Path

FEED_HOSTNAME = "bluesky-feed.smarthomenewsletter.com"
FEED_DID = f"did:web:{FEED_HOSTNAME}"
FEED_RECORD_NAME = "smart-home"
FEED_URI = f"at://{FEED_DID}/app.bsky.feed.generator/{FEED_RECORD_NAME}"
FEED_DISPLAY_NAME = "Smart Home"
FEED_DESCRIPTION = (
    "Smart home & Home Automation posts automatically curated for quality.\n"
    "No spam. No deals. English only.\n"
    "\n"
    "Home Assistant · HomeKit · SmartThings · Google Home · "
    "Matter · Zigbee · Philips Hue · Alexa · and more\n"
    "\n"
    "By Smart Home Newsletter — smarthomenewsletter.com"
)

# Feed settings
FEED_SIZE = 100
LANGUAGE = "en"

# Algorithm settings
SELF_AUTHOR_HANDLE = "smarthomenewsletter.bsky.social"
SEARCH_TIME_WINDOW_DAYS = 7
DECAY_HALF_LIFE_HOURS = 18

# Data directory
DATA_DIR = Path(__file__).parent.parent / "data"


def load_keywords() -> list[str]:
    """Load search keywords from data/keywords.txt."""
    keywords_file = DATA_DIR / "keywords.txt"
    if not keywords_file.exists():
        return []
    return [line.strip() for line in keywords_file.read_text().splitlines() if line.strip()]
