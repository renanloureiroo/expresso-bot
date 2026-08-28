#!/usr/bin/env python3
"""
Radar de IA — boletim diário de IA e tecnologia no Discord.

Roda no GitHub Actions (dias úteis, 07:00 BRT). O fluxo é:

    fontes RSS + Hacker News  ->  Gemini escolhe e resume  ->  webhook do Discord

Variáveis de ambiente necessárias:
    DISCORD_WEBHOOK_URL   webhook do canal #noticias-ia
    GEMINI_API_KEY        chave do Google AI Studio (aistudio.google.com/apikey)

Opcionais:
    JANELA_HORAS          quantas horas para trás buscar (padrão: 26)
    MODELO                modelo do Gemini (padrão: gemini-3.7-flash)
    DRY_RUN               "1" imprime o boletim em vez de publicar
"""

from __future__ import annotations

import os
import sys
import time
import html
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import feedparser
import requests

# --------------------------------------------------------------------------
# Configuração
# --------------------------------------------------------------------------

FUSO = ZoneInfo("America/Sao_Paulo")
JANELA_HORAS = int(os.environ.get("JANELA_HORAS", "26"))
LIMITE_DISCORD = 2000

# O free tier do Google AI Studio cobre a linha Flash (1.500 requisições por dia).
# Como usamos uma por dia útil, sobra folga de sobra. Se este nome de modelo for
# aposentado, troque por "gemini-3.5-flash" ou pelo Flash da vez — a lista está em
# https://ai.google.dev/gemini-api/docs/models
MODELO = os.environ.get("MODELO", "gemini-3.7-flash")

