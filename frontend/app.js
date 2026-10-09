/**
 * StatGPT v3 — Frontend Application
 * Auth-aware chat UI with Chart.js, data tables, infographic stat cards, and MoSPI dataset sidebar.
 */

'use strict';

// ─────────────────────────────────────────────────────────────────────────────
// Config
// ─────────────────────────────────────────────────────────────────────────────
const API_BASE = 'http://localhost:8000';

// Chart.js global defaults
Chart.defaults.color = '#64748b';
Chart.defaults.borderColor = 'rgba(255,255,255,0.05)';
Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
Chart.defaults.font.size = 11;

// ─────────────────────────────────────────────────────────────────────────────
// Auth Guard — redirect to login if not authenticated
// ─────────────────────────────────────────────────────────────────────────────
function checkAuth() {
  const token = localStorage.getItem('statgpt_token');
  if (!token) {
    window.location.href = '/login';
    return false;
  }
  return true;
}

// ─────────────────────────────────────────────────────────────────────────────
// State
// ─────────────────────────────────────────────────────────────────────────────
let _isLoading   = false;
let _charts      = {};
let _datasets    = [];
let _msgCount    = 0;
let _sessionId   = null; // NEW: Store uploaded dataset session

const QUICK_QUERIES = [
  "What is the unemployment rate in rural India for 2023-24?",
  "Show female LFPR trend from 2017-18 to 2023-24.",
  "What was India's GDP growth in 2023-24?",
  "What was CPI food inflation in July 2023?",
  "Compare urban vs rural WPR for males in 2022-23.",
  "Show IIP general index trend in 2023.",
];

// Typing indicator steps
const TYPING_STEPS = [
  "Detecting dataset…",
  "Querying MoSPI data…",
  "Analysing records…",
  "Generating answer…",
];

// ─────────────────────────────────────────────────────────────────────────────
// DOM refs
// ─────────────────────────────────────────────────────────────────────────────
const $  = id => document.getElementById(id);
const $chat     = $('chat-container');
const $welcome  = $('welcome');
const $input    = $('user-input');
const $sendBtn  = $('send-btn');
const $sidebar  = $('sidebar');
const $infoPanel = $('info-panel');

// ─────────────────────────────────────────────────────────────────────────────
// Boot
// ─────────────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  if (!checkAuth()) return;

  feather.replace();
  setupUser();
  buildChips();
  setupWelcomeCards();
  loadDatasets();
  attachListeners();
  autoResize();
});

// ─────────────────────────────────────────────────────────────────────────────
// User profile
// ─────────────────────────────────────────────────────────────────────────────
function setupUser() {
  try {
    const user = JSON.parse(localStorage.getItem('statgpt_user') || '{}');
    const name = user.name || user.email || 'Guest';
    $('user-name').textContent = name;
    $('user-avatar').textContent = name.charAt(0).toUpperCase();
  } catch (_) {}
}

function logout() {
  localStorage.removeItem('statgpt_token');
  localStorage.removeItem('statgpt_user');
  window.location.href = '/login';
}

// ─────────────────────────────────────────────────────────────────────────────
// Dataset sidebar
// ─────────────────────────────────────────────────────────────────────────────
async function loadDatasets() {
  try {
    const res = await fetch(`${API_BASE}/datasets`);
    const data = await res.json();
    _datasets = data.datasets || [];
    renderDatasetList();
    renderInfoStats();
  } catch (_) {
    $('dataset-list').innerHTML = `<div style="font-size:11px;color:var(--text-muted);padding:6px 10px;line-height:1.6">⚠ Backend not connected.<br>Start the server first.</div>`;
  }
}

const BADGE_COLORS = { plfs:'plfs', cpi:'cpi', nas:'nas', iip:'iip', asi:'asi', literacy:'literacy', poverty:'poverty' };
const DATASET_ICONS = { plfs:'👷', cpi:'📈', nas:'🏛️', iip:'🏭', asi:'🏗️', literacy:'📖', poverty:'🔻' };

