// Integração com o Claude (API da Anthropic), chamada direto do navegador com a chave salva no aparelho.
import { state } from './db.js';

const SDK_URL = 'https://cdn.jsdelivr.net/npm/@anthropic-ai/sdk@1.3.0/+esm';
let AnthropicCls;

async function client() {
  const key = (state.settings.apiKey || '').trim();
  if (!key) {
    const err = new Error('Coloque sua chave da API em Ajustes para usar a IA.');
    err.code = 'no_key';
    throw err;
  }
  if (!AnthropicCls) AnthropicCls = (await import(SDK_URL)).default;
  return new AnthropicCls({ apiKey: key, dangerouslyAllowBrowser: true });
}

function sobreMim() {
  const s = (state.settings.sobre || '').trim();
  return s ? `\n\nSobre a criadora (use para ajustar tom, nicho e exemplos):\n${s}` : '';
}

const BASE = `Você é a parceira criativa de uma criadora de conteúdo UGC brasileira que trabalha com marcas (parcerias pagas, permutas e afiliados) no Instagram e no TikTok.
Escreva sempre em português do Brasil, com linguagem natural de redes sociais, direta e sem enrolação.
Responda em Markdown simples: títulos com ##, listas com -, negrito com **. Tabelas só quando pedido.
Nunca invente informações sobre a marca que não estejam no material recebido; quando faltar algo, diga o que falta.`;

function imageBlocks(imagens = []) {
  return imagens.map((dataUrl) => {
    const [meta, data] = dataUrl.split(',');
    const media_type = (meta.match(/data:(.*?);/) || [])[1] || 'image/jpeg';
    return { type: 'image', source: { type: 'base64', media_type, data } };
  });
}

/**
 * Executa um pedido ao Claude mostrando o texto enquanto ele é escrito.
 * onText(textoAcumulado) é chamado a cada pedaço recebido.
 */
export async function run({ system, content, onText, signal }) {
  const c = await client();
  const stream = c.beta.messages.stream(
    {
      model: state.settings.model || 'claude-opus-5-5',
      max_tokens: 16000,
      system: BASE + sobreMim() + (system ? `\n\n${system}` : ''),
      messages: [{ role: 'user', content }],
      output_config: { effort: state.settings.effort || 'medium' },
      // Se o modelo principal recusar, a própria API tenta de novo com outro modelo.
      betas: ['server-side-fallback-2026-07-01'],
      fallbacks: 'default',
    },
    { signal }
  );
  let acc = '';
  stream.on('text', (t) => {
    acc += t;
    onText && onText(acc);
  });
  const msg = await stream.finalMessage();
  if (msg.stop_reason === 'refusal') {
    throw new Error('A IA não quis responder esse pedido. Tente reformular o texto.');
  }
  const text = msg.content.filter((b) => b.type === 'text').map((b) => b.text).join('');
  if (msg.stop_reason === 'max_tokens') return text + '\n\n_(A resposta ficou longa demais e foi cortada.)_';
  return text;
}

export function friendlyError(e) {
  if (e?.code === 'no_key') return e.message;
  const status = e?.status;
  if (status === 401) return 'A chave da API não foi aceita. Confira em Ajustes.';
  if (status === 429) return 'Muitos pedidos seguidos. Espere um pouco e tente de novo.';
  if (status === 400) return 'A API recusou o pedido: ' + (e?.error?.error?.message || e.message);
  if (status >= 500) return 'O serviço da IA está instável agora. Tente de novo em instantes.';
  if (e?.name === 'AbortError' || /abort/i.test(e?.message || '')) return 'Cancelado.';
  if (!navigator.onLine) return 'Sem internet. A IA precisa de conexão.';
  return e?.message || 'Algo deu errado ao falar com a IA.';
}

// ---------- Pedidos prontos ----------

export function analisarBriefing({ marca, texto, imagens }, opts) {
  const content = [
    ...imageBlocks(imagens),
    {
      type: 'text',
      text: `Marca: ${marca || 'não informada'}

Briefing (texto colado e/ou imagens acima):
${texto || '(só imagens)'}

Analise esse briefing para eu gravar sem erro. Use exatamente estas seções:
## Resumo em 3 linhas
## O que a marca quer comunicar
## Entregáveis
(formato, quantidade, duração, onde postar)
## Prazos e datas
## Obrigatório
(falas, menções, @, hashtags, cupom, link, mostrar produto de tal jeito)
## Proibido ou cuidado
## Público e tom
## Dúvidas para perguntar à marca antes de gravar
## Checklist de gravação
(lista de itens para marcar)`,
    },
  ];
  return run({ content, ...opts });
}

