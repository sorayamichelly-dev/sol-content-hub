// Utilidades de interface.
import { friendlyError, hasKey, runJob, promptText } from './ai.js';

export const esc = (s) =>
  String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

// ---------- Datas e dinheiro ----------
export const todayISO = () => toISO(new Date());
export function toISO(d) {
  const z = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${z(d.getMonth() + 1)}-${z(d.getDate())}`;
}
export function parseISO(s) {
  if (!s) return null;
  const [y, m, d] = s.split('-').map(Number);
  return new Date(y, m - 1, d);
}
export function fmtDate(s, opts = { day: '2-digit', month: 'short' }) {
  const d = parseISO(s);
  return d ? d.toLocaleDateString('pt-BR', opts).replace('.', '') : '';
}
export function daysFrom(s) {
  const d = parseISO(s);
  if (!d) return null;
  const t = parseISO(todayISO());
  return Math.round((d - t) / 86400000);
}
export function relDay(s) {
  const n = daysFrom(s);
  if (n === null) return '';
  if (n === 0) return 'hoje';
  if (n === 1) return 'amanhã';
  if (n === -1) return 'ontem';
  if (n < 0) return `há ${-n} dias`;
  if (n < 7) return `em ${n} dias`;
  return fmtDate(s);
}
export function money(v) {
  const n = Number(v);
  if (!v && v !== 0) return '';
  return isNaN(n) ? String(v) : n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

// ---------- Markdown simples e seguro ----------
export function md(src) {
  const lines = String(src || '').replace(/\r/g, '').split('\n');
  let out = '', list = null, para = [], table = null;
  const inline = (t) =>
    esc(t)
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/(^|[^*])\*(?!\s)(.+?)\*/g, '$1<em>$2</em>')
      .replace(/(^|\s)_(.+?)_(?=\s|$|[.,!?])/g, '$1<em>$2</em>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  const flushP = () => { if (para.length) { out += `<p>${para.map(inline).join('<br>')}</p>`; para = []; } };
  const flushL = () => { if (list) { out += `<${list.t}>${list.items.map((i) => `<li>${inline(i)}</li>`).join('')}</${list.t}>`; list = null; } };
  const flushT = () => {
    if (table) {
      const rows = table.filter((r) => !/^\s*\|?\s*:?-{2,}/.test(r));
      const cells = (r) => r.trim().replace(/^\||\|$/g, '').split('|').map((c) => c.trim());
      out += '<table>' + rows.map((r, i) => `<tr>${cells(r).map((c) => (i === 0 ? `<th>${inline(c)}</th>` : `<td>${inline(c)}</td>`)).join('')}</tr>`).join('') + '</table>';
      table = null;
    }
  };
  const flush = () => { flushP(); flushL(); flushT(); };
  for (const raw of lines) {
    const l = raw.trimEnd();
    let m;
    if (/^\s*\|.*\|\s*$/.test(l)) { flushP(); flushL(); (table ||= []).push(l); continue; } else flushT();
    if (!l.trim()) { flush(); continue; }
    if ((m = l.match(/^(#{1,4})\s+(.*)/))) { flush(); const n = Math.min(3, m[1].length + 1); out += `<h${n}>${inline(m[2])}</h${n}>`; continue; }
    if (/^\s*(-{3,}|\*{3,})\s*$/.test(l)) { flush(); out += '<hr>'; continue; }
    if ((m = l.match(/^\s*>\s?(.*)/))) { flush(); out += `<blockquote>${inline(m[1])}</blockquote>`; continue; }
    if ((m = l.match(/^\s*[-*•]\s+(.*)/))) { flushP(); if (!list || list.t !== 'ul') { flushL(); list = { t: 'ul', items: [] }; } list.items.push(m[1]); continue; }
    if ((m = l.match(/^\s*\d+[.)]\s+(.*)/))) { flushP(); if (!list || list.t !== 'ol') { flushL(); list = { t: 'ol', items: [] }; } list.items.push(m[1]); continue; }
    if (list && /^\s{2,}/.test(raw)) { list.items[list.items.length - 1] += ' ' + l.trim(); continue; }
    flushL();
    para.push(l);
  }
  flush();
  return out;
}

// ---------- Toast ----------
let toastT;
export function toast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(toastT);
  toastT = setTimeout(() => el.classList.remove('show'), 2600);
}

export async function copy(text) {
  try {
    await navigator.clipboard.writeText(text);
    toast('Copiado');
  } catch {
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    ta.remove();
    toast('Copiado');
  }
}

// ---------- Modal ----------
export function modal(html, onMount) {
  const root = document.getElementById('modalRoot');
  root.innerHTML = `<div class="backdrop" data-close></div><div class="sheet" role="dialog" aria-modal="true">${html}</div>`;
  root.classList.add('open');
  const close = () => { root.classList.remove('open'); root.innerHTML = ''; };
  root.querySelectorAll('[data-close]').forEach((b) => b.addEventListener('click', close));
  onMount && onMount(root.querySelector('.sheet'), close);
  const first = root.querySelector('input,textarea,select');
  if (first && window.matchMedia('(min-width:640px)').matches) first.focus();
  return close;
}

export function confirmBox(msg, okLabel = 'Excluir') {
  return new Promise((resolve) => {
    modal(
      `<h3>${esc(msg)}</h3><div class="actions"><button class="btn" data-close>Cancelar</button><button class="btn primary" id="okc">${esc(okLabel)}</button></div>`,
      (el, close) => {
        el.querySelector('#okc').onclick = () => { close(); resolve(true); };
        document.querySelectorAll('#modalRoot [data-close]').forEach((b) => b.addEventListener('click', () => resolve(false)));
      }
    );
  });
}

/**
 * Formulário genérico. fields: [{k, label, type, options, placeholder, full}]
 */
export function formModal({ title, fields, data = {}, submit = 'Salvar', onSubmit, onDelete }) {
  const inputs = fields.map((f) => fieldHTML(f, getPath(data, f.k))).join('');
  modal(
    `<h3>${esc(title)}</h3><form id="fm">${inputs}
      <div class="actions">${onDelete ? '<button type="button" class="btn danger" id="fdel">Excluir</button><span class="spacer"></span>' : ''}
      <button type="button" class="btn" data-close>Cancelar</button><button class="btn primary">${esc(submit)}</button></div></form>`,
    (el, close) => {
      wireSegs(el);
      el.querySelector('#fm').onsubmit = (e) => {
        e.preventDefault();
        const out = {};
        fields.forEach((f) => setPath(out, f.k, readField(el, f)));
        if (fields.some((f) => f.required && !getPath(out, f.k))) return toast('Preencha os campos obrigatórios');
        onSubmit(out);
        close();
      };
      if (onDelete) el.querySelector('#fdel').onclick = async () => { close(); if (await confirmBox('Excluir este item?')) onDelete(); };
    }
  );
}

export function fieldHTML(f, val) {
  const v = val ?? f.default ?? '';
  const ph = f.placeholder ? ` placeholder="${esc(f.placeholder)}"` : '';
  let ctl;
  if (f.type === 'textarea') ctl = `<textarea class="input" name="${f.k}"${ph} rows="${f.rows || 4}">${esc(v)}</textarea>`;
  else if (f.type === 'select')
    ctl = `<select class="input" name="${f.k}">${f.options.map((o) => { const [ov, ol] = Array.isArray(o) ? o : [o, o]; return `<option value="${esc(ov)}"${String(ov) === String(v) ? ' selected' : ''}>${esc(ol)}</option>`; }).join('')}</select>`;
  else if (f.type === 'seg')
    ctl = `<div class="seg" data-seg="${f.k}">${f.options.map((o) => { const [ov, ol] = Array.isArray(o) ? o : [o, o]; return `<button type="button" data-v="${esc(ov)}" class="${String(ov) === String(v) ? 'on' : ''}">${esc(ol)}</button>`; }).join('')}</div>`;
  else if (f.type === 'checkbox')
    return `<label class="check"><input type="checkbox" name="${f.k}"${v ? ' checked' : ''}><span class="lbl">${esc(f.label)}</span></label>`;
  else ctl = `<input class="input" name="${f.k}" type="${f.type || 'text'}"${f.type === 'number' ? ' inputmode="decimal" step="0.01"' : ''} value="${esc(v)}"${ph}>`;
  return `<label class="field"><span>${esc(f.label)}${f.required ? ' *' : ''}</span>${ctl}${f.hint ? `<small class="muted">${esc(f.hint)}</small>` : ''}</label>`;
}
function readField(el, f) {
  if (f.type === 'seg') return el.querySelector(`[data-seg="${f.k}"] .on`)?.dataset.v ?? '';
  const i = el.querySelector(`[name="${f.k}"]`);
  if (!i) return '';
  if (f.type === 'checkbox') return i.checked;
  if (f.type === 'number') return i.value === '' ? '' : Number(i.value);
  return i.value.trim();
}
export function wireSegs(el, onChange) {
  el.querySelectorAll('.seg').forEach((s) =>
    s.querySelectorAll('button').forEach((b) =>
      b.addEventListener('click', () => {
        s.querySelectorAll('button').forEach((x) => x.classList.toggle('on', x === b));
        onChange && onChange(s.dataset.seg, b.dataset.v);
      })
    )
  );
}
export function getPath(o, p) { return p.split('.').reduce((a, k) => (a == null ? a : a[k]), o); }
export function setPath(o, p, v) {
  const ks = p.split('.');
  let cur = o;
  ks.slice(0, -1).forEach((k) => { if (typeof cur[k] !== 'object' || cur[k] === null) cur[k] = {}; cur = cur[k]; });
  cur[ks[ks.length - 1]] = v;
}

/** Liga campos com data-k a um objeto e salva ao mudar. */
export function bindFields(container, obj, onSave) {
  container.querySelectorAll('[data-k]').forEach((el) => {
    const k = el.dataset.k;
    const cur = getPath(obj, k);
    if (el.classList.contains('seg')) {
      el.querySelectorAll('button').forEach((b) => {
        b.classList.toggle('on', String(b.dataset.v) === String(cur ?? ''));
        b.addEventListener('click', () => {
          el.querySelectorAll('button').forEach((x) => x.classList.toggle('on', x === b));
          setPath(obj, k, b.dataset.v);
          onSave(k);
        });
      });
      return;
    }
    if (el.type === 'checkbox') el.checked = !!cur;
    else el.value = cur ?? '';
    const ev = el.tagName === 'SELECT' || el.type === 'checkbox' || el.type === 'date' ? 'change' : 'input';
    el.addEventListener(ev, () => {
      let v = el.type === 'checkbox' ? el.checked : el.value;
      if (el.type === 'number') v = el.value === '' ? '' : Number(el.value);
      setPath(obj, k, v);
      onSave(k);
    });
  });
}

// ---------- Imagens (prints) ----------
export function pickImages({ multiple = true } = {}) {
  return new Promise((resolve) => {
    const inp = document.createElement('input');
    inp.type = 'file';
    inp.accept = 'image/*';
    inp.multiple = multiple;
    inp.onchange = async () => {
      const out = [];
      for (const f of inp.files) out.push(await compressImage(f));
      resolve(out);
    };
    inp.click();
  });
}
export function compressImage(file, max = 1568, quality = 0.85) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(file);
    img.onload = () => {
      const s = Math.min(1, max / Math.max(img.width, img.height));
      const c = document.createElement('canvas');
      c.width = Math.round(img.width * s);
      c.height = Math.round(img.height * s);
      c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
      URL.revokeObjectURL(url);
      resolve(c.toDataURL('image/jpeg', quality));
    };
    img.onerror = reject;
    img.src = url;
  });
}
export function thumbsHTML(imgs = []) {
  return `<div class="thumbs">${imgs.map((src, i) => `<div class="thumb"><img src="${src}" alt="Print ${i + 1}"><button type="button" data-rmimg="${i}" aria-label="Remover">✕</button></div>`).join('')}
    <button type="button" class="drop" data-addimg><span class="big">＋</span>Adicionar print</button></div>`;
}
export function wireThumbs(container, arr, onChange) {
  container.querySelectorAll('[data-rmimg]').forEach((b) => (b.onclick = () => { arr.splice(Number(b.dataset.rmimg), 1); onChange(); }));
  const add = container.querySelector('[data-addimg]');
  if (add) add.onclick = async () => { const imgs = await pickImages(); arr.push(...imgs); onChange(); };
}

// ---------- Painel de IA com versões, "Gerar novo" e ajuste por texto ----------
/**
 * obj.versoes = [{texto, pedido, criadoEm}], obj.atual = índice.
 * build({mode:'novo'|'ajuste', ajuste, base, anteriores}) => job (ver ai.js)
 * Com chave da API: gera direto. Sem chave: modo "meu Claude" (copiar o pedido, colar a resposta), sem custo.
 */
export function aiPanel(container, { obj, title, emptyLabel = 'Gerar', onSave, build, canGenerate = () => true }) {
  obj.versoes ||= [];
  let busy = false, ctrl = null;
  let copiado = null; // último pedido copiado no modo grátis: {mode, ajuste, imagens}

  const addVersion = (texto, pedido) => {
    obj.versoes.push({ texto, pedido: pedido || '', criadoEm: new Date().toISOString() });
    obj.atual = obj.versoes.length - 1;
    onSave();
  };

  const render = () => {
    const auto = hasKey();
    const n = obj.versoes.length;
    const idx = Math.min(obj.atual ?? n - 1, n - 1);
    const cur = obj.versoes[idx];
    container.innerHTML = `
      <div class="ai-box ${busy ? 'busy' : ''}">
        <div class="ai-head">✨ ${esc(title)}${auto ? '' : ' · com o seu Claude'}
          ${n > 1 && !busy ? `<div class="versions"><button class="btn sm ghost" data-v="-1" ${idx === 0 ? 'disabled' : ''} aria-label="Versão anterior">‹</button><span class="small">versão ${idx + 1} de ${n}</span><button class="btn sm ghost" data-v="1" ${idx === n - 1 ? 'disabled' : ''} aria-label="Próxima versão">›</button></div>` : ''}
        </div>
        <div class="ai-body">
          ${busy ? `<div class="md typing"><span class="thinking"><i></i><i></i><i></i>&nbsp;criando…</span></div>`
            : cur ? `${cur.pedido ? `<p class="small muted">Ajuste pedido: “${esc(cur.pedido)}”</p>` : ''}<div class="md">${md(cur.texto)}</div>`
            : auto ? `<p class="muted">Nada gerado ainda.</p>`
            : `<p class="muted" style="margin:0">Nada gerado ainda.</p>`}
        </div>
      </div>
      ${!auto && !busy ? passosHTML() : ''}
      <div class="row" style="margin-top:12px">
        ${busy ? `<button class="btn" data-stop>Parar</button>`
          : auto ? `<button class="btn primary" data-gen>${n ? '🔄 Gerar novo' : '✨ ' + esc(emptyLabel)}</button>${cur ? '<button class="btn" data-copy>Copiar</button>' : ''}`
          : `<button class="btn primary" data-gen>📋 ${n ? 'Copiar pedido de um novo' : 'Copiar pedido para o Claude'}</button>
             <a class="btn" href="https://claude.ai/new" target="_blank" rel="noopener">Abrir o Claude ↗</a>
             <button class="btn sun" data-paste>✍️ Colar resposta</button>
             ${cur ? '<button class="btn" data-copy>Copiar texto</button>' : ''}`}
      </div>
      ${cur && !busy ? `
      <div class="field" style="margin-top:16px">
        <span>Acrescentar ou remover algo</span>
        <textarea class="input" rows="2" data-adj placeholder="Ex.: tira a parte do preço, acrescenta uma cena mostrando a textura, deixa o gancho mais curto"></textarea>
      </div>
      <button class="btn" data-adjbtn>${auto ? '✏️ Ajustar' : '📋 Copiar pedido de ajuste'}</button>` : ''}`;

    container.querySelectorAll('[data-v]').forEach((b) => (b.onclick = () => { obj.atual = idx + Number(b.dataset.v); onSave(); render(); }));
    const gen = container.querySelector('[data-gen]');
    if (gen) gen.onclick = () => go('novo');
    const cp = container.querySelector('[data-copy]');
    if (cp) cp.onclick = () => copy(cur.texto);
    const st = container.querySelector('[data-stop]');
    if (st) st.onclick = () => ctrl && ctrl.abort();
    const ps = container.querySelector('[data-paste]');
    if (ps) ps.onclick = pasteAnswer;
    const dl = container.querySelector('[data-dlimg]');
    if (dl) dl.onclick = () => (copiado?.imagens || []).forEach((src, i) => { const a = document.createElement('a'); a.href = src; a.download = `print-${i + 1}.jpg`; a.click(); });
    const ab = container.querySelector('[data-adjbtn]');
    if (ab) ab.onclick = () => {
      const t = container.querySelector('[data-adj]').value.trim();
      if (!t) return toast('Escreva o que quer mudar');
      go('ajuste', t, cur.texto);
    };
  };

  const passosHTML = () => {
    const imgs = copiado?.imagens?.length || 0;
    return `<div class="callout small" style="margin-top:12px">
      <b>Modo grátis, com o seu Claude:</b>
      <ol style="margin:6px 0 0;padding-left:20px">
        <li>${copiado ? '✅ Pedido copiado.' : 'Toque em <b>Copiar pedido</b>.'}</li>
        <li>Abra o Claude, cole numa conversa nova${imgs ? ` e <b>anexe ${imgs === 1 ? 'o print' : `os ${imgs} prints`}</b>` : ''} e envie.</li>
        <li>Copie a resposta do Claude e toque em <b>Colar resposta</b>.</li>
      </ol>
      ${imgs ? `<button class="btn sm" data-dlimg style="margin-top:10px">⬇️ Baixar ${imgs === 1 ? 'o print' : 'os prints'}</button>` : ''}
    </div>`;
  };

  const pasteAnswer = () => {
    modal(`<h3>Colar resposta</h3>
      <p class="small muted" style="margin-top:0">Copie a resposta inteira do Claude e cole aqui.</p>
      <textarea class="input" rows="10" id="pasteTxt" placeholder="Cole aqui a resposta do Claude"></textarea>
      <div class="actions"><button class="btn" id="fromClip">📋 Colar da área de transferência</button><span class="spacer"></span>
        <button class="btn" data-close>Cancelar</button><button class="btn primary" id="savePaste">Salvar</button></div>`,
      (el, close) => {
        const ta = el.querySelector('#pasteTxt');
        el.querySelector('#fromClip').onclick = async () => {
          try { ta.value = await navigator.clipboard.readText(); } catch { toast('Toque e segure no campo e escolha Colar'); ta.focus(); }
        };
        el.querySelector('#savePaste').onclick = () => {
          const t = ta.value.trim();
          if (t.length < 20) return toast('Cole a resposta do Claude primeiro');
          addVersion(t, copiado?.mode === 'ajuste' ? copiado.ajuste : '');
          copiado = null;
          close();
          render();
          toast('Resposta salva ✨');
        };
      });
  };

  const go = async (mode, ajuste, base) => {
    if (busy) return;
    const why = canGenerate();
    if (why !== true) return toast(why || 'Falta informação para gerar');
    const job = build({ mode, ajuste, base, anteriores: mode === 'novo' ? obj.versoes.map((v) => v.texto) : [] });
    if (!hasKey()) {
      await copy(promptText(job));
      copiado = { mode, ajuste, imagens: job.imagens || [] };
      toast(job.imagens?.length ? 'Pedido copiado. Lembre de anexar o print no Claude' : 'Pedido copiado. Agora cole no Claude');
      render();
      return;
    }
    busy = true;
    ctrl = new AbortController();
    render();
    try {
      const texto = await runJob(job, {
        signal: ctrl.signal,
        onText: (t) => { const box = container.querySelector('.typing'); if (box) box.innerHTML = md(t); },
      });
      addVersion(texto, mode === 'ajuste' ? ajuste : '');
    } catch (e) {
      console.error(e);
      toast(friendlyError(e));
    } finally {
      busy = false;
      ctrl = null;
      render();
    }
  };

  render();
}

// ---------- Efeitos ----------
const reduced = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;

export function confetti(n = 90) {
  if (reduced()) return;
  const box = document.createElement('div');
  box.className = 'confetti';
  const cores = ['#D8386A', '#F2762E', '#FFC46B', '#8A6FD1', '#1F9C7E', '#3E8FD0', '#FFE0E9'];
  for (let i = 0; i < n; i++) {
    const c = document.createElement('i');
    c.style.left = Math.random() * 100 + 'vw';
    c.style.background = cores[i % cores.length];
    c.style.setProperty('--x', (Math.random() * 30 - 15) + 'vw');
    c.style.setProperty('--r', (Math.random() * 900 - 450) + 'deg');
    c.style.setProperty('--d', (1.3 + Math.random() * 1.4) + 's');
    c.style.animationDelay = Math.random() * 0.25 + 's';
    if (Math.random() > 0.6) { c.style.borderRadius = '50%'; c.style.height = '9px'; }
    box.appendChild(c);
  }
  document.body.appendChild(box);
  setTimeout(() => box.remove(), 3200);
}

export function countUp(el, to, fmt = (v) => String(Math.round(v)), ms = 900) {
  if (reduced() || !to) { el.textContent = fmt(to); return; }
  const t0 = performance.now();
  const step = (t) => {
    const k = Math.min(1, (t - t0) / ms);
    el.textContent = fmt(to * (1 - Math.pow(1 - k, 3)));
    if (k < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

/** Anima a entrada de cards e itens novos na tela, um depois do outro. */
export function revealNew(root) {
  let i = 0;
  root.querySelectorAll('.item, .stat, .card, .ai-box, .empty, .hero, .section-title').forEach((el) => {
    if (el.dataset.rv) return;
    el.dataset.rv = '1';
    el.classList.add('reveal');
    el.style.setProperty('--i', Math.min(i++, 14));
  });
}

export const SUN_SVG = `<svg class="sun-svg" viewBox="0 0 150 150" aria-hidden="true">
  <g class="rays" fill="#FFC46B" stroke="#2A1A1E" stroke-width="4" stroke-linejoin="round">
    ${Array.from({ length: 10 }, (_, k) => { const a = (k * Math.PI) / 5; const p = (r, d) => `${(75 + r * Math.cos(a + d)).toFixed(1)},${(75 + r * Math.sin(a + d)).toFixed(1)}`; return `<polygon points="${p(46, -0.16)} ${p(72, 0)} ${p(46, 0.16)}"/>`; }).join('')}
  </g>
  <circle class="core" cx="75" cy="75" r="40" fill="#F2762E" stroke="#2A1A1E" stroke-width="5"/>
  <path d="M60 80 q15 14 30 0" fill="none" stroke="#2A1A1E" stroke-width="5" stroke-linecap="round"/>
  <circle cx="62" cy="66" r="4.5" fill="#2A1A1E"/><circle cx="88" cy="66" r="4.5" fill="#2A1A1E"/>
</svg>`;
