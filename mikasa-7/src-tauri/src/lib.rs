// ========== lib.rs ==========
// Mikasa AI 7.x — Native Desktop Window Management & Runtime Backend Supervisor
// [Phase 1 & 2] To'liq mahalliy boshqaruv, dinamik yo'llar, va bolalar jarayonlarini xavfsiz tozalash

use std::net::TcpStream;
use std::path::PathBuf;
use std::process::{Child, Command};
use std::sync::{Arc, Mutex};
use std::time::Duration;

#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

#[derive(Clone, Default)]
pub struct SupervisorState {
    pub backend_child: Arc<Mutex<Option<Child>>>,
    pub backend_pid: Arc<Mutex<Option<u32>>>,
}

pub fn stop_backend(state: &SupervisorState) {
    if let Ok(mut lock) = state.backend_child.lock() {
        if let Some(mut child) = lock.take() {
            let pid = child.id();
            #[cfg(target_os = "windows")]
            {
                const CREATE_NO_WINDOW: u32 = 0x08000000;
                let _ = Command::new("taskkill")
                    .args(["/F", "/T", "/PID", &pid.to_string()])
                    .creation_flags(CREATE_NO_WINDOW)
                    .status();
            }
            let _ = child.kill();
            let _ = child.wait();
        }
    }
    if let Ok(mut pid_lock) = state.backend_pid.lock() {
        *pid_lock = None;
    }
}

fn resolve_base_dir() -> Option<PathBuf> {
    // 1. Ijro etilayotgan .exe fayli orqali tekshirish
    if let Ok(exe_path) = std::env::current_exe() {
        let mut curr = exe_path.as_path();
        while let Some(parent) = curr.parent() {
            if parent.join("core").join("api_server.py").exists() {
                return Some(parent.to_path_buf());
            }
            if parent.join("yordamchi_7.0.0").join("core").join("api_server.py").exists() {
                return Some(parent.join("yordamchi_7.0.0"));
            }
            curr = parent;
        }
    }

    // 2. Joriy ishchi katalog orqali tekshirish
    if let Ok(cwd) = std::env::current_dir() {
        if cwd.join("core").join("api_server.py").exists() {
            return Some(cwd);
        }
        if cwd.join("yordamchi_7.0.0").join("core").join("api_server.py").exists() {
            return Some(cwd.join("yordamchi_7.0.0"));
        }
        let mut curr = cwd.as_path();
        while let Some(parent) = curr.parent() {
            if parent.join("core").join("api_server.py").exists() {
                return Some(parent.to_path_buf());
            }
            if parent.join("yordamchi_7.0.0").join("core").join("api_server.py").exists() {
                return Some(parent.join("yordamchi_7.0.0"));
            }
            curr = parent;
        }
    }

    None
}

fn find_python_executable(base_dir: &PathBuf) -> Option<PathBuf> {
    let mut candidates: Vec<PathBuf> = Vec::new();
    candidates.push(base_dir.join(".venv").join("Scripts").join("python.exe"));
    if let Some(p1) = base_dir.parent() {
        candidates.push(p1.join(".venv").join("Scripts").join("python.exe"));
        if let Some(p2) = p1.parent() {
            candidates.push(p2.join(".venv").join("Scripts").join("python.exe"));
        }
    }

    for py in candidates {
        if py.exists() {
            return Some(py);
        }
    }
    None
}

