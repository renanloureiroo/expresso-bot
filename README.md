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

Roda no GitHub Actions, sem servidor e sem cartão de crédito: um pacote Python, dois segredos, um `cron`.

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

**Busca.** Dezoito feeds, agrupados pelas três frentes do boletim:

| Frente | Fontes |
|---|---|
| Programação | GitHub Blog, Stack Overflow, Pragmatic Engineer, InfoQ, Cloudflare, Simon Willison |
| Produto | Lenny's Newsletter, TechCrunch Startups, Brazil Journal, Tecnoblog, Ars Technica |
| IA | TechCrunch AI, The Verge AI, VentureBeat AI, MIT Tech Review, OpenAI, Hugging Face, Import AI |

Mais o Hacker News: histórias acima de 80 pontos nos termos de IA, linguagem, ferramenta de dev, banco, rodada e `Show HN`. Tudo em paralelo; feed fora do ar é ignorado sem derrubar a execução.

**Peneira.** Antes de a IA entrar, um filtro determinístico corta cupom, guia de compra e review de gadget, limita quantos itens cada fonte pode emplacar e derruba duplicata (a mesma notícia em duas fontes é reconhecida pela URL normalizada — sem `www`, sem `utm_`, sem barra final). Cada link publicado fica gravado por 14 dias em `history.json`, então notícia que já saiu não volta.

**Curadoria.** O Gemini recebe a lista limpa e escolhe as 4 a 6 que valem a atenção, priorizando o que muda o que dá para construir — código, produto ou modelo. Um dia bom tem mais de uma frente representada, mas nada é forçado: se só houve coisa boa em uma, o boletim é sobre ela. Se o dia estiver fraco, ele posta menos — encher linguiça é proibido no prompt. Se inventar um link que não estava na lista, o boletim é descartado e ele tenta de novo (até 3 vezes).

**Entrega.** Um webhook posta no canal, quebrando a mensagem se ela passar do limite de 2000 caracteres do Discord. Não há processo ligado 24/7: o GitHub Actions acorda o script uma vez por dia, ele faz o trabalho e morre.

## Começando

Você precisa de uma conta no GitHub, um servidor no Discord onde tenha permissão de criar webhook, e cerca de cinco minutos.

**1. Crie o repositório**

```bash
git init && git add . && git commit -m "Expresso"
gh repo create expresso --public --source=. --push
```

