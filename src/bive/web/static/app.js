// BIVE console — one input, one report. Vanilla, dependency-free, safe DOM only:
// nodes are built via createElement / createElementNS and textContent, never via
// raw HTML string injection. Operational surface lives in a lazy drawer.

const SVGNS = 'http://www.w3.org/2000/svg';
const el = (s) => document.querySelector(s);
const make = (tag, className = '') => {
  const n = document.createElement(tag);
  if (className) n.className = className;
  return n;
};
const clear = (n) => {
  while (n.firstChild) n.removeChild(n.firstChild);
};
const text = (n, v) => {
  n.textContent = String(v ?? '');
};
const svg = (tag, attrs = {}) => {
  const n = document.createElementNS(SVGNS, tag);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, String(v));
  return n;
};

const API_VERSION = '2026-06-11';
const MAX_UPLOAD_BYTES = 100_000_000;
const KNOWN_EXTENSIONS = ['json', 'jsonl', 'srt', 'vtt', 'csv', 'txt'];
const MEDIA_EXTENSIONS = ['mp3', 'wav', 'm4a', 'aac', 'ogg', 'flac', 'mp4', 'mov', 'mkv', 'webm', 'avi'];

const thread = el('#thread');
const hero = el('#hero');
const payload = el('#payload');
const fileInput = el('#fileInput');
const attachName = el('#attachName');
const statusText = el('#statusText');
const statusDot = el('#statusDot');
const systemReadiness = el('#systemReadiness');
const drawerMeta = el('#drawerMeta');
const apiToken = el('#apiToken');
const output = el('#output');
const markdownOutput = el('#markdownOutput');
const gatesList = el('#gatesList');
const scienceList = el('#scienceList');
const scienceBoundary = el('#scienceBoundary');
const productReadiness = el('#productReadiness');
const sendBtn = el('#send');

let pendingFile = null;
let lastOutput = {};
let lastMarkdown = '';
let lastReportId = '';
let contractsLoaded = false;
let busy = false;

const STATUS = {
  review_required: {label: 'Потрібна перевірка', tone: 'warn'},
  elevated_risk: {label: 'Підвищений ризик', tone: 'bad'},
  low_risk: {label: 'Низький ризик', tone: 'good'},
  inconclusive: {label: 'Недостатньо даних', tone: 'muted'},
  invalid_input: {label: 'Некоректний ввід', tone: 'bad'},
};

const HYP = {
  inconsistency_risk: 'Непослідовність',
  manipulation_risk: 'Маніпуляція',
  cognitive_load_risk: 'Когнітивне навантаження',
  evidence_gap_risk: 'Брак доказів',
};

const ICONS = {
  contradiction: ['M3 9h12l-4-4', 'M21 15H9l4 4'],
  absolute: ['M12 3l9 16H3z', 'M12 9v5', 'M12 17h.01'],
  pressure: ['M12 3l7 3v5c0 4-3 7-7 9-4-2-7-5-7-9V6z'],
  hedging: ['M3 13c2-3 4-3 6 0s4 3 6 0 4-3 6 0'],
  temporal: ['M12 4a8 8 0 100 16 8 8 0 000-16z', 'M12 8v4l3 2'],
  signal: ['M12 5v14', 'M5 12h14'],
  check: ['M20 6L9 17l-5-5'],
};

function iconEl(name) {
  const node = svg('svg', {viewBox: '0 0 24 24', 'aria-hidden': 'true', focusable: 'false'});
  for (const d of ICONS[name] || ICONS.signal) {
    node.append(svg('path', {d, fill: 'none', stroke: 'currentColor', 'stroke-width': 1.8, 'stroke-linecap': 'round', 'stroke-linejoin': 'round'}));
  }
  return node;
}

const SAMPLES = {
  contradiction:
    'subject: Я ніколи не отримував ці кошти, повірте, перевіряти немає потреби.\n' +
    'subject: Я отримав ці кошти пізніше, але це очевидно була не моя відповідальність.',
  pressure:
    'subject: Повір мені, зараз нікому не треба це перевіряти.\n' +
    'subject: Ти мусиш просто прийняти це — жодної потреби щось звіряти немає.',
};

function setStatus(message, mode = 'neutral') {
  text(statusText, message);
  statusText.dataset.mode = mode;
}