pub fn ensure_backend_running(state: &SupervisorState) {
    // 1. Agar 127.0.0.1:18420 allaqachon ishlab turgan bo'lsa, qayta ochmaymiz
    if let Ok(addr) = "127.0.0.1:18420".parse() {
        if TcpStream::connect_timeout(&addr, Duration::from_millis(300)).is_ok() {
            return;
        }
    }

    // 2. Dinamik ravishda asosiy loyiha katalogini aniqlash
    let base_dir = match resolve_base_dir() {
        Some(b) => b,
        None => return,
    };

    #[cfg(target_os = "windows")]
    const CREATE_NO_WINDOW: u32 = 0x08000000;

    let mut launched = false;

    // 3. Virtual muhitdagi python.exe orqali ishga tushirish
    if let Some(py) = find_python_executable(&base_dir) {
        let mut cmd = Command::new(&py);
        cmd.arg("core/api_server.py")
            .current_dir(&base_dir);

        #[cfg(target_os = "windows")]
        cmd.creation_flags(CREATE_NO_WINDOW);

        if let Ok(child) = cmd.spawn() {
            let pid = child.id();
            if let Ok(mut lock) = state.backend_child.lock() {
                *lock = Some(child);
            }
            if let Ok(mut pid_lock) = state.backend_pid.lock() {
                *pid_lock = Some(pid);
            }
            launched = true;
        }
    }

    // 4. Fallback: tizimdagi python
    if !launched {
        let mut cmd = Command::new("python");
        cmd.arg("core/api_server.py")
            .current_dir(&base_dir);

        #[cfg(target_os = "windows")]
        cmd.creation_flags(CREATE_NO_WINDOW);

        if let Ok(child) = cmd.spawn() {
            let pid = child.id();
            if let Ok(mut lock) = state.backend_child.lock() {
                *lock = Some(child);
            }
            if let Ok(mut pid_lock) = state.backend_pid.lock() {
                *pid_lock = Some(pid);
            }
        }
    }

    // 5. Tayyor bo'lguncha kutish (readiness polling: maks 15 soniya)
    if let Ok(addr) = "127.0.0.1:18420".parse() {
        for _ in 0..50 {
            if TcpStream::connect_timeout(&addr, Duration::from_millis(300)).is_ok() {
                break;
            }
            std::thread::sleep(Duration::from_millis(300));
        }
    }
}

// ========== Tauri Buyruqlari (IPC Commands) ==========

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
fn app_close(window: tauri::Window, state: tauri::State<SupervisorState>) -> Result<(), String> {
    stop_backend(&state);
    window.close().map_err(|e| e.to_string())
}

#[tauri::command]
fn app_is_maximized(window: tauri::Window) -> Result<bool, String> {
    window.is_maximized().map_err(|e| e.to_string())
}

#[tauri::command]
fn backend_get_status(state: tauri::State<SupervisorState>) -> serde_json::Value {
    let is_reachable = if let Ok(addr) = "127.0.0.1:18420".parse() {
        TcpStream::connect_timeout(&addr, Duration::from_millis(300)).is_ok()
    } else {
        false
    };
    let pid = state.backend_pid.lock().ok().and_then(|p| *p);
    serde_json::json!({
        "running": is_reachable,
        "port": 18420,
        "pid": pid,
        "managed": pid.is_some()
    })
}

#[tauri::command]
fn backend_restart(state: tauri::State<SupervisorState>) -> Result<bool, String> {
    stop_backend(&state);
    std::thread::sleep(Duration::from_millis(500));
    let state_clone = state.inner().clone();
    std::thread::spawn(move || {
        ensure_backend_running(&state_clone);
    });
    Ok(true)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let supervisor_state = SupervisorState::default();
    let state_for_setup = supervisor_state.clone();
    let state_for_window = supervisor_state.clone();
    let state_for_exit = supervisor_state.clone();

    tauri::Builder::default()
        .manage(supervisor_state)
        .setup(move |_app| {
            std::thread::spawn(move || {
                ensure_backend_running(&state_for_setup);
            });
            Ok(())
        })
        .on_window_event(move |_window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                stop_backend(&state_for_window);
            }
        })
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            greet,
            app_minimize,
            app_toggle_maximize,
            app_close,
            app_is_maximized,
            backend_get_status,
            backend_restart
        ])
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(move |_app_handle, event| {
            if let tauri::RunEvent::ExitRequested { .. } | tauri::RunEvent::Exit = event {
                stop_backend(&state_for_exit);
            }
        });
}

