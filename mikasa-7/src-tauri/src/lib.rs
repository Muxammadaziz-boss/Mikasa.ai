// ========== lib.rs ==========
// Mikasa AI 8.0.0 — Native Desktop Window Management & Runtime Backend Supervisor
// To'liq mahalliy boshqaruv, HTTP /api/health tekshiruvi, bolalar jarayonlarini xavfsiz tozalash

use std::io::{Read, Write};
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
    pub is_managed: Arc<Mutex<bool>>,
    pub is_spawning: Arc<Mutex<bool>>,
}

/// HTTP GET /api/health tekshiruvi (Pure Rust stdlib, uchinchi tomon kutubxonalarisiz)
pub fn check_http_health(addr_str: &str, path: &str) -> bool {
    let addr: std::net::SocketAddr = match addr_str.parse() {
        Ok(a) => a,
        Err(_) => return false,
    };
    let mut stream = match TcpStream::connect_timeout(&addr, Duration::from_millis(500)) {
        Ok(s) => s,
        Err(_) => return false,
    };
    let _ = stream.set_read_timeout(Some(Duration::from_millis(1500)));
    let _ = stream.set_write_timeout(Some(Duration::from_millis(1500)));

    let request = format!(
        "GET {} HTTP/1.1\r\nHost: {}\r\nUser-Agent: MikasaDesktopSupervisor/8.0.0\r\nConnection: close\r\n\r\n",
        path, addr_str
    );
    if stream.write_all(request.as_bytes()).is_err() {
        return false;
    }

    let mut buf = [0u8; 2048];
    match stream.read(&mut buf) {
        Ok(n) if n > 0 => {
            let response = String::from_utf8_lossy(&buf[..n]);
            response.contains("200 OK") && (response.contains("\"status\"") || response.contains("Mikasa AI"))
        }
        _ => false,
    }
}

pub fn stop_backend(state: &SupervisorState) {
    // Faqat o'zimiz ishga tushirgan (managed) backendni to'xtatamiz
    let is_managed = state.is_managed.lock().map(|m| *m).unwrap_or(false);
    if !is_managed {
        println!("[MIKASA] Backend tashqi/mavjud jarayon bo'lgani uchun to'xtatilmadi (unmanaged)");
        return;
    }

    if let Ok(mut lock) = state.backend_child.lock() {
        if let Some(mut child) = lock.take() {
            let pid = child.id();
            println!("[MIKASA] Backend jarayoni to'xtatilmoqda (PID: {})...", pid);
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
            println!("[MIKASA] Backend jarayoni muvaffaqiyatli to'xtatildi");
        }
    }
    if let Ok(mut pid_lock) = state.backend_pid.lock() {
        *pid_lock = None;
    }
    if let Ok(mut managed_lock) = state.is_managed.lock() {
        *managed_lock = false;
    }
}

/// Standalone yig'ilgan backend binarisini qidirish
fn find_bundled_backend_binary() -> Option<(PathBuf, PathBuf)> {
    let mut candidates: Vec<(PathBuf, PathBuf)> = Vec::new();

    // 1. Joriy ishga tushgan exe yonidagi backend papkasi
    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            // exe_dir\backend\mikasa_backend.exe
            candidates.push((exe_dir.join("backend").join("mikasa_backend.exe"), exe_dir.join("backend")));
            // exe_dir\mikasa_backend.exe
            candidates.push((exe_dir.join("mikasa_backend.exe"), exe_dir.to_path_buf()));
            // exe_dir\resources\backend\mikasa_backend.exe (Tauri resources)
            candidates.push((exe_dir.join("resources").join("backend").join("mikasa_backend.exe"), exe_dir.join("resources").join("backend")));
            candidates.push((exe_dir.join("resources").join("mikasa_backend.exe"), exe_dir.join("resources")));
        }
    }

    // 2. Joriy ishchi katalog
    if let Ok(cwd) = std::env::current_dir() {
        candidates.push((cwd.join("backend").join("mikasa_backend.exe"), cwd.join("backend")));
        candidates.push((cwd.join("release").join("v8.0.0").join("backend").join("mikasa_backend.exe"), cwd.join("release").join("v8.0.0").join("backend")));
        candidates.push((cwd.join("mikasa-7").join("src-tauri").join("backend").join("mikasa_backend.exe"), cwd.join("mikasa-7").join("src-tauri").join("backend")));
    }

    // 3. LocalAppData runtime katalogi (%LOCALAPPDATA%\MikasaAI\runtime\v8.0.0\backend\)
    if let Ok(local_app_data) = std::env::var("LOCALAPPDATA") {
        let p = PathBuf::from(local_app_data);
        candidates.push((p.join("MikasaAI").join("runtime").join("v8.0.0").join("backend").join("mikasa_backend.exe"), p.join("MikasaAI").join("runtime").join("v8.0.0").join("backend")));
        candidates.push((p.join("MikasaAI").join("backend").join("mikasa_backend.exe"), p.join("MikasaAI").join("backend")));
    }

    // 4. Loyiha reliz katalogi fallback (agar .exe alohida ko'chirilgan bo'lsa)
    for root_str in &[
        r"D:\Mikasa\yordamchi_8.0.0\release\v8.0.0\backend",
        r"D:\Ishchi stoli\Mikasa\yordamchi_8.0.0\release\v8.0.0\backend",
    ] {
        let bdir = PathBuf::from(root_str);
        candidates.push((bdir.join("mikasa_backend.exe"), bdir));
    }

    for (exe, work_dir) in candidates {
        if exe.exists() {
            return Some((exe, work_dir));
        }
    }

    None
}