function renderDatasetList() {
  $('dataset-list').innerHTML = _datasets.map(ds => {
    const icon = DATASET_ICONS[ds.key] || '📊';
    return `
    <div class="dataset-item" role="button" tabindex="0" data-ds="${ds.key}" aria-label="${ds.full_name}">
      <span class="dataset-badge badge-${BADGE_COLORS[ds.key]||'plfs'}">
        <span style="margin-right:3px; font-size:11px;">${icon}</span>${ds.name}
      </span>
      <div class="dataset-info">
        <div class="dataset-name">${ds.full_name}</div>
        <div class="dataset-years">${ds.years_covered||''}</div>
      </div>
    </div>
    `;
  }).join('');

  document.querySelectorAll('.dataset-item').forEach(el => {
    el.addEventListener('click', () => {
      document.querySelectorAll('.dataset-item').forEach(x => x.classList.remove('active'));
      el.classList.add('active');
      const ds = _datasets.find(d => d.key === el.dataset.ds);
      if (ds?.sample_queries?.[0]) sendMessage(ds.sample_queries[0]);
    });
    el.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') el.click(); });
  });
}

function renderInfoStats() {
  $('info-stats').innerHTML = _datasets.map(ds => `
    <div class="stat-card">
      <div class="stat-card-label">${ds.name} — ${ds.full_name}</div>
      <div class="stat-card-value">${ds.indicators?.length||0} indicators</div>
      <div class="stat-card-sub">${ds.years_covered} · ${ds.frequency}</div>
    </div>
  `).join('');
}

// ─────────────────────────────────────────────────────────────────────────────
// Quick query chips
// ─────────────────────────────────────────────────────────────────────────────
function buildChips() {
  $('chip-list').innerHTML = QUICK_QUERIES.map(q => `
    <button class="chip" role="listitem">${q}</button>
  `).join('');
  document.querySelectorAll('.chip').forEach(el => {
    el.addEventListener('click', () => sendMessage(el.textContent.trim()));
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Welcome cards
// ─────────────────────────────────────────────────────────────────────────────
function setupWelcomeCards() {
  document.querySelectorAll('.welcome-card').forEach(el => {
    el.addEventListener('click', () => {
      const query = el.dataset.query;
      if (query) sendMessage(query);
    });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Listeners
// ─────────────────────────────────────────────────────────────────────────────
function attachListeners() {
  $input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  });
  $input.addEventListener('input', () => { autoResize(); updateCharCount(); });

  $sendBtn.addEventListener('click', handleSend);

  $('reset-btn').addEventListener('click', handleReset);
  $('menu-btn').addEventListener('click', () => $sidebar.classList.toggle('open'));
  $('info-btn').addEventListener('click', () => $infoPanel.classList.toggle('open'));
  $('logout-btn').addEventListener('click', logout);
  $('user-card').addEventListener('keydown', e => { if (e.key === 'Enter') logout(); });

  // NEW: Tab navigation
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.target));
  });

  // NEW: Upload handler
  $('upload-submit-btn').addEventListener('click', handleUpload);
}

function switchTab(targetId) {
  document.querySelectorAll('.tab-content').forEach(el => {
    el.style.display = (el.id === targetId) ? (targetId === 'tab-chat' ? 'flex' : 'block') : 'none';
  });
  document.querySelectorAll('.tab-btn').forEach(btn => {
    if (btn.dataset.target === targetId) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });
}

