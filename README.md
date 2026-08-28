<p align="center">
  <img src="assets/banner.svg" alt="Expresso — curadoria de A.I para notícias de tech, direto no Discord" width="100%">
</p>

<p align="center">
  <a href="https://github.com/renanloureiroo/expresso-bot/actions/workflows/expresso.yml"><img src="https://github.com/renanloureiroo/expresso-bot/actions/workflows/expresso.yml/badge.svg" alt="status do boletim"></a>
  <img src="https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white" alt="Python 3.12">
  <img src="https://img.shields.io/badge/custo-US%24%200-2ea043" alt="Custo zero">
  <a href="LICENSE"><img src="https://img.shields.io/badge/licen%C3%A7a-MIT-blue" alt="Licença MIT"></a>
</p>

**Expresso é um bot de Discord que busca e faz a curadoria — com IA — das notícias de tecnologia do dia: programação, produto e IA.**

Todo dia útil às 7h da manhã ele varre dezenas de fontes, joga fora o que não interessa e posta no canal as 4 a 6 notícias que sobraram, cada uma com uma frase dizendo **por que aquilo importa para quem está construindo**.

Roda no GitHub Actions, sem servidor e sem cartão de crédito: um pacote Python, dois segredos, e um Worker da Cloudflare de vinte linhas que faz o papel de despertador.

## O que ele posta

> **☕ Expresso — quinta, 27/08**
>
> **Preço de modelo caiu mais em duas semanas do que em qualquer período desde o lançamento dos frontier models**
> Boa hora pra refazer a conta de custo por usuário. Margem que não fechava mês passado pode fechar agora. [ver]
>
> **Pinecone lança o Nexus, camada de "conhecimento pronto pra agente"**
> Mais um pedaço do stack de RAG virando commodity. Se o diferencial for infra de busca, vale repensar; se for o workflow em cima, ficou mais barato de construir. [ver]
>
> **💡 Pra pensar:** com ~70% do capital de risco indo pra IA, o que vocês têm que uma rodada não compra — dado próprio, canal, ou um nicho que ninguém grande quer atender?

## Como funciona

```
RSS + Hacker News  ──▶  peneira  ──▶  Gemini escolhe e resume  ──▶  #noticias-ia
    ~95 itens          ~55 itens           4 a 6 itens
```

Dezoito feeds mais o Hacker News são coletados em paralelo; um filtro determinístico corta ruído, duplicata e o que já saiu nos últimos 14 dias; o Gemini escolhe as 4 a 6 que valem a atenção e escreve o porquê; um webhook posta no canal. Quem marca as 7h é um Worker da Cloudflare, porque o `cron` do GitHub Actions não é confiável.

O passo a passo completo — fontes, critério de curadoria, despertador e as decisões por trás deles — está em [Como funciona](docs/como-funciona.md).

## Documentação

| | |
|---|---|
| [Instalação](docs/instalacao.md) | do repositório vazio ao boletim no ar, incluindo o Worker e o rodar local |
| [Configuração](docs/configuracao.md) | horário, fontes, prompt e todas as variáveis de ambiente |
| [Como funciona](docs/como-funciona.md) | o pipeline em detalhe, o despertador e a organização do código |
| [Solução de problemas](docs/problemas.md) | sintoma → onde olhar |

<p align="center"><sub>feito n'A Garagem · <a href="LICENSE">MIT</a></sub></p>
