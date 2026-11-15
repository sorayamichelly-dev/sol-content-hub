// Dados: cada pessoa tem sua conta (Supabase) e uma cópia no aparelho para abrir rápido e funcionar sem internet.
import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.118.0/+esm';

const SUPABASE_URL = 'https://thhxhoyrccvototsaykz.supabase.co';
const SUPABASE_KEY = 'sb_publishable_LkOTxoRkbKpn-VflobszjQ_PKCefDqE';
export const sb = createClient(SUPABASE_URL, SUPABASE_KEY, {
  auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
});

const COLLECTIONS = ['marcas', 'ideias', 'eventos', 'roteiros', 'propostas', 'videos', 'portfolio'];
const DEFAULT_SETTINGS = { nome: '', model: 'claude-opus-5-5', effort: 'medium', sobre: '', portfolioSite: '', portfolioPdf: '', theme: 'auto' };

export const state = { settings: { ...DEFAULT_SETTINGS }, user: null, isAdmin: false, syncing: false, pending: 0 };
COLLECTIONS.forEach((c) => (state[c] = []));

// ---------- Cache local (IndexedDB) ----------
let dbp;
function openDB() {
  dbp ||= new Promise((resolve, reject) => {
    const req = indexedDB.open('sol-hub', 1);
    req.onupgradeneeded = () => req.result.createObjectStore('kv');
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
  return dbp;
}
async function idb(mode, fn) {
  const db = await openDB();
  return new Promise((res, rej) => {
    const tx = db.transaction('kv', mode);
    const r = fn(tx.objectStore('kv'));
    tx.oncomplete = () => res(r?.result);
    tx.onerror = () => rej(tx.error);
  });
}
const cacheGet = (k) => idb('readonly', (s) => s.get(k)).catch(() => undefined);
const cacheSet = (k, v) => idb('readwrite', (s) => s.put(v, k)).catch(() => {});
const cacheDel = (k) => idb('readwrite', (s) => s.delete(k)).catch(() => {});

// A chave da IA fica só neste aparelho, nunca vai para o servidor.
export function getApiKey() { try { return localStorage.getItem('sol-api-key') || ''; } catch { return ''; } }
export function setApiKey(k) { try { k ? localStorage.setItem('sol-api-key', k) : localStorage.removeItem('sol-api-key'); } catch {} }

// ---------- Sincronização ----------
const synced = {}; // colecao -> Map(id -> json do último envio)
const dirty = new Set();

function snapshot() {
  const s = {};
  COLLECTIONS.forEach((c) => (s[c] = state[c]));
  s.settings = state.settings;
  return s;
}
async function writeCache() {
  if (state.user) await cacheSet('u:' + state.user.id, snapshot());
}

export async function loadUserData() {
  const uid = state.user.id;
  // 1) abre rápido com o que já está no aparelho
  const cached = await cacheGet('u:' + uid);
  if (cached) applySnapshot(cached);
  // 2) busca a versão do servidor
  const { data, error } = await sb.from('itens').select('colecao,id,conteudo');
  if (error) {
    console.warn(error);
    return { offline: true, fromCache: !!cached };
  }
  const fresh = { settings: { ...DEFAULT_SETTINGS } };
  COLLECTIONS.forEach((c) => { fresh[c] = []; synced[c] = new Map(); });
  synced.settings = new Map();
  for (const row of data) {
    if (row.colecao === 'settings') { Object.assign(fresh.settings, row.conteudo); synced.settings.set('main', JSON.stringify(row.conteudo)); }
    else if (fresh[row.colecao]) { fresh[row.colecao].push(row.conteudo); synced[row.colecao].set(row.id, JSON.stringify(row.conteudo)); }
  }
  COLLECTIONS.forEach((c) => fresh[c].sort((a, b) => (b.criadoEm || '').localeCompare(a.criadoEm || '')));
  applySnapshot(fresh);
  await writeCache();
  const { data: adm } = await sb.from('admins').select('user_id').eq('user_id', uid).maybeSingle();
  state.isAdmin = !!adm;
  return { offline: false, empty: data.length === 0 };
}
function applySnapshot(s) {
  COLLECTIONS.forEach((c) => (state[c] = Array.isArray(s[c]) ? s[c] : []));
  state.settings = { ...DEFAULT_SETTINGS, ...(s.settings || {}) };
  delete state.settings.apiKey;
}

let flushT;
export function save(collection) {
  dirty.add(collection);
  writeCache();
  clearTimeout(flushT);
  flushT = setTimeout(flush, 700);
}

export async function flush() {
  if (!state.user || state.syncing || !dirty.size) return;
  state.syncing = true;
  const cols = [...dirty];
  dirty.clear();
  try {
    for (const c of cols) {
      const prev = synced[c] || (synced[c] = new Map());
      const items = c === 'settings' ? [{ id: 'main', ...state.settings }] : state[c];
      const upserts = [], seen = new Set();
      for (const it of items) {
        const json = JSON.stringify(c === 'settings' ? { ...state.settings } : it);
        seen.add(it.id);
        if (prev.get(it.id) !== json) upserts.push({ colecao: c, id: it.id, conteudo: JSON.parse(json), atualizado_em: new Date().toISOString() });
      }
      const removed = [...prev.keys()].filter((id) => !seen.has(id));
      if (upserts.length) {
        const { error } = await sb.from('itens').upsert(upserts.map((u) => ({ ...u, user_id: state.user.id })));
        if (error) throw error;
        upserts.forEach((u) => prev.set(u.id, JSON.stringify(u.conteudo)));
      }
      if (removed.length) {
        const { error } = await sb.from('itens').delete().eq('colecao', c).in('id', removed);
        if (error) throw error;
        removed.forEach((id) => prev.delete(id));
      }
    }
    window.dispatchEvent(new CustomEvent('sync', { detail: 'ok' }));
  } catch (e) {
    console.warn('sync', e);
    cols.forEach((c) => dirty.add(c));
    window.dispatchEvent(new CustomEvent('sync', { detail: 'erro' }));
    clearTimeout(flushT);
    flushT = setTimeout(flush, 15000);
  } finally {
    state.syncing = false;
    state.pending = dirty.size;
  }
}
window.addEventListener('online', () => flush());
document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') flush(); });

// ---------- Itens ----------
export const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
export const find = (c, id) => state[c].find((x) => x.id === id);
export function add(c, obj) {
  const item = { id: uid(), criadoEm: new Date().toISOString(), ...obj };
  state[c].unshift(item);
  save(c);
  return item;
}
export function remove(c, id) {
  state[c] = state[c].filter((x) => x.id !== id);
  save(c);
}

// ---------- Conta ----------
export async function currentUser() {
  const { data } = await sb.auth.getSession();
  state.user = data.session?.user || null;
  return state.user;
}
export async function signIn(email, password) {
  const { data, error } = await sb.auth.signInWithPassword({ email, password });
  if (error) throw error;
  state.user = data.user;
}
export async function signUp(email, password, nome) {
  const { data, error } = await sb.auth.signUp({
    email, password,
    options: { data: { nome }, emailRedirectTo: location.origin + location.pathname },
  });
  if (error) throw error;
  return { needsConfirm: !data.session, user: data.user };
}
export async function resetPassword(email) {
  const { error } = await sb.auth.resetPasswordForEmail(email, { redirectTo: location.origin + location.pathname });
  if (error) throw error;
}
export async function updatePassword(password) {
  const { error } = await sb.auth.updateUser({ password });
  if (error) throw error;
}
export async function signOut() {
  await flush();
  await sb.auth.signOut();
  state.user = null;
  state.isAdmin = false;
}
export function authErrorMsg(e) {
  const m = (e?.message || '').toLowerCase();
  if (m.includes('database error') || m.includes('convite')) return 'Esse e-mail ainda não foi convidado. Peça para a administradora liberar seu acesso.';
  if (m.includes('invalid login')) return 'E-mail ou senha incorretos.';
  if (m.includes('email not confirmed')) return 'Confirme seu e-mail pelo link que enviamos antes de entrar.';
  if (m.includes('already registered') || m.includes('already been registered')) return 'Esse e-mail já tem conta. Use "Entrar".';
  if (m.includes('password') && m.includes('characters')) return 'A senha precisa ter pelo menos 6 caracteres.';
  if (m.includes('rate limit') || m.includes('too many')) return 'Muitas tentativas. Espere alguns minutos.';
  if (m.includes('failed to fetch') || m.includes('network')) return 'Sem conexão com o servidor. Confira a internet.';
  return e?.message || 'Algo deu errado.';
}

// ---------- Convites (administradora) ----------
export async function listConvites() {
  const { data, error } = await sb.from('convites').select('email,criado_em,usado_em').order('criado_em', { ascending: false });
  if (error) throw error;
  return data;
}
export async function addConvite(email) {
  const { error } = await sb.from('convites').insert({ email: email.trim().toLowerCase() });
  if (error) throw error;
}
export async function removeConvite(email) {
  const { error } = await sb.from('convites').delete().eq('email', email);
  if (error) throw error;
}

// ---------- Dados da versão anterior (só no aparelho) ----------
export async function legacyLocalData() {
  const has = await cacheGet('marcas');
  if (has === undefined) return null;
  const s = {};
  for (const c of COLLECTIONS) s[c] = (await cacheGet(c)) || [];
  s.settings = (await cacheGet('settings')) || {};
  const total = COLLECTIONS.reduce((n, c) => n + s[c].length, 0);
  return total ? s : null;
}
export async function importLegacy(s) {
  if (s.settings?.apiKey && !getApiKey()) setApiKey(s.settings.apiKey);
  COLLECTIONS.forEach((c) => {
    const ids = new Set(state[c].map((x) => x.id));
    state[c] = [...state[c], ...(s[c] || []).filter((x) => !ids.has(x.id))];
    save(c);
  });
  await dropLegacy();
}
export async function dropLegacy() {
  for (const k of [...COLLECTIONS, 'settings', 'seeded']) await cacheDel(k);
}

// Portfólio inicial da administradora (as marcas que já estão no portfólio)
export function seedPortfolio() {
  const now = new Date().toISOString();
  const p = (marca, temVideo, notas = '') => ({ id: uid(), criadoEm: now, marca, temVideo, linkVideo: '', logoOk: true, noSite: true, noPdf: true, notas });
  const falta = 'Falta o vídeo para entrar em "marcas e lojas que já gravei".';
  state.portfolio = [p('Simple', true), p('LUX', true), p('Letty', false, falta), p('By Gold Spell Co.', false, falta), p('Forever Liss', false, falta)];
  save('portfolio');
}

// ---------- Backup ----------
export function exportJSON() {
  return JSON.stringify({ app: 'sol-content-hub', versao: 2, exportadoEm: new Date().toISOString(), ...snapshot() }, null, 2);
}
export async function importJSON(text) {
  const data = JSON.parse(text);
  if (data.app !== 'sol-content-hub') throw new Error('Esse arquivo não é um backup do Sol Content Hub.');
  COLLECTIONS.forEach((c) => { state[c] = Array.isArray(data[c]) ? data[c] : []; save(c); });
  state.settings = { ...DEFAULT_SETTINGS, ...(data.settings || {}) };
  delete state.settings.apiKey;
  save('settings');
  await flush();
}