async function handleUpload() {
  const fileInput = $('file-upload');
  const statusEl = $('upload-status');
  if (!fileInput.files.length) {
    statusEl.textContent = 'Please select a file first.';
    return;
  }
  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append('file', file);
  
  statusEl.textContent = 'Uploading and analyzing...';
  $('upload-submit-btn').disabled = true;
  
  try {
    const res = await fetch(`${API_BASE}/dataset/upload`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Upload failed');
    }
    const data = await res.json();
    _sessionId = data.session_id;
    statusEl.textContent = 'Success!';
    renderPreview(data.summary);
    
    // Enable and switch to preview tab
    const previewBtn = document.querySelector('.tab-btn[data-target="tab-preview"]');
    previewBtn.style.display = 'block';
    previewBtn.disabled = false;
    switchTab('tab-preview');
    
  } catch (err) {
    statusEl.textContent = `Error: ${err.message}`;
  } finally {
    $('upload-submit-btn').disabled = false;
  }
}

function renderPreview(summary) {
  $('preview-summary').textContent = summary.summary_text;
  $('prev-rows').textContent = summary.shape.rows.toLocaleString();
  $('prev-cols').textContent = summary.shape.columns;
  const missingTotal = Object.values(summary.missing_values).reduce((a,b) => a+b, 0);
  $('prev-missing').textContent = missingTotal.toLocaleString();
  $('prev-dupes').textContent = summary.duplicates.toLocaleString();
  
  // Render table
  if (summary.sample_rows && summary.sample_rows.length > 0) {
    const cols = summary.columns;
    $('preview-thead').innerHTML = cols.map(c => `<th style="padding: 10px; border-bottom: 1px solid var(--border);">${escHtml(String(c))}</th>`).join('');
    $('preview-tbody').innerHTML = summary.sample_rows.map(row => {
      return `<tr>${cols.map(c => `<td style="padding: 10px; border-bottom: 1px solid var(--border);">${escHtml(String(row[c] ?? ''))}</td>`).join('')}</tr>`;
    }).join('');
  }
}

function autoResize() {
  $input.style.height = 'auto';
  $input.style.height = Math.min($input.scrollHeight, 150) + 'px';
}

function updateCharCount() {
  const len = $input.value.length;
  const el = $('char-count');
  if (len > 20) { el.textContent = `${len} chars`; }
  else { el.textContent = ''; }
}

// ─────────────────────────────────────────────────────────────────────────────
// Send flow
// ─────────────────────────────────────────────────────────────────────────────
async function handleSend() {
  const msg = $input.value.trim();
  if (!msg || _isLoading) return;
  sendMessage(msg);
}

async function sendMessage(msg) {
  if (!msg || _isLoading) return;

  $welcome.classList.add('hidden');

  appendUserMsg(msg);
  $input.value = '';
  autoResize();
  updateCharCount();

  const typingId = showTyping();
  setLoading(true);

  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg, session_id: _sessionId }),
    });
    if (!res.ok) throw new Error(`Server error ${res.status}`);
    const data = await res.json();
    removeTyping(typingId);
    appendAssistantMsg(data);
    _msgCount++;
    updateQueryCount();
  } catch (err) {
    removeTyping(typingId);
    appendErrorMsg(err.message);
  } finally {
    setLoading(false);
  }
}

async function handleReset() {
  if (_isLoading) return;
  try { await fetch(`${API_BASE}/reset`, { method: 'POST' }); } catch (_) {}
  document.querySelectorAll('.message').forEach(m => m.remove());
  Object.values(_charts).forEach(c => c.destroy());
  _charts = {};
  _msgCount = 0;
  updateQueryCount();
  $welcome.classList.remove('hidden');
  document.querySelectorAll('.dataset-item').forEach(x => x.classList.remove('active'));
}

