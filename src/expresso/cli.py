"""Orchestration: collect ▸ sift ▸ Gemini ▸ Discord ▸ history."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone

from expresso import history as history_store
from expresso import sources as source_catalog
from expresso.collect import collect_feeds, collect_hacker_news
from expresso.config import Config
from expresso.filtering import sift
from expresso.publishing import publish
from expresso.text import links_in, normalize_url, redact
from expresso.writer import write_bulletin

MAX_ITEMS_IN_DRY_RUN = 40


def _load_local_env() -> None:
    """Read a .env if present. On GitHub Actions there is none, secrets rule.

    load_dotenv() never overrides variables already set in the environment, so
    the file is a local convenience only — the public run behaves the same.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def main() -> int:
    _load_local_env()
    cfg = Config.from_env()

    if missing := cfg.missing():
        print(f"Falta {', '.join(missing)}.", file=sys.stderr)
        return 1

    catalog = source_catalog.load(cfg.sources_file)
    history = history_store.load(cfg)

    if history.published_today(cfg) and not (cfg.dry_run or cfg.force):
        print("O boletim de hoje já saiu. Use FORCE=1 para publicar de novo.")
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(hours=cfg.window_hours)
    already_published = history.published_urls
    print(
        f"Coletando o que saiu desde {cutoff:%d/%m %H:%M} UTC "
        f"({len(already_published)} já publicados):"
    )

    raw = collect_feeds(catalog.feeds, cutoff, cfg) + collect_hacker_news(
        catalog.hn_terms, cutoff, cfg
    )
    items = sift(raw, already_published, catalog.ignored_patterns, cfg)
    print(f"\n{len(raw)} itens brutos, {len(items)} depois da peneira.")

    if len(items) < cfg.min_items_to_publish:
        print("Material insuficiente hoje — nada publicado.")
        return 0

    if cfg.dry_run and not cfg.gemini_key:
        print("\n--- DRY RUN: itens coletados ---")
        for item in items[:MAX_ITEMS_IN_DRY_RUN]:
            print(item.as_line())
        return 0

    print(f"Escrevendo o boletim com {cfg.model}...")
    bulletin = write_bulletin(items, cfg)

    if cfg.dry_run:
        print("\n--- DRY RUN: boletim ---\n")
        print(bulletin)
        return 0

    publish(bulletin, cfg)
    history_store.save(history, {normalize_url(u) for u in links_in(bulletin)}, cfg)
    print(f"Publicado ({len(bulletin)} caracteres).")
    return 0


def run() -> int:
    """Entry point with the last redaction pass before the public Actions log."""
    try:
        return main()
    except Exception as error:
        print(
            redact(
                f"{type(error).__name__}: {error}",
                os.environ.get("DISCORD_WEBHOOK_URL", ""),
                os.environ.get("GEMINI_API_KEY", ""),
            ),
            file=sys.stderr,
        )
        return 1
