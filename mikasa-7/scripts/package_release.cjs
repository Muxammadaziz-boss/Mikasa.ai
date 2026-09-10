// ========== package_release.cjs ==========
// Mikasa AI 7.0 — Release Packaging and Version Management Script
// Places every built version into: yordamchi_7.0.0/release/v<version>/

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

// 1. Get current version from package.json
const packageJsonPath = path.resolve(__dirname, "../package.json");
const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, "utf-8"));
const version = packageJson.version || "7.0.0";
const versionName = `v${version}`;

// 2. Define release target directory inside yordamchi_7.0.0/release/v<version>
const projectRoot = path.resolve(__dirname, "../../");
const releaseBaseDir = path.resolve(projectRoot, "release");
const releaseVersionDir = path.join(releaseBaseDir, versionName);

console.log(`========================================`);
console.log(`📦 MIKASA AI Release Packaging: ${versionName}`);
console.log(`Katalog: ${releaseVersionDir}`);
console.log(`========================================`);

if (!fs.existsSync(releaseBaseDir)) {
  fs.mkdirSync(releaseBaseDir, { recursive: true });
}
if (!fs.existsSync(releaseVersionDir)) {
  fs.mkdirSync(releaseVersionDir, { recursive: true });
}

// 3. Locate built binaries
const tauriReleaseDir = path.resolve(__dirname, "../src-tauri/target/release");
const tauriBundleDir = path.join(tauriReleaseDir, "bundle");

const exeSource = path.join(tauriReleaseDir, "mikasa-7.exe");
const exeTarget = path.join(releaseVersionDir, `Mikasa-AI-${versionName}.exe`);

const manifest = {
  app: "Mikasa AI",
  version: version,
  version_name: versionName,
  release_date: new Date().toISOString(),
  files: [],
  backend: {
    service: "core/api_server.py",
    port: 18420,
    protocol: "HTTP/REST + WebSocket",
  },
};

function calculateSha256(filePath) {
  const fileBuffer = fs.readFileSync(filePath);
  return crypto.createHash("sha256").update(fileBuffer).digest("hex");
}

function copyFileWithLog(src, dest, friendlyName) {
  if (fs.existsSync(src)) {
    fs.copyFileSync(src, dest);
    const stat = fs.statSync(dest);
    const hash = calculateSha256(dest);
    console.log(`✔ ${friendlyName}: ${path.basename(dest)} (${(stat.size / (1024 * 1024)).toFixed(2)} MB)`);
    manifest.files.push({
      name: path.basename(dest),
      size_bytes: stat.size,
      size_mb: parseFloat((stat.size / (1024 * 1024)).toFixed(2)),
      sha256: hash,
    });
    return true;
  } else {
    console.warn(`⚠ Topilmadi: ${src}`);
    return false;
  }
}

// 4. Copy Standalone Executable
copyFileWithLog(exeSource, exeTarget, "Mustaqil (.exe)");

// 5. Copy MSI Installer if exists
const msiDir = path.join(tauriBundleDir, "msi");
if (fs.existsSync(msiDir)) {
  const msiFiles = fs.readdirSync(msiDir).filter((f) => f.endsWith(".msi"));
  if (msiFiles.length > 0) {
    const srcMsi = path.join(msiDir, msiFiles[0]);
    const destMsi = path.join(releaseVersionDir, `Mikasa-AI-${versionName}.msi`);
    copyFileWithLog(srcMsi, destMsi, "MSI Installer");
  }
}

// 6. Copy NSIS Setup if exists
const nsisDir = path.join(tauriBundleDir, "nsis");
if (fs.existsSync(nsisDir)) {
  const nsisFiles = fs.readdirSync(nsisDir).filter((f) => f.endsWith(".exe"));
  if (nsisFiles.length > 0) {
    const srcNsis = path.join(nsisDir, nsisFiles[0]);
    const destNsis = path.join(releaseVersionDir, `Mikasa-AI-Setup-${versionName}.exe`);
    copyFileWithLog(srcNsis, destNsis, "NSIS Setup (.exe)");
  }
}

// 7. Write Quick One-Click Launcher (run_portable.bat)
const launcherBatContent = `@echo off
title Mikasa AI ${versionName} Launcher
cd /d "%~dp0"
echo ========================================================
echo   MIKASA AI ${versionName} — Ishga tushirilmoqda...
echo ========================================================

REM 1. Orqa fonda Python backend xizmati mavjudligini tekshirish
powershell -NoProfile -Command "$conn = Test-NetConnection -ComputerName 127.0.0.1 -Port 18420 -WarningAction SilentlyContinue -InformationLevel Quiet; if (-not $conn) { Write-Host 'Python Backend ishga tushirilmoqda (127.0.0.1:18420)...' -ForegroundColor Cyan; $py1 = '..\\..\\..\\.venv\\Scripts\\python.exe'; $py2 = '..\\..\\.venv\\Scripts\\python.exe'; $workDir = (Resolve-Path '..\\..').Path; if (Test-Path $py1) { Start-Process -FilePath (Resolve-Path $py1).Path -ArgumentList 'core\\api_server.py' -WorkingDirectory $workDir -WindowStyle Hidden } elseif (Test-Path $py2) { Start-Process -FilePath (Resolve-Path $py2).Path -ArgumentList 'core\\api_server.py' -WorkingDirectory $workDir -WindowStyle Hidden } else { Start-Process -FilePath 'python' -ArgumentList 'core\\api_server.py' -WorkingDirectory $workDir -WindowStyle Hidden } Start-Sleep -Seconds 2 }"

REM 2. Desktop ilovani ochish
start "" "Mikasa-AI-${versionName}.exe"
`;

const batPath = path.join(releaseVersionDir, "run_portable.bat");
fs.writeFileSync(batPath, launcherBatContent, "utf-8");
console.log(`✔ Ishga tushirish fayli: run_portable.bat`);

// 8. Write Manifest
const manifestPath = path.join(releaseVersionDir, "version_manifest.json");
fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), "utf-8");
console.log(`✔ Versiya manifesti: version_manifest.json`);

// 9. Update global RELEASES.md in release directory
const releasesMdPath = path.join(releaseBaseDir, "RELEASES.md");
let existingReleases = "";
if (fs.existsSync(releasesMdPath)) {
  existingReleases = fs.readFileSync(releasesMdPath, "utf-8");
}

const releaseEntry = `### [${versionName}] — ${new Date().toLocaleDateString("uz-UZ")}
- **Desktop Ilova**: \`${versionName}/Mikasa-AI-${versionName}.exe\`
- **Windows MSI**: \`${versionName}/Mikasa-AI-${versionName}.msi\`
- **NSIS Setup**: \`${versionName}/Mikasa-AI-Setup-${versionName}.exe\`
- **Manifest**: \`${versionName}/version_manifest.json\`
- **Backend**: Python API Server (\`http://127.0.0.1:18420\`)

`;

if (!existingReleases.includes(`### [${versionName}]`)) {
  const newReleasesMd = `# 🚀 Mikasa AI Versiyalar Arxiv (Releases Archive)\n\n` + releaseEntry + existingReleases.replace("# 🚀 Mikasa AI Versiyalar Arxiv (Releases Archive)\n\n", "");
  fs.writeFileSync(releasesMdPath, newReleasesMd, "utf-8");
}

console.log(`========================================`);
console.log(`✨ ${versionName} reliz muvaffaqiyatli saqlandi!`);
console.log(`========================================`);
