"""Text cleanup, URL normalization and secret redaction."""

from __future__ import annotations

import html
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

HTML_TAGS = re.compile(r"<[^>]+>")
WHITESPACE = re.compile(r"\s+")
MARKDOWN_LINK = re.compile(r"\((https?://[^\s)]+)\)")
TRACKING_PARAMS = ("utm_", "ref")


def clean(text: str) -> str:
    """Strip tags, resolve entities and collapse whitespace."""
    text = HTML_TAGS.sub(" ", text or "")
    return WHITESPACE.sub(" ", html.unescape(text)).strip()


def normalize_url(url: str) -> str:
    """Stable key for a link, used to deduplicate and match the history."""
    try:
        parts = urlparse(url.strip().lower())
    except ValueError:
        return url.strip().lower()

    host = parts.netloc.removeprefix("www.")
    path = parts.path.rstrip("/") or "/"
    query = urlencode(
        [
            (key, value)
            for key, value in parse_qsl(parts.query)
            if not key.startswith(TRACKING_PARAMS)
        ]
    )
    return urlunparse(("", host, path, "", query, ""))


def links_in(text: str) -> set[str]:
    """URLs inside markdown links — how the bulletin cites its sources."""
    return set(MARKDOWN_LINK.findall(text))


def redact(text: str, *secrets: str) -> str:
    """Replace keys and webhooks with [oculto] before any public log."""
    for secret in secrets:
        if secret:
            text = text.replace(secret, "[oculto]")
    return text
