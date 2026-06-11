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

const payload = el('#payload');
const output = el('#output');
const markdownOutput = el('#markdownOutput');
const apiToken = el('#apiToken');
const statusText = el('#statusText');
const systemReadiness = el('#systemReadiness');
const systemVersion = el('#systemVersion');
const statusDot = el('#statusDot');
const metricReady = el('#metricReady');
const metricReports = el('#metricReports');
const metricAuth = el('#metricAuth');
const metricLimits = el('#metricLimits');
const metricGates = el('#metricGates');
const metricScience = el('#metricScience');
const metricAos = el('#metricAos');
const metricProduct = el('#metricProduct');
const metricLatency = el('#metricLatency');
const resultTitle = el('#resultTitle');
const resultStatus = el('#resultStatus');
const summaryCards = el('#summaryCards');
const evidenceList = el('#evidenceList');
const hypothesisList = el('#hypothesisList');
const questionsList = el('#questionsList');
const gatesList = el('#gatesList');
const capabilityList = el('#capabilityList');
const designContract = el('#designContract');
const scienceList = el('#scienceList');
const scienceBoundary = el('#scienceBoundary');
const aosKernel = el('#aosKernel');
const productReadiness = el('#productReadiness');

let lastOutput = {};
let lastMarkdown = '';
let lastReportId = '';
const API_VERSION = '2026-06-11';

function apiUrl(path) {
  const joiner = path.includes('?') ? '&' : '?';
  return `${path}${joiner}api-version=${encodeURIComponent(API_VERSION)}`;
}

const demo = {
  subject_scope: 'public_statement_review',
  segments: [
    {speaker: 'subject', start: 0, end: 4.1, text: 'Я точно ніколи не мав доступу до цих документів.'},
    {speaker: 'subject', start: 5.0, end: 8.0, text: 'Можливо, я бачив їх раніше, але не пам’ятаю коли.'},
    {speaker: 'subject', start: 9.2, end: 14.0, text: 'Усі рішення були прозорі, просто не треба зараз дивитися на деталі.'}
  ]
};

function setStatus(message, mode = 'neutral') {
  text(statusText, message);
  statusText.dataset.mode = mode;
}

// Session-bounded API token lifecycle. The token lives only in this browsing
// session (sessionStorage) or in memory; it is never written to persistent
// device storage, so it does not survive the tab being closed. Threat model: a
// shared-machine or XSS-persisted credential must not outlive the session. See
// docs/BACKEND_FRONTEND_CONTRACT.md.
const SESSION_TOKEN_KEY = 'bive_api_token';

function clearSessionToken() {
  sessionStorage.removeItem(SESSION_TOKEN_KEY);
  apiToken.value = '';
}

