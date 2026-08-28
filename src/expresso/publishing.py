"""Publishing to Discord, respecting the per-message character limit."""

from __future__ import annotations

import time

import requests

from expresso import USER_AGENT
from expresso.config import Config
from expresso.text import redact

WAIT_BETWEEN_PARTS = 1


def split(message: str, limit: int) -> list[str]:
    """Break the message into parts, preferring a cut between paragraphs."""
    parts: list[str] = []
    remaining = message

    while len(remaining) > limit:
        cut = remaining.rfind("\n\n", 0, limit)
        if cut == -1:
            cut = limit
        parts.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()

    parts.append(remaining)
    return parts


def publish(message: str, cfg: Config) -> None:
    for part in split(message, cfg.discord_limit):
        try:
            response = requests.post(
                cfg.webhook,
                json={"content": part, "allowed_mentions": {"parse": []}},
                headers={"User-Agent": USER_AGENT},
                timeout=cfg.discord_timeout,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            raise RuntimeError(
                f"Falha ao publicar no Discord ({type(error).__name__}): "
                f"{redact(str(error), cfg.webhook)}"
            ) from None
        time.sleep(WAIT_BETWEEN_PARTS)
