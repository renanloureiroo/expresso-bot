# Instalação

Você precisa de uma conta no GitHub, um servidor no Discord onde tenha permissão de criar webhook, e cerca de cinco minutos.

## 1. Crie o repositório

```bash
git init && git add . && git commit -m "Expresso"
gh repo create expresso --public --source=. --push
```

## 2. Pegue a chave do Gemini

Em [aistudio.google.com/apikey](https://aistudio.google.com/apikey) → *Create API key*. Login com Google, sem cartão.

## 3. Crie o webhook do Discord

Em *Configurações do canal → Integrações → Webhooks → Novo webhook* e copie a URL.

## 4. Cadastre os dois segredos

No repositório, em *Settings → Secrets and variables → Actions*:

| Nome | Valor |
|---|---|
| `DISCORD_WEBHOOK_URL` | o webhook do passo 3 |
| `GEMINI_API_KEY` | a chave do passo 2 |

## 5. Teste

Aba *Actions* → *Expresso* → *Run workflow*. Em cerca de um minuto o boletim aparece no Discord.

> [!NOTE]
> O workflow precisa de permissão de escrita para commitar o `history.json` de volta. Se o push falhar, confira *Settings → Actions → General → Workflow permissions* e marque *Read and write permissions*.

## 6. Ligue o despertador

Sem ele o boletim só sai na mão — o `cron` do GitHub sozinho não é confiável (veja [Despertador](como-funciona.md#despertador)). É um Worker da Cloudflare, dentro do free tier:

```bash
cd worker
npm install
npx wrangler login                    # abre o navegador, sem cartão

npx wrangler secret put GITHUB_TOKEN  # cole o token do passo abaixo
npx wrangler deploy
```

O token é um *fine-grained* PAT criado em [github.com/settings/personal-access-tokens](https://github.com/settings/personal-access-tokens/new), em *Repository access* escolha **Only select repositories** e marque este repositório — a opção *Public repositories* é somente leitura e não serve. Em *Permissions*, duas são necessárias:

| Permissão | Nível |
|---|---|
| Actions | Read and write |
| Contents | Read and write |

> [!IMPORTANT]
> `Actions` sozinha não basta: o `workflow_dispatch` responde `403 Resource not accessible by personal access token` sem a permissão de `Contents`. Se ainda assim der 403, um PAT *classic* com o escopo `repo` funciona — é o que a documentação da API descreve para este endpoint.

Ajuste o `GITHUB_REPO` no [`worker/wrangler.jsonc`](../worker/wrangler.jsonc) para o seu repositório, e o horário no `crons` do mesmo arquivo. Dois segredos são opcionais: `DISCORD_WEBHOOK_URL`, para o Worker avisar no canal se o dispatch nem sair; e `TRIGGER_TOKEN`, que libera um `POST /disparar?token=...` para acionar o boletim sem esperar o horário.

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
