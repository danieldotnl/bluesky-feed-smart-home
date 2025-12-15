#!/usr/bin/env python3
"""One-time script to register the feed on Bluesky."""

import asyncio
import os

from atproto import AsyncClient
from dotenv import load_dotenv

from src.config import FEED_DID

# Load .env file if it exists (for local development)
load_dotenv()

# Feed metadata
FEED_RECORD_NAME = "smart-home"
FEED_DISPLAY_NAME = "Smart Home"
FEED_DESCRIPTION = "Posts about smart home, home automation, Home Assistant, and IoT"


async def main() -> None:
    handle = os.environ.get("BSKY_HANDLE")
    password = os.environ.get("BSKY_PASSWORD")

    if not handle or not password:
        print("Error: Set BSKY_HANDLE and BSKY_PASSWORD environment variables")
        return

    client = AsyncClient()
    await client.login(handle, password)

    print(f"Logged in as {handle}")
    print(f"Publishing feed: {FEED_DISPLAY_NAME}")
    print(f"Feed DID: {FEED_DID}")

    # Create the feed generator record
    feed_record = {
        "$type": "app.bsky.feed.generator",
        "did": FEED_DID,
        "displayName": FEED_DISPLAY_NAME,
        "description": FEED_DESCRIPTION,
        "createdAt": client.get_current_time_iso(),
    }

    await client.com.atproto.repo.put_record(
        {
            "repo": client.me.did,
            "collection": "app.bsky.feed.generator",
            "rkey": FEED_RECORD_NAME,
            "record": feed_record,
        }
    )

    print("Feed published successfully!")
    print(f"Feed URI: at://{client.me.did}/app.bsky.feed.generator/{FEED_RECORD_NAME}")
    print(f"View at: https://bsky.app/profile/{handle}/feed/{FEED_RECORD_NAME}")


if __name__ == "__main__":
    asyncio.run(main())