// --- Session-bounded API token ---
const SESSION_TOKEN_KEY = 'bive_api_token';
function persistSessionToken() {
  const v = apiToken.value.trim();
  if (v) sessionStorage.setItem(SESSION_TOKEN_KEY, v);
  else sessionStorage.removeItem(SESSION_TOKEN_KEY);
}
function clearSessionToken() {
  sessionStorage.removeItem(SESSION_TOKEN_KEY);
  apiToken.value = '';
}
function authHeaders() {
  const t = apiToken.value.trim();
  return t ? {'x-bive-api-key': t} : {};
}
function captureUrlToken() {
  const params = new URLSearchParams(window.location.search);
  const urlToken = params.get('api-token');
  if (!urlToken) return;
  apiToken.value = urlToken.trim();
  persistSessionToken();
  params.delete('api-token');
  const scrubbed = params.toString();
  const next = window.location.pathname + (scrubbed ? `?${scrubbed}` : '') + window.location.hash;
  window.history.replaceState({}, document.title, next);
}

function apiUrl(path) {
  const j = path.includes('?') ? '&' : '?';
  return `${path}${j}api-version=${encodeURIComponent(API_VERSION)}`;
}

async function fetchJson(url, options = {}) {
  const headers = {accept: 'application/json', ...(options.headers || {}), ...authHeaders()};
  const response = await fetch(url, {...options, headers});
  const requestId = response.headers.get('x-request-id') || '';
  let data;
  try {
    data = await response.json();
  } catch (e) {
    data = {error: 'non_json_response'};
  }
  if (!response.ok) {
    if (response.status === 401) clearSessionToken();
    const code = (data.error && (data.error.code || data.error)) || `http_${response.status}`;
    const detail = data.error && data.error.details && data.error.details[0];
    const err = new Error(detail ? `${code}: ${detail}` : `${code}`);
    err.code = typeof code === 'string' ? code : '';
    throw err;
  }
  return {data, requestId};
}

async function fetchText(url, options = {}) {
  const headers = {accept: 'text/plain', ...(options.headers || {}), ...authHeaders()};
  const response = await fetch(url, {...options, headers});
  if (!response.ok) throw new Error(`http_${response.status}`);
  return await response.text();
}

// --- Thread primitives ---

function dismissHero() {
  if (hero && hero.parentNode) hero.remove();
}
function scrollThread() {
  const last = thread.lastElementChild;
  if (last && last.scrollIntoView) last.scrollIntoView({behavior: 'smooth', block: 'end'});
}
function addUserMessage(label) {
  dismissHero();
  const msg = make('article', 'msg msg--user');
  const bubble = make('div', 'bubble');
  text(bubble, label);
  msg.append(bubble);
  thread.append(msg);
  scrollThread();
}
function addSkeleton() {
  dismissHero();
  const sk = make('div', 'skeleton');
  ['w40', 'w80', 'w60', 'w80'].forEach((w) => sk.append(make('div', `sk-line ${w}`)));
  thread.append(sk);
  scrollThread();
  return sk;
}
function addNotice(title, body, tone = 'muted') {
  dismissHero();
  const msg = make('article', 'msg');
  const card = make('div', 'report');
  card.dataset.tone = tone;
  const head = make('div', 'report__head');
  const v = make('div', 'verdict');
  v.append(make('span', 'verdict__badge'));
  const box = make('div');
  const h = make('h3', 'verdict__label');
  text(h, title);
  box.append(h);
  if (body) {
    const p = make('p', 'verdict__meta');
    text(p, body);
    box.append(p);
  }
  v.append(box);
  head.append(v);
  card.append(head);
  msg.append(card);
  thread.append(msg);
  scrollThread();
}

// --- Report rendering ---

function tone(status) {
  return (STATUS[status] || {tone: 'muted'}).tone;
}
function riskTone(pct) {
  return pct >= 60 ? 'bad' : pct >= 40 ? 'warn' : 'good';
}

function describeEvent(event) {
  const f = event.feature || event.event_type || 'signal';
  const value = event.value;
  if (f === 'local_claim_tension' && value && typeof value === 'object') {
    return {icon: 'contradiction', tone: 'bad', kind: 'Суперечність', quote: `«${value.claim_a}» ↔ «${value.claim_b}»`, tag: 'tension'};
  }
  if (f === 'absolute_framing') {
    return {icon: 'absolute', tone: 'warn', kind: 'Категоричне формулювання', detail: 'абсолютні слова (ніколи / завжди / очевидно) звужують перевірку', tag: 'framing'};
  }
  if (f === 'verification_pressure') {
    return {icon: 'pressure', tone: 'warn', kind: 'Тиск проти перевірки', detail: 'мова відмовляє від звіряння («повір мені»)', tag: 'pressure'};
  }
  if (f === 'linguistic_hedging') {
    return {icon: 'hedging', tone: 'muted', kind: 'Хеджування', detail: 'ознаки невпевненості («можливо», «здається»)', tag: 'hedge'};
  }
  if (f === 'temporal_anchor') {
    return {icon: 'temporal', tone: 'muted', kind: 'Часовий маркер', detail: 'згадка часу — варто звірити таймлайн', tag: 'time'};
  }
  return {icon: 'signal', tone: 'muted', kind: f, detail: typeof value === 'string' ? value : '', tag: 'signal'};
}

