"""Feed algorithm - filtering and ranking posts."""

from src.config import FEED_SIZE
from src.filters import load_blacklist, passes_hard_filters
from src.scoring import calculate_final_score, load_promotional_domains


def filter_and_rank(posts: list[dict], limit: int = FEED_SIZE) -> list[dict]:
    """Filter and rank posts for the feed.

    Pipeline:
    1. Apply hard filters (exclude spam, replies, non-English, blacklisted)
    2. Calculate final scores (quality * decay + engagement)
    3. Sort by score descending
    4. Return top N posts

    Args:
        posts: List of post dictionaries from search
        limit: Maximum number of posts to return

    Returns:
        Ranked list of posts for the feed
    """
    # Load filter/scoring data
    blacklist = load_blacklist()
    promotional_domains = load_promotional_domains()

    # Step 1: Apply hard filters
    filtered = [p for p in posts if passes_hard_filters(p, blacklist)]
    print(f"After filtering: {len(filtered)}/{len(posts)} posts passed")

    # Step 2: Calculate scores
    scored = [(post, calculate_final_score(post, promotional_domains)) for post in filtered]

    # Step 3: Sort by score descending
    scored.sort(key=lambda x: x[1], reverse=True)

    # Step 4: Return top N posts
    result = [post for post, score in scored[:limit]]

    # Log top scores for debugging
    if scored:
        top_scores = [f"{score:.1f}" for _, score in scored[:5]]
        print(f"Top scores: {', '.join(top_scores)}")

    return result
