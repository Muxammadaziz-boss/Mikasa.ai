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
    use std::os::windows::process::CommandExt;

    const CREATE_NO_WINDOW: u32 = 0x08000000;

    // Check if 127.0.0.1:18420 is already reachable
    if let Ok(addr) = "127.0.0.1:18420".parse() {
        if TcpStream::connect_timeout(&addr, Duration::from_millis(300)).is_ok() {
            return; // Already running!
        }
    }

    let py_candidates = [
        r"D:\Ishchi stoli\Mikasa\.venv\Scripts\python.exe",
        r"..\..\.venv\Scripts\python.exe",
        r"..\.venv\Scripts\python.exe",
        "python",
    ];

    let base_dir = r"D:\Ishchi stoli\Mikasa\yordamchi_7.0.0";

    for py in py_candidates {
        if std::path::Path::new(py).exists() || py == "python" {
            let res = Command::new(py)
                .arg("core/api_server.py")
                .current_dir(base_dir)
                .creation_flags(CREATE_NO_WINDOW)
                .spawn();
            if res.is_ok() {
                break;
            }
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