export function gerarRoteiro({ marca, briefing, ideia, formato, duracao, extra, anteriores = [], ajuste, base }, opts) {
  let pedido;
  if (ajuste && base) {
    pedido = `Aqui está o roteiro atual:
"""
${base}
"""

Ajuste o roteiro seguindo este pedido: ${ajuste}
Mantenha tudo o que não foi pedido para mudar e devolva o roteiro completo, com as mesmas seções.`;
  } else {
    pedido = `Crie um roteiro criativo para eu gravar.
Formato: ${formato || 'Reels/TikTok vertical'}
Duração alvo: ${duracao || '30 a 45 segundos'}
${marca ? `Marca: ${marca}` : 'Conteúdo orgânico (sem marca)'}
${ideia ? `Ideia de partida: ${ideia}` : ''}
${extra ? `Observações: ${extra}` : ''}
${briefing ? `\nBriefing / análise do briefing:\n"""\n${briefing}\n"""` : ''}
${anteriores.length ? `\nJá gerei estes roteiros antes e NÃO gostei. Faça uma abordagem criativa claramente diferente (outro ângulo, outra estrutura, outros ganchos):\n${anteriores.map((a, i) => `--- versão ${i + 1} (trecho) ---\n${a.slice(0, 700)}`).join('\n')}` : ''}

Use exatamente estas seções:
## Ganchos
5 opções de gancho para os primeiros 3 segundos. Para cada um: a fala, o texto na tela e o tipo (curiosidade, dor, polêmica leve, resultado, identificação...).
## Roteiro
Cenas numeradas. Para cada cena: tempo aproximado, o que aparece (plano/ação), a fala exata e o texto na tela.
## Takes para gravar
Lista do que filmar, incluindo cenas de apoio (b-roll).
## Chamada para ação
## Legenda do post
Com 3 a 5 hashtags.
${briefing ? '## Conferência do briefing\nLista curta confirmando que cada item obrigatório do briefing aparece no roteiro.' : ''}`;
  }
  return run({ content: [{ type: 'text', text: pedido }], ...opts });
}

export function criarAbordagem({ marca, notas, imagens, anteriores = [], ajuste, base }, opts) {
  let text;
  if (ajuste && base) {
    text = `Esta é a abordagem atual:
"""
${base}
"""
Ajuste seguindo este pedido: ${ajuste}
Devolva o texto completo, com as mesmas seções.`;
  } else {
    text = `As imagens acima são prints do que uma marca está buscando (vaga, campanha, chamada de criadoras ou post).
${marca ? `Marca: ${marca}` : ''}
${notas ? `Minhas observações: ${notas}` : ''}
${anteriores.length ? `\nJá tenho estas versões e quero outra abordagem, diferente:\n${anteriores.map((a, i) => `--- versão ${i + 1} (trecho) ---\n${a.slice(0, 500)}`).join('\n')}` : ''}

Crie uma abordagem para eu me oferecer para essa parceria. Use exatamente estas seções:
## O que a marca está buscando
## Por que eu combino
(pontos a destacar; se faltar informação sobre mim, diga o que eu deveria acrescentar)
## Mensagem curta (direct)
## E-mail
Com linha de assunto.
## Ideias de conteúdo para oferecer
3 ideias rápidas de vídeo para essa marca.
## Próximo passo
O que anexar (mídia kit, portfólio) e quando cobrar resposta.`;
  }
  return run({ content: [...(ajuste ? [] : imageBlocks(imagens)), { type: 'text', text }], ...opts });
}

export function pedidoEdicao({ video, roteiro, marca }, opts) {
  const ck = video.checklist || {};
  const text = `Preciso editar um vídeo no Descript pedindo as mudanças em texto (para o editor de IA do Descript, o "Underlord").
Vídeo: ${video.titulo || ''}
${marca ? `Marca: ${marca}` : ''}
Duração alvo: ${video.duracaoAlvo || '30 a 45 s'}
Velocidade: ${video.velocidade || '1.0x'}
Preferências marcadas: ${Object.entries(ck).filter(([, v]) => v).map(([k]) => k).join(', ') || 'nenhuma'}
Observações: ${video.notas || '-'}
${roteiro ? `\nRoteiro usado na gravação:\n"""\n${roteiro.slice(0, 4000)}\n"""` : ''}

Escreva:
## Pedido para colar no Descript
Um texto único, claro, em passos numerados, com: cortes (tirar vícios de fala, repetições e silêncios, manter o gancho no início), áudio (Studio Sound leve, em torno de 40%, para não ficar metálico; trilha de fundo baixa, perto de -25 dB, com fade de entrada e saída), legendas (brancas com sombra, posição baixa, por volta de 76% da altura, destaque só nas palavras-chave), texto na tela (gancho nos 2 primeiros segundos, se fizer sentido), velocidade, zooms suaves nos momentos fortes, correção de cor leve e exportação vertical 1080x1920. Ajuste ao que foi marcado acima.
## O que conferir depois
## Legendas para o post
3 opções.
## Hashtags
5 hashtags.`;
  return run({ content: [{ type: 'text', text }], ...opts });
}
