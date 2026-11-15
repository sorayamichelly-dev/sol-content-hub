// Utilidades de interface.
import { friendlyError } from './ai.js';

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
 * generate({mode:'novo'|'ajuste', ajuste, base, anteriores, onText, signal}) => Promise<string>
 */
export function aiPanel(container, { obj, title, emptyLabel = 'Gerar', onSave, generate, canGenerate = () => true }) {
  obj.versoes ||= [];
  let busy = false, ctrl = null;

  const render = (streamText) => {
    const n = obj.versoes.length;
    const idx = Math.min(obj.atual ?? n - 1, n - 1);
    const cur = obj.versoes[idx];
    container.innerHTML = `
      <div class="ai-box">
        <div class="ai-head">✨ ${esc(title)}<span class="spacer"></span>
          ${n > 1 && !busy ? `<div class="versions"><button class="btn sm ghost" data-v="-1" ${idx === 0 ? 'disabled' : ''} aria-label="Versão anterior">‹</button><span class="small">versão ${idx + 1} de ${n}</span><button class="btn sm ghost" data-v="1" ${idx === n - 1 ? 'disabled' : ''} aria-label="Próxima versão">›</button></div>` : ''}
        </div>
        <div class="ai-body">
          ${busy ? `<div class="md typing">${md(streamText || 'Pensando…')}</div>`
            : cur ? `${cur.pedido ? `<p class="small muted">Ajuste pedido: “${esc(cur.pedido)}”</p>` : ''}<div class="md">${md(cur.texto)}</div>`
            : `<p class="muted">Nada gerado ainda.</p>`}
        </div>
      </div>
      <div class="row" style="margin-top:10px">
        ${busy ? `<button class="btn" data-stop>Parar</button>`
          : `<button class="btn primary" data-gen>${n ? '🔄 Gerar novo' : '✨ ' + esc(emptyLabel)}</button>
             ${cur ? '<button class="btn" data-copy>Copiar</button>' : ''}`}
      </div>
      ${cur && !busy ? `
      <div class="field" style="margin-top:14px">
        <span>Acrescentar ou remover algo</span>
        <textarea class="input" rows="2" data-adj placeholder="Ex.: tira a parte do preço, acrescenta uma cena mostrando a textura, deixa o gancho mais curto"></textarea>
      </div>
      <button class="btn" data-adjbtn>✏️ Ajustar</button>` : ''}`;

    container.querySelectorAll('[data-v]').forEach((b) => (b.onclick = () => { obj.atual = idx + Number(b.dataset.v); onSave(); render(); }));
    const gen = container.querySelector('[data-gen]');
    if (gen) gen.onclick = () => go('novo');
    const cp = container.querySelector('[data-copy]');
    if (cp) cp.onclick = () => copy(cur.texto);
    const st = container.querySelector('[data-stop]');
    if (st) st.onclick = () => ctrl && ctrl.abort();
    const ab = container.querySelector('[data-adjbtn]');
    if (ab) ab.onclick = () => {
      const t = container.querySelector('[data-adj]').value.trim();
      if (!t) return toast('Escreva o que quer mudar');
      go('ajuste', t, cur.texto);
    };
  };

  const go = async (mode, ajuste, base) => {
    if (busy) return;
    const why = canGenerate();
    if (why !== true) return toast(why || 'Falta informação para gerar');
    busy = true;
    ctrl = new AbortController();
    render();
    try {
      const texto = await generate({
        mode, ajuste, base,
        anteriores: mode === 'novo' ? obj.versoes.map((v) => v.texto) : [],
        signal: ctrl.signal,
        onText: (t) => {
          const box = container.querySelector('.typing');
          if (box) box.innerHTML = md(t);
        },
      });
      obj.versoes.push({ texto, pedido: mode === 'ajuste' ? ajuste : '', criadoEm: new Date().toISOString() });
      obj.atual = obj.versoes.length - 1;
      onSave();
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
