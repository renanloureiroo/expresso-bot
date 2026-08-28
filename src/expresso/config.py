"""All Expresso configuration, read from the environment exactly once.

Defaults reproduce the historical behavior: with nothing set, the bulletin
comes out the same as always. Only DISCORD_WEBHOOK_URL and GEMINI_API_KEY are
required, and only outside a dry run.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

# Relative paths given in the environment resolve from here — the repository
# root, two levels above src/expresso/.
ROOT = Path(__file__).resolve().parents[2]


def _text(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _integer(name: str, default: int) -> int:
    raw = _text(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as error:
        raise ValueError(f"{name} precisa ser um número inteiro, veio {raw!r}.") from error


def _decimal(name: str, default: float) -> float:
    raw = _text(name)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError as error:
        raise ValueError(f"{name} precisa ser um número, veio {raw!r}.") from error


def _list(name: str, default: str) -> tuple[str, ...]:
    raw = _text(name) or default
    return tuple(part.strip() for part in raw.split(",") if part.strip())


def _enabled(name: str) -> bool:
    return _text(name) == "1"


def _path(name: str, default: str) -> Path:
    path = Path(_text(name) or default).expanduser()
    return path if path.is_absolute() else ROOT / path


@dataclass(frozen=True)
class Config:
    # Secrets
    webhook: str
    gemini_key: str

    # Run mode
    dry_run: bool
    force: bool

    # Time
    timezone: ZoneInfo
    window_hours: int

    # Model
    model: str
    fallback_models: tuple[str, ...]
    temperature: float
    max_tokens: int
    thinking: str
    attempts: int

    # Network
    timeout: int
    gemini_timeout: int
    discord_timeout: int
    workers: int

    # Collection and filtering
    max_entries_per_feed: int
    max_per_source: int
    max_items_in_prompt: int
    min_items_to_publish: int
    hn_min_points: int
    hn_results_per_term: int

    # Files
    history_file: Path
    sources_file: Path
    prompt_file: Path
    history_days: int

    # Discord
    discord_limit: int

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            webhook=_text("DISCORD_WEBHOOK_URL"),
            gemini_key=_text("GEMINI_API_KEY"),
            dry_run=_enabled("DRY_RUN"),
            force=_enabled("FORCE"),
            timezone=ZoneInfo(_text("TIMEZONE") or "America/Sao_Paulo"),
            window_hours=_integer("WINDOW_HOURS", 26),
            # Stay on the Flash line: Pro left the free tier in April 2026.
            model=_text("MODEL") or "gemini-3.7-flash",
            # Reserves for when the main model answers 503 under load. Sorted
            # newest first, so the bulletin degrades one step at a time.
            fallback_models=_list("MODEL_FALLBACK", "gemini-3.6-flash,gemini-3.5-flash"),
            temperature=_decimal("MODEL_TEMPERATURE", 0.4),
            max_tokens=_integer("MODEL_MAX_TOKENS", 4000),
            thinking=_text("MODEL_THINKING") or "low",
            # Two are enough now that each one already sweeps the whole model
            # chain; more would risk the workflow timeout.
            attempts=_integer("ATTEMPTS", 2),
            timeout=_integer("TIMEOUT_SECONDS", 20),
            # Writing the bulletin takes far longer than fetching a feed, but a
            # hung request must not hold the run until the workflow kills it.
            gemini_timeout=_integer("GEMINI_TIMEOUT", 120),
            discord_timeout=_integer("DISCORD_TIMEOUT", 30),
            workers=_integer("WORKERS", 8),
            max_entries_per_feed=_integer("MAX_ENTRIES_PER_FEED", 25),
            # With many sources on the table, a per-source cap keeps one of them
            # from hijacking the day and leaves room for variety in the prompt.
            max_per_source=_integer("MAX_PER_SOURCE", 6),
            max_items_in_prompt=_integer("MAX_ITEMS_IN_PROMPT", 85),
            min_items_to_publish=_integer("MIN_ITEMS_TO_PUBLISH", 3),
            hn_min_points=_integer("HN_MIN_POINTS", 80),
            hn_results_per_term=_integer("HN_RESULTS_PER_TERM", 10),
            history_file=_path("HISTORY_FILE", "history.json"),
            sources_file=_path("SOURCES_FILE", "config/sources.toml"),
            prompt_file=_path("PROMPT_FILE", "config/prompt.md"),
            history_days=_integer("HISTORY_DAYS", 14),
            discord_limit=_integer("DISCORD_LIMIT", 2000),
        )

    def missing(self) -> list[str]:
        """Required variables absent for an actual publish."""
        if self.dry_run:
            return []
        return [
            name
            for name, value in (
                ("DISCORD_WEBHOOK_URL", self.webhook),
                ("GEMINI_API_KEY", self.gemini_key),
            )
            if not value
        ]

    @property
    def models(self) -> tuple[str, ...]:
        """The main model first, then its reserves, without repeats."""
        return tuple(dict.fromkeys((self.model, *self.fallback_models)))

    @property
    def secrets(self) -> tuple[str, ...]:
        """What must never show up in the public Actions log."""
        return (self.webhook, self.gemini_key)