function shortQuote(s, n = 90) {
  const t = String(s || '').trim();
  return t.length > n ? `${t.slice(0, n)}…` : t;
}

function ukrainianQuestions(report) {
  const claims = report.claims || [];
  const hyps = report.hypotheses || [];
  const out = [];
  claims.filter((c) => (c.qualifiers || []).includes('temporal')).slice(0, 2).forEach((c) => {
    out.push(`Чи підтверджує незалежне джерело часовий маркер у: «${shortQuote(c.text)}»?`);
  });
  claims.filter((c) => (c.qualifiers || []).includes('absolute')).slice(0, 2).forEach((c) => {
    out.push(`Які докази могли б спростувати категоричне твердження: «${shortQuote(c.text)}»?`);
  });
  hyps.filter((h) => ['review_required', 'elevated_risk'].includes(h.status)).forEach((h) => {
    out.push(`Які контр-докази знизили б ризик «${HYP[h.label] || h.label}» нижче порогу перегляду?`);
  });
  if (!out.length) {
    out.push('Яке незалежне джерело підтвердило б ключове твердження без опори на поведінкові сигнали?');
  }
  return [...new Set(out)].slice(0, 6);
}

function buildGauge(pct) {
  const wrap = make('div', 'gauge');
  const s = svg('svg', {viewBox: '0 0 68 68'});
  const c = 2 * Math.PI * 30;
  s.append(svg('circle', {class: 'gauge__track', cx: 34, cy: 34, r: 30}));
  const arc = svg('circle', {class: 'gauge__arc', cx: 34, cy: 34, r: 30});
  arc.style.stroke = `var(--${riskTone(pct)})`;
  arc.setAttribute('stroke-dasharray', String(c));
  arc.setAttribute('stroke-dashoffset', String(c * (1 - pct / 100)));
  s.append(arc);
  wrap.append(s);
  const val = make('div', 'gauge__val');
  text(val, `${pct}%`);
  wrap.append(val);
  return wrap;
}

function section(card, title) {
  const sec = make('section', 'report__section');
  const h = make('h4', 'section__title');
  text(h, title);
  sec.append(h);
  card.append(sec);
  return sec;
}

