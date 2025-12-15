#!/usr/bin/env python3
"""Fetch sample post data for test fixtures."""

import asyncio
import json

from dotenv import load_dotenv

from src.search import fetch_all_posts

load_dotenv()


async def main() -> None:
    posts = await fetch_all_posts()
    # Get a small sample for testing
    sample = posts[:5] if len(posts) >= 5 else posts

    print(f"Fetched {len(posts)} posts, using {len(sample)} as samples")
    print(json.dumps(sample, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
