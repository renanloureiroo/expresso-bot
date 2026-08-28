# Radar de IA

Boletim diário de IA e tecnologia no Discord d'A Garagem, dias úteis às 7h da manhã.

```
RSS + Hacker News  ──▶  Gemini escolhe e resume  ──▶  webhook do #noticias-ia
                        (GitHub Actions, cron)
```

Não depende de nenhuma máquina ligada: o cron roda no runner do GitHub. Não é um bot
com processo 24/7 — é um script que acorda, faz o trabalho e morre.

**Custo: zero.** GitHub Actions dá 2.000 minutos por mês em repositório privado e isso
aqui usa uns 20. O free tier do Google AI Studio cobre a linha Flash com 1.500
requisições por dia, sem cartão de crédito — usamos uma por dia útil.

Uma ressalva do free tier: o Google pode usar seus prompts para treinar modelos. Como o
que mandamos são manchetes públicas de RSS, não muda nada aqui — mas vale lembrar antes
de reaproveitar esse esqueleto para algo com dado de cliente dentro.

## O que ele posta

> **☕ Radar de IA — quinta, 27/08**
>
> **Preço de modelo caiu mais em duas semanas do que em qualquer período desde o lançamento dos frontier models**
> Boa hora pra refazer a conta de custo por usuário. Margem que não fechava mês passado pode fechar agora. [ver]
>
> **Pinecone lança o Nexus, camada de "conhecimento pronto pra agente"**
> Mais um pedaço do stack de RAG virando commodity. Se o diferencial for infra de busca, vale repensar; se for o workflow em cima, ficou mais barato de construir. [ver]
>
> **💡 Pra pensar:** com ~70% do capital de risco indo pra IA, o que vocês têm que uma rodada não compra — dado próprio, canal, ou um nicho que ninguém grande quer atender?

A graça não é agregar manchete — é o filtro. De 75 itens brutos numa janela de 26 horas,
a peneira determinística corta para ~47 e o modelo escolhe de 4 a 6, sempre respondendo
"por que isso importa para quem está construindo".

---

## Como subir (uma vez, ~10 minutos)

**1. Crie o repositório.** Pode ser privado — Actions funciona igual.

```bash
cd radar-de-ia
git init && git add . && git commit -m "Radar de IA"
gh repo create radar-de-ia --private --source=. --push
```

Sem o `gh` instalado: crie o repo pelo site e faça `git remote add origin ... && git push -u origin main`.

**2. Pegue uma chave grátis do Gemini** em
[aistudio.google.com/apikey](https://aistudio.google.com/apikey) → *Create API key*.
Login com Google, sem cartão de crédito. Leva um minuto.

**3. Cadastre os dois segredos.** No repositório: *Settings → Secrets and variables →
Actions → New repository secret*.

| Nome | Valor |
|---|---|
| `DISCORD_WEBHOOK_URL` | o webhook do canal `#noticias-ia` (está no arquivo `SEGREDOS.local.txt`, que não vai pro Git) |
| `GEMINI_API_KEY` | a chave do passo 2 |

**4. Teste na hora.** Aba *Actions* → *Radar de IA* → *Run workflow*. Em cerca de um
minuto o boletim aparece no Discord. Se der erro, o log da execução diz exatamente onde.

Pronto. A partir daí ele roda sozinho às 7h, de segunda a sexta.

---

## Mexendo nele

Tudo que você vai querer ajustar está no topo do `radar.py`:

- **`FEEDS`** — as fontes. Adicione ou remova à vontade; feed fora do ar é ignorado
  sem quebrar a execução.
- **`PADROES_IGNORADOS`** — pedaços de URL que viram lixo automático (cupom, guia de
  compra, review de tablet). Cresça essa lista conforme o ruído aparecer.
- **`MAX_POR_FONTE`** — teto por fonte, pra um feed tagarela não sequestrar o boletim.
- **`HN_PONTOS_MINIMOS`** e **`HN_TERMOS`** — o corte do Hacker News.
- **`PROMPT`** — o critério de curadoria e o formato do post. É aqui que se muda o tom,
  o número de itens ou o que conta como "importa pra gente".
- **`MODELO`** — hoje `gemini-3.7-flash`. Se o Google aposentar esse nome, troque pelo
  Flash da vez ([lista dos modelos](https://ai.google.dev/gemini-api/docs/models)); dá
  pra testar sem commit passando `MODELO=... python radar.py`. Fique na linha Flash —
  a Pro saiu do free tier em abril de 2026.

O **horário** fica no `.github/workflows/radar.yml`. O cron do GitHub é em UTC, então
some 3 horas: `0 10 * * 1-5` = 7h de Brasília. No horário de verão do hemisfério norte
o servidor não muda, mas seu relógio pode — se incomodar, ajuste o número.

## Rodando na sua máquina

```bash
pip install -r requirements.txt

# só a coleta, sem gastar API nem publicar nada:
DRY_RUN=1 python radar.py

# boletim completo impresso no terminal, sem publicar:
DRY_RUN=1 GEMINI_API_KEY=... python radar.py
```

## Quando algo quebrar

- **Não postou e o Action ficou verde** — provavelmente caiu no "material insuficiente"
  (menos de 3 itens na janela). Veja o log; talvez os feeds tenham mudado de URL.
- **Erro 400 dizendo que o modelo não existe** — o nome foi aposentado. Troque `MODELO`
  por outro Flash da [lista](https://ai.google.dev/gemini-api/docs/models).
- **Erro 429** — estourou a cota do free tier (1.500/dia). Com uma execução por dia isso
  só acontece se você ficar testando na mão; espera o dia virar.
- **Resposta vazia do modelo** — o script levanta erro com o retorno bruto no log.
  Costuma ser filtro de segurança ou `max_output_tokens` curto demais.
- **Erro 404 no Discord** — o webhook foi deletado. Recrie em *Configurações do canal →
  Integrações → Webhooks* e atualize o secret.
- **Ficou dias sem rodar** — o GitHub desativa o cron de repositórios sem commits há
  60 dias. Ele avisa por e-mail; basta reativar na aba Actions.

## Segredo nenhum entra no repositório

O repositório é público, então o código trata log como coisa que qualquer um lê:

- O webhook e a chave da API só existem como secrets do Actions. O Git ignora
  `SEGREDOS.local.txt`, onde eles ficam na máquina.
- Toda exceção passa por `_sem_segredo()` antes de virar log. Isso não é paranoia: o
  `requests` põe a URL inteira na mensagem de erro, então um webhook expirado imprimiria
  o token em texto puro num log público. Com a peneira, sai `[oculto]`.

## O que dá pra fazer depois

O mesmo esqueleto serve pra qualquer coisa que valha uma mensagem por dia: resumo dos
issues abertos, alerta de menção à marca, digest de podcast. É só trocar a coleta e o
prompt — o resto do arquivo continua igual.
