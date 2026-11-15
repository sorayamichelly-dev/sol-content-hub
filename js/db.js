// Armazenamento local (IndexedDB). Tudo fica salvo no próprio aparelho.
const DB_NAME = 'sol-hub';
const STORE = 'kv';
const COLLECTIONS = ['marcas', 'ideias', 'eventos', 'roteiros', 'propostas', 'videos', 'portfolio'];

let dbp;
function openDB() {
  if (!dbp) {
    dbp = new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, 1);
      req.onupgradeneeded = () => req.result.createObjectStore(STORE);
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }
  return dbp;
}
async function idbGet(key) {
  const db = await openDB();
  return new Promise((res, rej) => {
    const r = db.transaction(STORE).objectStore(STORE).get(key);
    r.onsuccess = () => res(r.result);
    r.onerror = () => rej(r.error);
  });
}
async function idbSet(key, val) {
  const db = await openDB();
  return new Promise((res, rej) => {
    const tx = db.transaction(STORE, 'readwrite');
    tx.objectStore(STORE).put(val, key);
    tx.oncomplete = () => res();
    tx.onerror = () => rej(tx.error);
  });
}

export const state = { settings: {} };
COLLECTIONS.forEach((c) => (state[c] = []));

const DEFAULT_SETTINGS = {
  apiKey: '',
  model: 'claude-opus-5-5',
  effort: 'medium',
  sobre: '',
  portfolioSite: '',
  portfolioPdf: '',
  theme: 'auto',
};

export async function loadAll() {
  let usable = true;
  try {
    for (const c of COLLECTIONS) state[c] = (await idbGet(c)) || [];
    state.settings = { ...DEFAULT_SETTINGS, ...((await idbGet('settings')) || {}) };
  } catch (e) {
    console.error(e);
    usable = false;
    state.settings = { ...DEFAULT_SETTINGS };
  }
  if (usable && !(await idbGet('seeded'))) {
    seed();
    await saveAll();
    await idbSet('seeded', true);
  }
  return usable;
}

const timers = {};
export function save(collection) {
  clearTimeout(timers[collection]);
  timers[collection] = setTimeout(() => {
    idbSet(collection, collection === 'settings' ? state.settings : state[collection]).catch((e) => {
      console.error(e);
      window.dispatchEvent(new CustomEvent('save-error'));
    });
  }, 250);
}
export async function saveAll() {
  for (const c of COLLECTIONS) await idbSet(c, state[c]);
  await idbSet('settings', state.settings);
}

export const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 8);

export function find(collection, id) {
  return state[collection].find((x) => x.id === id);
}
export function add(collection, obj) {
  const item = { id: uid(), criadoEm: new Date().toISOString(), ...obj };
  state[collection].unshift(item);
  save(collection);
  return item;
}
export function remove(collection, id) {
  state[collection] = state[collection].filter((x) => x.id !== id);
  save(collection);
}

// Backup
export function exportJSON() {
  const data = { app: 'sol-content-hub', versao: 1, exportadoEm: new Date().toISOString(), settings: { ...state.settings, apiKey: '' } };
  COLLECTIONS.forEach((c) => (data[c] = state[c]));
  return JSON.stringify(data, null, 2);
}
export async function importJSON(text) {
  const data = JSON.parse(text);
  if (data.app !== 'sol-content-hub') throw new Error('Esse arquivo não é um backup do Sol Content Hub.');
  COLLECTIONS.forEach((c) => (state[c] = Array.isArray(data[c]) ? data[c] : []));
  const key = state.settings.apiKey;
  state.settings = { ...DEFAULT_SETTINGS, ...(data.settings || {}), apiKey: key };
  await saveAll();
}

// Dados iniciais: as marcas que já estão no portfólio (vindas da conversa "Portfólio UGC").
function seed() {
  const now = new Date().toISOString();
  const p = (marca, temVideo, notas = '') => ({
    id: uid(), criadoEm: now, marca, temVideo, linkVideo: '', logoOk: true, noSite: true, noPdf: true, notas,
  });
  state.portfolio = [
    p('Simple', true),
    p('LUX', true),
    p('Letty', false, 'Falta o vídeo para entrar em "marcas e lojas que já gravei".'),
    p('By Gold Spell Co.', false, 'Falta o vídeo para entrar em "marcas e lojas que já gravei".'),
    p('Forever Liss', false, 'Falta o vídeo para entrar em "marcas e lojas que já gravei".'),
  ];
}
