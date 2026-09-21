use std::process::Command;
use std::env;

fn main() {
    println!("cargo:rerun-if-changed=build.rs");
    let out_dir = env::var("OUT_DIR").unwrap();
    let icon_path = "../../mikasa-7/src-tauri/icons/icon.ico".replace('\\', "/");
    let rc_content = format!("1 ICON \"{}\"\n", icon_path);
    let rc_path = format!("{}/app.rc", out_dir);
    let res_path = format!("{}/app.res", out_dir);
    
    if std::fs::write(&rc_path, rc_content).is_ok() {
        let status = Command::new("windres")
            .args(&["-i", &rc_path, "-O", "coff", "-o", &res_path])
            .status();
        if let Ok(s) = status {
            if s.success() {
                println!("cargo:rustc-link-arg={}", res_path);
            }
        }
    }
}
