"""What flows between collection, filtering and writing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

MAX_SUMMARY_IN_LINE = 280


@dataclass(frozen=True)
class Item:
    source: str
    title: str
    url: str
    summary: str
    published: datetime

    def as_line(self) -> str:
        """One line of the raw list handed to the model."""
        summary = self.summary[:MAX_SUMMARY_IN_LINE].strip()
        base = f"- [{self.source}] {self.title} — {self.url}"
        return f"{base}\n  {summary}" if summary else base

    @property
    def base_source(self) -> str:
        """Source name without its parenthesized suffix ("Hacker News (120 pts)")."""
        return self.source.split(" (")[0]
