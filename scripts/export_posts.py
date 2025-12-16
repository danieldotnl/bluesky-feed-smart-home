#!/usr/bin/env python3
"""Export all searched posts with their content and scores to YAML."""

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.filters import get_author_handle, load_blacklist, passes_hard_filters
from src.scoring import (
    calculate_engagement_bonus,
    calculate_final_score,
    calculate_quality_score,
    calculate_time_decay,
    extract_features,
    load_promotional_domains,
)
from src.search import fetch_all_posts

# Load .env file if it exists (for local development)
load_dotenv()


def calculate_quality_breakdown(post: dict, features: dict, promotional_domains: set[str]) -> dict:
    """Calculate quality score with a breakdown of each component."""
    breakdown = {}

    # Positive signals
    if features["core_matches"] > 0:
        breakdown["core_topic_match"] = 20
    if features["secondary_matches"] > 0:
        breakdown["secondary_topic_match"] = 10
    if features["has_code"]:
        breakdown["has_code"] = 15
    if features["has_images"]:
        breakdown["has_images"] = 10
    if features["has_doc_link"]:
        breakdown["has_doc_link"] = 10

    # Text length bonus/penalty
    text_len = features["text_length"]
    if 100 <= text_len <= 500:
        breakdown["good_text_length"] = 5
    elif text_len < 50:
        breakdown["too_short"] = -15

    # Negative signals
    if features["hype_count"] > 0:
        breakdown["hype_penalty"] = -min(features["hype_count"] * 5, 10)
    if features["is_meme"]:
        breakdown["meme_penalty"] = -10
    if features["has_all_caps"]:
        breakdown["all_caps_penalty"] = -5

    # Promotional domain penalty
    for domain in features["link_domains"]:
        if domain in promotional_domains:
            breakdown["promotional_link"] = -20
            break

    # Self-promotional penalty
    author_handle = get_author_handle(post)
    for domain in features["link_domains"]:
        handle_base = author_handle.split(".")[0]
        domain_base = domain.split(".")[0]
        if handle_base in domain_base or domain_base in handle_base:
            if len(handle_base) > 3:
                breakdown["self_promo_link"] = -15
                break

    return breakdown


def extract_post_data(post: dict, promotional_domains: set[str], blacklist: set[str]) -> dict:
    """Extract relevant data from a post including scores."""
    record = post.get("record", {})
    author = post.get("author", {})

    # Calculate scores
    features = extract_features(post)
    quality_score = calculate_quality_score(post, features, promotional_domains)
    quality_breakdown = calculate_quality_breakdown(post, features, promotional_domains)
    engagement_bonus = calculate_engagement_bonus(post)
    time_decay = calculate_time_decay(post)
    final_score = calculate_final_score(post, promotional_domains)

    # Check filter status
    passed_filters = passes_hard_filters(post, blacklist)

    return {
        "uri": post.get("uri", ""),
        "cid": post.get("cid", ""),
        "author": {
            "handle": get_author_handle(post),
            "display_name": author.get("displayName") or author.get("display_name", ""),
        },
        "content": {
            "text": record.get("text", ""),
            "created_at": record.get("createdAt") or record.get("created_at", ""),
            "langs": record.get("langs", []),
        },
        "engagement": {
            "likes": post.get("like_count") or post.get("likeCount", 0) or 0,
            "reposts": post.get("repost_count") or post.get("repostCount", 0) or 0,
            "replies": post.get("reply_count") or post.get("replyCount", 0) or 0,
        },
        "indexed_at": post.get("indexed_at") or post.get("indexedAt", ""),
        "scores": {
            "final_score": round(final_score, 2),
            "quality_score": round(quality_score, 2),
            "quality_breakdown": quality_breakdown,
            "engagement_bonus": round(engagement_bonus, 2),
            "time_decay": round(time_decay, 4),
        },
        "features": {
            "core_matches": features["core_matches"],
            "secondary_matches": features["secondary_matches"],
            "has_code": features["has_code"],
            "has_images": features["has_images"],
            "has_doc_link": features["has_doc_link"],
            "text_length": features["text_length"],
            "hype_count": features["hype_count"],
            "is_meme": features["is_meme"],
        },
        "passed_filters": passed_filters,
    }


async def main() -> None:
    print("Fetching posts from Bluesky...")
    posts = await fetch_all_posts()
    print(f"Found {len(posts)} unique posts")

    # Load scoring/filter data
    promotional_domains = load_promotional_domains()
    blacklist = load_blacklist()

    print("Processing posts...")
    exported_posts = []
    for post in posts:
        post_data = extract_post_data(post, promotional_domains, blacklist)
        exported_posts.append(post_data)

    # Sort by final score descending
    exported_posts.sort(key=lambda p: p["scores"]["final_score"], reverse=True)

    # Prepare output
    output = {
        "exported_at": datetime.now(UTC).isoformat(),
        "total_posts": len(exported_posts),
        "posts_passing_filters": sum(1 for p in exported_posts if p["passed_filters"]),
        "posts": exported_posts,
    }

    # Write to file
    output_path = Path(__file__).parent.parent / "output" / "exported_posts.yaml"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(output, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"Exported {len(exported_posts)} posts to {output_path}")

    # Print summary
    if exported_posts:
        top_5 = exported_posts[:5]
        print("\nTop 5 posts by score:")
        for i, post in enumerate(top_5, 1):
            score = post["scores"]["final_score"]
            handle = post["author"]["handle"]
            text_preview = post["content"]["text"][:60].replace("\n", " ")
            print(f"  {i}. [{score:.1f}] @{handle}: {text_preview}...")


if __name__ == "__main__":
    asyncio.run(main())
