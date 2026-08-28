"""From the raw list to the one the model sees: no repeats, no coupons."""

from __future__ import annotations

from expresso.config import Config
from expresso.models import Item
from expresso.text import normalize_url

TITLE_KEY_LENGTH = 70


def sift(
    items: list[Item],
    already_published: set[str],
    ignored_patterns: tuple[str, ...],
    cfg: Config,
) -> list[Item]:
    """Drop repeats, known noise and whatever exceeds one source's share.

    Walks from newest to oldest, so the per-source cap always keeps that
    source's most recent stories.
    """
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    per_source: dict[str, int] = {}
    kept: list[Item] = []

    for item in sorted(items, key=lambda i: i.published, reverse=True):
        url_key = normalize_url(item.url)
        if url_key in already_published or url_key in seen_urls:
            continue

        lowercase_url = item.url.lower()
        if any(pattern in lowercase_url for pattern in ignored_patterns):
            continue

        title_key = item.title.lower()[:TITLE_KEY_LENGTH]
        if title_key in seen_titles:
            continue

        if per_source.get(item.base_source, 0) >= cfg.max_per_source:
            continue

        seen_urls.add(url_key)
        seen_titles.add(title_key)
        per_source[item.base_source] = per_source.get(item.base_source, 0) + 1
        kept.append(item)

    return kept
