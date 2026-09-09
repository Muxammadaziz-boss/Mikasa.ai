import { spawn } from 'child_process';
import net from 'net';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

console.log('\x1b[36m===================================================\x1b[0m');
console.log('\x1b[36m   MIKASA AI 7.0 - DESKTOP ISHCHI STOLI ILOVASI   \x1b[0m');
console.log('\x1b[36m===================================================\x1b[0m\n');

function checkServer(port, host = '127.0.0.1') {
  return new Promise((resolve) => {
    const socket = new net.Socket();
    socket.setTimeout(1000);
    socket.on('connect', () => {
      socket.destroy();
      resolve(true);
    });
    socket.on('timeout', () => {
      socket.destroy();
      resolve(false);
    });
    socket.on('error', () => {
      resolve(false);
    });
    socket.connect(port, host);
  });
}

async function startDevServer() {
  console.log('\x1b[33m[1/2] Frontend serveri tekshirilmoqda...\x1b[0m');
  const isRunning = await checkServer(1420);
  if (isRunning) {
    console.log('\x1b[32m[1/2] Frontend serveri allaqachon faol (Port 1420).\x1b[0m');
    return;
  }

  console.log('\x1b[33m[1/2] Frontend serveri ishga tushirilmoqda...\x1b[0m');
  const devProcess = spawn('cmd.exe', ['/c', 'npm', 'run', 'dev'], {
    cwd: __dirname,
    detached: true,
    stdio: 'ignore'
  });
  devProcess.unref();

  for (let i = 0; i < 20; i++) {
    await new Promise((r) => setTimeout(r, 500));
    if (await checkServer(1420)) {
      console.log('\x1b[32m[1/2] Frontend muvaffaqiyatli ishga tushdi!\x1b[0m');
      return;
    }
  }
}

async function launchDesktopWindow() {
  console.log('\x1b[36m[2/2] Mikasa AI 7.0 Desktop oynasi ochilmoqda...\x1b[0m');

  const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
  const chromeX86Path = 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe';
  const edgePath = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
  const edgePath64 = 'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe';

  const appUrl = 'http://localhost:1420';
  const appArgs = [`--app=${appUrl}`, '--window-size=1280,800', '--app-id=mikasa-ai-7'];

  let targetExe = null;
  if (fs.existsSync(chromePath)) targetExe = chromePath;
  else if (fs.existsSync(chromeX86Path)) targetExe = chromeX86Path;
  else if (fs.existsSync(edgePath)) targetExe = edgePath;
  else if (fs.existsSync(edgePath64)) targetExe = edgePath64;

  if (targetExe) {
    const appProcess = spawn(targetExe, appArgs, {
      detached: true,
      stdio: 'ignore'
    });
    appProcess.unref();
  } else {
    spawn('cmd.exe', ['/c', 'start', appUrl], {
      detached: true,
      stdio: 'ignore'
    }).unref();
  }

  console.log('\x1b[32mMikasa AI 7.0 Desktop oynasi ochildi!\x1b[0m\n');
}

async function main() {
  await startDevServer();
  await launchDesktopWindow();
}

main().catch(console.error);
