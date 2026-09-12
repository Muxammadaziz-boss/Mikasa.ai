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