# Adicionar ou remover fontes aqui. Feed que sai do ar é ignorado sem quebrar
# a execução — dá para deixar a lista generosa.
FEEDS: list[tuple[str, str]] = [
    ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("The Verge AI", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/technology-lab"),
    ("VentureBeat AI", "https://venturebeat.com/category/ai/feed/"),
    ("MIT Tech Review", "https://www.technologyreview.com/topic/artificial-intelligence/feed"),
    ("OpenAI", "https://openai.com/news/rss.xml"),
    ("Hugging Face", "https://huggingface.co/blog/feed.xml"),
    ("Simon Willison", "https://simonwillison.net/atom/everything/"),
    ("Import AI", "https://importai.substack.com/feed"),
    ("Tecnoblog", "https://tecnoblog.net/feed/"),
    ("Brazil Journal", "https://braziljournal.com/feed/"),
]

# Histórias do Hacker News: só o que passou desta pontuação entra.
HN_PONTOS_MINIMOS = 80
HN_TERMOS = ["AI", "LLM", "OpenAI", "Anthropic", "startup funding"]

# Lixo recorrente: cupom, review de tablet, guia de compra. Some antes de
# chegar no modelo — é ruído que só encarece e dilui a curadoria.
PADROES_IGNORADOS = [
    "/achados/", "/guias/", "/responde/", "/promocao", "/cupom",
    "/deals/", "/review/", "/best-",
]

# Teto por fonte, para um feed tagarela não sequestrar o boletim.
MAX_POR_FONTE = 8

PROMPT = """Você monta o boletim matinal de IA e tecnologia de dois sócios brasileiros \
que estão construindo um produto: um é dev, o outro cuida do negócio. Escreva em \
português do Brasil.

Abaixo está a lista crua do que saiu nas últimas {janela} horas. Escolha de 4 a 6 itens \
que realmente importam para quem está CONSTRUINDO com IA, nesta ordem de prioridade:

1. Lançamento de modelo, API, preço ou ferramenta que muda o que dá para construir
2. Movimento de mercado ou rodada que sinaliza onde tem dinheiro e oportunidade
3. Regulação ou mudança de política que afeta quem opera no Brasil
4. Um item de oportunidade: brecha, nicho ou padrão emergente que dois fundadores \
pequenos conseguiriam atacar

Descarte hype, opinião solta e release sem substância. Se o dia estiver fraco, escolha \
menos itens — nunca encha linguiça. Nunca invente notícia nem link: use apenas o que \
está na lista.

Responda SOMENTE com a mensagem final, no formato exato abaixo, em markdown do Discord, \
com no máximo 1800 caracteres no total:

**☕ Radar de IA — {data}**

**<Manchete curta em português>**
<Uma ou duas frases dizendo o que aconteceu E por que importa para eles.> [ver](<url>)

(um bloco desses por item, separados por linha em branco)

**💡 Pra pensar:** <uma frase: a implicação prática ou a pergunta que os dois deveriam \
se fazer hoje.>

Regras de escrita: frases diretas, voz ativa, sem jargão de release, sem "revolucionário" \
ou "game-changer". Nenhum emoji além dos dois já presentes no template. Todo item leva link.

LISTA CRUA:
{itens}
"""


@dataclass
class Item:
    fonte: str
    titulo: str
    url: str
    resumo: str
    publicado: datetime

    def como_linha(self) -> str:
        resumo = self.resumo[:280].strip()
        base = f"- [{self.fonte}] {self.titulo} — {self.url}"
        return f"{base}\n  {resumo}" if resumo else base


# --------------------------------------------------------------------------
# Coleta
# --------------------------------------------------------------------------


def _limpar(texto: str) -> str:
    """Tira tags e entidades HTML do resumo do feed."""
    import re

    texto = re.sub(r"<[^>]+>", " ", texto or "")
    texto = html.unescape(texto)
    return re.sub(r"\s+", " ", texto).strip()


def _data_da_entrada(entrada) -> datetime | None:
    for campo in ("published_parsed", "updated_parsed"):
        valor = getattr(entrada, campo, None)
        if valor:
            return datetime.fromtimestamp(time.mktime(valor), tz=timezone.utc)
    return None


def coletar_feeds(corte: datetime) -> list[Item]:
    itens: list[Item] = []
    for fonte, url in FEEDS:
        try:
            feed = feedparser.parse(url)
        except Exception as erro:  # feed fora do ar não derruba a execução
            print(f"  ! {fonte}: {erro}", file=sys.stderr)
            continue

        novos = 0
        for entrada in feed.entries[:25]:
            publicado = _data_da_entrada(entrada)
            if not publicado or publicado < corte:
                continue
            link = getattr(entrada, "link", "")
            titulo = _limpar(getattr(entrada, "title", ""))
            if not link or not titulo:
                continue
            itens.append(
                Item(
                    fonte=fonte,
                    titulo=titulo,
                    url=link,
                    resumo=_limpar(getattr(entrada, "summary", "")),
                    publicado=publicado,
                )
            )
            novos += 1
        print(f"  {fonte}: {novos}")
    return itens


def coletar_hacker_news(corte: datetime) -> list[Item]:
    itens: list[Item] = []
    depois = int(corte.timestamp())
    for termo in HN_TERMOS:
        try:
            resposta = requests.get(
                "https://hn.algolia.com/api/v1/search_by_date",
                params={
                    "query": termo,
                    "tags": "story",
                    "numericFilters": f"created_at_i>{depois},points>{HN_PONTOS_MINIMOS}",
                    "hitsPerPage": 10,
                },
                timeout=20,
            )
            resposta.raise_for_status()
            dados = resposta.json()
        except Exception as erro:
            print(f"  ! Hacker News ({termo}): {erro}", file=sys.stderr)
            continue

        for hit in dados.get("hits", []):
            url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit['objectID']}"
            itens.append(
                Item(
                    fonte=f"Hacker News ({hit.get('points', 0)} pts)",
                    titulo=_limpar(hit.get("title", "")),
                    url=url,
                    resumo="",
                    publicado=datetime.fromtimestamp(hit["created_at_i"], tz=timezone.utc),
                )
            )
    print(f"  Hacker News: {len(itens)}")
    return itens


def peneirar(itens: list[Item]) -> list[Item]:
    """Tira duplicatas, corta o ruído conhecido e limita cada fonte."""
    vistos: set[str] = set()
    por_fonte: dict[str, int] = {}
    limpos: list[Item] = []

    for item in sorted(itens, key=lambda i: i.publicado, reverse=True):
        url = item.url.lower()
        if any(padrao in url for padrao in PADROES_IGNORADOS):
            continue

        chave = item.titulo.lower()[:70]
        if chave in vistos:
            continue

        fonte = item.fonte.split(" (")[0]  # "Hacker News (91 pts)" -> "Hacker News"
        if por_fonte.get(fonte, 0) >= MAX_POR_FONTE:
            continue

        vistos.add(chave)
        por_fonte[fonte] = por_fonte.get(fonte, 0) + 1
        limpos.append(item)

    return limpos