// Main renderer (name kept for the frontend contract).
function renderReport(data) {
  const report = data.report || data;
  lastReportId = report.report_id || data.report_id || '';
  lastOutput = data;
  text(output, JSON.stringify(data, null, 2));

  const status = report.final_status || data.status || 'inconclusive';
  const meta = STATUS[status] || {label: status, tone: 'muted'};
  const events = (report.evidence_events || []).slice();
  const hyps = (report.hypotheses || []).filter((h) => (h.score || 0) > 0);
  const summary = report.input_summary || {};
  const claims = summary.claims ?? (report.claims || []).length;
  const topRisk = Math.round(Math.max(0, ...hyps.map((h) => h.score || 0)) * 100);

  dismissHero();
  const msg = make('article', 'msg');
  const card = make('div', 'report');
  card.dataset.tone = meta.tone;

  // Header: verdict + gauge
  const head = make('div', 'report__head');
  const verdict = make('div', 'verdict');
  verdict.append(make('span', 'verdict__badge'));
  const vbox = make('div');
  const label = make('h3', 'verdict__label');
  text(label, meta.label);
  const vmeta = make('p', 'verdict__meta');
  const fmt = data.detected_format ? ` · формат ${String(data.detected_format).toUpperCase()}` : '';
  text(vmeta, `${claims} тверджень · ${events.length} сигналів${fmt}`);
  vbox.append(label, vmeta);
  verdict.append(vbox);
  head.append(verdict);
  if (hyps.length) head.append(buildGauge(topRisk));
  card.append(head);

  // Signals
  if (events.length) {
    const sec = section(card, 'Що знайдено');
    const list = make('ul', 'signals');
    events
      .sort((a, b) => (a.feature === 'local_claim_tension' ? 0 : 1) - (b.feature === 'local_claim_tension' ? 0 : 1))
      .slice(0, 8)
      .forEach((event) => {
        const d = describeEvent(event);
        const li = make('li', 'signal');
        li.dataset.tone = d.tone;
        const ic = make('span', 'signal__icon');
        ic.append(iconEl(d.icon));
        const body = make('div', 'signal__body');
        const kind = make('span', 'signal__kind');
        text(kind, d.kind);
        body.append(kind);
        const detail = make('span', 'signal__detail');
        if (d.quote) {
          const q = make('span', 'signal__quote');
          text(q, d.quote);
          detail.append(q);
        } else {
          text(detail, d.detail || '');
        }
        body.append(detail);
        const tag = make('span', 'signal__tag');
        text(tag, d.tag);
        li.append(ic, body, tag);
        list.append(li);
      });
    sec.append(list);
  }

  // Risk meters
  if (hyps.length) {
    const sec = section(card, 'Оцінка ризику');
    const risks = make('div', 'risks');
    hyps
      .sort((a, b) => (b.score || 0) - (a.score || 0))
      .slice(0, 4)
      .forEach((h) => {
        const pct = Math.round((h.score || 0) * 100);
        const row = make('div', 'risk');
        const rhead = make('div', 'risk__head');
        const name = make('span', 'risk__name');
        text(name, HYP[h.label] || h.label);
        const val = make('span', 'risk__val');
        text(val, `${pct}% · невизначеність ${Math.round((h.uncertainty || 0) * 100)}%`);
        rhead.append(name, val);
        const track = make('div', 'risk__track');
        const fill = make('div', 'risk__fill');
        fill.dataset.tone = riskTone(pct);
        fill.style.width = `${pct}%`;
        track.append(fill);
        row.append(rhead, track);
        risks.append(row);
      });
    sec.append(risks);
  }

  // Questions (Ukrainian, derived from structured report)
  const questions = ukrainianQuestions(report);
  if (questions.length) {
    const sec = section(card, 'Питання для перевірки');
    const list = make('ul', 'questions');
    questions.forEach((q) => {
      const li = make('li', 'question');
      const mark = make('span', 'question__mark');
      mark.append(iconEl('check'));
      const t = make('span');
      text(t, q);
      li.append(mark, t);
      list.append(li);
    });
    sec.append(list);
  }

  // Footer
  const foot = make('div', 'report__foot');
  const disc = make('p', 'disclaimer');
  text(disc, 'Це аналітична поверхня, а не вирок про людину. Рішення потребує людської перевірки, контексту й зовнішніх джерел.');
  const actions = make('div', 'foot-actions');
  const copyBtn = make('button', 'btn btn--ghost');
  text(copyBtn, 'Copy JSON');
  copyBtn.type = 'button';
  copyBtn.addEventListener('click', () => copyJson());
  const dlBtn = make('button', 'btn btn--ghost');
  text(dlBtn, 'Download JSON');
  dlBtn.type = 'button';
  dlBtn.addEventListener('click', () => downloadJson());
  const mdBtn = make('button', 'btn btn--ghost');
  text(mdBtn, 'Copy Markdown');
  mdBtn.type = 'button';
  mdBtn.addEventListener('click', () => copyMarkdown());
  actions.append(copyBtn, dlBtn, mdBtn);
  foot.append(disc, actions);
  card.append(foot);

  msg.append(card);
  thread.append(msg);
  scrollThread();
  refreshMarkdown();
}

async function refreshMarkdown() {
  if (!lastReportId) return;
  try {
    lastMarkdown = await fetchText(apiUrl(`/api/v1/reports/${encodeURIComponent(lastReportId)}/markdown`));
    text(markdownOutput, lastMarkdown);
  } catch (e) {
    text(markdownOutput, `markdown недоступний: ${e.message}`);
  }
}

// --- Submission ---

function fileExtension(name) {
  const dot = name.lastIndexOf('.');
  return dot >= 0 ? name.slice(dot + 1).toLowerCase() : '';
}

function structuredPayload(raw) {
  if (raw.trimStart()[0] !== '{') return null;
  try {
    const parsed = JSON.parse(raw);
    if (parsed && Array.isArray(parsed.segments)) return parsed;
  } catch (e) {
    return null;
  }
  return null;
}

function setBusy(on) {
  busy = on;
  sendBtn.disabled = on;
}

