# Como funciona

```
RSS + Hacker News  ──▶  peneira  ──▶  Gemini escolhe e resume  ──▶  #noticias-ia
    ~95 itens          ~55 itens           4 a 6 itens
```

## Busca

Dezoito feeds, agrupados pelas três frentes do boletim:

| Frente | Fontes |
|---|---|
| Programação | GitHub Blog, Stack Overflow, Pragmatic Engineer, InfoQ, Cloudflare, Simon Willison |
| Produto | Lenny's Newsletter, TechCrunch Startups, Brazil Journal, Tecnoblog, Ars Technica |
| IA | TechCrunch AI, The Verge AI, VentureBeat AI, MIT Tech Review, OpenAI, Hugging Face, Import AI |

Mais o Hacker News: histórias acima de 80 pontos nos termos de IA, linguagem, ferramenta de dev, banco, rodada e `Show HN`. Tudo em paralelo; feed fora do ar é ignorado sem derrubar a execução.

## Peneira

Antes de a IA entrar, um filtro determinístico corta cupom, guia de compra e review de gadget, limita quantos itens cada fonte pode emplacar e derruba duplicata (a mesma notícia em duas fontes é reconhecida pela URL normalizada — sem `www`, sem `utm_`, sem barra final). Cada link publicado fica gravado por 14 dias em `history.json`, então notícia que já saiu não volta.

## Curadoria

O Gemini recebe a lista limpa e escolhe as 4 a 6 que valem a atenção, priorizando o que muda o que dá para construir — código, produto ou modelo. Um dia bom tem mais de uma frente representada, mas nada é forçado: se só houve coisa boa em uma, o boletim é sobre ela. Se o dia estiver fraco, ele posta menos — encher linguiça é proibido no prompt. Se inventar um link que não estava na lista, o boletim é descartado e ele tenta de novo (até 3 vezes).

## Entrega

Um webhook posta no canal, quebrando a mensagem se ela passar do limite de 2000 caracteres do Discord. Não há processo ligado 24/7: o script é acordado uma vez por dia, faz o trabalho e morre.

## Despertador

Quem marca as 7h é um Worker da Cloudflare, não o `cron` do GitHub. O `schedule` do Actions não é garantido — em repositório novo ele pode atrasar horas ou ser descartado sem deixar rastro, e foi exatamente o que aconteceu aqui: dois agendamentos seguidos sumiram sem gerar execução nenhuma. O Worker acorda no horário e chama o `workflow_dispatch` pela API, que é o caminho confiável. O workflow não tem mais `schedule` algum: manter um cron que dispara em hora incerta publicaria o boletim fora de hora, o que é pior do que não publicar. Se o dispatch falhar, quem avisa no canal é o próprio Worker.

## Detalhes que importam

- **Não publica duas vezes no mesmo dia.** A data do último boletim fica no `history.json`, e uma segunda execução automática no mesmo dia sai sem publicar. O `concurrency` do workflow garante que duas execuções não disputem o push, e o push do histórico tenta de novo se alguém commitar no `main` durante a escrita do boletim.
- **Publicar na mão não cancela o boletim do dia.** Um *Run workflow* com *forçar* marcado guarda os links que publicou, mas não carimba o dia como entregue: o boletim das 7h sai na mesma, já sabendo o que a execução manual cobriu, sem repetir notícia.
- **Dia fraco não vira boletim ruim.** Com menos de 3 itens depois da peneira, o script sai sem publicar e sem gastar API.
- **Link inventado invalida o boletim.** Toda URL da resposta é conferida contra a lista enviada ao modelo. Não bateu, descarta e tenta de novo.
- **Segredo não vaza no log.** O repositório é público e o `requests` põe a URL inteira na mensagem de erro — token do webhook incluído. Toda saída de erro passa por um filtro antes de chegar no log do Actions.
- **Falha avisa.** Se o job quebrar, o próprio bot posta no canal com o link do log. E se o dispatch nem chegar a sair, quem avisa é o Worker — senão não haveria job nenhum para reclamar.

## Organização do código

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
worker/
  src/index.js     o despertador: chama o workflow_dispatch no horário
  wrangler.jsonc   horário, repositório e nome do Worker
pyproject.toml     dependências e empacotamento
```
