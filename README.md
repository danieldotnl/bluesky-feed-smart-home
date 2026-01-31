# Smart Home Feed for Bluesky

A curated Bluesky feed surfacing the best smart home and home automation content from the community.

**Created by [Smart Home Newsletter](https://smarthomenewsletter.com)** - Your weekly dose of smart home news, tips, and tutorials.

## Follow the Feed

**[Add to Bluesky](https://bsky.app/profile/did:plc:r36vlvkntmnbs6nsbmqqbajm/feed/smart-home)**

## What Makes This Feed Special

This feed goes beyond simple hashtag following to deliver high-quality smart home content:

- **Smart filtering** - Automatically filters out spam, affiliate links, and low-quality posts
- **Quality scoring** - Prioritizes posts with code examples, documentation links, and substantive content
- **Freshness** - Updated every 30 minutes with the latest posts
- **Topic focused** - Covers Home Assistant, ESPHome, Matter, Thread, Zigbee, Z-Wave, and more

## How It Works

This is a static feed generator that runs as a scheduled GitHub Action:

1. **Search** - Queries Bluesky for posts matching smart home keywords
2. **Filter** - Removes spam, replies, non-English content, and blacklisted accounts
3. **Score** - Ranks posts by quality signals and engagement
4. **Generate** - Writes static JSON files with the top 50 posts
5. **Deploy** - Publishes to Cloudflare Pages with a Pages Function for pagination

### Architecture Highlights

- **Static-first**: Pre-generates feed data as JSON files for fast delivery
- **Hybrid approach**: Cloudflare Pages Function handles pagination while serving static data
- **Python + uv**: Modern Python tooling with the uv package manager
- **No database**: Fully stateless, regenerates feed on each run
- **Cost-effective**: Runs on free GitHub Actions and Cloudflare Pages tiers

## Quality Filters

Posts are evaluated across multiple dimensions:

### Hard Filters (Binary Pass/Fail)
- No spam keywords (deals, discounts, affiliate marketing)
- No Amazon affiliate links
- Maximum 1 external link
- Maximum 3 emojis
- Maximum 5 hashtags
- English language only
- No replies (original posts only)
- Language verification (blocks mis-tagged non-English posts)

### Quality Scoring
**Positive signals:**
- Core topics (Home Assistant, Matter, Thread, Zigbee, etc.)
- Code blocks or YAML configurations
- Images or screenshots
- Links to documentation (GitHub, Home Assistant docs, etc.)
- Medium-length posts (100-500 characters)

**Negative signals:**
- Hype words ("game changer", "insane", fire emojis)
- Meme patterns ("POV:", "nobody:", etc.)
- ALL CAPS text
- Promotional domains (tech news sites)
- Self-promotional links (author's own domain)

### Time Decay
Recent posts get priority via exponential decay (24-hour half-life).

## Development

### Prerequisites

- Python 3.14 or later
- [uv](https://github.com/astral-sh/uv) package manager
- Bluesky account credentials

### Setup

```bash
# Clone the repository
git clone https://github.com/danieldotnl/bluesky-feed-smart-home.git
cd bluesky-feed-smart-home

# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env and add your BSKY_HANDLE and BSKY_PASSWORD
```

### Running Locally

```bash
# Update the feed (generates output/ directory)
uv run python scripts/update_feed.py

# Test the Cloudflare Pages Function locally
npm install
npm test
```

### Linting and Testing

```bash
# Run linter
uv run ruff check .

# Format code
uv run ruff format .

# Run tests
uv run pytest
```

## Configuration

All feed settings are in [src/config.py](src/config.py):

- `SEARCH_KEYWORDS` - Keywords and hashtags to search for
- `FEED_SIZE` - Number of posts to include (default: 50)
- `DECAY_HALF_LIFE_HOURS` - Time decay rate (default: 24 hours)
- `SEARCH_TIME_WINDOW_DAYS` - How far back to search (default: 3 days)

Blacklisted accounts and promotional domains are maintained in:
- [data/blacklist.txt](data/blacklist.txt) - User handles to exclude
- [data/promotional_domains.txt](data/promotional_domains.txt) - Domains to penalize

## Deployment

This feed deploys automatically via GitHub Actions:

- **Schedule**: Every 30 minutes via cron
- **Platform**: Cloudflare Pages
- **Secrets required**:
  - `BSKY_HANDLE` - Your Bluesky handle
  - `BSKY_PASSWORD` - Your Bluesky password
  - `CLOUDFLARE_API_TOKEN` - Cloudflare API token
  - `CLOUDFLARE_ACCOUNT_ID` - Cloudflare account ID

## Project Structure

```
.
├── src/
│   ├── algorithm.py      # Main filtering and ranking pipeline
│   ├── config.py         # Feed configuration
│   ├── filters.py        # Hard filters (spam, language, etc.)
│   ├── generator.py      # Static file generation
│   ├── scoring.py        # Quality scoring logic
│   └── search.py         # Bluesky API search
├── scripts/
│   ├── update_feed.py    # Main entry point (run by GitHub Actions)
│   └── publish_feed.py   # One-time feed registration
├── functions/
│   └── xrpc/
│       └── app.bsky.feed.getFeedSkeleton.js  # Pagination handler
├── data/
│   ├── blacklist.txt           # Blocked accounts
│   └── promotional_domains.txt # Penalized domains
└── output/                # Generated feed files (git-ignored)
```

## Tech Stack

- **Language**: Python 3.14+
- **Package Manager**: [uv](https://github.com/astral-sh/uv)
- **API Client**: [atproto](https://github.com/MarshalX/atproto) Python library
- **CI/CD**: GitHub Actions
- **Hosting**: Cloudflare Pages
- **Testing**: pytest + vitest (for JS function)

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

### Reporting Spam

If you notice spam or low-quality posts in the feed, please [open an issue](https://github.com/danieldotnl/bluesky-feed-smart-home/issues) with:
- Link to the post
- Reason it should be filtered
- Suggested filter improvement

## License

MIT License - see [LICENSE](LICENSE) file for details.

## About

This feed is maintained by [Daniel](https://bsky.app/profile/smarthomenewsletter.com), creator of the [Smart Home Newsletter](https://smarthomenewsletter.com).

**Want more smart home content?** Subscribe to the newsletter for weekly curated news, tutorials, and deep dives into home automation.

---

Built with the [AT Protocol](https://atproto.com/) | Powered by [Bluesky](https://bsky.app/)