async function analyzeText(raw) {
  addUserMessage(raw.length > 260 ? `${raw.slice(0, 260)}…` : raw);
  const sk = addSkeleton();
  setStatus('Аналізую…', 'busy');
  try {
    const structured = structuredPayload(raw);
    const req = structured
      ? {url: '/api/v1/reports/from-transcript', body: JSON.stringify(structured), type: 'application/json'}
      : {url: '/api/v1/reports/from-upload', body: raw, type: 'text/plain; charset=utf-8'};
    const {data} = await fetchJson(apiUrl(req.url), {method: 'POST', headers: {'content-type': req.type}, body: req.body});
    sk.remove();
    renderReport(data);
    setStatus('Готово.', 'ok');
    refreshStatus();
  } catch (e) {
    sk.remove();
    throw e;
  }
}

async function analyzeFile(file) {
  const ext = fileExtension(file.name);
  addUserMessage(`📎 ${file.name}`);
  if (MEDIA_EXTENSIONS.includes(ext)) {
    addNotice('Аудіо/відео потребує транскрипції', 'BIVE аналізує текст. Транскрибуй запис (напр. Whisper → SRT/JSON) і завантаж результат — розбір буде миттєвим.', 'muted');
    setStatus('Потрібен транскрипт.', 'neutral');
    return;
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    addNotice('Файл завеликий', `${(file.size / 1e6).toFixed(1)}MB перевищує ліміт 100MB.`, 'bad');
    return;
  }
  const sk = addSkeleton();
  setStatus(`Аналізую ${file.name}…`, 'busy');
  try {
    const content = await file.text();
    let url = apiUrl('/api/v1/reports/from-upload');
    if (KNOWN_EXTENSIONS.includes(ext)) url += `&format=${encodeURIComponent(ext)}`;
    const {data} = await fetchJson(url, {
      method: 'POST',
      headers: {'content-type': 'text/plain; charset=utf-8', 'x-bive-filename': encodeURIComponent(file.name)},
      body: content,
    });
    sk.remove();
    renderReport(data);
    setStatus(`Готово · ${data.detected_format || ext}.`, 'ok');
    refreshStatus();
  } catch (e) {
    sk.remove();
    throw e;
  }
}

function humanError(error) {
  const code = error.code || '';
  if (code.startsWith('transcript_parse_error')) return 'Не вдалося розпізнати формат. Спробуй SRT, VTT, CSV, TXT або JSON.';
  if (code === 'empty_upload') return 'Порожні дані.';
  if (code === 'invalid_utf8') return 'Схоже на бінарний файл. Для аудіо/відео спершу зроби транскрипцію.';
  if (code === 'too_many_segments') return 'Документ завеликий навіть після розбиття. Надішли частинами.';
  if (code === 'authentication_required') return 'Потрібен API token (розділ «Система»).';
  if (code === 'InvalidInput' || code === 'ValidationError') return 'Дані не пройшли валідацію. Спробуй менший фрагмент або інший формат.';
  return error.message;
}

async function submit() {
  if (busy) return;
  setBusy(true);
  try {
    if (pendingFile) {
      const file = pendingFile;
      setPendingFile(null);
      await analyzeFile(file);
    } else {
      const raw = payload.value.trim();
      if (!raw) {
        setStatus('Порожньо. Встав текст або додай файл.', 'error');
        return;
      }
      payload.value = '';
      autoGrow();
      await analyzeText(raw);
    }
  } catch (error) {
    addNotice('Не вдалося обробити', humanError(error), 'bad');
    setStatus(error.message, 'error');
  } finally {
    setBusy(false);
  }
}

// --- Attach / drag-drop ---

function setPendingFile(file) {
  pendingFile = file;
  text(attachName, file ? file.name : '');
  el('#composer').dataset.hasFile = file ? 'true' : 'false';
}
function autoGrow() {
  payload.style.height = 'auto';
  payload.style.height = `${Math.min(payload.scrollHeight, 200)}px`;
}

// --- Export handlers ---

async function copyJson() {
  try {
    await navigator.clipboard.writeText(JSON.stringify(lastOutput, null, 2));
    setStatus('JSON скопійовано.', 'ok');
  } catch (e) {
    setStatus(`Clipboard: ${e.message}`, 'error');
  }
}
async function copyMarkdown() {
  try {
    await navigator.clipboard.writeText(lastMarkdown || markdownOutput.textContent);
    setStatus('Markdown скопійовано.', 'ok');
  } catch (e) {
    setStatus(`Clipboard: ${e.message}`, 'error');
  }
}
function downloadJson() {
  const blob = new Blob([JSON.stringify(lastOutput, null, 2)], {type: 'application/json'});
  const href = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = href;
  link.download = `${lastReportId || 'bive-report'}.json`;
  link.click();
  URL.revokeObjectURL(href);
  setStatus('JSON завантажується.', 'ok');
}

