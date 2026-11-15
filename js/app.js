import { state, loadAll, save, add, find, remove, exportJSON, importJSON, uid } from './db.js';
import * as AI from './ai.js';
import {
  esc, md, toast, copy, modal, confirmBox, formModal, bindFields, wireSegs, aiPanel,
  thumbsHTML, wireThumbs, todayISO, toISO, parseISO, fmtDate, relDay, daysFrom, money,
} from './ui.js';

const $view = document.getElementById('view');
const $title = document.getElementById('pageTitle');
const $actions = document.getElementById('topActions');
const $back = document.getElementById('backBtn');

// ---------- Navegação ----------
const NAV = [
  { r: 'agenda', ic: '📅', t: 'Agenda', tab: true },
  { r: 'marcas', ic: '🏷️', t: 'Marcas', tab: true },
  { r: 'roteiros', ic: '🎬', t: 'Roteiros', tab: true },
  { r: 'ideias', ic: '💡', t: 'Ideias', tab: true },
  { r: 'propostas', ic: '🤝', t: 'Propostas' },
  { r: 'videos', ic: '✂️', t: 'Edição de vídeo' },
  { r: 'portfolio', ic: '⭐', t: 'Portfólio' },
  { r: 'ajustes', ic: '⚙️', t: 'Ajustes' },
];
const SECTION_OF = { marca: 'marcas', roteiro: 'roteiros', proposta: 'propostas', video: 'videos', mais: 'mais' };

function renderNav(section) {
  document.getElementById('sidebar').innerHTML =
    `<div class="brandmark"><img src="icons/icon-192.png" alt="">Sol Content Hub</div>` +
    NAV.map((n) => `<a href="#/${n.r}" class="${section === n.r ? 'active' : ''}"><span>${n.ic}</span>${n.t}</a>`).join('');
  const inMore = !NAV.find((n) => n.r === section)?.tab;
  document.getElementById('tabbar').innerHTML =
    NAV.filter((n) => n.tab).map((n) => `<a class="tab ${section === n.r ? 'active' : ''}" href="#/${n.r}"><span class="ic">${n.ic}</span>${n.t}</a>`).join('') +
    `<a class="tab ${inMore ? 'active' : ''}" href="#/mais"><span class="ic">☰</span>Mais</a>`;
}

function setTop(title, { back = false, actions = '' } = {}) {
  $title.textContent = title;
  document.title = title === 'Sol Content Hub' ? title : `${title} · Sol Hub`;
  $back.hidden = !back;
  $actions.innerHTML = actions;
}
$back.onclick = () => (history.length > 1 ? history.back() : go('agenda'));

export function go(path) { location.hash = '#/' + path; }