function updateQueryCount() {
  const el = $('query-count');
  if (_msgCount > 0) {
    el.textContent = `${_msgCount} question${_msgCount > 1 ? 's' : ''}`;
    el.style.display = 'inline-flex';
  } else {
    el.style.display = 'none';
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Message renderers
// ─────────────────────────────────────────────────────────────────────────────
function appendUserMsg(text) {
  const el = document.createElement('div');
  el.className = 'message user';
  el.setAttribute('role', 'listitem');
  el.innerHTML = `
    <div class="msg-avatar" aria-hidden="true">👤</div>
    <div class="msg-body">
      <div class="msg-bubble">${escHtml(text)}</div>
      <div class="msg-meta">${fmtTime()}</div>
    </div>
  `;
  $chat.appendChild(el);
  scrollBottom();
}

function appendAssistantMsg(data) {
  const isErr = !!data.error;
  const chartId = isErr ? null : `chart-${Date.now()}`;

  const el = document.createElement('div');
  el.className = `message assistant${isErr ? ' error-msg' : ''}`;
  el.setAttribute('role', 'listitem');

  // Build infographic stats section
  const infraHtml = renderInfographicStats(data.infographic_stats);

  // Render citations
  let citationsHtml = '';
  if (data.citations && data.citations.length > 0) {
    const list = data.citations.map(c => 
      `<li>${escHtml(c.document)} ${c.page ? `(Page ${c.page})` : ''} - ${escHtml(c.source_org)}</li>`
    ).join('');
    citationsHtml = `<div class="citations-panel" role="note"><div class="citations-title">📄 Official Sources</div><ul>${list}</ul></div>`;
  }
  
  // Confidence badge
  const confClass = data.confidence === 'HIGH' ? 'conf-high' : data.confidence === 'MEDIUM' ? 'conf-med' : 'conf-low';
  const confBadge = `<span class="confidence-badge ${confClass}">${escHtml(data.confidence || 'LOW')} CONFIDENCE</span>`;

  el.innerHTML = `
    <div class="msg-avatar" aria-hidden="true">📊</div>
    <div class="msg-body">
      <div class="msg-bubble">
        <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
          ${isErr ? `<div class="error-badge">⚠ Error</div>` : `<div></div>`}
          ${!isErr ? confBadge : ''}
        </div>
        ${infraHtml}
        <div class="answer-text">${renderMd(data.answer || '')}</div>
        ${renderTable(data.data_table)}
        ${data.chart_config && !isErr ? `
          <div class="chart-wrap">
            <p class="chart-title">${escHtml(data.chart_config.title || 'Chart')}</p>
            <canvas id="${chartId}" role="img" aria-label="${escHtml(data.chart_config.title || 'Chart')}"></canvas>
          </div>` : ''}
        ${data.interpretation ? `<div class="interpretation" role="note">${renderMd(data.interpretation)}</div>` : ''}
        ${citationsHtml}
        ${data.source && !citationsHtml ? `<div class="source-badge" role="note"><span class="source-icon">📄</span>${escHtml(data.source)}</div>` : ''}
      </div>
      <div class="msg-meta">${fmtTime()}</div>
    </div>
  `;

  $chat.appendChild(el);
  if (chartId && data.chart_config) renderChart(chartId, data.chart_config);

  // Animate infographic stat values after insertion
  animateStatValues(el);

  scrollBottom();
}

function appendErrorMsg(msg) {
  appendAssistantMsg({
    answer: `Could not reach the StatGPT backend at \`${API_BASE}\`.\n\nError: ${msg}`,
    data_table: [],
    infographic_stats: [],
    interpretation: 'Make sure the server is running: `python -m uvicorn backend.main:app --reload`',
    source: '',
    chart_config: null,
    error: true,
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Infographic stat cards
// ─────────────────────────────────────────────────────────────────────────────
function renderInfographicStats(stats) {
  if (!stats || !stats.length) return '';

  const cards = stats.map(s => {
    const trendClass = s.trend === 'up' ? 'trend-up' : s.trend === 'down' ? 'trend-down' : 'trend-neutral';
    const trendIcon  = s.trend === 'up' ? '↑' : s.trend === 'down' ? '↓' : '→';
    const safeVal = escHtml(String(s.value));
    const safeLabel = escHtml(String(s.label));
    const safeUnit  = escHtml(String(s.unit || ''));
    const safeIcon  = escHtml(String(s.icon || '📊'));
    return `
      <div class="infographic-card">
        <div class="infographic-icon">${safeIcon}</div>
        <div class="infographic-body">
          <div class="infographic-value" data-target="${safeVal}">${safeVal}</div>
          <div class="infographic-unit">${safeUnit}</div>
          <div class="infographic-label">${safeLabel}</div>
        </div>
        <div class="infographic-trend ${trendClass}" aria-label="trend ${s.trend}">${trendIcon}</div>
      </div>
    `;
  }).join('');

  return `
    <div class="infographic-grid" role="region" aria-label="Key statistics">
      ${cards}
    </div>
  `;
}

/**
 * Animate the numeric counter on newly added infographic stat values.
 */
function animateStatValues(container) {
  container.querySelectorAll('.infographic-value').forEach(el => {
    const raw = el.dataset.target || '';
    // Only animate if the value is a plain number or ends with %
    const numStr = raw.replace('%', '').replace(',', '');
    const num = parseFloat(numStr);
    if (isNaN(num)) return;

    const isPercent = raw.includes('%');
    const isInt = Number.isInteger(num);
    const duration = 900; // ms
    const steps = 40;
    const step = duration / steps;
    let current = 0;
    let frame = 0;

    const timer = setInterval(() => {
      frame++;
      current = num * (frame / steps);
      const display = isInt ? Math.round(current) : current.toFixed(1);
      el.textContent = display + (isPercent ? '%' : '');
      if (frame >= steps) {
        el.textContent = raw; // restore exact original
        clearInterval(timer);
      }
    }, step);
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Typing indicator — multi-step progress
// ─────────────────────────────────────────────────────────────────────────────
function showTyping() {
  const id = `typing-${Date.now()}`;
  const el = document.createElement('div');
  el.className = 'message assistant'; el.id = id;
  el.setAttribute('aria-label', 'StatGPT is analysing data');
  el.innerHTML = `
    <div class="msg-avatar" aria-hidden="true">📊</div>
    <div class="msg-body">
      <div class="msg-bubble">
        <div class="typing-indicator" aria-hidden="true">
          <span></span><span></span><span></span>
          <span class="typing-label" id="${id}-label">${TYPING_STEPS[0]}</span>
        </div>
      </div>
    </div>
  `;
  $chat.appendChild(el);
  scrollBottom();

  // Rotate through step labels
  let stepIdx = 0;
  el._stepTimer = setInterval(() => {
    stepIdx = (stepIdx + 1) % TYPING_STEPS.length;
    const label = document.getElementById(`${id}-label`);
    if (label) {
      label.style.opacity = '0';
      setTimeout(() => {
        label.textContent = TYPING_STEPS[stepIdx];
        label.style.opacity = '1';
      }, 150);
    }
  }, 1800);

  return id;
}

function removeTyping(id) {
  const el = $(id);
  if (el) {
    if (el._stepTimer) clearInterval(el._stepTimer);
    el.remove();
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Table renderer
// ─────────────────────────────────────────────────────────────────────────────
function renderTable(rows) {
  if (!rows?.length) return '';
  const cols = Object.keys(rows[0]);
  const th = cols.map(c => `<th scope="col">${escHtml(String(c))}</th>`).join('');
  const tb = rows.map((r, i) =>
    `<tr class="${i % 2 === 0 ? 'row-even' : 'row-odd'}">${cols.map(c => `<td>${escHtml(String(r[c]??''))}</td>`).join('')}</tr>`
  ).join('');
  return `<div class="data-table-wrap" role="region" aria-label="Data table">
    <table class="data-table">
      <thead><tr>${th}</tr></thead>
      <tbody>${tb}</tbody>
    </table>
  </div>`;
}

// ─────────────────────────────────────────────────────────────────────────────
// Chart renderer
// ─────────────────────────────────────────────────────────────────────────────
const PALETTE = [
  'rgba(99,102,241,', 'rgba(16,185,129,',  'rgba(245,158,11,',
  'rgba(6,182,212,',  'rgba(244,63,94,',   'rgba(168,85,247,',
];

function renderChart(id, cfg) {
  const canvas = $(id); if (!canvas) return;
  const type = cfg.type || 'bar';

  const datasets = (cfg.datasets||[]).map((ds, i) => {
    const base = PALETTE[i % PALETTE.length];
    return {
      label: ds.label || '',
      data: ds.data || [],
      backgroundColor: type === 'line' ? `${base}0.12)` : `${base}0.8)`,
      borderColor:     `${base}1)`,
      borderWidth: type === 'line' ? 2 : 0,
      pointBackgroundColor: `${base}1)`,
      pointRadius: type === 'line' ? 4 : 0,
      pointHoverRadius: type === 'line' ? 6 : 0,
      tension: 0.4, fill: type === 'line',
    };
  });

  const chart = new Chart(canvas, {
    type,
    data: { labels: cfg.labels||[], datasets },
    options: {
      responsive: true, maintainAspectRatio: true,
      animation: { duration: 800, easing: 'easeOutQuart' },
      interaction: { mode:'index', intersect:false },
      plugins: {
        legend: {
          display: datasets.length > 1,
          labels: { color:'#64748b', usePointStyle:true, padding:14, font:{size:11} },
        },
        tooltip: {
          backgroundColor: 'rgba(10,14,26,0.97)',
          borderColor: 'rgba(99,102,241,0.2)', borderWidth:1,
          padding:12, titleFont:{weight:'700',size:12},
          callbacks: { label: ctx => `  ${ctx.dataset.label}: ${ctx.parsed.y??ctx.parsed}` },
        },
      },
      scales: type === 'pie' ? {} : {
        x: { grid:{color:'rgba(255,255,255,0.03)'}, ticks:{color:'#475569',maxRotation:40} },
        y: { grid:{color:'rgba(255,255,255,0.05)'}, ticks:{color:'#475569'}, beginAtZero:false },
      },
    },
  });
  _charts[id] = chart;
}

// ─────────────────────────────────────────────────────────────────────────────
// Utilities
// ─────────────────────────────────────────────────────────────────────────────
function setLoading(v) {
  _isLoading = v;
  $sendBtn.disabled = v;
  $input.disabled = v;
}
function scrollBottom() {
  requestAnimationFrame(() => $chat.scrollTo({ top: $chat.scrollHeight, behavior:'smooth' }));
}
function fmtTime() {
  return new Date().toLocaleTimeString('en-IN', { hour:'2-digit', minute:'2-digit' });
}
function escHtml(s) {
  return String(s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

/**
 * Render lightweight markdown:
 * **bold**, *italic*, `code`, bullet lists, numbered lists, newlines.
 */
function renderMd(text) {
  if (!text) return '';
  // Escape HTML first, then apply markdown
  let html = escHtml(text)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,     '<em>$1</em>')
    .replace(/`([^`]+)`/g,     '<code>$1</code>');

  // Convert bullet list lines (- item or * item)
  html = html.replace(/((?:^|\n)(?:- |\* ).+)+/g, match => {
    const items = match.trim().split(/\n/).map(line =>
      `<li>${line.replace(/^[-*]\s+/, '')}</li>`
    ).join('');
    return `<ul class="md-list">${items}</ul>`;
  });

  // Convert numbered list lines (1. item)
  html = html.replace(/((?:^|\n)\d+\.\s.+)+/g, match => {
    const items = match.trim().split(/\n/).map(line =>
      `<li>${line.replace(/^\d+\.\s+/, '')}</li>`
    ).join('');
    return `<ol class="md-list">${items}</ol>`;
  });

  // Remaining newlines → line breaks
  html = html.replace(/\n/g, '<br>');
  return html;
}
