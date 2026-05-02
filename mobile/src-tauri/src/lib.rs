// 읽힘 desktop shell entry. Plugin order matters:
//   single_instance must be registered BEFORE deep_link so that on Windows
//   the second-instance argv (which holds the file path) is forwarded to the
//   running window instead of being dropped when a duplicate launch is
//   collapsed.

use std::sync::Mutex;

use tauri::{AppHandle, Emitter, Manager, State};

#[derive(Default)]
struct PendingFiles(Mutex<Vec<String>>);

fn argv_to_files(argv: Vec<String>) -> Vec<String> {
    argv.into_iter()
        .skip(1)
        .filter(|arg| !arg.starts_with("--"))
        .filter(|arg| {
            let lower = arg.to_lowercase();
            lower.ends_with(".md") || lower.ends_with(".pdf") || lower.ends_with(".hwpx")
        })
        .collect()
}

fn forward_argv(app: &AppHandle, argv: Vec<String>) {
    let files = argv_to_files(argv);
    if files.is_empty() {
        return;
    }
    // Always stash into pending state — frontend drains on mount, which
    // covers cold-start (frontend not yet listening when we'd emit). Then
    // also emit for the warm-start / second-instance case where the React
    // tree is already mounted with a listener.
    if let Some(state) = app.try_state::<PendingFiles>() {
        if let Ok(mut buf) = state.0.lock() {
            buf.extend(files.iter().cloned());
        }
    }
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.emit("tauri://file-opened-from-argv", files);
        let _ = window.set_focus();
    }
}

#[tauri::command]
fn drain_pending_files(state: State<'_, PendingFiles>) -> Vec<String> {
    let mut buf = state.0.lock().expect("PendingFiles mutex poisoned");
    std::mem::take(&mut *buf)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(PendingFiles::default())
        .invoke_handler(tauri::generate_handler![drain_pending_files])
        .plugin(tauri_plugin_single_instance::init(|app, argv, _cwd| {
            forward_argv(app, argv);
        }))
        .plugin(tauri_plugin_deep_link::init())
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_clipboard_manager::init())
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .setup(|app| {
            // Initial argv on cold start (Windows / Linux launch with file).
            let initial_argv: Vec<String> = std::env::args().collect();
            let handle = app.handle().clone();
            forward_argv(&handle, initial_argv);

            // macOS uses Apple Events for file-open on a running instance.
            // tauri-plugin-deep-link surfaces those via on_open_url.
            #[cfg(any(target_os = "macos", target_os = "linux"))]
            {
                use tauri_plugin_deep_link::DeepLinkExt;
                let handle = app.handle().clone();
                app.deep_link().on_open_url(move |event| {
                    let urls = event.urls();
                    let mut files: Vec<String> = Vec::new();
                    for url in urls {
                        let s = url.to_string();
                        if let Some(rest) = s.strip_prefix("file://") {
                            files.push(percent_decode(rest));
                        } else if !s.contains("://") {
                            files.push(s);
                        }
                    }
                    if files.is_empty() {
                        return;
                    }
                    if let Some(window) = handle.get_webview_window("main") {
                        let _ = window.emit("tauri://file-opened-from-argv", files);
                        let _ = window.set_focus();
                    }
                });
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

fn percent_decode(input: &str) -> String {
    // Minimal percent-decoder for common file path characters; avoids pulling
    // in a separate crate just for this. Falls back to the original byte on
    // any malformed escape.
    let mut out = String::with_capacity(input.len());
    let bytes = input.as_bytes();
    let mut i = 0;
    while i < bytes.len() {
        let b = bytes[i];
        if b == b'%' && i + 2 < bytes.len() {
            let hi = (bytes[i + 1] as char).to_digit(16);
            let lo = (bytes[i + 2] as char).to_digit(16);
            if let (Some(hi), Some(lo)) = (hi, lo) {
                out.push(((hi * 16 + lo) as u8) as char);
                i += 3;
                continue;
            }
        }
        out.push(b as char);
        i += 1;
    }
    out
}
