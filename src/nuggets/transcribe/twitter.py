"""Twitter/X content fetching for Podcast Nuggets.

Fetches threads and articles from Twitter/X using Jina Reader API.
No API keys required - Jina Reader is a free web service.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import httpx


def extract_tweet_id(url: str) -> str:
    """Extract tweet/status ID from X/Twitter URL.

    Args:
        url: Twitter/X URL (x.com or twitter.com)

    Returns:
        Tweet ID string.

    Raises:
        ValueError: If URL format is not recognized.

    Examples:
        >>> extract_tweet_id("https://x.com/user/status/123456")
        "123456"
        >>> extract_tweet_id("https://twitter.com/user/status/789")
        "789"
    """
    match = re.search(r"(?:twitter|x)\.com/\w+/status/(\d+)", url)
    if match:
        return match.group(1)
    raise ValueError(f"Could not extract tweet ID from: {url}")


def extract_author(url: str) -> str:
    """Extract author username from X/Twitter URL.

    Args:
        url: Twitter/X URL.

    Returns:
        Username without @ symbol.
    """
    match = re.search(r"(?:twitter|x)\.com/(\w+)/status/", url)
    return match.group(1) if match else "unknown"


def fetch_via_jina(url: str, timeout: float = 60.0) -> dict:
    """Fetch content via Jina Reader API.

    Jina Reader converts web pages to markdown format.
    Free to use, no API key required.

    Args:
        url: URL to fetch.
        timeout: Request timeout in seconds.

    Returns:
        Dict with 'content' and 'title' keys.

    Raises:
        httpx.HTTPError: If request fails.
    """
    jina_url = f"https://r.jina.ai/{url}"
    response = httpx.get(jina_url, timeout=timeout, follow_redirects=True)
    response.raise_for_status()

    content = response.text

    # Parse title from first markdown heading
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    title = title_match.group(1) if title_match else "X Thread"

    return {
        "content": content,
        "title": title,
        "source": "jina",
    }


def process_twitter_source(url: str) -> dict:
    """Process Twitter/X URL and return content dict.

    Fetches content via Jina Reader and extracts metadata.

    Args:
        url: Twitter/X URL to process.

    Returns:
        Dict with tweet_id, author, url, title, content, date, source.
    """
    tweet_id = extract_tweet_id(url)
    author = extract_author(url)

    result = fetch_via_jina(url)

    return {
        "tweet_id": tweet_id,
        "author": author,
        "url": url,
        "title": result["title"],
        "content": result["content"],
        "date": date.today().isoformat(),
        "source": "twitter",
    }


def save_raw_twitter(result: dict, base_path: Path | None = None) -> Path:
    """Save raw Twitter content to library structure.

    Args:
        result: Dict from process_twitter_source.
        base_path: Optional custom base path.

    Returns:
        Path to saved file.
    """
    from nuggets.library import LibraryPaths

    paths = LibraryPaths(base_path)
    output_path = paths.raw_twitter(
        result["author"],
        result["date"],
        result["tweet_id"],
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output_path
