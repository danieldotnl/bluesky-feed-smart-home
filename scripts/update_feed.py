#!/usr/bin/env python3
"""Main entry point for updating the feed via GitHub Actions."""

import asyncio
from pathlib import Path

from src.algorithm import filter_and_rank
from src.config import FEED_SIZE
from src.generator import write_output_files
from src.search import fetch_all_posts


async def main() -> None:
    print("Fetching posts from Bluesky...")
    posts = await fetch_all_posts()
    print(f"Found {len(posts)} unique posts")

    print("Filtering and ranking posts...")
    ranked_posts = filter_and_rank(posts, limit=FEED_SIZE)
    print(f"Selected top {len(ranked_posts)} posts")

    output_dir = Path(__file__).parent.parent / "output"
    write_output_files(ranked_posts, output_dir)

    print("Feed update complete!")


if __name__ == "__main__":
    asyncio.run(main())