function persistSessionToken() {
  const value = apiToken.value.trim();
  if (value) {
    sessionStorage.setItem(SESSION_TOKEN_KEY, value);
  } else {
    sessionStorage.removeItem(SESSION_TOKEN_KEY);
  }
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

function authHeaders() {
  const token = apiToken.value.trim();
  return token ? {'x-bive-api-key': token} : {};
}

async function fetchJson(url, options = {}) {
  const headers = {'accept': 'application/json', ...(options.headers || {}), ...authHeaders()};
  const response = await fetch(url, {...options, headers});
  const requestId = response.headers.get('x-request-id') || 'missing-request-id';
  let data;
  try {
    data = await response.json();
  } catch (error) {
    data = {error: 'non_json_response', details: [error.message], request_id: requestId};
  }
  if (!response.ok) {
    if (response.status === 401) clearSessionToken();
    const message = (data.error && data.error.code) || data.error || `http_${response.status}`;
    throw new Error(`${message} [${requestId}]`);
  }
  return {data, requestId};
}

async function fetchText(url, options = {}) {
  const headers = {'accept': 'text/plain', ...(options.headers || {}), ...authHeaders()};
  const response = await fetch(url, {...options, headers});
  const requestId = response.headers.get('x-request-id') || 'missing-request-id';
  const data = await response.text();
  if (!response.ok) throw new Error(`http_${response.status} [${requestId}]`);
  return {data, requestId};
}

function renderJson(data) {
  lastOutput = data;
  output.textContent = JSON.stringify(data, null, 2);
}

function renderSystem(data) {
  text(systemReadiness, data.readiness.toUpperCase());
  text(systemVersion, `${data.service} v${data.version} · ${data.environment}`);
  statusDot.dataset.ready = data.readiness === 'ready' ? 'true' : 'false';
  text(metricReady, data.readiness);
  text(metricReports, data.storage.report_count);
  text(metricAuth, data.limits.auth_required ? 'required' : 'local-open');
  text(metricLimits, `${data.limits.max_segments} segments`);
  const passed = data.gates.filter((gate) => gate.last_observed === 'pass').length;
  text(metricGates, `${passed}/${data.gates.length}`);
  renderGates(data.gates);
}

function renderMetricsText(metricsText) {
  const match = metricsText.match(/bive_request_latency_seconds_sum\s+([0-9.]+)/);
  if (match) text(metricLatency, `${Number(match[1]).toFixed(3)}s`);
}

function appendMiniCard(parent, label, value) {
  const card = make('article', 'mini-card');
  const small = make('span');
  const strong = make('b');
  text(small, label);
  text(strong, value);
  card.append(small, strong);
  parent.append(card);
}

function appendEvidence(parent, title, description, meta) {
  const item = make('article', 'evidence-item');
  const heading = make('strong');
  const body = make('p');
  const small = make('small');
  text(heading, title);
  text(body, description);
  text(small, meta);
  item.append(heading, body, small);
  parent.append(item);
}

function renderReport(data) {
  const report = data.report;
  lastReportId = report.report_id || data.report_id || '';
  text(resultTitle, lastReportId || 'report');
  text(resultStatus, data.status || report.final_status || 'unknown');

  const events = report.evidence_events || [];
  const hypotheses = report.hypotheses || [];
  const questions = report.verification_questions || [];

  clear(summaryCards);
  appendMiniCard(summaryCards, 'Evidence events', events.length);
  appendMiniCard(summaryCards, 'Hypotheses', hypotheses.length);
  appendMiniCard(summaryCards, 'Questions', questions.length);
  appendMiniCard(summaryCards, 'Scope', report.subject_scope || 'unknown');

  clear(evidenceList);
  if (!events.length) {
    text(evidenceList, 'Evidence events відсутні.');
  } else {
    events.slice(0, 10).forEach((event) => {
      appendEvidence(
        evidenceList,
        event.event_type || 'event',
        event.description || event.text || 'no description',
        `source=${event.source || 'unknown'} · confidence=${event.confidence ?? 'n/a'}`
      );
    });
  }

  clear(hypothesisList);
  if (!hypotheses.length) {
    text(hypothesisList, 'Гіпотези відсутні.');
  } else {
    hypotheses.slice(0, 8).forEach((hypothesis) => {
      appendEvidence(
        hypothesisList,
        hypothesis.label || 'hypothesis',
        hypothesis.rationale || hypothesis.description || 'no rationale',
        `score=${hypothesis.score ?? 'n/a'} · uncertainty=${hypothesis.uncertainty ?? 'n/a'}`
      );
    });
  }

  clear(questionsList);
  if (!questions.length) {
    text(questionsList, 'Питання для review відсутні.');
  } else {
    questions.slice(0, 8).forEach((question, index) => {
      appendEvidence(questionsList, `Q${index + 1}`, question.question || question, question.reason || 'human_review');
    });
  }
}

function renderGates(gates) {
  clear(gatesList);
  gates.forEach((gate) => {
    const item = make('div', 'gate-row');
    const name = make('span');
    const status = make('b');
    text(name, gate.name);
    text(status, gate.last_observed);
    status.dataset.status = gate.last_observed;
    item.append(name, status);
    gatesList.append(item);
  });
}

function renderCapabilities(data) {
  clear(capabilityList);
  [...data.modalities, ...data.outputs, ...data.production_gates].forEach((item) => {
    const tag = make('span', 'tag');
    text(tag, item);
    capabilityList.append(tag);
  });
}

function renderDesignContract(data) {
  clear(designContract);
  Object.entries(data).forEach(([key, value]) => {
    const dt = make('dt');
    const dd = make('dd');
    text(dt, key.replaceAll('_', ' '));
    text(dd, Array.isArray(value) ? value.join(' · ') : value);
    designContract.append(dt, dd);
  });
}

function renderScienceRegistry(data) {
  text(metricScience, `${data.reference_count} refs`);
  clear(scienceList);
  data.disciplines.forEach((discipline) => {
    const tag = make('span', 'tag');
    text(tag, discipline.name);
    scienceList.append(tag);
  });
  clear(scienceBoundary);
  data.hard_boundaries.slice(0, 4).forEach((boundary, index) => {
    appendEvidence(scienceBoundary, `B${index + 1}`, boundary, 'claim_boundary');
  });
}

function renderAosKernel(data) {
  text(metricAos, `${data.eval_tasks} evals`);
  clear(aosKernel);
  appendEvidence(aosKernel, data.name || 'AOS', `version=${data.version} · status=${data.status}`, data.release_gate || 'make aos-kernel');
  appendEvidence(aosKernel, 'Pipeline', `${data.pipeline_steps} canonical steps`, 'intent → boundary → contract → evidence → status');
  appendEvidence(aosKernel, 'Evidence classes', (data.evidence_classes || []).join(' · '), 'fail-closed epistemics');
}

function renderProductReadiness(data) {
  text(metricProduct, data.overall_status || 'unknown');
  clear(productReadiness);
  appendEvidence(productReadiness, 'Stage', data.stage || 'unknown', data.release_gate || 'make product-readiness');
  appendEvidence(productReadiness, 'Status', data.overall_status || 'unknown', data.boundary || 'product boundary missing');
  appendEvidence(productReadiness, 'Blocking unknowns', (data.blocking_unknowns || []).join(' · ') || 'none', 'fail-closed release state');
}

async function refreshSystem() {
  const {data} = await fetchJson(apiUrl('/api/v1/system/status'));
  renderSystem(data);
  try {
    const metrics = await fetchText('/metrics');
    renderMetricsText(metrics.data);
  } catch (error) {
    text(metricLatency, 'unknown');
  }
  setStatus('Системний статус оновлено.', 'ok');
}

async function refreshContracts() {
  const [capabilities, design, science, aos, product] = await Promise.all([
    fetchJson(apiUrl('/api/v1/capabilities')),
    fetchJson(apiUrl('/api/v1/system/design-contract')),
    fetchJson(apiUrl('/api/v1/system/science-registry')),
    fetchJson(apiUrl('/api/v1/system/aos-kernel')),
    fetchJson(apiUrl('/api/v1/system/product-readiness'))
  ]);
  renderCapabilities(capabilities.data);
  renderDesignContract(design.data);
  renderScienceRegistry(science.data);
  renderAosKernel(aos.data);
  renderProductReadiness(product.data);
}

async function refreshMarkdown() {
  if (!lastReportId) {
    text(markdownOutput, 'Спочатку побудуй звіт. Машина не читає наміри через ауру, поки що.');
    return;
  }
  const {data} = await fetchText(apiUrl(`/api/v1/reports/${encodeURIComponent(lastReportId)}/markdown`));
  lastMarkdown = data;
  text(markdownOutput, data);
}

async function runAnalysis() {
  setStatus('Аналіз запущено.', 'busy');
  let parsed;
  try {
    parsed = JSON.parse(payload.value);
  } catch (error) {
    setStatus(`JSON помилка: ${error.message}`, 'error');
    return;
  }
  const {data, requestId} = await fetchJson(apiUrl('/api/v1/reports/from-transcript'), {
    method: 'POST',
    headers: {'content-type': 'application/json'},
    body: JSON.stringify(parsed)
  });
  renderJson(data);
  renderReport(data);
  await refreshMarkdown();
  setStatus(`Звіт побудовано. request_id=${requestId}`, 'ok');
  await refreshSystem();
}

el('#loadDemo').addEventListener('click', () => {
  payload.value = JSON.stringify(demo, null, 2);
  setStatus('Демо завантажено.', 'ok');
});

el('#health').addEventListener('click', async () => {
  try {
    const {data} = await fetchJson('/health');
    renderJson(data);
    setStatus('Health отримано.', 'ok');
  } catch (error) {
    setStatus(error.message, 'error');
  }
});

el('#run').addEventListener('click', () => runAnalysis().catch((error) => setStatus(error.message, 'error')));
el('#runHero').addEventListener('click', () => el('#console').scrollIntoView({behavior: 'smooth'}));
el('#refreshSystem').addEventListener('click', () => refreshSystem().catch((error) => setStatus(error.message, 'error')));
el('#refreshContracts').addEventListener('click', () => refreshContracts().catch((error) => setStatus(error.message, 'error')));

el('#saveToken').addEventListener('click', () => {
  persistSessionToken();
  setStatus('Token збережено лише на цю сесію браузера.', 'ok');
});

el('#copyOutput').addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(JSON.stringify(lastOutput, null, 2));
    setStatus('JSON скопійовано.', 'ok');
  } catch (error) {
    setStatus(`Clipboard error: ${error.message}`, 'error');
  }
});

el('#copyMarkdown').addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(lastMarkdown || markdownOutput.textContent);
    setStatus('Markdown скопійовано.', 'ok');
  } catch (error) {
    setStatus(`Clipboard error: ${error.message}`, 'error');
  }
});

el('#downloadOutput').addEventListener('click', () => {
  const blob = new Blob([JSON.stringify(lastOutput, null, 2)], {type: 'application/json'});
  const href = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = href;
  link.download = 'bive-report.json';
  link.click();
  URL.revokeObjectURL(href);
  setStatus('JSON підготовлено до завантаження.', 'ok');
});

const savedToken = sessionStorage.getItem(SESSION_TOKEN_KEY);
if (savedToken) apiToken.value = savedToken;
captureUrlToken();
payload.value = JSON.stringify(demo, null, 2);
Promise.all([refreshSystem(), refreshContracts()]).catch((error) => setStatus(error.message, 'error'));
