"""What has already been published. The Action commits the file back each run."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from expresso.config import Config

DATE_FORMAT = "%Y-%m-%d"


@dataclass
class History:
    last_bulletin: str = ""
    links: dict[str, str] = field(default_factory=dict)

    @property
    def published_urls(self) -> set[str]:
        return set(self.links)

    def published_today(self, cfg: Config) -> bool:
        return self.last_bulletin == _today(cfg)


def _today(cfg: Config) -> str:
    return datetime.now(cfg.timezone).strftime(DATE_FORMAT)


def load(cfg: Config) -> History:
    """Read the history, already forgetting whatever fell out of the window."""
    try:
        data = json.loads(cfg.history_file.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    limit = (datetime.now(timezone.utc) - timedelta(days=cfg.history_days)).isoformat()
    return History(
        last_bulletin=data.get("last_bulletin", ""),
        links={url: date for url, date in data.get("links", {}).items() if date >= limit},
    )


def save(history: History, new_links: set[str], cfg: Config) -> None:
    now = datetime.now(timezone.utc).isoformat()
    history.links.update({url: now for url in new_links})
    history.last_bulletin = _today(cfg)

    cfg.history_file.write_text(
        json.dumps(
            {"last_bulletin": history.last_bulletin, "links": history.links},
            indent=1,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