/// Rivojlantirish (dev) muhiti uchun loyiha katalogini aniqlash
fn resolve_dev_base_dir() -> Option<PathBuf> {
    if let Ok(exe_path) = std::env::current_exe() {
        let mut curr = exe_path.as_path();
        while let Some(parent) = curr.parent() {
            if parent.join("core").join("api_server.py").exists() {
                return Some(parent.to_path_buf());
            }
            if parent.join("yordamchi_8.0.0").join("core").join("api_server.py").exists() {
                return Some(parent.join("yordamchi_8.0.0"));
            }
            curr = parent;
        }
    }

    if let Ok(cwd) = std::env::current_dir() {
        if cwd.join("core").join("api_server.py").exists() {
            return Some(cwd);
        }
        if cwd.join("yordamchi_8.0.0").join("core").join("api_server.py").exists() {
            return Some(cwd.join("yordamchi_8.0.0"));
        }
        let mut curr = cwd.as_path();
        while let Some(parent) = curr.parent() {
            if parent.join("core").join("api_server.py").exists() {
                return Some(parent.to_path_buf());
            }
            if parent.join("yordamchi_8.0.0").join("core").join("api_server.py").exists() {
                return Some(parent.join("yordamchi_8.0.0"));
            }
            curr = parent;
        }
    }

    None
}

