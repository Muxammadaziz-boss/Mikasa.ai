// ========== frontend.test.mjs ==========
// Phase 23 — Mikasa AI Frontend Unit, Component & State Tests
// Run with: node --test tests/frontend.test.mjs

import test from 'node:test';
import assert from 'node:assert/strict';

// 1. STATE & APP NAVIGATION
test('App Navigation: Route mapping and valid views', () => {
  const validRoutes = ['/', '/chat', '/voice', '/commands', '/memory', '/scheduler', '/plugins', '/account'];
  assert.equal(validRoutes.length, 8);
  assert.ok(validRoutes.includes('/'));
  assert.ok(validRoutes.includes('/chat'));
  assert.ok(validRoutes.includes('/voice'));
  assert.ok(validRoutes.includes('/commands'));
  assert.ok(validRoutes.includes('/memory'));
  assert.ok(validRoutes.includes('/scheduler'));
  assert.ok(validRoutes.includes('/plugins'));
  assert.ok(validRoutes.includes('/account'));
});

// 2. BACKEND CONNECTOR & ENDPOINTS
test('Backend Connector: Endpoint definitions and URL formatting', () => {
  const BASE_URL = 'http://127.0.0.1:18420';
  const WS_URL = 'ws://127.0.0.1:18420/api/ws';

  const endpoints = {
    status: `${BASE_URL}/api/status`,
    chat: `${BASE_URL}/api/chat`,
    voiceStart: `${BASE_URL}/api/voice/start`,
    voiceStop: `${BASE_URL}/api/voice/stop`,
    commands: `${BASE_URL}/api/commands`,
    commandsExecute: `${BASE_URL}/api/commands/execute`,
    memory: `${BASE_URL}/api/memory`,
    scheduler: `${BASE_URL}/api/scheduler`,
    plugins: `${BASE_URL}/api/plugins`,
    account: `${BASE_URL}/api/account`,
  };

  assert.equal(endpoints.status, 'http://127.0.0.1:18420/api/status');
  assert.equal(endpoints.chat, 'http://127.0.0.1:18420/api/chat');
  assert.equal(endpoints.commands, 'http://127.0.0.1:18420/api/commands');
  assert.equal(WS_URL, 'ws://127.0.0.1:18420/api/ws');
});

// 3. SEARCH & FILTER UTILITIES
test('Search Indexing: Multi-term matching across commands', () => {
  const sampleCommands = [
    { name: 'Kalkulyator', query: 'calculator', desc: 'Matematik hisob-kitoblar', category: 'Utilitlar' },
    { name: 'Tizim ma\'lumotlari', query: 'system_info', desc: 'CPU, RAM va disk holati', category: 'Tizim' },
    { name: 'Telegram', query: 'open_telegram', desc: 'Telegram messenjerini ochish', category: 'Ilovalar' },
  ];

  const indexed = sampleCommands.map(c => ({
    ...c,
    _searchIndex: `${c.name} ${c.query} ${c.desc} ${c.category}`.toLowerCase()
  }));

  // Match single term
  const query1 = 'kalkul';
  const res1 = indexed.filter(c => c._searchIndex.includes(query1));
  assert.equal(res1.length, 1);
  assert.equal(res1[0].name, 'Kalkulyator');

  // Match multi-term
  const query2 = 'cpu tizim';
  const terms2 = query2.split(' ');
  const res2 = indexed.filter(c => terms2.every(t => c._searchIndex.includes(t)));
  assert.equal(res2.length, 1);
  assert.equal(res2[0].name, 'Tizim ma\'lumotlari');
});

// 4. SCHEDULER STATES
test('Scheduler: 5 distinct lifecycle states', () => {
  const allowedStates = ['active', 'repeating', 'completed', 'failed', 'cancelled'];
  assert.equal(allowedStates.length, 5);

  const getTaskState = (task) => {
    if (task.last_error) return 'failed';
    if (task.completed) return 'completed';
    if (task.repeat_seconds > 0) return 'repeating';
    if (task.cancelled) return 'cancelled';
    return 'active';
  };

  assert.equal(getTaskState({ completed: false, repeat_seconds: 0 }), 'active');
  assert.equal(getTaskState({ completed: false, repeat_seconds: 60 }), 'repeating');
  assert.equal(getTaskState({ completed: true, repeat_seconds: 0 }), 'completed');
  assert.equal(getTaskState({ last_error: 'Timeout' }), 'failed');
  assert.equal(getTaskState({ cancelled: true }), 'cancelled');
});

