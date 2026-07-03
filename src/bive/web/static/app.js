// BIVE minimal conversational console.
// One input -> one readable answer. Safe DOM only — no dynamic HTML injection. The operational
// surface (gates, science registry, product readiness, raw JSON/Markdown export)
// lives in a collapsed drawer for power users and loads lazily when opened.

const el = (selector) => document.querySelector(selector);
const make = (tag, className = '') => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  return node;
};
const clear = (node) => {
  while (node.firstChild) node.removeChild(node.firstChild);
};
const text = (node, value) => {
  node.textContent = String(value ?? '');
};

const API_VERSION = '2026-06-11';
const MAX_UPLOAD_BYTES = 25_000_000;
const KNOWN_EXTENSIONS = ['json', 'jsonl', 'srt', 'vtt', 'csv', 'txt'];
const MEDIA_EXTENSIONS = ['mp3', 'wav', 'm4a', 'aac', 'ogg', 'flac', 'mp4', 'mov', 'mkv', 'webm', 'avi'];

const thread = el('#thread');
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

let pendingFile = null;
let lastOutput = {};
let lastMarkdown = '';
let lastReportId = '';
let contractsLoaded = false;

const STATUS_LABEL = {
  review_required: {label: 'Потрібна перевірка', tone: 'warn'},
  elevated_risk: {label: 'Підвищений ризик', tone: 'bad'},
  low_risk: {label: 'Низький ризик', tone: 'good'},
  inconclusive: {label: 'Недостатньо даних', tone: 'muted'},
  invalid_input: {label: 'Некоректний ввід', tone: 'bad'},
};

const HYP_LABEL = {
  inconsistency_risk: 'Непослідовність',
  manipulation_risk: 'Маніпуляція',
  cognitive_load_risk: 'Когнітивне навантаження',
  evidence_gap_risk: 'Брак доказів',
};

const SAMPLES = {
  contradiction:
    'subject: Я ніколи не отримував ці кошти, повірте, перевіряти немає потреби.\n' +
    'subject: Я отримав ці кошти пізніше, але це очевидно була не моя відповідальність.',
  pressure:
    'subject: Trust me, nobody needs to check this today.\n' +
    'subject: You must believe me, there is no need to verify anything.',
};

function setStatus(message, mode = 'neutral') {
  text(statusText, message);
  statusText.dataset.mode = mode;
}

// --- API token: session-bounded only (never persisted to disk). ---
const SESSION_TOKEN_KEY = 'bive_api_token';

function persistSessionToken() {
  const value = apiToken.value.trim();
  if (value) sessionStorage.setItem(SESSION_TOKEN_KEY, value);
  else sessionStorage.removeItem(SESSION_TOKEN_KEY);
}

function clearSessionToken() {
  sessionStorage.removeItem(SESSION_TOKEN_KEY);
  apiToken.value = '';
}

function authHeaders() {
  const token = apiToken.value.trim();
  return token ? {'x-bive-api-key': token} : {};
}

// Accept a token passed via ?api-token= once, then scrub it from the URL so it
// is never retained in history, bookmarks or referrer headers.
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
  const joiner = path.includes('?') ? '&' : '?';
  return `${path}${joiner}api-version=${encodeURIComponent(API_VERSION)}`;
}

async function fetchJson(url, options = {}) {
  const headers = {accept: 'application/json', ...(options.headers || {}), ...authHeaders()};
  const response = await fetch(url, {...options, headers});
  const requestId = response.headers.get('x-request-id') || 'missing-request-id';
  let data;
  try {
    data = await response.json();
  } catch (error) {
    data = {error: 'non_json_response', details: [error.message]};
  }
  if (!response.ok) {
    if (response.status === 401) clearSessionToken();
    const code = (data.error && (data.error.code || data.error)) || `http_${response.status}`;
    const detail = data.error && data.error.details && data.error.details[0];
    const error = new Error(detail ? `${code}: ${detail}` : `${code}`);
    error.code = typeof code === 'string' ? code : '';
    throw error;
  }
  return {data, requestId};
}

async function fetchText(url, options = {}) {
  const headers = {accept: 'text/plain', ...(options.headers || {}), ...authHeaders()};
  const response = await fetch(url, {...options, headers});
  if (!response.ok) throw new Error(`http_${response.status}`);
  return await response.text();
}

// --- Thread rendering (assistant/user messages) ---

function dismissIntro() {
  const intro = thread.querySelector('.msg-intro');
  if (intro) intro.remove();
}

function addUserMessage(label) {
  dismissIntro();
  const msg = make('article', 'msg msg-user');
  const bubble = make('div', 'bubble');
  text(bubble, label);
  msg.append(bubble);
  thread.append(msg);
  scrollThread();
}

