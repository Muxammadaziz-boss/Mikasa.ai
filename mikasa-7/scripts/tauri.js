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

// 2. Working directory resolution (portable & space-safe on Windows MinGW toolchain)
let workingDir = projectRoot;
if (process.platform === 'win32' && workingDir.includes(' ')) {
  // If invoked from an active junction/subst without spaces, prefer it
  if (process.cwd() && !process.cwd().includes(' ')) {
    try {
      if (fs.realpathSync(process.cwd()) === fs.realpathSync(workingDir)) {
        workingDir = process.cwd();
      }
    } catch {}
  }

  // If still containing spaces, dynamically map space-ancestor to a root junction
  if (workingDir.includes(' ')) {
    const rootDrive = path.parse(workingDir).root;
    let spaceAncestor = workingDir;
    while (spaceAncestor && path.dirname(spaceAncestor) !== spaceAncestor) {
      const parent = path.dirname(spaceAncestor);
      if (!parent.includes(' ')) break;
      spaceAncestor = parent;
    }
    const junctionBase = path.join(rootDrive, 'mikasa_ws');
    try {
      if (!fs.existsSync(junctionBase)) {
        execSync(`cmd /c mklink /J "${junctionBase}" "${spaceAncestor}"`, { stdio: 'ignore' });
      }
      const rel = path.relative(spaceAncestor, workingDir);
      const spaceFreePath = path.join(junctionBase, rel);
      if (fs.existsSync(spaceFreePath)) {
        workingDir = spaceFreePath;
      }
    } catch {}
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
