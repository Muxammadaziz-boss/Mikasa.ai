#![windows_subsystem = "windows"]

use std::env;
use std::fs;
use std::net::TcpStream;
use std::path::PathBuf;
use std::process::Command;
use std::time::Duration;

const APP_VERSION: &str = "v8.0.0";
static APP_CORE_BYTES: &[u8] = include_bytes!("../../../mikasa-7/src-tauri/target/release/mikasa-7.exe");
static WEBVIEW2_BYTES: &[u8] = include_bytes!("../../../mikasa-7/src-tauri/target/release/WebView2Loader.dll");

fn main() {
    // 1. If writable, extract WebView2Loader.dll next to this running launcher
    if let Ok(current_exe) = env::current_exe() {
        if let Some(parent) = current_exe.parent() {
            let local_dll = parent.join("WebView2Loader.dll");
            if !local_dll.exists() || fs::metadata(&local_dll).map(|m| m.len()).unwrap_or(0) != WEBVIEW2_BYTES.len() as u64 {
                let _ = fs::write(&local_dll, WEBVIEW2_BYTES);
            }
        }
    }

    // 2. Prepare isolated local runtime folder in %LOCALAPPDATA%\MikasaAI\runtime\v8.0.0
    let local_app_data = env::var("LOCALAPPDATA")
        .map(PathBuf::from)
        .unwrap_or_else(|_| env::temp_dir());
    let runtime_dir = local_app_data.join("MikasaAI").join("runtime").join(APP_VERSION);
    let _ = fs::create_dir_all(&runtime_dir);

    let target_dll = runtime_dir.join("WebView2Loader.dll");
    let target_exe = runtime_dir.join("Mikasa-AI-Core.exe");

    // Write WebView2Loader.dll if missing or size differs
    if !target_dll.exists() || fs::metadata(&target_dll).map(|m| m.len()).unwrap_or(0) != WEBVIEW2_BYTES.len() as u64 {
        let _ = fs::write(&target_dll, WEBVIEW2_BYTES);
    }

    // Write core executable if missing or size differs
    if !target_exe.exists() || fs::metadata(&target_exe).map(|m| m.len()).unwrap_or(0) != APP_CORE_BYTES.len() as u64 {
        let _ = fs::write(&target_exe, APP_CORE_BYTES);
    }

    // 3. Check if backend port 18420 is listening; if not and running near repo, probe backend
    let is_backend_listening = TcpStream::connect_timeout(
        &"127.0.0.1:18420".parse().unwrap(),
        Duration::from_millis(150),
    ).is_ok();

    if !is_backend_listening {
        if let Ok(current_exe) = env::current_exe() {
            if let Some(parent) = current_exe.parent() {
                let candidates = [
                    parent.join("core").join("api_server.py"),
                    parent.join("..").join("core").join("api_server.py"),
                    parent.join("..").join("..").join("core").join("api_server.py"),
                ];
                for cand in &candidates {
                    if cand.exists() {
                        let work_dir = cand.parent().unwrap().parent().unwrap_or(parent);
                        let py_cands = [
                            work_dir.join(".venv").join("Scripts").join("python.exe"),
                            PathBuf::from("python.exe"),
                        ];
                        for py in &py_cands {
                            let _ = Command::new(py)
                                .arg("core/api_server.py")
                                .current_dir(work_dir)
                                .spawn();
                            break;
                        }
                        break;
                    }
                }
            }
        }
    }

    // 4. Launch the core Tauri executable
    let args: Vec<String> = env::args().skip(1).collect();
    let mut cmd = Command::new(&target_exe);
    cmd.args(&args);
    cmd.current_dir(&runtime_dir);

    let _ = cmd.spawn();
}
