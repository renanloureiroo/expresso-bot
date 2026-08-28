"""Gemini picks the items and writes the bulletin — invented links rejected."""

from __future__ import annotations

import sys
import time
from datetime import datetime

from expresso.config import Config
from expresso.models import Item
from expresso.text import links_in, normalize_url

# The bulletin is written in Brazilian Portuguese, so are the weekday names.
WEEKDAYS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
WAIT_BETWEEN_ATTEMPTS = 60


def _load_prompt(cfg: Config) -> str:
    try:
        return cfg.prompt_file.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise RuntimeError(
            f"Arquivo de prompt não encontrado: {cfg.prompt_file}. "
            "Aponte outro com PROMPT_FILE."
        ) from None


def _build_prompt(items: list[Item], cfg: Config) -> str:
    now = datetime.now(cfg.timezone)
    return _load_prompt(cfg).format(
        window=cfg.window_hours,
        date=f"{WEEKDAYS[now.weekday()]}, {now:%d/%m}",
        items="\n".join(item.as_line() for item in items),
    )


def _generate(prompt: str, cfg: Config):
    from google import genai
    from google.genai import types

    # HttpOptions.timeout is in milliseconds. Without it a stalled request
    # hangs forever and the whole run dies on the workflow timeout instead of
    # spending its retries.
    client = genai.Client(
        api_key=cfg.gemini_key,
        http_options=types.HttpOptions(timeout=cfg.gemini_timeout * 1000),
    )
    return client.models.generate_content(
        model=cfg.model,
        contents=prompt,
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level=cfg.thinking),
            max_output_tokens=cfg.max_tokens,
            temperature=cfg.temperature,
        ),
    )


def _finish_reason(response) -> str:
    try:
        return str(response.candidates[0].finish_reason)
    except (AttributeError, IndexError):
        return "desconhecido"


def write_bulletin(items: list[Item], cfg: Config) -> str:
    """Return the bulletin text, or raise after exhausting the retries."""
    candidates = items[: cfg.max_items_in_prompt]
    prompt = _build_prompt(candidates, cfg)
    allowed = {normalize_url(item.url) for item in candidates}

    last_error = ""
    for attempt in range(1, cfg.attempts + 1):
        try:
            response = _generate(prompt, cfg)
        except Exception as error:
            last_error = f"{type(error).__name__}: {error}"
            print(f"  tentativa {attempt}: {last_error}", file=sys.stderr)
            time.sleep(WAIT_BETWEEN_ATTEMPTS * attempt)
            continue

        text = (response.text or "").strip()
        if not text:
            last_error = f"resposta vazia (finish_reason: {_finish_reason(response)})"
            print(f"  tentativa {attempt}: {last_error}", file=sys.stderr)
            continue

        invented = {url for url in links_in(text) if normalize_url(url) not in allowed}
        if invented:
            last_error = f"link fora da lista: {', '.join(sorted(invented))}"
            print(f"  tentativa {attempt}: {last_error}", file=sys.stderr)
            continue

        return text

    raise RuntimeError(
        f"Não saiu boletim em {cfg.attempts} tentativas. Último: {last_error}"
    )
