# Solução de problemas

| Sintoma | O que olhar |
|---|---|
| Nada aparece no Discord | O log do Actions. Se disser "O boletim de hoje já saiu", rode com *forçar* marcado |
| "Material insuficiente hoje" | A peneira deixou menos de 3 itens: janela curta, feeds fora do ar, ou tudo já publicado |
| "Não saiu boletim em 3 tentativas" | Cota do Gemini estourada, chave inválida, ou o modelo insistindo em inventar link |
| O `history.json` não atualiza | Permissão de escrita do workflow (veja a nota em [Instalação](instalacao.md#5-teste)) |
| Uma fonte aparece como `! Nome: HTTPError` | Feed fora do ar. É ignorado de propósito; se for permanente, tire de [`config/sources.toml`](../config/sources.toml) |
| Deu a hora e não apareceu nenhuma execução | O Worker não disparou. `cd worker && npx wrangler tail` mostra o log do horário; se o token expirou, o GitHub responde 401 ali |
