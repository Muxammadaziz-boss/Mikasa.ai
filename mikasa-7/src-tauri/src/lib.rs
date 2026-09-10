// ========== lib.rs ==========
// Mikasa AI 7.0 — Desktop Native Window Management & Backend Automation

use std::process::Command;

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[tauri::command]
fn app_minimize(window: tauri::Window) -> Result<(), String> {
    window.minimize().map_err(|e| e.to_string())
}

#[tauri::command]
fn app_toggle_maximize(window: tauri::Window) -> Result<bool, String> {
    let is_max = window.is_maximized().map_err(|e| e.to_string())?;
    if is_max {
        window.unmaximize().map_err(|e| e.to_string())?;
        Ok(false)
    } else {
        window.maximize().map_err(|e| e.to_string())?;
        Ok(true)
    }
}

#[tauri::command]
fn app_close(window: tauri::Window) -> Result<(), String> {
    window.close().map_err(|e| e.to_string())
}

#[tauri::command]
fn app_is_maximized(window: tauri::Window) -> Result<bool, String> {
    window.is_maximized().map_err(|e| e.to_string())
}

#[cfg(target_os = "windows")]
fn ensure_backend_running() {
    use std::net::TcpStream;
    use std::time::Duration;
    use std::path::PathBuf;
    use std::os::windows::process::CommandExt;

    const CREATE_NO_WINDOW: u32 = 0x08000000;

    // 1. Check if 127.0.0.1:18420 is already reachable
    if let Ok(addr) = "127.0.0.1:18420".parse() {
        if TcpStream::connect_timeout(&addr, Duration::from_millis(300)).is_ok() {
            return; // Already running!
        }
    }

    // 2. Dynamically resolve base_dir containing core/api_server.py
    let mut resolved_base: Option<PathBuf> = None;
    if let Ok(exe_path) = std::env::current_exe() {
        let mut curr = exe_path.as_path();
        while let Some(parent) = curr.parent() {
            if parent.join("core").join("api_server.py").exists() {
                resolved_base = Some(parent.to_path_buf());
                break;
            }
            if parent.join("yordamchi_7.0.0").join("core").join("api_server.py").exists() {
                resolved_base = Some(parent.join("yordamchi_7.0.0"));
                break;
            }
            curr = parent;
        }
    }

    let base_dir = resolved_base.unwrap_or_else(|| {
        PathBuf::from(r"D:\Ishchi stoli\Mikasa\yordamchi_7.0.0")
    });

    // 3. Find Python executable
    let mut candidates: Vec<PathBuf> = Vec::new();

    if let Some(parent) = base_dir.parent() {
        candidates.push(parent.join(".venv").join("Scripts").join("python.exe"));
    }
    candidates.push(base_dir.join(".venv").join("Scripts").join("python.exe"));
    candidates.push(PathBuf::from(r"D:\Ishchi stoli\Mikasa\.venv\Scripts\python.exe"));

    let mut launched = false;
    for py in candidates {
        if py.exists() {
            let res = Command::new(&py)
                .arg("core/api_server.py")
                .current_dir(&base_dir)
                .creation_flags(CREATE_NO_WINDOW)
                .spawn();
            if res.is_ok() {
                launched = true;
                break;
            }
        }
    }

    if !launched {
        let _ = Command::new("python")
            .arg("core/api_server.py")
            .current_dir(&base_dir)
            .creation_flags(CREATE_NO_WINDOW)
            .spawn();
    }

    // 4. Give it a moment to bind to the port
    if let Ok(addr) = "127.0.0.1:18420".parse() {
        for _ in 0..10 {
            if TcpStream::connect_timeout(&addr, Duration::from_millis(200)).is_ok() {
                break;
            }
            std::thread::sleep(Duration::from_millis(250));
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|_app| {
            #[cfg(target_os = "windows")]
            std::thread::spawn(|| {
                ensure_backend_running();
            });
            Ok(())
        })
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            greet,
            app_minimize,
            app_toggle_maximize,
            app_close,
            app_is_maximized
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
