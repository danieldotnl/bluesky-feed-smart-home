import json
from pathlib import Path

import aiofiles

from src.config import FEED_DID, FEED_HOSTNAME


def generate_did_document() -> dict:
    """Generate the DID document for the feed generator."""
    return {
        "@context": ["https://www.w3.org/ns/did/v1"],
        "id": FEED_DID,
        "service": [
            {
                "id": "#bsky_fg",
                "type": "BskyFeedGenerator",
                "serviceEndpoint": f"https://{FEED_HOSTNAME}",
            }
        ],
    }


def generate_feed_skeleton(posts: list[dict]) -> dict:
    """Generate the feed skeleton response.

    Note: We intentionally omit the cursor field. Since this is a static feed
    that cannot handle pagination requests, omitting the cursor tells Bluesky
    clients that all posts are included and no more pages exist.
    """
    feed = [{"post": post["uri"]} for post in posts if "uri" in post]
    return {"feed": feed}


async def write_output_files(posts: list[dict], output_dir: Path) -> None:
    """Write the static JSON files for Cloudflare Pages."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write DID document
    well_known_dir = output_dir / ".well-known"
    well_known_dir.mkdir(exist_ok=True)
    did_path = well_known_dir / "did.json"
    did_doc = generate_did_document()
    async with aiofiles.open(did_path, "w") as f:
        await f.write(json.dumps(did_doc, indent=2))

    # Write feed skeleton
    xrpc_dir = output_dir / "xrpc"
    xrpc_dir.mkdir(exist_ok=True)
    feed_path = xrpc_dir / "app.bsky.feed.getFeedSkeleton"
    feed_skeleton = generate_feed_skeleton(posts)
    async with aiofiles.open(feed_path, "w") as f:
        await f.write(json.dumps(feed_skeleton, indent=2))

    # Write Cloudflare Pages headers
    headers_content = """\
/*
  Access-Control-Allow-Origin: *
  Content-Type: application/json

/xrpc/*
  Cache-Control: public, max-age=300, s-maxage=300
"""
    headers_path = output_dir / "_headers"
    async with aiofiles.open(headers_path, "w") as f:
        await f.write(headers_content)

    print(f"Written {len(posts)} posts to feed skeleton")
    print(f"Output files written to {output_dir}")
