/**
 * O despertador do Expresso.
 *
 * O `schedule` do GitHub Actions não entrega de forma confiável em repositório
 * novo — dois agendamentos seguidos foram descartados sem deixar rastro. Este
 * Worker assume o horário: às 7h da manhã ele chama a API do GitHub pedindo um
 * `workflow_dispatch`, que é o caminho que sempre funcionou.
 *
 * Ele não sabe nada sobre o boletim. Só acorda o workflow e confere se o pedido
 * foi aceito; toda a lógica continua no Python, do outro lado.
 */

const GITHUB_API = "https://api.github.com";

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(dispatch(env));
  },

  /**
   * Chamar o Worker pela URL dispara o boletim na mão, útil para testar sem
   * esperar o cron. Exige o mesmo segredo do dispatch para não deixar um
   * gatilho aberto na internet.
   */
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname !== "/disparar") {
      return new Response("expresso-despertador", { status: 200 });
    }
    if (request.method !== "POST") {
      return new Response("Use POST.", { status: 405 });
    }
    if (!env.TRIGGER_TOKEN || url.searchParams.get("token") !== env.TRIGGER_TOKEN) {
      return new Response("Token inválido.", { status: 403 });
    }

    const result = await dispatch(env);
    return new Response(result.message, { status: result.ok ? 202 : 502 });
  },
};

async function dispatch(env) {
  const repo = env.GITHUB_REPO;
  const workflow = env.WORKFLOW_FILE || "expresso.yml";
  const ref = env.GITHUB_REF || "main";

  let result;
  try {
    const response = await fetch(
      `${GITHUB_API}/repos/${repo}/actions/workflows/${workflow}/dispatches`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${env.GITHUB_TOKEN}`,
          Accept: "application/vnd.github+json",
          "X-GitHub-Api-Version": "2022-11-28",
          // A API do GitHub recusa requisição sem User-Agent.
          "User-Agent": "expresso-despertador",
          "Content-Type": "application/json",
        },
        // `forcar: false` deixa o workflow se comportar como o agendado de
        // sempre: se o boletim do dia já saiu, ele pula em vez de repetir.
        body: JSON.stringify({ ref, inputs: { forcar: false } }),
      },
    );

    // 204 sem corpo é o sucesso; qualquer outra coisa traz a explicação no corpo.
    result = response.status === 204
      ? { ok: true, message: "Boletim pedido ao GitHub." }
      : { ok: false, message: `GitHub respondeu ${response.status}: ${await response.text()}` };
  } catch (error) {
    result = { ok: false, message: `Não deu pra falar com o GitHub: ${error.message}` };
  }

  console.log(result.message);
  if (!result.ok) {
    await avisarNoDiscord(env, result.message);
  }
  return result;
}

/**
 * O workflow avisa no canal quando ele mesmo quebra, mas se o dispatch nem sair
 * daqui não há workflow para avisar — este é o único lugar que enxerga a falha.
 */
async function avisarNoDiscord(env, motivo) {
  if (!env.DISCORD_WEBHOOK_URL) return;
  try {
    await fetch(env.DISCORD_WEBHOOK_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        content: `⚠️ O Expresso não foi nem chamado hoje: ${motivo}`.slice(0, 2000),
      }),
    });
  } catch (error) {
    console.log(`E o aviso no Discord também falhou: ${error.message}`);
  }
}
