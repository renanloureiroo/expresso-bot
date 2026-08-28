# Configuração

## Horário

O horário do boletim fica no `crons` do [`worker/wrangler.jsonc`](../worker/wrangler.jsonc), sempre em UTC — some 3 horas para converter de Brasília:

```jsonc
"triggers": {
  "crons": ["0 10 * * 1-5"]   // 10:00 UTC = 07:00 em Brasília, de segunda a sexta
}
```

Mudou o horário aqui? Rode `npx wrangler deploy` de novo — é só isso, o `expresso.yml` não tem horário nenhum.

> [!TIP]
> O `cron` não aceita variável de ambiente: ele é lido antes de o código existir. Por isso o horário mora no próprio `wrangler.jsonc`, e não em `env`.

## Fontes e prompt

As fontes e o prompt são dados, não código — ficam em arquivos próprios, e mexer neles não encosta na lógica:

| Arquivo | O que tem |
|---|---|
| [`config/sources.toml`](../config/sources.toml) | os feeds (agrupados por frente), os termos do Hacker News e os padrões de URL ignorados |
| [`config/prompt.md`](../config/prompt.md) | as três frentes, o critério de curadoria e o formato do post |

Um feed novo são quatro linhas:

```toml
[[feeds]]
track = "programacao"   # programacao | produto | ia
name = "Nome da fonte"
url = "https://exemplo.com/feed/"
```

## Variáveis de ambiente

Todo o resto do comportamento vem de variáveis de ambiente, e cada uma tem um padrão — nada precisa ser definido para o boletim sair como sempre. A lista completa, comentada, está no [`.env.example`](../.env.example).

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