**2. Pegue a chave do Gemini** em [aistudio.google.com/apikey](https://aistudio.google.com/apikey) → *Create API key*. Login com Google, sem cartão.

**3. Crie o webhook do Discord** em *Configurações do canal → Integrações → Webhooks → Novo webhook* e copie a URL.

**4. Cadastre os dois segredos** no repositório, em *Settings → Secrets and variables → Actions*:

| Nome | Valor |
|---|---|
| `DISCORD_WEBHOOK_URL` | o webhook do passo 3 |
| `GEMINI_API_KEY` | a chave do passo 2 |

**5. Teste.** Aba *Actions* → *Expresso* → *Run workflow*. Em cerca de um minuto o boletim aparece no Discord. A partir daí ele roda sozinho.

> [!NOTE]
> O workflow precisa de permissão de escrita para commitar o `history.json` de volta. Se o push falhar, confira *Settings → Actions → General → Workflow permissions* e marque *Read and write permissions*.

## Configuração

O horário fica no `cron` do [`expresso.yml`](.github/workflows/expresso.yml), sempre em UTC — some 3 horas para converter de Brasília:

```yaml
- cron: "0 10 * * 1-5"   # 10:00 UTC = 07:00 em Brasília, de segunda a sexta
```

> [!TIP]
> O cron do GitHub não aceita variável de ambiente: ele é lido antes de o workflow existir. Por isso o horário mora no próprio arquivo, e não em `env`.

As fontes e o prompt são dados, não código — ficam em arquivos próprios, e mexer neles não encosta na lógica:

| Arquivo | O que tem |
|---|---|
| [`config/sources.toml`](config/sources.toml) | os feeds (agrupados por frente), os termos do Hacker News e os padrões de URL ignorados |
| [`config/prompt.md`](config/prompt.md) | as três frentes, o critério de curadoria e o formato do post |

Um feed novo são quatro linhas:

```toml
[[feeds]]
track = "programacao"   # programacao | produto | ia
name = "Nome da fonte"
url = "https://exemplo.com/feed/"
```

Todo o resto do comportamento vem de variáveis de ambiente, e cada uma tem um padrão — nada precisa ser definido para o boletim sair como sempre. A lista completa, comentada, está no [`.env.example`](.env.example).

| Variável | Padrão | O que faz |
|---|---|---|
| `DISCORD_WEBHOOK_URL` | — | webhook do canal. Obrigatória fora do dry run |
| `GEMINI_API_KEY` | — | chave da API. Obrigatória fora do dry run |
| `DRY_RUN` | `0` | `1` imprime o boletim em vez de publicar |
| `FORCE` | `0` | `1` publica de novo mesmo se o boletim de hoje já saiu |
| `TIMEZONE` | `America/Sao_Paulo` | fuso usado na data do boletim e na trava diária |
| `WINDOW_HOURS` | `26` | quanto tempo para trás a coleta olha |
| `MODEL` | `gemini-3.7-flash` | modelo do Gemini |
| `MODEL_TEMPERATURE` | `0.4` | criatividade da escrita |
| `MODEL_MAX_TOKENS` | `4000` | teto da resposta |
| `MODEL_THINKING` | `low` | esforço de raciocínio do modelo |
| `ATTEMPTS` | `3` | quantas vezes tentar antes de desistir do boletim |
| `TIMEOUT_SECONDS` | `20` | timeout de cada feed e da busca no Hacker News |
| `DISCORD_TIMEOUT` | `30` | timeout do POST no webhook |
| `WORKERS` | `8` | requisições simultâneas na coleta |
| `MAX_ENTRIES_PER_FEED` | `25` | entradas lidas de cada feed antes do corte por data |
| `MAX_PER_SOURCE` | `6` | teto por fonte, pra um feed tagarela não sequestrar o boletim |
| `MAX_ITEMS_IN_PROMPT` | `85` | tamanho da lista crua enviada ao modelo |
| `MIN_ITEMS_TO_PUBLISH` | `3` | abaixo disso o dia é fraco e o boletim não sai |
| `HN_MIN_POINTS` | `80` | corte de pontos no Hacker News |
| `HN_RESULTS_PER_TERM` | `10` | quantas histórias buscar por termo |
| `HISTORY_DAYS` | `14` | por quantos dias um link publicado fica bloqueado |
| `HISTORY_FILE` | `history.json` | onde fica o histórico |
| `SOURCES_FILE` | `config/sources.toml` | catálogo de fontes |
| `PROMPT_FILE` | `config/prompt.md` | prompt da curadoria |
| `DISCORD_LIMIT` | `2000` | limite da API do Discord por mensagem |

> [!IMPORTANT]
> Fique na linha Flash do Gemini. A Pro saiu do free tier em abril de 2026, e trocar o `MODEL` para ela passa a gerar cobrança.

## Rodando na sua máquina

Precisa de Python 3.12.

```bash
pip install -e .
cp .env.example .env          # preencha o que quiser mudar

# só a busca e a peneira, sem usar a API nem publicar:
DRY_RUN=1 python -m expresso

# boletim inteiro no terminal, sem publicar:
DRY_RUN=1 GEMINI_API_KEY=... python -m expresso
```

O `.env` é conveniência local e está no `.gitignore` — no GitHub Actions ele não existe, e os secrets do repositório é que mandam.

O dry run nunca toca no `history.json` nem no webhook, então dá pra rodar quantas vezes quiser.

## Organização

O código é em inglês; o prompt, os textos do boletim e a documentação, em português.

```
src/expresso/
  cli.py           orquestração: coleta ▸ peneira ▸ Gemini ▸ Discord ▸ histórico
  config.py        toda a configuração, lida do ambiente uma vez só
  sources.py       leitura do config/sources.toml
  collect.py       feeds RSS/Atom e Hacker News, em paralelo
  filtering.py     deduplicação, filtros e teto por fonte
  writer.py        prompt, chamada ao Gemini e checagem de link inventado
  publishing.py    quebra da mensagem e POST no webhook
  history.py       o que já foi publicado
  models.py        o Item que circula entre as etapas
  text.py          limpeza de HTML, normalização de URL, ocultação de segredo
config/
  sources.toml     feeds, termos do Hacker News e filtros
  prompt.md        o prompt da curadoria
pyproject.toml     dependências e empacotamento
```

## Detalhes que importam

- **Não publica duas vezes no mesmo dia.** A data do último boletim fica no `history.json`; o cron e um *Run workflow* na mão não se atropelam (e o `concurrency` do workflow garante que não disputem o push).
- **Dia fraco não vira boletim ruim.** Com menos de 3 itens depois da peneira, o script sai sem publicar e sem gastar API.
- **Link inventado invalida o boletim.** Toda URL da resposta é conferida contra a lista enviada ao modelo. Não bateu, descarta e tenta de novo.
- **Segredo não vaza no log.** O repositório é público e o `requests` põe a URL inteira na mensagem de erro — token do webhook incluído. Toda saída de erro passa por um filtro antes de chegar no log do Actions.
- **Falha avisa.** Se o job quebrar, o próprio bot posta no canal com o link do log.

## Solução de problemas

| Sintoma | O que olhar |
|---|---|
| Nada aparece no Discord | O log do Actions. Se disser "O boletim de hoje já saiu", rode com *forçar* marcado |
| "Material insuficiente hoje" | A peneira deixou menos de 3 itens: janela curta, feeds fora do ar, ou tudo já publicado |
| "Não saiu boletim em 3 tentativas" | Cota do Gemini estourada, chave inválida, ou o modelo insistindo em inventar link |
| O `history.json` não atualiza | Permissão de escrita do workflow (veja a nota em *Começando*) |
| Uma fonte aparece como `! Nome: HTTPError` | Feed fora do ar. É ignorado de propósito; se for permanente, tire de `config/sources.toml` |

<p align="center"><sub>feito n'A Garagem · <a href="LICENSE">MIT</a></sub></p>
