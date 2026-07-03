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
const calibrationBox = el('#calibrationBox');
const sendBtn = el('#send');

let pendingFile = null;
let lastOutput = {};
let lastMarkdown = '';
let lastReportId = '';
let lastVerifyInput = '';
let lastVerifyFilename = '';
let caseStatuses = {};
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
  linguistic_style_risk: 'Лінгвістичний стиль',
  cognitive_load_risk: 'Когнітивне навантаження',
  evidence_gap_risk: 'Брак доказів',
};

const FEATURE_LABEL = {
  local_claim_tension: 'суперечність',
  absolute_framing: 'категоричність',
  verification_pressure: 'тиск проти перевірки',
  linguistic_hedging: 'хеджування',
  temporal_anchor: 'часовий маркер',
  low_first_person_singular: 'мало самопосилань',
  low_exclusive_words: 'проста наративна структура',
  elevated_negative_emotion: 'негативні емоції',
  elevated_motion_verbs: 'дієслова руху',
  impression_management: 'керування враженням',
  cognitive_load_markers: 'когнітивне навантаження',
};

// Short human citations for the science registry reference ids.
const CITE = {
  newman_pennebaker_2003: 'Newman & Pennebaker, 2003',
  vrij_2008: 'Vrij, 2008',
  ekman_friesen_1969: 'Ekman & Friesen, 1969',
  perez_rosas_2015: 'Pérez-Rosas, 2015',
};

function citation(event) {
  const ref = event.provenance && event.provenance.parameters && event.provenance.parameters.reference;
  return ref && CITE[ref] ? CITE[ref] : '';
}

// Display order: most informative first, repetitive stylistic cues last.
const SIGNAL_PRIORITY = {
  local_claim_tension: 0,
  high_verifiability: 1,
  impression_management: 2,
  verification_pressure: 3,
  cognitive_load_markers: 4,
  low_exclusive_words: 5,
  low_first_person_singular: 6,
  elevated_negative_emotion: 7,
  elevated_motion_verbs: 8,
  absolute_framing: 9,
  linguistic_hedging: 10,
  temporal_anchor: 11,
};

const RECOMMENDATION = {
  review_required: 'Рекомендація: ручна перевірка із залученням незалежних джерел.',
  elevated_risk: 'Рекомендація: пріоритетна перевірка й активний пошук контр-доказів.',
  low_risk: 'Рекомендація: базовий контроль — критичних сигналів немає.',
  inconclusive: 'Рекомендація: додай контекст або більше матеріалу — даних замало для висновку.',
  invalid_input: 'Рекомендація: перевір формат вхідних даних.',
};