function addNoticeMessage(title, body, tone = 'muted') {
  dismissIntro();
  const msg = make('article', 'msg msg-assistant');
  const card = make('div', `answer answer-${tone}`);
  const h = make('p', 'answer-verdict');
  text(h, title);
  card.append(h);
  if (body) {
    const p = make('p', 'answer-line');
    text(p, body);
    card.append(p);
  }
  msg.append(card);
  thread.append(msg);
  scrollThread();
}

function scrollThread() {
  thread.scrollTop = thread.scrollHeight;
  const last = thread.lastElementChild;
  if (last && last.scrollIntoView) last.scrollIntoView({behavior: 'smooth', block: 'end'});
}

function section(parent, title) {
  const wrap = make('div', 'answer-section');
  const h = make('p', 'answer-section-title');
  text(h, title);
  wrap.append(h);
  parent.append(wrap);
  return wrap;
}

function describeEvent(event) {
  const feature = event.feature || event.event_type || 'signal';
  const value = event.value;
  if (feature === 'local_claim_tension' && value && typeof value === 'object') {
    return {kind: 'Суперечність', detail: `«${value.claim_a}» ↔ «${value.claim_b}»`, tone: 'bad'};
  }
  if (feature === 'absolute_framing') {
    return {kind: 'Абсолютне формулювання', detail: 'категоричні слова (ніколи/завжди/очевидно)', tone: 'warn'};
  }
  if (feature === 'verification_pressure') {
    return {kind: 'Тиск проти перевірки', detail: 'мова відмовляє перевіряти («повір мені»)', tone: 'warn'};
  }
  if (feature === 'linguistic_hedging') {
    return {kind: 'Хеджування', detail: 'ознаки невпевненості («можливо», «здається»)', tone: 'muted'};
  }
  if (feature === 'temporal_anchor') {
    return {kind: 'Часовий маркер', detail: 'згадка часу — перевір таймлайн', tone: 'muted'};
  }
  return {kind: feature, detail: typeof value === 'string' ? value : '', tone: 'muted'};
}

// Main answer renderer (name kept for the frontend-quality contract).
function renderReport(data) {
  const report = data.report || data;
  lastReportId = report.report_id || data.report_id || '';
  lastOutput = data;
  text(output, JSON.stringify(data, null, 2));

  const status = report.final_status || data.status || 'inconclusive';
  const meta = STATUS_LABEL[status] || {label: status, tone: 'muted'};
  const events = (report.evidence_events || []).slice();
  const hypotheses = (report.hypotheses || []).filter((h) => (h.score || 0) > 0);
  const questions = report.verification_questions || [];
  const summary = report.input_summary || {};

  dismissIntro();
  const msg = make('article', 'msg msg-assistant');
  const card = make('div', `answer answer-${meta.tone}`);

  const verdict = make('p', 'answer-verdict');
  text(verdict, meta.label);
  card.append(verdict);

  const line = make('p', 'answer-line');
  const claims = summary.claims ?? (report.claims || []).length;
  const evCount = events.length;
  text(
    line,
    data.detected_format
      ? `Формат ${data.detected_format}. Витягнуто ${claims} тверджень і ${evCount} evidence-подій.`
      : `Витягнуто ${claims} тверджень і ${evCount} evidence-подій.`
  );
  card.append(line);

  // Findings — contradictions first, then linguistic risk signals.
  events.sort((a, b) => (a.feature === 'local_claim_tension' ? -1 : 0) - (b.feature === 'local_claim_tension' ? -1 : 0));
  if (events.length) {
    const sec = section(card, 'Що знайдено');
    events.slice(0, 8).forEach((event) => {
      const described = describeEvent(event);
      const item = make('div', `finding finding-${described.tone}`);
      const k = make('span', 'finding-kind');
      text(k, described.kind);
      const d = make('span', 'finding-detail');
      text(d, described.detail);
      item.append(k, d);
      sec.append(item);
    });
  }

  // Risk hypotheses as labelled meters.
  if (hypotheses.length) {
    const sec = section(card, 'Оцінка ризику');
    hypotheses
      .sort((a, b) => (b.score || 0) - (a.score || 0))
      .slice(0, 4)
      .forEach((h) => {
        const row = make('div', 'hyp-row');
        const name = make('span', 'hyp-name');
        text(name, HYP_LABEL[h.label] || h.label);
        const meter = make('div', 'hyp-meter');
        const fill = make('div', 'hyp-fill');
        fill.style.width = `${Math.round((h.score || 0) * 100)}%`;
        fill.dataset.tone = (h.score || 0) >= 0.6 ? 'bad' : (h.score || 0) >= 0.4 ? 'warn' : 'good';
        meter.append(fill);
        const val = make('span', 'hyp-val');
        text(val, `${Math.round((h.score || 0) * 100)}% · невизначеність ${Math.round((h.uncertainty || 0) * 100)}%`);
        row.append(name, meter, val);
        sec.append(row);
      });
  }

  // Human-review questions.
  if (questions.length) {
    const sec = section(card, 'Питання для перевірки');
    const list = make('ul', 'q-list');
    questions.slice(0, 6).forEach((q) => {
      const li = make('li');
      text(li, typeof q === 'string' ? q : q.question || '');
      list.append(li);
    });
    sec.append(list);
  }

  const note = make('p', 'answer-note');
  text(note, 'Це поверхня для аналізу, а не вирок про людину. Рішення потребує людської перевірки й зовнішніх джерел.');
  card.append(note);

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
  } catch (error) {
    text(markdownOutput, `markdown недоступний: ${error.message}`);
  }
}

