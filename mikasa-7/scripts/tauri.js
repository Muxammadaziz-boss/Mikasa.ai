import { spawn, execSync } from 'child_process';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '..');

// 1. Ensure w64devkit is in PATH
const w64devkitBin = 'D:\\tools\\w64devkit\\bin';
const env = { ...process.env };
if (fs.existsSync(w64devkitBin)) {
  env.PATH = `${w64devkitBin};${env.PATH || ''}`;
}

// 2. Ensure NTFS junction D:\Mikasa exists if running inside a path with spaces
let workingDir = projectRoot;
if (projectRoot.includes('Ishchi stoli')) {
  const junctionRoot = 'D:\\Mikasa';
  if (!fs.existsSync(junctionRoot)) {
    try {
      execSync(`cmd /c mklink /J "D:\\Mikasa" "D:\\Ishchi stoli\\Mikasa"`);
    } catch {}
  }
  const relativePath = path.relative('D:\\Ishchi stoli\\Mikasa', projectRoot);
  const junctionPath = path.join(junctionRoot, relativePath);
  if (fs.existsSync(junctionPath)) {
    workingDir = junctionPath;
  }
}

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