// Auto-generated plain-language summary: what was found + a recommendation.
function buildSummary(report, events, hyps, status) {
  const counts = {};
  events.forEach((e) => {
    counts[e.feature] = (counts[e.feature] || 0) + 1;
  });
  const found = Object.entries(counts)
    .filter(([f]) => FEATURE_LABEL[f])
    .sort((a, b) => b[1] - a[1])
    .map(([f, n]) => (n > 1 ? `${FEATURE_LABEL[f]} ×${n}` : FEATURE_LABEL[f]));
  const top = hyps.slice().sort((a, b) => (b.score || 0) - (a.score || 0))[0];
  const sentences = [];
  sentences.push(found.length ? `Знайдено: ${found.join(', ')}.` : 'Явних мовних сигналів не виявлено.');
  if (top && (top.score || 0) > 0) {
    sentences.push(`Найвищий ризик — ${HYP[top.label] || top.label} ${Math.round((top.score || 0) * 100)}% (невизначеність ${Math.round((top.uncertainty || 0) * 100)}%).`);
  }
  if (events.some((e) => e.feature === 'high_verifiability')) {
    sentences.push('Пом’якшує: багато перевірюваних деталей (Verifiability Approach).');
  }
  const othello = hyps.some((h) => (h.alternative_explanations || []).some((a) => String(a).includes('othello_error_guard')));
  if (othello) {
    sentences.push('Захист Othello (Ekman): емоційне збудження не приписано обману.');
  }
  return {text: sentences.join(' '), rec: RECOMMENDATION[status] || ''};
}

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
  const cite = citation(event);
  const withCite = (detail) => (cite ? `${detail} · ${cite}` : detail);
  if (f === 'high_verifiability') {
    return {icon: 'check', tone: 'good', kind: 'Багато перевірюваних деталей', detail: withCite('імена, числа, дати — асоційовано з правдивими розповідями'), tag: 'контр-доказ'};
  }
  if (f === 'impression_management') {
    return {icon: 'pressure', tone: 'warn', kind: 'Керування враженням', detail: withCite('щільні запевнення («повірте», «чесно», «я пишаюся»)'), tag: 'style'};
  }
  if (f === 'low_exclusive_words') {
    return {icon: 'signal', tone: 'muted', kind: 'Проста наративна структура', detail: withCite('мало виключних слів (але / крім / без)'), tag: 'style'};
  }
  if (f === 'low_first_person_singular') {
    return {icon: 'signal', tone: 'muted', kind: 'Знижене самопосилання', detail: withCite('мало «я»-звертань — мовне дистанціювання'), tag: 'style'};
  }
  if (f === 'elevated_negative_emotion') {
    return {icon: 'absolute', tone: 'warn', kind: 'Негативно-емоційна лексика', detail: withCite('підвищена частка негативних емоцій'), tag: 'style'};
  }
  if (f === 'elevated_motion_verbs') {
    return {icon: 'hedging', tone: 'muted', kind: 'Дієслова руху', detail: withCite('підвищена динаміка розповіді'), tag: 'style'};
  }
  if (f === 'cognitive_load_markers') {
    return {icon: 'signal', tone: 'warn', kind: 'Когнітивне навантаження', detail: withCite('низька лексична різноманітність (повтори) — когнітивний підхід'), tag: 'load'};
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

  // Auto summary (always visible) + disclosure control
  const autoSummary = buildSummary(report, events, hyps, status);
  const sumSec = make('section', 'report__section summary');
  const sumText = make('p', 'summary__text');
  text(sumText, autoSummary.text);
  sumSec.append(sumText);
  if (autoSummary.rec) {
    const rec = make('div', 'summary__rec');
    rec.dataset.tone = meta.tone;
    const rtext = make('span');
    text(rtext, autoSummary.rec);
    rec.append(rtext);
    sumSec.append(rec);
  }
  const controls = make('div', 'summary__controls');
  const toggle = make('button', 'disclose');
  toggle.type = 'button';
  toggle.setAttribute('aria-expanded', 'false');
  const tlabel = make('span');
  text(tlabel, 'Показати деталі');
  const chev = svg('svg', {viewBox: '0 0 24 24', class: 'disclose__chev', 'aria-hidden': 'true'});
  chev.append(svg('path', {d: 'M6 9l6 6 6-6', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round'}));
  toggle.append(tlabel, chev);
  const quickCopy = make('button', 'btn btn--ghost');
  quickCopy.type = 'button';
  text(quickCopy, 'Copy JSON');
  quickCopy.addEventListener('click', copyJson);
  controls.append(toggle, quickCopy);
  sumSec.append(controls);
  const note = make('p', 'summary__note');
  text(note, 'Аналітична поверхня, не вирок про людину — потрібна людська перевірка.');
  sumSec.append(note);
  card.append(sumSec);

  // Everything below is hidden until the user asks for details.
  const details = make('div', 'details');
  details.hidden = true;
  toggle.addEventListener('click', () => {
    const opening = details.hidden;
    details.hidden = !opening;
    toggle.setAttribute('aria-expanded', String(opening));
    toggle.dataset.open = opening ? 'true' : 'false';
    text(tlabel, opening ? 'Згорнути' : 'Показати деталі');
    if (opening) scrollThread();
  });

  // Signals — group repetitive markers, keep contradictions individual, and
  // surface the most informative signals first (not nine identical time cues).
  if (events.length) {
    const sec = section(details, 'Що знайдено');
    const list = make('ul', 'signals');
    const byFeature = {};
    events.forEach((e) => {
      (byFeature[e.feature] = byFeature[e.feature] || []).push(e);
    });
    const display = [];
    Object.entries(byFeature).forEach(([f, group]) => {
      if (f === 'local_claim_tension') group.forEach((e) => display.push({event: e, count: 1}));
      else display.push({event: group[0], count: group.length});
    });
    display.sort((a, b) => (SIGNAL_PRIORITY[a.event.feature] ?? 50) - (SIGNAL_PRIORITY[b.event.feature] ?? 50));
    display.slice(0, 8).forEach(({event, count}) => {
      const d = describeEvent(event);
      const li = make('li', 'signal');
      li.dataset.tone = d.tone;
      const ic = make('span', 'signal__icon');
      ic.append(iconEl(d.icon));
      const body = make('div', 'signal__body');
      const kind = make('span', 'signal__kind');
      text(kind, count > 1 ? `${d.kind} ×${count}` : d.kind);
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
    const sec = section(details, 'Оцінка ризику');
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
    const cap = make('p', 'risk-caption');
    text(cap, 'Показники — індекс пріоритету перевірки, не калібрована ймовірність обману. Виміряні характеристики: розділ «Система».');
    sec.append(cap);
  }

  // Questions (Ukrainian, derived from structured report)
  const questions = ukrainianQuestions(report);
  if (questions.length) {
    const sec = section(details, 'Питання для перевірки');
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
  details.append(foot);
  card.append(details);

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
function renderCalibration(data) {
  const b = (data && data.benchmark) || {};
  const o = (data && data.othello_guard) || {};
  const g = (data && data.gate) || {};
  const auc = g.roc_auc_ci || {};
  const ece = g.ece_ci || {};
  clear(calibrationBox);
  const rows = [
    ['Zero-trust gate', g.passed === undefined ? '—' : g.passed ? 'PASS' : 'FAIL'],
    ['Конструкт', b.construct || '—'],
    ['Вибірка', `${b.n ?? '?'} (позитивів ${b.positives ?? '?'})`],
    ['ROC-AUC [95% CI]', auc.point !== undefined ? `${auc.point} [${auc.lower}–${auc.upper}]` : (b.roc_auc ?? '—')],
    ['Average precision', b.average_precision ?? '—'],
    ['ECE сир.→калібр. [95% CI]', `${b.raw_ece ?? '—'} → ${b.calibrated_ece_cv ?? '—'}${ece.point !== undefined ? ` [${ece.lower}–${ece.upper}]` : ''}`],
    ['Othello-специфічність (Ekman)', `${o.specificity ?? '—'} (${o.n ?? '?'} affect-only)`],
  ];
  rows.forEach(([k, v]) => {
    const item = make('div', 'lineitem');
    const bold = make('b');
    text(bold, `${k}: `);
    const s = make('span');
    text(s, v);
    item.append(bold, s);
    calibrationBox.append(item);
  });
  const note = make('div', 'lineitem');
  text(note, b.note || 'Показники ризику — індекс пріоритету перевірки, не калібрована ймовірність обману.');
  calibrationBox.append(note);
}

async function loadContracts() {
  if (contractsLoaded) return;
  contractsLoaded = true;
  try {
    const [science, product, calibration] = await Promise.all([
      fetchJson(apiUrl('/api/v1/system/science-registry')),
      fetchJson(apiUrl('/api/v1/system/product-readiness')),
      fetchJson(apiUrl('/api/v1/system/calibration')),
    ]);
    renderScienceRegistry(science.data);
    renderProductReadiness(product.data);
    renderCalibration(calibration.data);
  } catch (e) {
    contractsLoaded = false;
  }
}

// --- Wiring ---

// COGVERITAS verifiability review — fail-closed, no verdict.
const GAP_LABEL = {
  elevated: {label: 'Розрив перевірюваності: підвищений', tone: 'warn'},
  nominal: {label: 'Розрив перевірюваності: номінальний', tone: 'good'},
  insufficient: {label: 'Недостатньо даних для перевірки', tone: 'muted'},
};

// Progressive disclosure: "why no verdict?" lazy-fetches the empirical contract
// (the negative result that forces the no-verdict invariant) on first open.
function methodologyDisclosure() {
  const why = make('details', 'why');
  const sum = make('summary', 'why__summary');
  text(sum, 'Чому вирок відсутній?');
  const body = make('div', 'why__body');
  text(body, 'Натисни, щоб побачити емпіричну основу.');
  why.append(sum, body);
  let loaded = false;
  why.addEventListener('toggle', async () => {
    if (!why.open || loaded) return;
    loaded = true;
    text(body, 'Завантаження…');
    try {
      const {data} = await fetchJson(apiUrl('/api/v1/cogveritas/methodology'));
      text(body, '');
      const law = make('p', 'why__law');
      text(law, data.empirical_law);
      body.append(law);
      const ul = make('ul', 'why__findings');
      (data.findings || []).slice(0, 3).forEach((f) => {
        const li = make('li');
        text(li, `${f.regime} — AUC ${f.roc_auc}: ${f.reads}`);
        ul.append(li);
      });
      body.append(ul);
      const prov = make('p', 'why__prov');
      text(prov, `Джерело: ${data.provenance}`);
      body.append(prov);
    } catch (error) {
      loaded = false;
      text(body, 'Не вдалося завантажити методологію.');
    }
  });
  return why;
}

// Export the current verifiability review as a printable Markdown dossier.
// Corroboration status is analyst state, kept per-input in this browser session.
const STATUS_CYCLE = ['pending', 'confirmed', 'refuted'];
const STATUS_LABEL = {pending: 'очікує', confirmed: 'підтверджено', refuted: 'спростовано'};

function caseKey(t) {
  let h = 5381;
  for (let i = 0; i < t.length; i += 1) h = ((h << 5) + h + t.charCodeAt(i)) | 0;
  return `cogv:${h >>> 0}`;
}
function loadCaseStatuses(key) {
  try {
    return JSON.parse(sessionStorage.getItem(key) || '{}') || {};
  } catch (e) {
    return {};
  }
}
function saveCaseStatuses(key) {
  try {
    sessionStorage.setItem(key, JSON.stringify(caseStatuses));
  } catch (e) {
    /* session storage unavailable — statuses stay in-memory only */
  }
}

async function downloadDossier() {
  if (!lastVerifyInput) {
    setStatus('Немає даних для досьє — спершу зроби перевірку.', 'error');
    return;
  }
  setStatus('Готую досьє…', 'busy');
  try {
    const md = await fetchText(apiUrl('/api/v1/cogveritas/case'), {
      method: 'POST',
      headers: {'content-type': 'application/json'},
      body: JSON.stringify({text: lastVerifyInput, statuses: caseStatuses, format: 'markdown', filename: lastVerifyFilename}),
    });
    const blob = new Blob([md], {type: 'text/markdown;charset=utf-8'});
    const url = URL.createObjectURL(blob);
    const a = make('a');
    a.href = url;
    a.download = 'cogveritas-dossier.md';
    a.click();
    URL.revokeObjectURL(url);
    setStatus('Досьє завантажено.', 'ok');
  } catch (error) {
    setStatus(`Не вдалося: ${error.message}`, 'error');
  }
}

function renderVerifiability(data) {
  dismissHero();
  const msg = make('article', 'msg');
  const card = make('div', 'report');
  const meta = GAP_LABEL[data.verifiability_gap] || {label: data.verifiability_gap, tone: 'muted'};
  card.dataset.tone = meta.tone;

  const head = make('div', 'report__head');
  const v = make('div', 'verdict');
  v.append(make('span', 'verdict__badge'));
  const box = make('div');
  const h = make('h3', 'verdict__label');
  text(h, meta.label);
  const m = make('p', 'verdict__meta');
  const caseId = (data.integrity && data.integrity.case_id) ? ` · case ${data.integrity.case_id}` : '';
  text(m, `COGVERITAS · вирок: відсутній (за задумом) · ${(data.audit_trail || []).length} тверджень${caseId}`);
  box.append(h, m);
  v.append(box);
  head.append(v);
  card.append(head);

  // At-a-glance case summary strip.
  const summary = make('div', 'casesummary');
  const chip = (label, value) => {
    const c = make('span', 'casechip');
    const k = make('span', 'casechip__k');
    text(k, label);
    const val = make('span', 'casechip__v');
    text(val, String(value));
    c.append(k, val);
    return c;
  };
  summary.append(chip('тверджень', (data.audit_trail || []).length));
  if ((data.witnesses || []).length) summary.append(chip('свідків', data.witnesses.length));
  summary.append(chip('перевірити', (data.corroboration_worklist || []).length));
  if ((data.conflicts || []).length) summary.append(chip('суперечностей', data.conflicts.length));
  if ((data.cross_witness || []).length) summary.append(chip('крос-звірок', data.cross_witness.length));
  const p = data.verification_progress || {};
  if (p.total) summary.append(chip('підтверджено', `${p.confirmed || 0}/${p.total}`));
  card.append(summary);

  const details = make('div', 'details');

  if ((data.entities || []).length) {
    const es = section(details, 'Сутності справи');
    const el2 = make('ul', 'entities');
    data.entities.forEach((e) => {
      const li = make('li', 'entity');
      const name = make('span', 'entity__name');
      text(name, e.canonical);
      const cnt = make('span', 'entity__count');
      text(cnt, `×${e.count}`);
      li.append(name, cnt);
      const others = (e.forms || []).filter((f) => f !== e.canonical);
      if (others.length) {
        const forms = make('span', 'entity__forms');
        text(forms, others.join(', '));
        li.append(forms);
      }
      el2.append(li);
    });
    es.append(el2);
  }

  if ((data.speaker_profiles || []).length) {
    const ps = section(details, 'Профілі свідків (перевірюваність)');
    const pl = make('ul', 'profiles');
    data.speaker_profiles.forEach((p) => {
      const li = make('li', 'profile');
      const nm = make('span', 'profile__name');
      text(nm, p.speaker);
      const bar = make('span', 'profile__stat');
      text(bar, `${p.checkable}/${p.total} перевірюваних · ${p.unverifiable} голослівних`);
      li.append(nm, bar);
      pl.append(li);
    });
    ps.append(pl);
  }

  if ((data.cross_witness || []).length) {
    const xs = section(details, 'Крос-звірка показів свідків');
    const xl = make('ul', 'conflicts');
    const CROSS_LABEL = {
      cross_contradiction: 'суперечність між свідками',
      cross_corroboration: 'взаємне підтвердження',
    };
    data.cross_witness.forEach((x) => {
      const li = make('li', 'conflict');
      li.dataset.kind = x.type;
      const tag = make('span', 'conflict__tag');
      text(tag, `${CROSS_LABEL[x.type] || x.type} · ${(x.speakers || []).join(' / ')}`);
      li.append(tag);
      (x.quotes || []).forEach((q) => {
        const p = make('p', 'conflict__quote');
        text(p, `«${q}»`);
        li.append(p);
      });
      xl.append(li);
    });
    xs.append(xl);
  }

  if ((data.conflicts || []).length) {
    const cs = section(details, 'Потенційні суперечності — перевірити вручну');
    const cl = make('ul', 'conflicts');
    const CONFLICT_LABEL = {
      negation_polarity: 'протилежні твердження',
      figure_mismatch: 'розбіжність у числах',
    };
    data.conflicts.forEach((c) => {
      const li = make('li', 'conflict');
      const tag = make('span', 'conflict__tag');
      text(tag, CONFLICT_LABEL[c.type] || c.type);
      li.append(tag);
      (c.quotes || []).forEach((q) => {
        const p = make('p', 'conflict__quote');
        text(p, `«${q}»`);
        li.append(p);
      });
      cl.append(li);
    });
    cs.append(cl);
  }

  if ((data.timeline || []).length) {
    const ts = section(details, 'Хронологія');
    const tl = make('ol', 'timeline');
    data.timeline.forEach((entry) => {
      const li = make('li', 'timeline__item');
      const when = make('span', 'timeline__time');
      text(when, entry.time_label || '—');
      if (!entry.resolved) when.dataset.approx = 'true';
      const q = make('span', 'timeline__claim');
      text(q, entry.quote);
      li.append(when, q);
      tl.append(li);
    });
    ts.append(tl);
  }

  const qs = section(details, 'Питання для корроборації');
  const list = make('ul', 'questions');
  (data.corroboration_questions || []).forEach((q) => {
    const li = make('li', 'question');
    const mark = make('span', 'question__mark');
    mark.append(iconEl('check'));
    const t = make('span');
    text(t, q);
    li.append(mark, t);
    list.append(li);
  });
  qs.append(list);

  if ((data.interview_questions || []).length) {
    const iqs = section(details, 'Питання для допиту — закрити прогалини');
    const il = make('ul', 'questions');
    data.interview_questions.forEach((iq) => {
      const li = make('li', 'question');
      const mark = make('span', 'question__mark');
      mark.append(iconEl('check'));
      const t = make('span');
      text(t, iq.question);
      li.append(mark, t);
      il.append(li);
    });
    iqs.append(il);
  }

  if ((data.corroboration_worklist || []).length) {
    const ws = section(details, 'Лист корроборації — що перевірити');
    const key = caseKey(lastVerifyInput);
    caseStatuses = loadCaseStatuses(key);
    const items = data.corroboration_worklist;
    const progress = make('p', 'worklist__progress');
    const renderProgress = () => {
      let c = 0;
      let r = 0;
      items.forEach((it) => {
        const st = (caseStatuses[it.claim_id] || {}).status || 'pending';
        if (st === 'confirmed') c += 1;
        else if (st === 'refuted') r += 1;
      });
      text(progress, `Прогрес: підтверджено ${c} · спростовано ${r} · очікує ${items.length - c - r} / ${items.length}`);
    };
    renderProgress();
    ws.append(progress);
    const wl = make('ul', 'worklist');
    items.forEach((item) => {
      const li = make('li', 'worklist__item');
      const head = make('div', 'worklist__head');
      const q = make('p', 'worklist__claim');
      text(q, `«${item.quote}»`);
      const btn = make('button', 'statusbtn');
      btn.type = 'button';
      const paint = () => {
        const st = (caseStatuses[item.claim_id] || {}).status || 'pending';
        btn.dataset.status = st;
        li.dataset.status = st;
        text(btn, STATUS_LABEL[st]);
      };
      btn.addEventListener('click', () => {
        const cur = (caseStatuses[item.claim_id] || {}).status || 'pending';
        const next = STATUS_CYCLE[(STATUS_CYCLE.indexOf(cur) + 1) % STATUS_CYCLE.length];
        caseStatuses[item.claim_id] = {status: next, note: (caseStatuses[item.claim_id] || {}).note || ''};
        saveCaseStatuses(key);
        paint();
        renderProgress();
      });
      paint();
      head.append(q, btn);
      li.append(head);
      const rl = make('ul', 'worklist__records');
      (item.record_types || []).forEach((r) => {
        const rli = make('li', 'worklist__record');
        const mark = make('span', 'question__mark');
        mark.append(iconEl('check'));
        const rt = make('span');
        text(rt, r);
        rli.append(mark, rt);
        rl.append(rli);
      });
      li.append(rl);
      wl.append(li);
    });
    ws.append(wl);
  }

  if ((data.rm_criteria_flagged || []).length) {
    const ns = section(details, 'Неперевірювані твердження');
    const nl = make('ul', 'questions');
    data.rm_criteria_flagged.forEach((n) => {
      const li = make('li', 'question');
      li.append(make('span', 'question__mark'));
      const t = make('span');
      text(t, n);
      li.append(t);
      nl.append(li);
    });
    ns.append(nl);
  }

  const foot = make('div', 'report__foot');
  const actions = make('div', 'foot-actions');
  const dl = make('button', 'btn btn--ghost');
  dl.type = 'button';
  text(dl, 'Завантажити досьє (.md)');
  dl.addEventListener('click', () => downloadDossier());
  actions.append(dl);
  foot.append(actions);
  const disc = make('p', 'disclaimer');
  text(disc, 'COGVERITAS не визначає, чи людина бреше. Він виділяє зовнішньо перевірювані твердження, ставить питання для корроборації і зберігає provenance. Жодних ймовірностей поза доменом.');
  foot.append(disc);
  foot.append(methodologyDisclosure());
  details.append(foot);
  card.append(details);

  // Details visible by default here (the questions ARE the product).
  details.hidden = false;
  msg.append(card);
  thread.append(msg);
  scrollThread();
}

// Resolve the text to verify from an attached file (preferred) or the textarea,
// applying the same media/size guards as the main analysis path. Returns the
// content string, or null if the caller already surfaced a blocking notice.
async function resolveVerifiabilityInput() {
  if (pendingFile) {
    const file = pendingFile;
    setPendingFile(null);
    const ext = fileExtension(file.name);
    if (MEDIA_EXTENSIONS.includes(ext)) {
      addNotice('Аудіо/відео потребує транскрипції', 'Транскрибуй запис (напр. Whisper → SRT/JSON) і завантаж текст.', 'muted');
      setStatus('Потрібен транскрипт.', 'neutral');
      return null;
    }
    if (file.size > MAX_UPLOAD_BYTES) {
      addNotice('Файл завеликий', `${(file.size / 1e6).toFixed(1)}MB перевищує ліміт 100MB.`, 'bad');
      return null;
    }
    addUserMessage(`📎 ${file.name}`);
    lastVerifyFilename = file.name; // lets the backend pick the transcript parser
    return (await file.text()).trim();
  }
  const raw = payload.value.trim();
  if (!raw) {
    setStatus('Порожньо. Встав текст або додай файл для перевірки.', 'error');
    return null;
  }
  addUserMessage(raw.length > 260 ? `${raw.slice(0, 260)}…` : raw);
  payload.value = '';
  autoGrow();
  lastVerifyFilename = '';
  return raw;
}

async function verifiability() {
  if (busy) return;
  setBusy(true);
  try {
    const content = await resolveVerifiabilityInput();
    if (content === null) return; // blocking notice already shown
    lastVerifyInput = content; // kept so the dossier can be exported
    setStatus('Перевіряю зовнішню перевірюваність…', 'busy');
    const headers = {'content-type': 'text/plain; charset=utf-8'};
    if (lastVerifyFilename) headers['x-bive-filename'] = encodeURIComponent(lastVerifyFilename);
    const {data} = await fetchJson(apiUrl('/api/v1/cogveritas/verifiability'), {
      method: 'POST',
      headers,
      body: content,
    });
    renderVerifiability(data);
    setStatus('Готово · COGVERITAS (вирок відсутній).', 'ok');
  } catch (error) {
    addNotice('Не вдалося перевірити', humanError(error), 'bad');
    setStatus(error.message, 'error');
  } finally {
    setBusy(false);
  }
}

el('#verify').addEventListener('click', () => verifiability());

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