// --- Submission ---

function fileExtension(name) {
  const dot = name.lastIndexOf('.');
  return dot >= 0 ? name.slice(dot + 1).toLowerCase() : '';
}

// Pasted BIVE JSON ({subject_scope, segments:[...]}) goes to the strict
// structured endpoint; everything else (SRT, VTT, CSV, plain text, ASR JSON)
// goes through the auto-detecting upload endpoint.
function structuredPayload(raw) {
  const trimmed = raw.trimStart();
  if (trimmed[0] !== '{') return null;
  try {
    const parsed = JSON.parse(raw);
    if (parsed && Array.isArray(parsed.segments)) return parsed;
  } catch (error) {
    return null;
  }
  return null;
}

async function analyzeText(raw) {
  addUserMessage(raw.length > 240 ? `${raw.slice(0, 240)}…` : raw);
  setStatus('Аналізую…', 'busy');
  const structured = structuredPayload(raw);
  const request = structured
    ? {url: '/api/v1/reports/from-transcript', body: JSON.stringify(structured), type: 'application/json'}
    : {url: '/api/v1/reports/from-upload', body: raw, type: 'text/plain; charset=utf-8'};
  const {data} = await fetchJson(apiUrl(request.url), {
    method: 'POST',
    headers: {'content-type': request.type},
    body: request.body,
  });
  renderReport(data);
  setStatus('Готово.', 'ok');
  refreshStatus();
}

async function analyzeFile(file) {
  const ext = fileExtension(file.name);
  addUserMessage(`📎 ${file.name}`);
  if (MEDIA_EXTENSIONS.includes(ext)) {
    addNoticeMessage(
      'Аудіо/відео потребує транскрипції',
      'BIVE аналізує текст. Транскрибуй запис у текст (напр. Whisper: `whisper запис.mp3 --output_format srt`) і завантаж отриманий SRT / VTT / JSON — розбір буде миттєвим.',
      'muted'
    );
    setStatus('Потрібен транскрипт.', 'neutral');
    return;
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    addNoticeMessage('Файл завеликий', `${(file.size / 1e6).toFixed(1)}MB перевищує ліміт 25MB.`, 'bad');
    return;
  }
  setStatus(`Аналізую ${file.name}…`, 'busy');
  const content = await file.text();
  let url = apiUrl('/api/v1/reports/from-upload');
  if (KNOWN_EXTENSIONS.includes(ext)) url += `&format=${encodeURIComponent(ext)}`;
  const {data} = await fetchJson(url, {
    method: 'POST',
    headers: {'content-type': 'text/plain; charset=utf-8', 'x-bive-filename': encodeURIComponent(file.name)},
    body: content,
  });
  renderReport(data);
  setStatus(`Готово · ${data.detected_format || ext}.`, 'ok');
  refreshStatus();
}

async function submit() {
  try {
    if (pendingFile) {
      const file = pendingFile;
      setPendingFile(null);
      await analyzeFile(file);
      return;
    }
    const raw = payload.value.trim();
    if (!raw) {
      setStatus('Порожньо. Встав текст або додай файл.', 'error');
      return;
    }
    payload.value = '';
    autoGrow();
    await analyzeText(raw);
  } catch (error) {
    addNoticeMessage('Не вдалося обробити', humanError(error), 'bad');
    setStatus(error.message, 'error');
  }
}