function route() {
  const [name = 'agenda', id, sub] = location.hash.replace(/^#\/?/, '').split('/');
  const section = SECTION_OF[name] || name;
  renderNav(section);
  document.querySelectorAll('.fab').forEach((f) => f.remove());
  const views = {
    agenda: viewAgenda, marcas: viewMarcas, marca: () => viewMarca(id, sub), roteiros: viewRoteiros, roteiro: () => viewRoteiro(id),
    ideias: viewIdeias, propostas: viewPropostas, proposta: () => viewProposta(id), videos: viewVideos, video: () => viewVideo(id),
    portfolio: viewPortfolio, ajustes: viewAjustes, mais: viewMais,
  };
  (views[name] || viewAgenda)();
  window.scrollTo(0, 0);
}

function fab(label, onClick) {
  document.querySelectorAll('.fab').forEach((f) => f.remove());
  const b = document.createElement('button');
  b.className = 'fab';
  b.setAttribute('aria-label', label);
  b.textContent = '+';
  b.onclick = onClick;
  document.body.appendChild(b);
}

const emptyBox = (icon, text, btn = '') => `<div class="empty"><div class="big">${icon}</div><p>${text}</p>${btn}</div>`;
const marcaNome = (id) => find('marcas', id)?.nome || '';
const marcaOptions = (withNone = true) => [...(withNone ? [['', '— sem marca —']] : []), ...state.marcas.map((m) => [m.id, m.nome])];
const initials = (s) => (s || '?').trim().split(/\s+/).slice(0, 2).map((w) => w[0]).join('').toUpperCase();

// ---------- Agenda: junta tudo que tem data ----------
const TIPOS_EVENTO = [['gravacao', 'Gravação'], ['postagem', 'Postagem'], ['reuniao', 'Reunião'], ['outro', 'Outro']];
const COR = { prazo: 'c-prazo', pag: 'c-pag', ideia: 'c-ideia', gravacao: 'c-grav', postagem: 'c-post', reuniao: 'c-evento', outro: 'c-evento', envio: 'c-envio' };

function allEntries() {
  const out = [];
  for (const e of state.eventos) {
    out.push({ data: e.data, hora: e.hora, tipo: e.tipo || 'outro', titulo: e.titulo, sub: [TIPOS_EVENTO.find((t) => t[0] === e.tipo)?.[1], marcaNome(e.marcaId)].filter(Boolean).join(' · '), feito: e.feito, open: () => editEvento(e) });
  }
  for (const m of state.marcas) {
    if (m.status === 'cancelada') continue;
    for (const en of m.entregas || []) {
      if (en.prazo) out.push({ data: en.prazo, tipo: 'prazo', titulo: `Entrega: ${en.descricao || 'material'}`, sub: m.nome, feito: en.feito, open: () => go(`marca/${m.id}/entregas`) });
    }
    if (m.tipo === 'pago' && m.dataRecebimento) {
      out.push({ data: m.dataRecebimento, tipo: 'pag', titulo: `Receber ${money(m.valor) || 'pagamento'}`, sub: m.nome, feito: m.recebido, open: () => go(`marca/${m.id}`) });
    }
    if (m.envio?.temEnvio && m.envio.previsao) {
      out.push({ data: m.envio.previsao, tipo: 'envio', titulo: 'Chegada do produto', sub: [m.nome, m.envio.rastreio].filter(Boolean).join(' · '), feito: m.envio.recebido, open: () => go(`marca/${m.id}`) });
    }
  }
  for (const i of state.ideias) {
    if (i.data) out.push({ data: i.data, tipo: 'ideia', titulo: i.titulo, sub: `Ideia · ${i.status || 'ideia'}`, feito: i.status === 'postada', open: () => editIdeia(i) });
  }
  return out.sort((a, b) => (a.data + (a.hora || '')).localeCompare(b.data + (b.hora || '')));
}

function entryItem(e, showDate = true) {
  const n = daysFrom(e.data);
  const late = !e.feito && n < 0;
  return `<div class="item" data-entry>
    <span class="dot ${COR[e.tipo]}"></span>
    <div class="body"><div class="title" style="${e.feito ? 'text-decoration:line-through;opacity:.6' : ''}">${esc(e.titulo)}</div>
      <div class="sub">${esc(e.sub || '')}</div></div>
    <div class="end">${showDate ? `<div class="${late ? 'badge b-bad' : 'muted'}">${esc(relDay(e.data))}</div>` : ''}${e.hora ? `<div class="muted">${esc(e.hora)}</div>` : ''}</div>
  </div>`;
}
function wireEntries(container, list) {
  container.querySelectorAll('[data-entry]').forEach((el, i) => (el.onclick = list[i].open));
}

let calMonth = null, calSel = null;
function viewAgenda() {
  setTop('Agenda');
  const entries = allEntries();
  const today = todayISO();
  calSel ||= today;
  const base = calMonth || parseISO(today);
  const y = base.getFullYear(), mo = base.getMonth();
  const first = new Date(y, mo, 1);
  const start = new Date(y, mo, 1 - ((first.getDay() + 6) % 7));
  const byDay = {};
  entries.forEach((e) => (byDay[e.data] ||= []).push(e));

  let cells = '';
  for (let i = 0; i < 42; i++) {
    const d = new Date(start.getFullYear(), start.getMonth(), start.getDate() + i);
    const iso = toISO(d);
    const es = byDay[iso] || [];
    const types = [...new Set(es.filter((e) => !e.feito).map((e) => e.tipo))].slice(0, 4);
    cells += `<button class="day ${d.getMonth() !== mo ? 'out' : ''} ${iso === today ? 'today' : ''} ${iso === calSel ? 'sel' : ''}" data-day="${iso}">
      <span class="n">${d.getDate()}</span><span class="dots">${types.map((t) => `<i class="${COR[t]}"></i>`).join('')}</span></button>`;
    if (i === 34 && new Date(start.getFullYear(), start.getMonth(), start.getDate() + 35).getMonth() !== mo) break;
  }

  const pend = entries.filter((e) => !e.feito);
  const atrasados = pend.filter((e) => e.data < today);
  const proximos = pend.filter((e) => e.data >= today && daysFrom(e.data) <= 14);
  const doDia = entries.filter((e) => e.data === calSel);
  const aReceber = state.marcas.filter((m) => m.tipo === 'pago' && !m.recebido && m.status !== 'cancelada').reduce((s, m) => s + (Number(m.valor) || 0), 0);
  const entregas7 = pend.filter((e) => e.tipo === 'prazo' && daysFrom(e.data) <= 7).length;
  const ativas = state.marcas.filter((m) => !['concluída', 'cancelada'].includes(m.status)).length;

  $view.innerHTML = `
    ${installBanner()}
    <div class="stats">
      <div class="stat"><div class="v">${entregas7}</div><div class="l">entregas em 7 dias</div></div>
      <div class="stat"><div class="v money">${money(aReceber) || 'R$ 0'}</div><div class="l">a receber</div></div>
      <div class="stat"><div class="v">${ativas}</div><div class="l">marcas ativas</div></div>
      <div class="stat"><div class="v">${state.ideias.filter((i) => i.status !== 'postada').length}</div><div class="l">ideias no banco</div></div>
    </div>

    ${atrasados.length ? `<div class="section-title"><h2>⚠️ Atrasados</h2></div><div class="list" id="lAtr">${atrasados.map((e) => entryItem(e)).join('')}</div>` : ''}

    <div class="section-title"><h2>Calendário</h2></div>
    <div class="card">
      <div class="cal-head"><button class="iconbtn" id="prevM" aria-label="Mês anterior">‹</button>
        <h2>${(() => { const t = first.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' }); return t[0].toUpperCase() + t.slice(1); })()}</h2>
        <button class="btn sm" id="hojeBtn">Hoje</button><button class="iconbtn" id="nextM" aria-label="Próximo mês">›</button></div>
      <div class="cal">${['S', 'T', 'Q', 'Q', 'S', 'S', 'D'].map((d) => `<div class="dow">${d}</div>`).join('')}${cells}</div>
      <div class="legend"><span><i class="c-prazo"></i>Entrega</span><span><i class="c-pag"></i>Pagamento</span><span><i class="c-grav"></i>Gravação</span>
        <span><i class="c-post"></i>Postagem</span><span><i class="c-ideia"></i>Ideia</span><span><i class="c-envio"></i>Produto chegando</span><span><i class="c-evento"></i>Outros</span></div>
    </div>

    <div class="section-title"><h2>${calSel === today ? 'Hoje' : fmtDate(calSel, { weekday: 'long', day: '2-digit', month: 'long' })}</h2>
      <button class="btn sm" id="addDia">+ Compromisso</button></div>
    <div class="list" id="lDia">${doDia.length ? doDia.map((e) => entryItem(e, false)).join('') : '<p class="muted small">Nada marcado.</p>'}</div>

    <div class="section-title"><h2>Próximos 14 dias</h2></div>
    <div class="list" id="lProx">${proximos.length ? proximos.map((e) => entryItem(e)).join('') : emptyBox('🌤️', 'Nenhum prazo nas próximas duas semanas.')}</div>`;

  wireInstall();
  if (atrasados.length) wireEntries($view.querySelector('#lAtr'), atrasados);
  wireEntries($view.querySelector('#lDia'), doDia);
  if (proximos.length) wireEntries($view.querySelector('#lProx'), proximos);
  $view.querySelectorAll('[data-day]').forEach((b) => (b.onclick = () => { calSel = b.dataset.day; calMonth = parseISO(calSel); calMonth.setDate(1); viewAgenda(); }));
  $view.querySelector('#prevM').onclick = () => { calMonth = new Date(y, mo - 1, 1); viewAgenda(); };
  $view.querySelector('#nextM').onclick = () => { calMonth = new Date(y, mo + 1, 1); viewAgenda(); };
  $view.querySelector('#hojeBtn').onclick = () => { calMonth = null; calSel = today; viewAgenda(); };
  $view.querySelector('#addDia').onclick = () => editEvento(null, calSel);
  fab('Novo compromisso', () => editEvento(null, calSel));
}

function editEvento(ev, data) {
  formModal({
    title: ev ? 'Editar compromisso' : 'Novo compromisso',
    data: ev || { data: data || todayISO(), tipo: 'gravacao' },
    fields: [
      { k: 'titulo', label: 'O que é', required: true, placeholder: 'Ex.: Gravar vídeo da Simple' },
      { k: 'tipo', label: 'Tipo', type: 'seg', options: TIPOS_EVENTO },
      { k: 'data', label: 'Data', type: 'date', required: true },
      { k: 'hora', label: 'Horário', type: 'time' },
      { k: 'marcaId', label: 'Marca', type: 'select', options: marcaOptions() },
      { k: 'notas', label: 'Anotações', type: 'textarea', rows: 2 },
      ...(ev ? [{ k: 'feito', label: 'Feito', type: 'checkbox' }] : []),
    ],
    onSubmit: (d) => { if (ev) Object.assign(ev, d); else add('eventos', d); save('eventos'); route(); toast('Salvo'); },
    onDelete: ev ? () => { remove('eventos', ev.id); route(); } : null,
  });
}

// ---------- Marcas ----------
const STATUS_MARCA = ['aprovada', 'em produção', 'entregue', 'concluída', 'cancelada'];
const TIPO_LABEL = { pago: 'Pago', permuta: 'Permuta', afiliado: 'Afiliado' };
const TIPO_BADGE = { pago: 'b-ok', permuta: 'b-pink', afiliado: 'b-info' };
const STATUS_BADGE = { aprovada: 'b-info', 'em produção': 'b-warn', entregue: 'b-ok', 'concluída': 'b-muted', cancelada: 'b-bad' };
let marcaFiltro = 'ativas';

function proxPrazo(m) {
  return (m.entregas || []).filter((e) => !e.feito && e.prazo).sort((a, b) => a.prazo.localeCompare(b.prazo))[0];
}

function viewMarcas() {
  setTop('Marcas');
  const filtros = [['ativas', 'Ativas'], ['todas', 'Todas'], ...STATUS_MARCA.map((s) => [s, s[0].toUpperCase() + s.slice(1)])];
  const list = state.marcas.filter((m) => marcaFiltro === 'todas' || (marcaFiltro === 'ativas' ? !['concluída', 'cancelada'].includes(m.status) : m.status === marcaFiltro));
  $view.innerHTML = `
    <div class="chips">${filtros.map(([v, l]) => `<button class="chip ${marcaFiltro === v ? 'on' : ''}" data-f="${v}">${l}</button>`).join('')}</div>
    <div class="list" style="margin-top:12px">
      ${list.length ? list.map((m) => {
        const p = proxPrazo(m);
        return `<a class="item" href="#/marca/${m.id}"><div class="avatar">${esc(initials(m.nome))}</div>
          <div class="body"><div class="title">${esc(m.nome)}</div>
            <div class="sub">${m.origem === 'plataforma' && m.plataforma ? `via ${esc(m.plataforma)} · ` : ''}${p ? `entrega ${esc(relDay(p.prazo))}` : 'sem prazo pendente'}</div></div>
          <div class="end"><span class="badge ${TIPO_BADGE[m.tipo] || ''}">${TIPO_LABEL[m.tipo] || '—'}</span>
            ${m.tipo === 'pago' && m.valor ? `<div class="money" style="margin-top:4px">${money(m.valor)}</div>` : ''}</div></a>`;
      }).join('') : emptyBox('🏷️', marcaFiltro === 'ativas' ? 'Nenhuma marca ativa. Quando for aprovada em uma parceria, cadastre aqui.' : 'Nada por aqui.', '<button class="btn primary" id="nm">+ Nova marca</button>')}
    </div>`;
  $view.querySelectorAll('[data-f]').forEach((b) => (b.onclick = () => { marcaFiltro = b.dataset.f; viewMarcas(); }));
  const nm = $view.querySelector('#nm');
  if (nm) nm.onclick = novaMarca;
  fab('Nova marca', novaMarca);
}

function novaMarca(preset = {}) {
  formModal({
    title: 'Fui aprovada! Nova marca',
    data: { origem: 'marca', tipo: 'pago', ...preset },
    submit: 'Criar pasta da marca',
    fields: [
      { k: 'nome', label: 'Nome da marca', required: true },
      { k: 'origem', label: 'Veio de onde?', type: 'seg', options: [['marca', 'Direto da marca'], ['plataforma', 'Plataforma']] },
      { k: 'plataforma', label: 'Nome da plataforma (se for o caso)', placeholder: 'Ex.: Squid, Inflr, BrandLovers' },
      { k: 'tipo', label: 'Tipo de parceria', type: 'seg', options: [['pago', 'Pago'], ['permuta', 'Permuta'], ['afiliado', 'Afiliado']] },
      { k: 'valor', label: 'Valor (se for pago)', type: 'number', placeholder: '0,00' },
      { k: 'dataRecebimento', label: 'Quando vou receber', type: 'date' },
    ],
    onSubmit: (d) => {
      const m = add('marcas', { status: 'aprovada', entregas: [], emails: [], briefing: { texto: '', imagens: [], versoes: [] }, envio: {}, ...d });
      go(`marca/${m.id}`);
    },
  });
}

function viewMarca(id, tab = 'parceria') {
  const m = find('marcas', id);
  if (!m) return go('marcas');
  m.entregas ||= []; m.emails ||= []; m.envio ||= {}; m.briefing ||= { texto: '', imagens: [], versoes: [] };
  setTop(m.nome, { back: true });
  const tabs = [['parceria', 'Parceria'], ['entregas', `Entregas${m.entregas.filter((e) => !e.feito).length ? ` (${m.entregas.filter((e) => !e.feito).length})` : ''}`], ['briefing', 'Briefing'], ['roteiros', 'Roteiros'], ['emails', `E-mails${m.emails.length ? ` (${m.emails.length})` : ''}`], ['videos', 'Vídeos']];
  $view.innerHTML = `
    <div class="row" style="margin-bottom:12px"><span class="badge ${STATUS_BADGE[m.status] || ''}">${esc(m.status || 'aprovada')}</span>
      <span class="badge ${TIPO_BADGE[m.tipo] || ''}">${TIPO_LABEL[m.tipo] || ''}</span>
      ${m.origem === 'plataforma' ? `<span class="badge b-muted">via ${esc(m.plataforma || 'plataforma')}</span>` : '<span class="badge b-muted">direto da marca</span>'}</div>
    <div class="ptabs">${tabs.map(([k, l]) => `<button class="ptab ${tab === k ? 'on' : ''}" data-tab="${k}">${l}</button>`).join('')}</div>
    <div id="tabBody"></div>`;
  $view.querySelectorAll('[data-tab]').forEach((b) => (b.onclick = () => history.replaceState(null, '', `#/marca/${id}/${b.dataset.tab}`) || viewMarca(id, b.dataset.tab)));
  const body = $view.querySelector('#tabBody');
  ({ parceria: tabParceria, entregas: tabEntregas, briefing: tabBriefing, roteiros: tabRoteirosMarca, emails: tabEmails, videos: tabVideosMarca }[tab] || tabParceria)(m, body);
}

function tabParceria(m, body) {
  const e = m.envio;
  body.innerHTML = `
    <div class="card">
      <div class="grid2">
        <label class="field"><span>Nome da marca</span><input class="input" data-k="nome"></label>
        <label class="field"><span>Status</span><select class="input" data-k="status">${STATUS_MARCA.map((s) => `<option>${s}</option>`).join('')}</select></label>
      </div>
      <div class="field"><span>Veio de onde?</span><div class="seg" data-k="origem"><button data-v="marca">Direto da marca</button><button data-v="plataforma">Plataforma</button></div></div>
      ${m.origem === 'plataforma' ? `<label class="field"><span>Nome da plataforma</span><input class="input" data-k="plataforma" placeholder="Ex.: Squid, Inflr"></label>` : ''}
      <div class="grid2">
        <label class="field"><span>Contato (nome)</span><input class="input" data-k="contato"></label>
        <label class="field"><span>E-mail do contato</span><input class="input" type="email" data-k="emailContato"></label>
      </div>
      <label class="field"><span>Site ou domínio da marca</span><input class="input" data-k="dominio" placeholder="ex.: marca.com.br"></label>
    </div>

    <div class="section-title"><h2>💰 Quanto e quando</h2></div>
    <div class="card">
      <div class="field"><span>Tipo de parceria</span><div class="seg" data-k="tipo"><button data-v="pago">Pago</button><button data-v="permuta">Permuta</button><button data-v="afiliado">Afiliado</button></div></div>
      ${m.tipo === 'pago' ? `
        <div class="grid2">
          <label class="field"><span>Valor que vou ganhar (R$)</span><input class="input" type="number" inputmode="decimal" step="0.01" data-k="valor"></label>
          <label class="field"><span>Quando vou receber</span><input class="input" type="date" data-k="dataRecebimento"></label>
        </div>
        <label class="field"><span>Forma de pagamento</span><input class="input" data-k="formaPagamento" placeholder="Pix, nota fiscal, pela plataforma..."></label>
        <label class="check"><input type="checkbox" data-k="recebido"><span class="lbl">Já recebi</span></label>` : ''}
      ${m.tipo === 'permuta' ? `
        <label class="field"><span>O que vou receber em troca</span><textarea class="input" rows="3" data-k="permutaItens"></textarea></label>
        <label class="field"><span>Valor estimado dos produtos (R$)</span><input class="input" type="number" inputmode="decimal" step="0.01" data-k="permutaValor"></label>` : ''}
      ${m.tipo === 'afiliado' ? `
        <div class="grid2">
          <label class="field"><span>Comissão</span><input class="input" data-k="comissao" placeholder="Ex.: 10% por venda"></label>
          <label class="field"><span>Cupom</span><input class="input" data-k="cupom"></label>
        </div>
        <label class="field"><span>Link de afiliada</span><input class="input" type="url" data-k="linkAfiliado"></label>
        <label class="field"><span>Quando a comissão é paga</span><input class="input" data-k="pagamentoComissao" placeholder="Ex.: todo dia 15"></label>` : ''}
    </div>

    <div class="section-title"><h2>📦 Envio do produto</h2></div>
    <div class="card">
      <label class="check"><input type="checkbox" data-k="envio.temEnvio"><span class="lbl">A marca vai me enviar produto</span></label>
      ${e.temEnvio ? `
        <div class="grid2">
          <label class="field"><span>Código de rastreio</span><input class="input" data-k="envio.rastreio" autocapitalize="characters" placeholder="Ex.: AB123456789BR"></label>
          <label class="field"><span>Transportadora</span><input class="input" data-k="envio.transportadora" placeholder="Correios, Jadlog, Loggi..."></label>
        </div>
        <div class="grid2">
          <label class="field"><span>Previsão de chegada</span><input class="input" type="date" data-k="envio.previsao"></label>
          <label class="field"><span>O que vem no pacote</span><input class="input" data-k="envio.itens"></label>
        </div>
        <label class="check"><input type="checkbox" data-k="envio.recebido"><span class="lbl">Produto já chegou</span></label>
        <div class="row" id="rastreioBtns"></div>` : ''}
    </div>

    <div class="section-title"><h2>📝 Anotações</h2></div>
    <div class="card"><textarea class="input" rows="4" data-k="notas" placeholder="Combinados, links, observações..."></textarea></div>

    <div class="row" style="margin-top:18px">
      <button class="btn" id="toPort">⭐ Adicionar ao portfólio</button><span class="spacer"></span>
      <button class="btn danger" id="delM">Excluir marca</button></div>`;

  const renderRastreio = () => {
    const box = body.querySelector('#rastreioBtns');
    if (!box) return;
    const code = (m.envio.rastreio || '').trim();
    box.innerHTML = code
      ? `<a class="btn sm" target="_blank" rel="noopener" href="https://t.17track.net/pt#nums=${encodeURIComponent(code)}">🔎 Rastrear</a>
         <a class="btn sm" target="_blank" rel="noopener" href="https://rastreamento.correios.com.br/app/index.php">Correios</a>
         <button class="btn sm" id="cpR">Copiar código</button>`
      : '';
    const cp = box.querySelector('#cpR');
    if (cp) cp.onclick = () => copy(code);
  };
  bindFields(body, m, (k) => {
    save('marcas');
    if (['tipo', 'origem', 'envio.temEnvio'].includes(k)) tabParceria(m, body);
    if (k === 'nome') $title.textContent = m.nome;
    if (k === 'envio.rastreio') renderRastreio();
    if (k === 'status') viewMarca(m.id, 'parceria');
  });
  renderRastreio();
  body.querySelector('#toPort').onclick = () => addToPortfolio(m.nome);
  body.querySelector('#delM').onclick = async () => {
    if (await confirmBox(`Excluir ${m.nome} e tudo que está na pasta?`)) { remove('marcas', m.id); go('marcas'); }
  };
}

function tabEntregas(m, body) {
  const list = [...m.entregas].sort((a, b) => (a.feito - b.feito) || (a.prazo || '9').localeCompare(b.prazo || '9'));
  body.innerHTML = `
    <p class="muted small">Cada entrega com prazo aparece na agenda.</p>
    <div class="list">${list.length ? list.map((e) => `
      <div class="item"><input type="checkbox" data-done="${e.id}" ${e.feito ? 'checked' : ''} style="width:22px;height:22px;accent-color:var(--brand)" aria-label="Marcar como entregue">
        <div class="body" data-edit="${e.id}"><div class="title" style="${e.feito ? 'text-decoration:line-through;opacity:.6' : ''}">${esc(e.descricao)}</div>
          <div class="sub">${e.prazo ? `prazo ${fmtDate(e.prazo)} (${relDay(e.prazo)})` : 'sem prazo'}${e.link ? ' · link salvo' : ''}</div></div>
        ${!e.feito && e.prazo && daysFrom(e.prazo) < 0 ? '<span class="badge b-bad">atrasada</span>' : ''}</div>`).join('')
      : emptyBox('🗓️', 'Nenhuma entrega cadastrada. Ex.: "1 Reels de 30s", "3 stories", "6 fotos".')}</div>
    <button class="btn primary" id="addE" style="margin-top:12px">+ Entrega</button>`;
  const edit = (e) => formModal({
    title: e ? 'Editar entrega' : 'Nova entrega',
    data: e || {},
    fields: [
      { k: 'descricao', label: 'O que entregar', required: true, placeholder: 'Ex.: 1 Reels de 30s + 3 stories' },
      { k: 'prazo', label: 'Prazo de entrega do material', type: 'date' },
      { k: 'link', label: 'Link do material entregue', type: 'url' },
      ...(e ? [{ k: 'feito', label: 'Entregue', type: 'checkbox' }] : []),
    ],
    onSubmit: (d) => { if (e) Object.assign(e, d); else m.entregas.push({ id: uid(), feito: false, ...d }); save('marcas'); viewMarca(m.id, 'entregas'); },
    onDelete: e ? () => { m.entregas = m.entregas.filter((x) => x !== e); save('marcas'); viewMarca(m.id, 'entregas'); } : null,
  });
  body.querySelector('#addE').onclick = () => edit(null);
  body.querySelectorAll('[data-edit]').forEach((el) => (el.onclick = () => edit(m.entregas.find((x) => x.id === el.dataset.edit))));
  body.querySelectorAll('[data-done]').forEach((el) => (el.onchange = () => {
    const e = m.entregas.find((x) => x.id === el.dataset.done);
    e.feito = el.checked;
    if (m.entregas.length && m.entregas.every((x) => x.feito) && ['aprovada', 'em produção'].includes(m.status)) { m.status = 'entregue'; toast('Tudo entregue! Status mudou para "entregue"'); }
    save('marcas'); viewMarca(m.id, 'entregas');
  }));
}

function tabBriefing(m, body) {
  const b = m.briefing;
  b.imagens ||= [];
  body.innerHTML = `
    <div class="card">
      <label class="field"><span>Cole o briefing aqui</span><textarea class="input" rows="7" data-k="texto" placeholder="Cole o texto do briefing que a marca ou a plataforma mandou"></textarea></label>
      <div class="field"><span>Ou adicione prints / fotos do briefing</span><div id="bImgs"></div></div>
    </div>
    <div class="section-title"><h2>Análise</h2></div>
    <div id="bAi"></div>
    <div class="row" style="margin-top:14px"><button class="btn" id="toRot">🎬 Criar roteiro com esse briefing</button></div>`;
  bindFields(body, b, () => save('marcas'));
  const renderImgs = () => { body.querySelector('#bImgs').innerHTML = thumbsHTML(b.imagens); wireThumbs(body.querySelector('#bImgs'), b.imagens, () => { save('marcas'); renderImgs(); }); };
  renderImgs();
  aiPanel(body.querySelector('#bAi'), {
    obj: b, title: 'Análise do briefing', emptyLabel: 'Ler e analisar o briefing', onSave: () => save('marcas'),
    canGenerate: () => (b.texto?.trim() || b.imagens.length ? true : 'Cole o briefing ou adicione um print'),
    generate: ({ mode, ajuste, base, onText, signal }) =>
      mode === 'ajuste'
        ? AI.run({ content: [{ type: 'text', text: `Análise atual:\n"""\n${base}\n"""\nAjuste: ${ajuste}\nDevolva a análise completa.` }], onText, signal })
        : AI.analisarBriefing({ marca: m.nome, texto: b.texto, imagens: b.imagens }, { onText, signal }),
  });
  body.querySelector('#toRot').onclick = () => novoRoteiro({ marcaId: m.id, usarBriefing: true });
}

function tabRoteirosMarca(m, body) {
  const list = state.roteiros.filter((r) => r.marcaId === m.id);
  body.innerHTML = `<div class="list">${list.length ? list.map(roteiroItem).join('') : emptyBox('🎬', 'Nenhum roteiro para essa marca ainda.')}</div>
    <button class="btn primary" id="nr" style="margin-top:12px">+ Novo roteiro</button>`;
  body.querySelector('#nr').onclick = () => novoRoteiro({ marcaId: m.id, usarBriefing: !!m.briefing?.versoes?.length });
}

function gmailQuery(m) {
  const parts = [];
  if (m.nome) parts.push(`"${m.nome}"`);
  if (m.dominio) parts.push(`from:${m.dominio.replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0]}`);
  if (m.emailContato) parts.push(`from:${m.emailContato}`, `to:${m.emailContato}`);
  if (m.origem === 'plataforma' && m.plataforma) parts.push(`"${m.plataforma}"`);
  return parts.join(' OR ');
}

function tabEmails(m, body) {
  const q = gmailQuery(m);
  const list = [...m.emails].sort((a, b) => (b.data || '').localeCompare(a.data || ''));
  body.innerHTML = `
    <div class="callout info small">Os e-mails da ${m.origem === 'plataforma' ? `plataforma <b>${esc(m.plataforma || '')}</b> e da marca` : 'marca'} ficam guardados aqui na pasta.
      O botão abaixo abre o Gmail já filtrado por ${esc(m.nome)}${m.origem === 'plataforma' && m.plataforma ? ` e ${esc(m.plataforma)}` : ''}${m.dominio ? ' e pelo domínio' : ''}. Cole aqui o que for importante.</div>
    <div class="row" style="margin:12px 0">
      <a class="btn" target="_blank" rel="noopener" href="https://mail.google.com/mail/u/0/#search/${encodeURIComponent(q)}">📬 Buscar no Gmail</a>
      <button class="btn primary" id="addMail">+ Registrar e-mail</button></div>
    <div class="list">${list.length ? list.map((e) => `<div class="item" data-mail="${e.id}"><div class="avatar">✉️</div>
      <div class="body"><div class="title">${esc(e.assunto || '(sem assunto)')}</div><div class="sub">${esc(e.de || '')}${e.origem ? ` · ${esc(e.origem)}` : ''}</div></div>
      <div class="end muted">${esc(fmtDate(e.data))}</div></div>`).join('') : emptyBox('📭', 'Nenhum e-mail registrado.')}</div>`;
  const edit = (e) => formModal({
    title: e ? 'E-mail' : 'Registrar e-mail',
    data: e || { data: todayISO(), origem: m.origem === 'plataforma' ? 'plataforma' : 'marca' },
    fields: [
      { k: 'assunto', label: 'Assunto', required: true },
      { k: 'de', label: 'De / para', placeholder: 'quem mandou' },
      { k: 'origem', label: 'Veio de', type: 'seg', options: [['marca', 'Marca'], ['plataforma', 'Plataforma'], ['eu', 'Eu enviei']] },
      { k: 'data', label: 'Data', type: 'date' },
      { k: 'texto', label: 'Conteúdo (cole o e-mail)', type: 'textarea', rows: 7 },
    ],
    onSubmit: (d) => { if (e) Object.assign(e, d); else m.emails.push({ id: uid(), ...d }); save('marcas'); viewMarca(m.id, 'emails'); },
    onDelete: e ? () => { m.emails = m.emails.filter((x) => x !== e); save('marcas'); viewMarca(m.id, 'emails'); } : null,
  });
  body.querySelector('#addMail').onclick = () => edit(null);
  body.querySelectorAll('[data-mail]').forEach((el) => (el.onclick = () => edit(m.emails.find((x) => x.id === el.dataset.mail))));
}

function tabVideosMarca(m, body) {
  const list = state.videos.filter((v) => v.marcaId === m.id);
  body.innerHTML = `<div class="list">${list.length ? list.map(videoItem).join('') : emptyBox('✂️', 'Nenhum vídeo dessa marca na edição.')}</div>
    <button class="btn primary" id="nv" style="margin-top:12px">+ Vídeo para editar</button>`;
  body.querySelector('#nv').onclick = () => novoVideo({ marcaId: m.id });
}

// ---------- Ideias ----------
const STATUS_IDEIA = ['ideia', 'agendada', 'gravada', 'postada'];
const FORMATOS = ['Reels', 'TikTok', 'Stories', 'Carrossel', 'Foto', 'YouTube Shorts', 'Live'];
let ideiaFiltro = 'abertas';

function viewIdeias() {
  setTop('Ideias de posts');
  const filtros = [['abertas', 'Em aberto'], ...STATUS_IDEIA.map((s) => [s, s[0].toUpperCase() + s.slice(1)]), ['todas', 'Todas']];
  const list = state.ideias.filter((i) => ideiaFiltro === 'todas' || (ideiaFiltro === 'abertas' ? i.status !== 'postada' : i.status === ideiaFiltro));
  $view.innerHTML = `
    <div class="chips">${filtros.map(([v, l]) => `<button class="chip ${ideiaFiltro === v ? 'on' : ''}" data-f="${v}">${l}</button>`).join('')}</div>
    <div class="list" style="margin-top:12px">${list.length ? list.map((i) => `
      <div class="item" data-i="${i.id}"><span class="dot c-ideia"></span>
        <div class="body"><div class="title">${esc(i.titulo)}</div>
          <div class="sub">${[i.formato, marcaNome(i.marcaId), i.data ? relDay(i.data) : ''].filter(Boolean).map(esc).join(' · ') || esc(i.descricao || '')}</div></div>
        <div class="end"><span class="badge ${i.status === 'postada' ? 'b-ok' : i.status === 'agendada' ? 'b-info' : i.status === 'gravada' ? 'b-warn' : ''}">${esc(i.status || 'ideia')}</span></div></div>`).join('')
      : emptyBox('💡', 'Anote aqui toda ideia de post que aparecer. Depois é só colocar uma data ou virar roteiro.')}</div>`;
  $view.querySelectorAll('[data-f]').forEach((b) => (b.onclick = () => { ideiaFiltro = b.dataset.f; viewIdeias(); }));
  $view.querySelectorAll('[data-i]').forEach((el) => (el.onclick = () => editIdeia(find('ideias', el.dataset.i))));
  fab('Nova ideia', () => editIdeia(null));
}

function editIdeia(i) {
  formModal({
    title: i ? 'Ideia' : 'Nova ideia',
    data: i || { status: 'ideia', formato: 'Reels' },
    fields: [
      { k: 'titulo', label: 'Ideia', required: true, placeholder: 'Ex.: 3 erros que eu cometia no skincare' },
      { k: 'descricao', label: 'Detalhes', type: 'textarea', rows: 3 },
      { k: 'formato', label: 'Formato', type: 'select', options: FORMATOS },
      { k: 'marcaId', label: 'Marca (se for publi)', type: 'select', options: marcaOptions() },
      { k: 'data', label: 'Data para postar/gravar', type: 'date' },
      { k: 'status', label: 'Status', type: 'seg', options: STATUS_IDEIA },
    ],
    onSubmit: (d) => {
      if (d.data && d.status === 'ideia') d.status = 'agendada';
      if (i) Object.assign(i, d); else add('ideias', d);
      save('ideias'); route(); toast('Ideia salva');
    },
    onDelete: i ? () => { remove('ideias', i.id); route(); } : null,
  });
  if (i) {
    const actions = document.querySelector('#modalRoot .actions');
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'btn'; b.textContent = '🎬 Virar roteiro';
    b.onclick = () => { document.querySelector('#modalRoot [data-close]').click(); novoRoteiro({ ideiaId: i.id, ideia: i.titulo + (i.descricao ? ` — ${i.descricao}` : ''), marcaId: i.marcaId || '', formato: i.formato, titulo: i.titulo }); };
    actions.prepend(b);
  }
}

// ---------- Roteiros ----------
const roteiroItem = (r) => `<a class="item" href="#/roteiro/${r.id}"><div class="avatar">🎬</div>
  <div class="body"><div class="title">${esc(r.titulo || 'Roteiro sem título')}</div>
    <div class="sub">${[marcaNome(r.marcaId) || 'orgânico', r.formato, r.versoes?.length ? `${r.versoes.length} versão(ões)` : 'não gerado'].filter(Boolean).map(esc).join(' · ')}</div></div></a>`;

function viewRoteiros() {
  setTop('Roteiros');
  $view.innerHTML = `
    <p class="muted small">Cada roteiro vem com ganchos. Não gostou? Clique em <b>Gerar novo</b> ou escreva o que quer acrescentar ou tirar.</p>
    <div class="list">${state.roteiros.length ? state.roteiros.map(roteiroItem).join('') : emptyBox('🎬', 'Nenhum roteiro ainda.', '<button class="btn primary" id="nr">+ Novo roteiro</button>')}</div>`;
  const nr = $view.querySelector('#nr');
  if (nr) nr.onclick = () => novoRoteiro();
  fab('Novo roteiro', () => novoRoteiro());
}

function novoRoteiro(preset = {}) {
  const m = preset.marcaId ? find('marcas', preset.marcaId) : null;
  const r = add('roteiros', { titulo: preset.titulo || (m ? `Roteiro ${m.nome}` : 'Novo roteiro'), formato: 'Reels', duracao: '30 a 45 segundos', versoes: [], ...preset });
  go(`roteiro/${r.id}`);
}

function viewRoteiro(id) {
  const r = find('roteiros', id);
  if (!r) return go('roteiros');
  setTop(r.titulo || 'Roteiro', { back: true });
  const render = () => {
    const m = find('marcas', r.marcaId);
    const temAnalise = !!m?.briefing?.versoes?.length;
    $view.innerHTML = `
      <div class="card">
        <label class="field"><span>Título</span><input class="input" data-k="titulo"></label>
        <div class="grid2">
          <label class="field"><span>Marca</span><select class="input" data-k="marcaId">${marcaOptions().map(([v, l]) => `<option value="${esc(v)}">${esc(l)}</option>`).join('')}</select></label>
          <label class="field"><span>Formato</span><select class="input" data-k="formato">${FORMATOS.map((f) => `<option>${f}</option>`).join('')}</select></label>
        </div>
        <label class="field"><span>Duração alvo</span><input class="input" data-k="duracao"></label>
        <label class="field"><span>Ideia / tema</span><textarea class="input" rows="2" data-k="ideia" placeholder="Sobre o que é o vídeo"></textarea></label>
        <label class="field"><span>Observações</span><textarea class="input" rows="2" data-k="extra" placeholder="Ex.: gravar no banheiro, mostrar antes e depois, tom engraçado"></textarea></label>
        ${m ? (temAnalise
          ? `<label class="check"><input type="checkbox" data-k="usarBriefing"><span class="lbl">Usar a análise do briefing da ${esc(m.nome)}</span></label>`
          : `<p class="small muted">A ${esc(m.nome)} ainda não tem briefing analisado. <a href="#/marca/${m.id}/briefing">Analisar briefing</a></p>`) : ''}
      </div>
      <div class="section-title"><h2>Roteiro</h2></div>
      <div id="rAi"></div>
      <div class="row" style="margin-top:18px"><button class="btn" id="toVid">✂️ Mandar para edição de vídeo</button><span class="spacer"></span><button class="btn danger" id="delR">Excluir</button></div>`;
    bindFields($view, r, (k) => { save('roteiros'); if (k === 'titulo') $title.textContent = r.titulo; if (k === 'marcaId') render(); });
    aiPanel($view.querySelector('#rAi'), {
      obj: r, title: 'Ganchos + roteiro', emptyLabel: 'Gerar roteiro', onSave: () => save('roteiros'),
      canGenerate: () => (r.ideia?.trim() || m || r.extra?.trim() ? true : 'Escreva a ideia ou escolha uma marca'),
      generate: ({ ajuste, base, anteriores, onText, signal }) => {
        const mm = find('marcas', r.marcaId);
        const bv = mm?.briefing?.versoes;
        const briefing = r.usarBriefing && bv?.length ? bv[mm.briefing.atual ?? bv.length - 1].texto : mm?.briefing?.texto || '';
        return AI.gerarRoteiro({ marca: mm?.nome, briefing, ideia: r.ideia, formato: r.formato, duracao: r.duracao, extra: r.extra, anteriores, ajuste, base }, { onText, signal });
      },
    });
    $view.querySelector('#toVid').onclick = () => novoVideo({ marcaId: r.marcaId, roteiroId: r.id, titulo: r.titulo });
    $view.querySelector('#delR').onclick = async () => { if (await confirmBox('Excluir este roteiro?')) { remove('roteiros', r.id); history.back(); } };
  };
  render();
}

// ---------- Propostas ----------
const STATUS_PROP = [['rascunho', 'Rascunho'], ['enviada', 'Enviada'], ['aprovada', 'Aprovada'], ['recusada', 'Recusada']];
function viewPropostas() {
  setTop('Propostas de parceria');
  $view.innerHTML = `
    <p class="muted small">Coloque o print do que a marca está buscando e a IA monta a abordagem: direct, e-mail e ideias para oferecer.</p>
    <div class="list">${state.propostas.length ? state.propostas.map((p) => `<a class="item" href="#/proposta/${p.id}">
      ${p.imagens?.[0] ? `<img src="${p.imagens[0]}" alt="" style="width:40px;height:40px;border-radius:10px;object-fit:cover">` : '<div class="avatar">🤝</div>'}
      <div class="body"><div class="title">${esc(p.marca || 'Proposta sem marca')}</div><div class="sub">${p.versoes?.length ? 'abordagem pronta' : 'sem abordagem'} · ${esc(fmtDate(p.criadoEm?.slice(0, 10)))}</div></div>
      <div class="end"><span class="badge ${p.status === 'aprovada' ? 'b-ok' : p.status === 'recusada' ? 'b-bad' : p.status === 'enviada' ? 'b-info' : 'b-muted'}">${esc(p.status || 'rascunho')}</span></div></a>`).join('')
      : emptyBox('🤝', 'Nenhuma proposta ainda.', '<button class="btn primary" id="np">+ Nova proposta</button>')}</div>`;
  const np = $view.querySelector('#np');
  if (np) np.onclick = novaProposta;
  fab('Nova proposta', novaProposta);
}
function novaProposta() { const p = add('propostas', { marca: '', notas: '', imagens: [], versoes: [], status: 'rascunho' }); go(`proposta/${p.id}`); }

function viewProposta(id) {
  const p = find('propostas', id);
  if (!p) return go('propostas');
  setTop(p.marca || 'Proposta', { back: true });
  p.imagens ||= [];
  $view.innerHTML = `
    <div class="card">
      <label class="field"><span>Marca</span><input class="input" data-k="marca" placeholder="Nome da marca"></label>
      <div class="field"><span>Print do que a marca está buscando</span><div id="pImgs"></div></div>
      <label class="field"><span>Observações (opcional)</span><textarea class="input" rows="2" data-k="notas" placeholder="Ex.: vi no grupo de UGC, eles querem vídeos de unboxing"></textarea></label>
      <div class="field"><span>Status</span><div class="seg" data-k="status">${STATUS_PROP.map(([v, l]) => `<button data-v="${v}">${l}</button>`).join('')}</div></div>
    </div>
    <div class="section-title"><h2>Abordagem</h2></div>
    <div id="pAi"></div>
    <div class="row" style="margin-top:18px"><button class="btn sun" id="aprov">🎉 Fui aprovada: criar pasta da marca</button><span class="spacer"></span><button class="btn danger" id="delP">Excluir</button></div>`;
  bindFields($view, p, (k) => { save('propostas'); if (k === 'marca') $title.textContent = p.marca || 'Proposta'; });
  const renderImgs = () => { const c = $view.querySelector('#pImgs'); c.innerHTML = thumbsHTML(p.imagens); wireThumbs(c, p.imagens, () => { save('propostas'); renderImgs(); }); };
  renderImgs();
  aiPanel($view.querySelector('#pAi'), {
    obj: p, title: 'Abordagem para a marca', emptyLabel: 'Criar abordagem', onSave: () => save('propostas'),
    canGenerate: () => (p.imagens.length || p.notas?.trim() ? true : 'Adicione o print do que a marca está buscando'),
    generate: ({ ajuste, base, anteriores, onText, signal }) => AI.criarAbordagem({ marca: p.marca, notas: p.notas, imagens: p.imagens, anteriores, ajuste, base }, { onText, signal }),
  });
  $view.querySelector('#aprov').onclick = () => { p.status = 'aprovada'; save('propostas'); novaMarca({ nome: p.marca }); };
  $view.querySelector('#delP').onclick = async () => { if (await confirmBox('Excluir esta proposta?')) { remove('propostas', p.id); history.back(); } };
}

// ---------- Edição de vídeo ----------
const STATUS_VIDEO = ['a gravar', 'gravado', 'editando', 'pronto', 'postado'];
const CHECK_EDICAO = [
  ['cortes', 'Cortar vícios de fala, repetições e silêncios'],
  ['audio', 'Limpar o áudio (Studio Sound leve, ~40%)'],
  ['trilha', 'Trilha de fundo baixa com fade'],
  ['legendas', 'Legendas brancas com sombra, posição baixa'],
  ['gancho', 'Texto de gancho nos primeiros segundos'],
  ['citacao', 'Frase de destaque grande na tela'],
  ['zoom', 'Zooms suaves nos momentos fortes'],
  ['cor', 'Correção de cor leve'],
  ['vertical', 'Exportar vertical 1080x1920'],
];
const CHECK_CONFERIR = [
  ['tomVoz', 'Tom da voz natural depois de acelerar'],
  ['zoomAlinhado', 'Zooms alinhados com a fala'],
  ['fade', 'Música com fade de entrada e saída'],
  ['legendaPos', 'Legenda não cobre o produto nem a interface do app'],
  ['obrigatorios', 'Itens obrigatórios do briefing aparecem'],
];
const videoItem = (v) => `<a class="item" href="#/video/${v.id}"><div class="avatar">✂️</div>
  <div class="body"><div class="title">${esc(v.titulo || 'Vídeo')}</div><div class="sub">${esc(marcaNome(v.marcaId) || 'orgânico')}${v.duracaoAlvo ? ' · ' + esc(v.duracaoAlvo) : ''}</div></div>
  <div class="end"><span class="badge ${v.status === 'postado' ? 'b-ok' : v.status === 'pronto' ? 'b-info' : v.status === 'editando' ? 'b-warn' : 'b-muted'}">${esc(v.status || 'a gravar')}</span></div></a>`;

function viewVideos() {
  setTop('Edição de vídeo');
  $view.innerHTML = `
    <p class="muted small">Organize os vídeos, marque o que precisa ser feito e gere o pedido de edição para colar no Descript, junto com legenda e hashtags.</p>
    <div class="list">${state.videos.length ? state.videos.map(videoItem).join('') : emptyBox('✂️', 'Nenhum vídeo na fila de edição.', '<button class="btn primary" id="nv">+ Novo vídeo</button>')}</div>`;
  const nv = $view.querySelector('#nv');
  if (nv) nv.onclick = () => novoVideo();
  fab('Novo vídeo', () => novoVideo());
}
function novoVideo(preset = {}) {
  const v = add('videos', {
    titulo: preset.titulo || 'Novo vídeo', status: 'a gravar', duracaoAlvo: '30 a 45 s', velocidade: '1.0x',
    checklist: Object.fromEntries(CHECK_EDICAO.map(([k]) => [k, true])), conferir: {}, versoes: [], ...preset,
  });
  go(`video/${v.id}`);
}

function viewVideo(id) {
  const v = find('videos', id);
  if (!v) return go('videos');
  v.checklist ||= {}; v.conferir ||= {};
  setTop(v.titulo || 'Vídeo', { back: true });
  const linkRow = (k, label, ph) => `<label class="field"><span>${label}</span><div class="row" style="flex-wrap:nowrap"><input class="input" type="url" data-k="${k}" placeholder="${ph}">
    ${v[k] ? `<a class="btn sm" href="${esc(v[k])}" target="_blank" rel="noopener">Abrir</a>` : ''}</div></label>`;
  $view.innerHTML = `
    <div class="card">
      <label class="field"><span>Título</span><input class="input" data-k="titulo"></label>
      <div class="grid2">
        <label class="field"><span>Marca</span><select class="input" data-k="marcaId">${marcaOptions().map(([a, b]) => `<option value="${esc(a)}">${esc(b)}</option>`).join('')}</select></label>
        <label class="field"><span>Roteiro usado</span><select class="input" data-k="roteiroId"><option value="">— nenhum —</option>${state.roteiros.map((r) => `<option value="${r.id}">${esc(r.titulo)}</option>`).join('')}</select></label>
      </div>
      <div class="field"><span>Status</span><div class="seg" data-k="status">${STATUS_VIDEO.map((s) => `<button data-v="${s}">${s}</button>`).join('')}</div></div>
      <div class="grid2">
        <label class="field"><span>Duração alvo</span><input class="input" data-k="duracaoAlvo"></label>
        <label class="field"><span>Velocidade</span><select class="input" data-k="velocidade">${['1.0x', '1.1x', '1.2x', '1.25x', '1.3x'].map((s) => `<option>${s}</option>`).join('')}</select></label>
      </div>
    </div>

    <div class="section-title"><h2>O que fazer na edição</h2></div>
    <div class="card">${CHECK_EDICAO.map(([k, l]) => `<label class="check"><input type="checkbox" data-k="checklist.${k}"><span class="lbl">${l}</span></label>`).join('')}
      <label class="field" style="margin-top:8px"><span>Outros pedidos</span><textarea class="input" rows="2" data-k="notas" placeholder="Ex.: tirar o texto de abertura, baixar a legenda"></textarea></label></div>

    <div class="section-title"><h2>Links</h2></div>
    <div class="card">
      ${linkRow('linkBruto', 'Vídeo bruto (Drive, Dropbox...)', 'https://')}
      ${linkRow('linkDescript', 'Projeto no Descript', 'https://web.descript.com/...')}
      ${linkRow('linkFinal', 'Vídeo final / post publicado', 'https://')}
    </div>

    <div class="section-title"><h2>Pedido de edição + legenda</h2></div>
    <div id="vAi"></div>

    <div class="section-title"><h2>Conferir antes de entregar</h2></div>
    <div class="card">${CHECK_CONFERIR.map(([k, l]) => `<label class="check"><input type="checkbox" data-k="conferir.${k}"><span class="lbl">${l}</span></label>`).join('')}</div>

    <div class="row" style="margin-top:18px"><button class="btn" id="vPort">⭐ Adicionar ao portfólio</button><span class="spacer"></span><button class="btn danger" id="delV">Excluir</button></div>`;
  bindFields($view, v, (k) => {
    save('videos');
    if (k === 'titulo') $title.textContent = v.titulo;
    if (k.startsWith('link')) viewVideo(id);
    if (k.startsWith('conferir.')) $view.querySelector(`[data-k="${k}"]`).closest('.check').classList.toggle('done', getChecked(v, k));
  });
  $view.querySelectorAll('[data-k^="conferir."]').forEach((el) => el.closest('.check').classList.toggle('done', el.checked));
  aiPanel($view.querySelector('#vAi'), {
    obj: v, title: 'Pedido para o Descript', emptyLabel: 'Gerar pedido de edição', onSave: () => save('videos'),
    generate: ({ mode, ajuste, base, onText, signal }) => {
      if (mode === 'ajuste') return AI.run({ content: [{ type: 'text', text: `Texto atual:\n"""\n${base}\n"""\nAjuste: ${ajuste}\nDevolva o texto completo, com as mesmas seções.` }], onText, signal });
      const r = find('roteiros', v.roteiroId);
      const rt = r?.versoes?.length ? r.versoes[r.atual ?? r.versoes.length - 1].texto : '';
      return AI.pedidoEdicao({ video: v, roteiro: rt, marca: marcaNome(v.marcaId) }, { onText, signal });
    },
  });
  $view.querySelector('#vPort').onclick = () => addToPortfolio(marcaNome(v.marcaId) || v.titulo, v.linkFinal);
  $view.querySelector('#delV').onclick = async () => { if (await confirmBox('Excluir este vídeo?')) { remove('videos', v.id); history.back(); } };
}
const getChecked = (v, k) => !!k.split('.').reduce((a, x) => a?.[x], v);

// ---------- Portfólio ----------
function addToPortfolio(nome, link = '') {
  if (!nome) return toast('Sem nome para adicionar');
  let it = state.portfolio.find((p) => p.marca.toLowerCase() === nome.toLowerCase());
  if (it) {
    if (link) { it.linkVideo = link; it.temVideo = true; }
    toast('Já está no portfólio' + (link ? ' (link atualizado)' : ''));
  } else {
    it = add('portfolio', { marca: nome, temVideo: !!link, linkVideo: link, logoOk: false, noSite: false, noPdf: false, notas: '' });
    toast('Adicionado ao portfólio');
  }
  save('portfolio');
}

function viewPortfolio() {
  setTop('Portfólio');
  const s = state.settings;
  const itens = state.portfolio;
  const nomes = new Set(itens.map((p) => p.marca.toLowerCase()));
  const sugestoes = state.marcas.filter((m) => ['entregue', 'concluída'].includes(m.status) && !nomes.has(m.nome.toLowerCase()));
  const pend = itens.filter((p) => !p.temVideo || !p.logoOk || !p.noSite || !p.noPdf);
  const logos = itens.filter((p) => p.logoOk);
  $view.innerHTML = `
    <div class="card">
      <div class="grid2">
        <label class="field"><span>Site do portfólio</span><input class="input" type="url" id="pSite" placeholder="https://"></label>
        <label class="field"><span>PDF do portfólio</span><input class="input" type="url" id="pPdf" placeholder="https://"></label>
      </div>
      <div class="row">${s.portfolioSite ? `<a class="btn sm" target="_blank" rel="noopener" href="${esc(s.portfolioSite)}">Abrir site</a>` : ''}${s.portfolioPdf ? `<a class="btn sm" target="_blank" rel="noopener" href="${esc(s.portfolioPdf)}">Abrir PDF</a>` : ''}</div>
    </div>

    <div class="section-title"><h2>Faixa de logos (${logos.length})</h2></div>
    <div class="card"><div class="logos">${itens.map((p) => `<div class="logo-c ${p.logoOk ? '' : 'pending'}" title="${esc(p.marca)}">${esc(p.marca)}</div>`).join('')}</div>
      ${logos.length >= 6 ? '<p class="callout small" style="margin-top:12px">Com 6 ou mais logos a faixa quebra em duas linhas. Peça para ajustar o tamanho dos círculos na próxima atualização.</p>' : `<p class="small muted" style="margin-top:10px">Cabem 5 logos em uma linha. ${5 - logos.length > 0 ? `Ainda cabe${5 - logos.length > 1 ? 'm' : ''} ${5 - logos.length}.` : 'A linha está cheia.'}</p>`}</div>

    ${sugestoes.length ? `<div class="section-title"><h2>Marcas entregues fora do portfólio</h2></div>
      <div class="list">${sugestoes.map((m) => `<div class="item"><div class="avatar">${esc(initials(m.nome))}</div><div class="body"><div class="title">${esc(m.nome)}</div><div class="sub">${esc(m.status)}</div></div><button class="btn sm primary" data-add="${esc(m.nome)}">Adicionar</button></div>`).join('')}</div>` : ''}

    <div class="section-title"><h2>Marcas no portfólio</h2><button class="btn sm" id="addP">+ Marca</button></div>
    <div class="list">${itens.map((p) => `<div class="item" data-p="${p.id}"><div class="avatar">${esc(initials(p.marca))}</div>
      <div class="body"><div class="title">${esc(p.marca)}</div><div class="sub">${[p.temVideo ? 'com vídeo' : 'sem vídeo', p.logoOk ? 'logo ok' : 'falta logo', p.noSite ? 'no site' : 'fora do site', p.noPdf ? 'no PDF' : 'fora do PDF'].join(' · ')}</div></div>
      ${!p.temVideo || !p.logoOk || !p.noSite || !p.noPdf ? '<span class="badge b-warn">pendente</span>' : '<span class="badge b-ok">ok</span>'}</div>`).join('')}</div>

    <div class="section-title"><h2>Atualizar o portfólio</h2></div>
    <div class="card"><p class="small muted" style="margin-top:0">O site e o PDF são atualizados na conversa "Portfólio UGC". Copie o pedido abaixo e cole lá.</p>
      <button class="btn primary" id="cpPed" ${pend.length ? '' : 'disabled'}>📋 Copiar pedido de atualização (${pend.length})</button></div>`;
  const site = $view.querySelector('#pSite'), pdf = $view.querySelector('#pPdf');
  site.value = s.portfolioSite || ''; pdf.value = s.portfolioPdf || '';
  site.onchange = () => { s.portfolioSite = site.value.trim(); save('settings'); viewPortfolio(); };
  pdf.onchange = () => { s.portfolioPdf = pdf.value.trim(); save('settings'); viewPortfolio(); };
  $view.querySelectorAll('[data-add]').forEach((b) => (b.onclick = () => { addToPortfolio(b.dataset.add); viewPortfolio(); }));
  const edit = (p) => formModal({
    title: p ? p.marca : 'Marca no portfólio',
    data: p || {},
    fields: [
      { k: 'marca', label: 'Marca', required: true },
      { k: 'linkVideo', label: 'Link do vídeo (Reels/TikTok)', type: 'url' },
      { k: 'temVideo', label: 'Tem vídeo publicado', type: 'checkbox' },
      { k: 'logoOk', label: 'Logo na faixa de logos', type: 'checkbox' },
      { k: 'noSite', label: 'Já está no site', type: 'checkbox' },
      { k: 'noPdf', label: 'Já está no PDF', type: 'checkbox' },
      { k: 'notas', label: 'Anotações', type: 'textarea', rows: 2 },
    ],
    onSubmit: (d) => { if (d.linkVideo) d.temVideo = true; if (p) Object.assign(p, d); else add('portfolio', d); save('portfolio'); viewPortfolio(); },
    onDelete: p ? () => { remove('portfolio', p.id); viewPortfolio(); } : null,
  });
  $view.querySelector('#addP').onclick = () => edit(null);
  $view.querySelectorAll('[data-p]').forEach((el) => (el.onclick = () => edit(find('portfolio', el.dataset.p))));
  $view.querySelector('#cpPed').onclick = () => {
    const linhas = pend.map((p) => {
      const o = [];
      if (!p.logoOk) o.push('colocar o logo na faixa de logos');
      if (p.temVideo && p.linkVideo) o.push(`incluir o vídeo ${p.linkVideo} em "marcas e lojas que já gravei"`);
      else if (!p.temVideo) o.push('ainda sem vídeo (só registrar)');
      if (!p.noSite) o.push('incluir no site');
      if (!p.noPdf) o.push('incluir no PDF');
      return `- ${p.marca}: ${o.join('; ')}`;
    });
    copy(`Atualizar meu portfólio UGC (site e PDF):\n${linhas.join('\n')}${logos.length >= 6 ? '\n\nObs.: agora são ' + logos.length + ' logos, ajustar a faixa para não quebrar feio.' : ''}`);
  };
}

// ---------- Mais / Ajustes ----------
function viewMais() {
  setTop('Mais');
  $view.innerHTML = `<div class="list">${NAV.filter((n) => !n.tab).map((n) => `<a class="item" href="#/${n.r}"><div class="avatar">${n.ic}</div><div class="body"><div class="title">${n.t}</div>
    <div class="sub">${{ propostas: 'Print da marca → abordagem pronta', videos: 'Pedido de edição, legenda e hashtags', portfolio: 'Marcas, logos e pendências', ajustes: 'Chave da IA, backup, instalar o app' }[n.r]}</div></div><span class="muted">›</span></a>`).join('')}</div>`;
}

function viewAjustes() {
  setTop('Ajustes');
  const s = state.settings;
  $view.innerHTML = `
    <div class="section-title"><h2>✨ Inteligência artificial</h2></div>
    <div class="card">
      <p class="small muted" style="margin-top:0">A análise de briefing, os roteiros, as abordagens e os pedidos de edição usam o Claude. Para isso, crie uma chave em
        <a href="https://console.anthropic.com/settings/keys" target="_blank" rel="noopener">console.anthropic.com</a> e cole abaixo. A chave fica salva só neste aparelho. Cada uso é cobrado na sua conta da Anthropic.</p>
      <label class="field"><span>Chave da API</span><input class="input" type="password" id="sKey" autocomplete="off" placeholder="sk-ant-..."></label>
      <div class="grid2">
        <label class="field"><span>Modelo</span><select class="input" data-k="model">
          <option value="claude-opus-5-5">Claude Opus 5.5 (melhor qualidade)</option>
          <option value="claude-sonnet-5-5">Claude Sonnet 5.5 (mais barato)</option>
          <option value="claude-haiku-5-5">Claude Haiku 5.5 (mais rápido e barato)</option></select></label>
        <label class="field"><span>Capricho</span><select class="input" data-k="effort">
          <option value="low">Rápido</option><option value="medium">Equilibrado</option><option value="high">Caprichado</option></select></label>
      </div>
      <label class="field"><span>Sobre mim (a IA usa para acertar o tom)</span><textarea class="input" rows="4" data-k="sobre" placeholder="Ex.: @seuperfil, criadora UGC de beleza e rotina, público feminino 25-40, tom leve e sincero, grava em casa..."></textarea></label>
    </div>

    <div class="section-title"><h2>📲 Instalar como app</h2></div>
    <div class="card" id="installCard"></div>

    <div class="section-title"><h2>💾 Backup</h2></div>
    <div class="card">
      <p class="small muted" style="margin-top:0">Seus dados ficam salvos neste aparelho. Baixe um backup de vez em quando, e use-o para passar os dados para outro celular ou computador.</p>
      <div class="row"><button class="btn" id="exp">⬇️ Baixar backup</button><button class="btn" id="imp">⬆️ Restaurar backup</button></div>
    </div>

    <div class="section-title"><h2>Aparência</h2></div>
    <div class="card"><div class="seg" data-k="theme"><button data-v="auto">Automático</button><button data-v="light">Claro</button><button data-v="dark">Escuro</button></div></div>`;
  const key = $view.querySelector('#sKey');
  key.value = s.apiKey || '';
  key.onchange = () => { s.apiKey = key.value.trim(); save('settings'); toast(s.apiKey ? 'Chave salva neste aparelho' : 'Chave removida'); };
  bindFields($view, s, (k) => { save('settings'); if (k === 'theme') applyTheme(); });
  renderInstallCard();
  $view.querySelector('#exp').onclick = () => {
    const blob = new Blob([exportJSON()], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `sol-hub-backup-${todayISO()}.json`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  };
  $view.querySelector('#imp').onclick = () => {
    const inp = document.createElement('input');
    inp.type = 'file'; inp.accept = 'application/json,.json';
    inp.onchange = async () => {
      try {
        const text = await inp.files[0].text();
        if (!(await confirmBox('Restaurar substitui os dados atuais deste aparelho. Continuar?', 'Restaurar'))) return;
        await importJSON(text);
        toast('Backup restaurado'); applyTheme(); route();
      } catch (e) { toast(e.message || 'Arquivo inválido'); }
    };
    inp.click();
  };
}

// ---------- Instalação (PWA) ----------
let deferredPrompt = null;
window.addEventListener('beforeinstallprompt', (e) => { e.preventDefault(); deferredPrompt = e; if (/agenda|^$/.test(location.hash.replace('#/', ''))) route(); });
const isStandalone = () => window.matchMedia('(display-mode: standalone)').matches || navigator.standalone;
const isIOS = () => /iphone|ipad|ipod/i.test(navigator.userAgent);

function installBanner() {
  if (isStandalone() || localStorage.getItem('hideInstall')) return '';
  if (!deferredPrompt && !isIOS()) return '';
  return `<div class="callout" id="instBanner" style="margin-bottom:14px;display:flex;gap:10px;align-items:center">
    <span style="font-size:22px">📲</span><span style="flex:1">Instale o Sol Hub na tela inicial para usar como app.</span>
    <button class="btn sm primary" id="instGo">Instalar</button><button class="iconbtn" id="instX" aria-label="Fechar">✕</button></div>`;
}
function wireInstall() {
  const b = document.getElementById('instBanner');
  if (!b) return;
  b.querySelector('#instGo').onclick = doInstall;
  b.querySelector('#instX').onclick = () => { try { localStorage.setItem('hideInstall', '1'); } catch {} b.remove(); };
}
async function doInstall() {
  if (deferredPrompt) {
    deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    deferredPrompt = null;
    route();
  } else go('ajustes');
}
function renderInstallCard() {
  const c = document.getElementById('installCard');
  if (!c) return;
  if (isStandalone()) c.innerHTML = '<p style="margin:0">✅ Você já está usando o app instalado.</p>';
  else if (deferredPrompt) { c.innerHTML = '<button class="btn primary" id="instNow">Instalar o app</button>'; c.querySelector('#instNow').onclick = doInstall; }
  else c.innerHTML = `<p style="margin:0" class="small"><b>iPhone (Safari):</b> toque em Compartilhar <span aria-hidden="true">⬆️</span> e depois em <b>Adicionar à Tela de Início</b>.<br>
    <b>Android (Chrome):</b> menu ⋮ e depois <b>Instalar app</b> ou <b>Adicionar à tela inicial</b>.<br>
    <b>Computador (Chrome/Edge):</b> ícone de instalar na barra de endereço.</p>`;
}

function applyTheme() {
  const t = state.settings.theme;
  if (t === 'light' || t === 'dark') document.documentElement.dataset.theme = t;
  else delete document.documentElement.dataset.theme;
}

// ---------- Início ----------
(async function start() {
  const ok = await loadAll();
  applyTheme();
  if (!ok) toast('Não deu para salvar dados neste navegador (modo anônimo?).');
  window.addEventListener('hashchange', route);
  window.addEventListener('save-error', () => toast('Erro ao salvar. Pode faltar espaço no aparelho.'));
  route();
  if ('serviceWorker' in navigator && location.protocol !== 'file:') {
    navigator.serviceWorker.register('sw.js').catch((e) => console.warn('SW', e));
  }
})();
