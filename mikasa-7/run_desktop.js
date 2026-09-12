// ========== run_desktop.js ==========
// Mikasa AI 7.x — Native Desktop Launcher
// [Phase 1] Chrome/Edge --app rejimi butunlay bekor qilindi.
// Endi to'g'ridan-to'g'ri mahalliy Tauri 2 desktop oynasi (Mikasa AI.exe) ishga tushadi.

import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

console.log('\x1b[36m===================================================\x1b[0m');
console.log('\x1b[36m   MIKASA AI 7.x — MAHALLIY DESKTOP ILOVASI       \x1b[0m');
console.log('\x1b[36m===================================================\x1b[0m');
console.log('\x1b[33m[Eslatma] Chrome/Edge --app rejimi o\'rniga toza mahalliy Tauri oynasi ochilmoqda...\x1b[0m\n');

const tauriScript = path.resolve(__dirname, 'scripts', 'tauri.js');
const child = spawn(process.execPath, [tauriScript, 'dev'], {
  cwd: __dirname,
  stdio: 'inherit'
});

child.on('exit', (code) => {
  process.exit(code || 0);
});

