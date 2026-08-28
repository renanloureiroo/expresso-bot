"""Today's collection: RSS/Atom feeds and Hacker News, fetched in parallel."""

from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import feedparser
import requests

from expresso import USER_AGENT
from expresso.config import Config
from expresso.models import Item
from expresso.sources import Feed
from expresso.text import clean

HN_SEARCH = "https://hn.algolia.com/api/v1/search_by_date"


def _entry_date(entry) -> datetime | None:
    for field in ("published_parsed", "updated_parsed"):
        value = getattr(entry, field, None)
        if value:
            return datetime.fromtimestamp(time.mktime(value), tz=timezone.utc)
    return None


def _read_feed(feed: Feed, cutoff: datetime, cfg: Config) -> list[Item]:
    try:
        response = requests.get(
            feed.url, timeout=cfg.timeout, headers={"User-Agent": USER_AGENT}
        )
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
    except Exception as error:
        print(f"  ! {feed.name}: {type(error).__name__}", file=sys.stderr)
        return []

    items: list[Item] = []
    for entry in parsed.entries[: cfg.max_entries_per_feed]:
        published = _entry_date(entry)
        if not published or published < cutoff:
            continue

        link = getattr(entry, "link", "")
        title = clean(getattr(entry, "title", ""))
        if not link or not title:
            continue

        items.append(
            Item(
                source=feed.name,
                title=title,
                url=link,
                summary=clean(getattr(entry, "summary", "")),
                published=published,
            )
        )

    print(f"  {feed.name}: {len(items)}")
    return items


def collect_feeds(feeds: tuple[Feed, ...], cutoff: datetime, cfg: Config) -> list[Item]:
    with ThreadPoolExecutor(max_workers=cfg.workers) as pool:
        batches = pool.map(lambda feed: _read_feed(feed, cutoff, cfg), feeds)
    return [item for batch in batches for item in batch]


def _search_hn(term: str, cutoff: datetime, cfg: Config) -> list[Item]:
    after = int(cutoff.timestamp())
    try:
        response = requests.get(
            HN_SEARCH,
            params={
                "query": term,
                "tags": "story",
                "numericFilters": f"created_at_i>{after},points>{cfg.hn_min_points}",
                "hitsPerPage": cfg.hn_results_per_term,
            },
            timeout=cfg.timeout,
        )
        response.raise_for_status()
        hits = response.json().get("hits", [])
    except Exception as error:
        print(f"  ! Hacker News ({term}): {type(error).__name__}", file=sys.stderr)
        return []

    return [
        Item(
            source=f"Hacker News ({hit.get('points', 0)} pts)",
            title=clean(hit.get("title", "")),
            url=hit.get("url")
            or f"https://news.ycombinator.com/item?id={hit['objectID']}",
            summary="",
            published=datetime.fromtimestamp(hit["created_at_i"], tz=timezone.utc),
        )
        for hit in hits
    ]


def collect_hacker_news(
    terms: tuple[str, ...], cutoff: datetime, cfg: Config
) -> list[Item]:
    if not terms:
        return []

    with ThreadPoolExecutor(max_workers=min(cfg.workers, len(terms))) as pool:
        batches = pool.map(lambda term: _search_hn(term, cutoff, cfg), terms)

    items = [item for batch in batches for item in batch]
    print(f"  Hacker News: {len(items)}")
    return items
