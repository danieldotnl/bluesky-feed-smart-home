from datetime import datetime


def sort_by_date(posts: list[dict]) -> list[dict]:
    """Sort posts by creation date, newest first."""

    def get_timestamp(post: dict) -> datetime:
        indexed_at = post.get("indexedAt", "")
        try:
            return datetime.fromisoformat(indexed_at.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return datetime.min

    return sorted(posts, key=get_timestamp, reverse=True)


def filter_and_rank(posts: list[dict], limit: int = 50) -> list[dict]:
    """Filter and rank posts for the feed."""
    # Sort by date (newest first)
    sorted_posts = sort_by_date(posts)

    # Return top N posts
    return sorted_posts[:limit]
