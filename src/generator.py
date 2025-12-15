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
    """Generate the feed skeleton response."""
    feed = [{"post": post["uri"]} for post in posts if "uri" in post]

    # Use the last post's indexed_at as cursor for pagination
    cursor = None
    if posts:
        last_post = posts[-1]
        cursor = last_post.get("indexed_at") or last_post.get("indexedAt", "")

    result = {"feed": feed}
    if cursor:
        result["cursor"] = cursor

    return result


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

    print(f"Written {len(posts)} posts to feed skeleton")
    print(f"Output files written to {output_dir}")