function humanError(error) {
  const code = error.code || '';
  if (code.startsWith('transcript_parse_error')) return 'Не вдалося розпізнати формат даних. Спробуй SRT, VTT, CSV, TXT або JSON.';
  if (code === 'empty_upload') return 'Порожні дані.';
  if (code === 'invalid_utf8') return 'Файл не є текстом (схоже на бінарні дані). Для аудіо/відео спершу зроби транскрипцію.';
  if (code === 'too_many_segments') return 'Забагато сегментів для одного запуску.';
  if (code === 'authentication_required') return 'Потрібен API token (див. розділ «Система»).';
  return error.message;
}

// --- Attach / drag-drop ---

function setPendingFile(file) {
  pendingFile = file;
  text(attachName, file ? file.name : '');
  el('#composer').dataset.hasFile = file ? 'true' : 'false';
}

function autoGrow() {
  payload.style.height = 'auto';
  payload.style.height = `${Math.min(payload.scrollHeight, 220)}px`;
}

// --- System surface (lazy) ---

async function refreshStatus() {
  try {
    const {data} = await fetchJson(apiUrl('/api/v1/system/status'));
    text(systemReadiness, data.readiness === 'ready' ? 'готово' : 'не готово');
    statusDot.dataset.ready = data.readiness === 'ready' ? 'true' : 'false';
    text(drawerMeta, `${data.storage.report_count} звітів · ${data.limits.auth_required ? 'auth' : 'local'}`);
    renderGates(data.gates || []);
  } catch (error) {
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
  gates.forEach((gate) => {
    const row = make('div', 'gate-row');
    const name = make('span');
    text(name, gate.name);
    const status = make('b');
    text(status, gate.last_observed);
    status.dataset.status = gate.last_observed;
    row.append(name, status);
    gatesList.append(row);
  });
}

function renderScienceRegistry(data) {
  clear(scienceList);
  (data.disciplines || []).forEach((d) => {
    const tag = make('span', 'tag');
    text(tag, d.name);
    scienceList.append(tag);
  });
  clear(scienceBoundary);
  (data.hard_boundaries || []).slice(0, 4).forEach((b) => {
    const item = make('div', 'mini-item');
    text(item, b);
    scienceBoundary.append(item);
  });
}

function renderProductReadiness(data) {
  clear(productReadiness);
  const rows = [
    ['Стадія', data.stage || 'unknown'],
    ['Статус', data.overall_status || 'unknown'],
    ['Блокери', (data.blocking_unknowns || []).join(' · ') || 'немає'],
  ];
  rows.forEach(([k, v]) => {
    const item = make('div', 'mini-item');
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
  } catch (error) {
    contractsLoaded = false;
  }
}

// --- Wiring ---

el('#composerForm').addEventListener('submit', (event) => {
  event.preventDefault();
  submit();
});

payload.addEventListener('input', autoGrow);
payload.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
    event.preventDefault();
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
['dragenter', 'dragover'].forEach((name) => {
  composer.addEventListener(name, (event) => {
    event.preventDefault();
    composer.dataset.drag = 'true';
  });
});
['dragleave', 'dragend', 'drop'].forEach((name) => {
  composer.addEventListener(name, () => {
    composer.dataset.drag = 'false';
  });
});
composer.addEventListener('drop', (event) => {
  event.preventDefault();
  const file = event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files[0];
  if (file) {
    setPendingFile(file);
    submit();
  }
});

document.querySelectorAll('.chip[data-sample]').forEach((chip) => {
  chip.addEventListener('click', () => {
    payload.value = SAMPLES[chip.dataset.sample] || '';
    autoGrow();
    payload.focus();
  });
});

el('#saveToken').addEventListener('click', () => {
  persistSessionToken();
  setStatus('Token збережено лише на цю сесію.', 'ok');
});

el('.system-drawer').addEventListener('toggle', (event) => {
  if (event.target.open) loadContracts();
});

el('#copyOutput').addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(JSON.stringify(lastOutput, null, 2));
    setStatus('JSON скопійовано.', 'ok');
  } catch (error) {
    setStatus(`Clipboard: ${error.message}`, 'error');
  }
});

el('#copyMarkdown').addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(lastMarkdown || markdownOutput.textContent);
    setStatus('Markdown скопійовано.', 'ok');
  } catch (error) {
    setStatus(`Clipboard: ${error.message}`, 'error');
  }
});

el('#downloadOutput').addEventListener('click', () => {
  const blob = new Blob([JSON.stringify(lastOutput, null, 2)], {type: 'application/json'});
  const href = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = href;
  link.download = `${lastReportId || 'bive-report'}.json`;
  link.click();
  URL.revokeObjectURL(href);
  setStatus('JSON завантажується.', 'ok');
});

const savedToken = sessionStorage.getItem(SESSION_TOKEN_KEY);
if (savedToken) apiToken.value = savedToken;
captureUrlToken();
autoGrow();
refreshStatus();
