FEED_HOSTNAME = "bluesky-feed.smarthomenewsletter.com"
FEED_DID = f"did:web:{FEED_HOSTNAME}"
FEED_RECORD_NAME = "smart-home"
FEED_URI = f"at://{FEED_DID}/app.bsky.feed.generator/{FEED_RECORD_NAME}"
FEED_DISPLAY_NAME = "Smart Home"
FEED_DESCRIPTION = "Posts about smart home, home automation, Home Assistant, and IoT"

# Search keywords for smart home content
SEARCH_KEYWORDS = [
    "#smarthome",
    "#homeassistant",
    "#homeautomation",
    "#iot",
    "#zigbee",
    "#zwave",
    "#matter",
    "#thread",
    "#esphome",
    "#tasmota",
    "#mqtt",
    "smart home",
    "home assistant",
    "home automation",
]

# Feed settings
FEED_SIZE = 50
LANGUAGE = "en"