/// Rivojlantirish muhitidagi python.exe ni aniqlash
fn find_dev_python_executable(base_dir: &PathBuf) -> Option<PathBuf> {
    let mut candidates: Vec<PathBuf> = Vec::new();
    candidates.push(base_dir.join(".venv").join("Scripts").join("python.exe"));
    candidates.push(base_dir.join("python").join("python.exe"));
    candidates.push(base_dir.join("runtime").join("python.exe"));

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
    println!("[MIKASA] Desktop ishga tushmoqda: backend holati tekshirilmoqda...");

    // 1. Agar 127.0.0.1:18420 da backend allaqachon ishlab turgan bo'lsa
    if check_http_health("127.0.0.1:18420", "/api/health") {
        println!("[MIKASA] Mavjud backend aniqlandi va faol (127.0.0.1:18420) — yangi jarayon ochilmaydi");
        if let Ok(mut m) = state.is_managed.lock() {
            *m = false;
        }
        return;
    }

    // 2. Bir vaqtning o'zida bir nechta backend ishga tushishini bloklash (Concurrency guard)
    if let Ok(mut spawning) = state.is_spawning.lock() {
        if *spawning {
            println!("[MIKASA] Backend allaqachon ishga tushirilmoqda, kutilmoqda...");
            return;
        }
        *spawning = true;
    }

    #[cfg(target_os = "windows")]
    const CREATE_NO_WINDOW: u32 = 0x08000000;
    #[cfg(target_os = "windows")]
    const CREATE_NEW_PROCESS_GROUP: u32 = 0x00000200;
    #[cfg(target_os = "windows")]
    let creation_flags = CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP;

    let mut child_opt: Option<Child> = None;

    // 3. Variant A: Standalone bundled backend (mikasa_backend.exe)
    if let Some((backend_bin, work_dir)) = find_bundled_backend_binary() {
        println!("[MIKASA] Standalone bundled backend ishga tushirilmoqda: {:?}", backend_bin);
        let mut cmd = Command::new(&backend_bin);
        cmd.current_dir(&work_dir)
            .env("MIKASA_API_HOST", "127.0.0.1")
            .env("MIKASA_API_PORT", "18420")
            .env("PORT", "18420")
            .env("ENVIRONMENT", "production");

        #[cfg(target_os = "windows")]
        cmd.creation_flags(creation_flags);

        match cmd.spawn() {
            Ok(c) => child_opt = Some(c),
            Err(e) => println!("[MIKASA] Bundled backendni ishga tushirishda xatolik: {}", e),
        }
    }

    // 4. Variant B: Rivojlantirish muhiti orqali python fallback
    if child_opt.is_none() {
        if let Some(base_dir) = resolve_dev_base_dir() {
            let py_exe = find_dev_python_executable(&base_dir).unwrap_or_else(|| PathBuf::from("python"));
            println!("[MIKASA] Python fallback orqali ishga tushirilmoqda: {:?} core/api_server.py", py_exe);
            let mut cmd = Command::new(&py_exe);
            cmd.arg("core/api_server.py")
                .current_dir(&base_dir)
                .env("MIKASA_API_HOST", "127.0.0.1")
                .env("MIKASA_API_PORT", "18420")
                .env("PORT", "18420");

            #[cfg(target_os = "windows")]
            cmd.creation_flags(creation_flags);

            match cmd.spawn() {
                Ok(c) => child_opt = Some(c),
                Err(e) => println!("[MIKASA] Python orqali ishga tushirishda xatolik: {}", e),
            }
        }
    }

    // 5. Jarayon qayd etildi
    if let Some(child) = child_opt {
        let pid = child.id();
        println!("[MIKASA] Backend jarayoni boshlandi (PID: {})", pid);
        if let Ok(mut lock) = state.backend_child.lock() {
            *lock = Some(child);
        }
        if let Ok(mut pid_lock) = state.backend_pid.lock() {
            *pid_lock = Some(pid);
        }
        if let Ok(mut managed_lock) = state.is_managed.lock() {
            *managed_lock = true;
        }
    } else {
        println!("[MIKASA] Xatolik: Hech qanday backend ijrochi fayli topilmadi!");
        if let Ok(mut spawning) = state.is_spawning.lock() {
            *spawning = false;
        }
        return;
    }

    // 6. Eksponentsial kutish bilan /api/health tekshiruvi (Health check with backoff)
    println!("[MIKASA] /api/health tayyor bo'lishi kutilmoqda...");
    let backoff_delays = [100, 250, 500, 1000, 1500, 2000, 2000, 2000, 2000, 2000];
    let mut is_ready = false;

    for delay in backoff_delays {
        // Jarayon barvaqt to'xtab qolmaganini tekshirish
        if let Ok(mut lock) = state.backend_child.lock() {
            if let Some(ref mut child) = *lock {
                if let Ok(Some(status)) = child.try_wait() {
                    println!("[MIKASA] Xatolik: Backend jarayoni kutilmaganda to'xtadi: {:?}", status);
                    break;
                }
            } else {
                break;
            }
        }

        if check_http_health("127.0.0.1:18420", "/api/health") {
            is_ready = true;
            break;
        }
        std::thread::sleep(Duration::from_millis(delay));
    }

    if is_ready {
        println!("[MIKASA] Backend 127.0.0.1:18420 da muvaffaqiyatli tayyor bo'ldi (READY) ✓");
    } else {
        println!("[MIKASA] Ogohlantirish: Backend health check vaqt chegarasiga yetdi (Timeout)");
    }

    if let Ok(mut spawning) = state.is_spawning.lock() {
        *spawning = false;
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
    // Check if tracked child process has exited unexpectedly
    if let Ok(mut lock) = state.backend_child.lock() {
        if let Some(ref mut child) = *lock {
            if let Ok(Some(_exit_status)) = child.try_wait() {
                *lock = None;
                if let Ok(mut pid_lock) = state.backend_pid.lock() {
                    *pid_lock = None;
                }
                if let Ok(mut managed_lock) = state.is_managed.lock() {
                    *managed_lock = false;
                }
            }
        }
    }

    let is_healthy = check_http_health("127.0.0.1:18420", "/api/health");
    let is_spawning = state.is_spawning.lock().map(|s| *s).unwrap_or(false);

    if !is_healthy && !is_spawning {
        let state_clone = state.inner().clone();
        std::thread::spawn(move || {
            ensure_backend_running(&state_clone);
        });
    }

    let is_managed = state.is_managed.lock().map(|m| *m).unwrap_or(false);
    let pid = state.backend_pid.lock().ok().and_then(|p| *p);

    serde_json::json!({
        "running": is_healthy,
        "healthy": is_healthy,
        "spawning": is_spawning || !is_healthy,
        "port": 18420,
        "pid": pid,
        "managed": is_managed
    })
}

#[tauri::command]
fn backend_restart(state: tauri::State<SupervisorState>) -> Result<bool, String> {
    // Agar backend hozirgina ishga tushayotgan bo'lsa (spawning) yoki allaqachon sog'lom bo'lsa, uni o'ldirmaymiz
    let currently_spawning = state.is_spawning.lock().map(|s| *s).unwrap_or(false);
    if currently_spawning || check_http_health("127.0.0.1:18420", "/api/health") {
        return Ok(true);
    }
    stop_backend(&state);
    if let Ok(mut spawning) = state.is_spawning.lock() {
        *spawning = false;
    }
    std::thread::sleep(Duration::from_millis(300));
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