// --- System surface (lazy) ---

async function refreshStatus() {
  try {
    const {data} = await fetchJson(apiUrl('/api/v1/system/status'));
    text(systemReadiness, data.readiness === 'ready' ? 'готово' : 'не готово');
    statusDot.dataset.ready = data.readiness === 'ready' ? 'true' : 'false';
    text(drawerMeta, `${data.storage.report_count} звітів · ${data.limits.auth_required ? 'auth' : 'local'}`);
    renderGates(data.gates || []);
  } catch (e) {
    text(systemReadiness, 'офлайн');
    statusDot.dataset.ready = 'false';
  }
}
function renderGates(gates) {
  clear(gatesList);
  if (!gates.length) {
    text(gatesList, 'немає даних');
    return;
  }
  gates.forEach((g) => {
    const row = make('div', 'gaterow');
    const name = make('span');
    text(name, g.name);
    const st = make('b');
    text(st, g.last_observed);
    st.dataset.status = g.last_observed;
    row.append(name, st);
    gatesList.append(row);
  });
}
function renderScienceRegistry(data) {
  clear(scienceList);
  (data.disciplines || []).forEach((d) => {
    const chip = make('span', 'chip');
    text(chip, d.name);
    scienceList.append(chip);
  });
  clear(scienceBoundary);
  (data.hard_boundaries || []).slice(0, 4).forEach((b) => {
    const item = make('div', 'lineitem');
    text(item, b);
    scienceBoundary.append(item);
  });
}
function renderProductReadiness(data) {
  clear(productReadiness);
  [
    ['Стадія', data.stage || 'unknown'],
    ['Статус', data.overall_status || 'unknown'],
    ['Блокери', (data.blocking_unknowns || []).join(' · ') || 'немає'],
  ].forEach(([k, v]) => {
    const item = make('div', 'lineitem');
    const b = make('b');
    text(b, `${k}: `);
    const s = make('span');
    text(s, v);
    item.append(b, s);
    productReadiness.append(item);
  });
}
async function loadContracts() {
  if (contractsLoaded) return;
  contractsLoaded = true;
  try {
    const [science, product] = await Promise.all([
      fetchJson(apiUrl('/api/v1/system/science-registry')),
      fetchJson(apiUrl('/api/v1/system/product-readiness')),
    ]);
    renderScienceRegistry(science.data);
    renderProductReadiness(product.data);
  } catch (e) {
    contractsLoaded = false;
  }
}

// --- Wiring ---

el('#composerForm').addEventListener('submit', (e) => {
  e.preventDefault();
  submit();
});
payload.addEventListener('input', autoGrow);
payload.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    submit();
  }
});
el('#attach').addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', () => {
  const file = fileInput.files && fileInput.files[0];
  if (file) setPendingFile(file);
  fileInput.value = '';
});

const composer = el('#composer');
['dragenter', 'dragover'].forEach((n) => composer.addEventListener(n, (e) => {
  e.preventDefault();
  composer.dataset.drag = 'true';
}));
['dragleave', 'dragend'].forEach((n) => composer.addEventListener(n, () => {
  composer.dataset.drag = 'false';
}));
composer.addEventListener('drop', (e) => {
  e.preventDefault();
  composer.dataset.drag = 'false';
  const file = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
  if (file) {
    setPendingFile(file);
    submit();
  }
});
document.querySelectorAll('.example[data-sample]').forEach((ex) => {
  ex.addEventListener('click', () => {
    payload.value = SAMPLES[ex.dataset.sample] || '';
    autoGrow();
    payload.focus();
  });
});
el('#saveToken').addEventListener('click', () => {
  persistSessionToken();
  setStatus('Token збережено лише на цю сесію.', 'ok');
});
el('.system').addEventListener('toggle', (e) => {
  if (e.target.open) loadContracts();
});
el('#copyOutput').addEventListener('click', copyJson);
el('#copyMarkdown').addEventListener('click', copyMarkdown);
el('#downloadOutput').addEventListener('click', downloadJson);

const savedToken = sessionStorage.getItem(SESSION_TOKEN_KEY);
if (savedToken) apiToken.value = savedToken;
captureUrlToken();
autoGrow();
refreshStatus();
