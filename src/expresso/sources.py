"""Reading config/sources.toml — feeds, Hacker News terms and filters."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Feed:
    track: str
    name: str
    url: str


@dataclass(frozen=True)
class Sources:
    feeds: tuple[Feed, ...]
    hn_terms: tuple[str, ...]
    ignored_patterns: tuple[str, ...]


def load(path: Path) -> Sources:
    """Read the sources file, failing loudly if it is missing or broken."""
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise RuntimeError(
            f"Arquivo de fontes não encontrado: {path}. "
            "Aponte outro com SOURCES_FILE."
        ) from None
    except tomllib.TOMLDecodeError as error:
        raise RuntimeError(f"Arquivo de fontes inválido ({path}): {error}") from None

    feeds = tuple(
        Feed(
            track=str(raw.get("track", "geral")),
            name=str(raw["name"]),
            url=str(raw["url"]),
        )
        for raw in data.get("feeds", [])
    )
    if not feeds:
        raise RuntimeError(f"Nenhum feed declarado em {path}.")

    return Sources(
        feeds=feeds,
        hn_terms=tuple(data.get("hacker_news", {}).get("terms", [])),
        ignored_patterns=tuple(data.get("filters", {}).get("ignored_patterns", [])),
    )