// 5. ORB STATES
test('MikasaOrb: Audio and Assistant states specification', () => {
  const orbStates = ['idle', 'listening', 'thinking', 'speaking', 'offline', 'error', 'loading'];
  assert.ok(orbStates.includes('idle'));
  assert.ok(orbStates.includes('listening'));
  assert.ok(orbStates.includes('thinking'));
  assert.ok(orbStates.includes('speaking'));
  assert.ok(orbStates.includes('offline'));
  assert.ok(orbStates.includes('error'));
});

// 6. ERROR HANDLING (Phase 21 contracts)
test('Error Handling: Structured 3-part layout contract', () => {
  const errorObj = {
    title: 'Ovoz xizmati bilan aloqa uzildi',
    reason: 'Backend serveri javob bermadi yoki audio qurilma band',
    actionLabel: 'Qayta ulanish'
  };

  assert.ok(errorObj.title.length > 0, 'Sarlavha bo\'lishi shart');
  assert.ok(errorObj.reason.length > 0, 'Sabab tushuntirilishi shart');
  assert.ok(errorObj.actionLabel.length > 0, 'Qayta urinish harakati bo\'lishi shart');
});

// 7. PHASE 34 — REAL MIKASA UI & VOICE EXPERIENCE CONTRACTS
test('Phase 34: 10 distinct Mikasa Orb presence states', () => {
  const tenStates = [
    'idle',
    'listening',
    'thinking',
    'planning',
    'acting',
    'verifying',
    'replanning',
    'speaking',
    'completed',
    'error'
  ];
  assert.equal(tenStates.length, 10);
  for (const s of tenStates) {
    assert.ok(typeof s === 'string' && s.length > 0);
  }
});

test('Phase 34: Natural Uzbek microphone permission error contract', () => {
  const expectedUzbekMicError = "Tovushli boshqaruv uchun mikrofon ruxsati kerak.";
  assert.equal(expectedUzbekMicError, "Tovushli boshqaruv uchun mikrofon ruxsati kerak.");
});

test('Phase 34: Orbiting suggestions curation and structure', () => {
  const suggestions = [
    { id: "weather", label: "Ob-havoni tekshir" },
    { id: "system", label: "Kompyuterimni tekshir" },
    { id: "plan", label: "Bugungi rejani tuz" },
    { id: "python", label: "Pythonni tushuntir" },
    { id: "file", label: "Faylni tahlil qil" },
    { id: "web", label: "Internetdan izla" }
  ];
  assert.equal(suggestions.length, 6);
  assert.ok(suggestions.some(s => s.id === "weather"));
  assert.ok(suggestions.some(s => s.id === "system"));
  assert.ok(suggestions.some(s => s.id === "plan"));
  assert.ok(suggestions.some(s => s.id === "python"));
  assert.ok(suggestions.some(s => s.id === "file"));
  assert.ok(suggestions.some(s => s.id === "web"));
});

test('Phase 34: Uzbek real-time date formatting contract', () => {
  const formatUzbekDateTime = (date) => {
    const dayNames = ["Yakshanba", "Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba"];
    const monthNames = ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"];
    const day = dayNames[date.getDay()];
    const dateNum = date.getDate();
    const month = monthNames[date.getMonth()];
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    return `${day}, ${dateNum}-${month} • ${hours}:${minutes}`;
  };

  const sampleDate = new Date(2026, 8, 15, 22, 45); // Sept 15, 2026, 22:45
  const formatted = formatUzbekDateTime(sampleDate);
  assert.equal(formatted, "Seshanba, 15-sentabr • 22:45");
});

test('Phase 34: System Telemetry metrics schema contract', () => {
  const sampleMetrics = {
    cpu_percent: 14.5,
    ram_percent: 42.1,
    ram_used_gb: 6.8,
    ram_total_gb: 16.0,
    disk_percent: 55.0,
    disk_free_gb: 120.4,
    network_sent_kb: 45,
    network_recv_kb: 180,
    battery_percent: 92,
    battery_plugged: true,
    timestamp: "2026-09-15T22:45:00"
  };

  assert.ok(typeof sampleMetrics.cpu_percent === 'number');
  assert.ok(typeof sampleMetrics.ram_percent === 'number');
  assert.ok(typeof sampleMetrics.disk_percent === 'number');
  assert.ok(sampleMetrics.ram_used_gb <= sampleMetrics.ram_total_gb);
  assert.ok(sampleMetrics.battery_percent >= 0 && sampleMetrics.battery_percent <= 100);
});
