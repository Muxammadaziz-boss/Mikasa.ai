import { spawn, execSync } from 'child_process';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '..');

// 1. Dynamic Toolchain Discovery (if configured in environment)
const env = { ...process.env };
const toolchainCandidates = [
  process.env.W64DEVKIT_BIN,
  process.env.MINGW_HOME ? path.join(process.env.MINGW_HOME, 'bin') : null,
  process.env.CARGO_HOME ? path.join(process.env.CARGO_HOME, 'bin') : null,
].filter(Boolean);

for (const dir of toolchainCandidates) {
  if (fs.existsSync(dir)) {
    env.PATH = `${dir};${env.PATH || ''}`;
    break;
  }
}

// 2. Working directory is projectRoot (portable across any folder)
const workingDir = projectRoot;

// 3. Forward all CLI arguments to tauri
const args = process.argv.slice(2);
const tauriCli = path.resolve(projectRoot, 'node_modules', '@tauri-apps', 'cli', 'tauri.js');

const child = spawn(process.execPath, [tauriCli, ...args], {
  cwd: workingDir,
  env,
  stdio: 'inherit'
});

child.on('exit', (code) => {
  process.exit(code || 0);
});