# --------------------------------------------------------------------------
# Curadoria
# --------------------------------------------------------------------------


def escrever_boletim(itens: list[Item]) -> str:
    from google import genai
    from google.genai import types

    agora = datetime.now(FUSO)
    dias = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
    data = f"{dias[agora.weekday()]}, {agora:%d/%m}"

    prompt = PROMPT.format(
        janela=JANELA_HORAS,
        data=data,
        itens="\n".join(item.como_linha() for item in itens[:70]),
    )

    cliente = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    resposta = cliente.models.generate_content(
        model=MODELO,
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=1600,
            temperature=0.4,  # baixo: queremos fidelidade à lista, não criatividade
        ),
    )

    texto = (resposta.text or "").strip()
    if not texto:
        raise RuntimeError(f"O modelo devolveu resposta vazia. Retorno bruto: {resposta}")
    return texto


# --------------------------------------------------------------------------
# Publicação
# --------------------------------------------------------------------------


def _sem_segredo(texto: str, *segredos: str) -> str:
    """Troca qualquer segredo que tenha vazado para dentro de uma string por [oculto]."""
    for segredo in segredos:
        if segredo:
            texto = texto.replace(segredo, "[oculto]")
    return texto


def publicar(mensagem: str, webhook: str) -> None:
    """Publica no Discord, quebrando em partes se passar do limite de 2000."""
    partes: list[str] = []
    restante = mensagem
    while len(restante) > LIMITE_DISCORD:
        corte = restante.rfind("\n\n", 0, LIMITE_DISCORD)
        if corte == -1:
            corte = LIMITE_DISCORD
        partes.append(restante[:corte].strip())
        restante = restante[corte:].strip()
    partes.append(restante)

    for parte in partes:
        try:
            resposta = requests.post(
                webhook,
                json={"content": parte},
                headers={"User-Agent": "radar-de-ia/1.0"},
                timeout=30,
            )
            resposta.raise_for_status()
        except requests.RequestException as erro:
            # O repositório é público: a mensagem de erro do requests carrega a URL
            # inteira, token do webhook incluído. Nunca deixe isso chegar ao log.
            raise RuntimeError(
                f"Falha ao publicar no Discord ({type(erro).__name__}): "
                f"{_sem_segredo(str(erro), webhook)}"
            ) from None
        time.sleep(1)  # respeita o rate limit do webhook


# --------------------------------------------------------------------------


def main() -> int:
    webhook = os.environ.get("DISCORD_WEBHOOK_URL", "")
    dry_run = os.environ.get("DRY_RUN") == "1"

    if not webhook and not dry_run:
        print("Falta DISCORD_WEBHOOK_URL.", file=sys.stderr)
        return 1
    if not os.environ.get("GEMINI_API_KEY") and not dry_run:
        print("Falta GEMINI_API_KEY.", file=sys.stderr)
        return 1

    corte = datetime.now(timezone.utc) - timedelta(hours=JANELA_HORAS)
    print(f"Coletando o que saiu desde {corte:%d/%m %H:%M} UTC:")

    itens = peneirar(coletar_feeds(corte) + coletar_hacker_news(corte))
    print(f"\n{len(itens)} itens depois da peneira.")

    if len(itens) < 3:
        print("Material insuficiente hoje — nada publicado.")
        return 0

    if dry_run and not os.environ.get("GEMINI_API_KEY"):
        print("\n--- DRY RUN: itens coletados ---")
        for item in itens[:40]:
            print(item.como_linha())
        return 0

    print(f"Escrevendo o boletim com {MODELO}...")
    boletim = escrever_boletim(itens)

    if dry_run:
        print("\n--- DRY RUN: boletim ---\n")
        print(boletim)
        return 0

    publicar(boletim, webhook)
    print(f"Publicado ({len(boletim)} caracteres).")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as erro:
        # Rede de segurança para repositório público: o log do Actions é visível para
        # qualquer pessoa, então nenhuma exceção sai daqui sem passar pela peneira.
        limpo = _sem_segredo(
            f"{type(erro).__name__}: {erro}",
            os.environ.get("DISCORD_WEBHOOK_URL", ""),
            os.environ.get("GEMINI_API_KEY", ""),
        )
        print(limpo, file=sys.stderr)
        sys.exit(1)
