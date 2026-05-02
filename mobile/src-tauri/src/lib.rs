// 읽힘 desktop shell entry. Plugin order matters:
//   single_instance must be registered BEFORE deep_link so that on Windows
//   the second-instance argv (which holds the file path) is forwarded to the
//   running window instead of being dropped when a duplicate launch is
//   collapsed.

use std::sync::Mutex;
use tauri::menu::{MenuBuilder, MenuItemBuilder, PredefinedMenuItem, SubmenuBuilder};
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

fn build_menu(app: &AppHandle) -> tauri::Result<tauri::menu::Menu<tauri::Wry>> {
    // File menu — Open / Save dispatch to React via emitted events; React
    // listens for "menu://open-file" and "menu://save-file".
    let open_item = MenuItemBuilder::with_id("menu-open-file", "열기...")
        .accelerator("CmdOrCtrl+O")
        .build(app)?;
    let save_item = MenuItemBuilder::with_id("menu-save-file", "Markdown 저장...")
        .accelerator("CmdOrCtrl+S")
        .build(app)?;
    let copy_md_item = MenuItemBuilder::with_id("menu-copy-md", "Markdown 클립보드 복사")
        .accelerator("CmdOrCtrl+Shift+C")
        .build(app)?;
    let policy_briefings_item = MenuItemBuilder::with_id("menu-open-briefings", "정책브리핑 열기...")
        .accelerator("CmdOrCtrl+B")
        .build(app)?;
    let file_menu = SubmenuBuilder::new(app, "파일")
        .item(&open_item)
        .item(&policy_briefings_item)
        .separator()
        .item(&save_item)
        .item(&copy_md_item)
        .separator()
        .item(&PredefinedMenuItem::quit(app, Some("종료"))?)
        .build()?;

    // Edit menu — system-provided cut/copy/paste/select-all.
    let edit_menu = SubmenuBuilder::new(app, "편집")
        .item(&PredefinedMenuItem::undo(app, Some("실행 취소"))?)
        .item(&PredefinedMenuItem::redo(app, Some("다시 실행"))?)
        .separator()
        .item(&PredefinedMenuItem::cut(app, Some("잘라내기"))?)
        .item(&PredefinedMenuItem::copy(app, Some("복사"))?)
        .item(&PredefinedMenuItem::paste(app, Some("붙여넣기"))?)
        .item(&PredefinedMenuItem::select_all(app, Some("모두 선택"))?)
        .build()?;

    // View menu — reload + DevTools (DevTools only in debug builds).
    let reload_item = MenuItemBuilder::with_id("menu-reload", "새로 고침")
        .accelerator("CmdOrCtrl+R")
        .build(app)?;
    let view_menu = SubmenuBuilder::new(app, "보기").item(&reload_item).build()?;

    // Help menu — About / open project page.
    let about_item = MenuItemBuilder::with_id("menu-about", "정보").build(app)?;
    let github_item = MenuItemBuilder::with_id("menu-github", "GitHub 저장소 열기").build(app)?;
    let help_menu = SubmenuBuilder::new(app, "도움말")
        .item(&about_item)
        .item(&github_item)
        .build()?;

    MenuBuilder::new(app)
        .item(&file_menu)
        .item(&edit_menu)
        .item(&view_menu)
        .item(&help_menu)
        .build()
}

fn handle_menu_event(app: &AppHandle, event_id: &str) {
    let Some(window) = app.get_webview_window("main") else {
        return;
    };
    match event_id {
        "menu-open-file" => {
            let _ = window.emit("menu://open-file", ());
        }
        "menu-save-file" => {
            let _ = window.emit("menu://save-file", ());
        }
        "menu-copy-md" => {
            let _ = window.emit("menu://copy-markdown", ());
        }
        "menu-open-briefings" => {
            let _ = window.emit("menu://open-briefings", ());
        }
        "menu-reload" => {
            let _ = window.emit("menu://reload", ());
        }
        "menu-about" => {
            let _ = window.emit("menu://about", ());
        }
        "menu-github" => {
            let _ = window.emit("menu://open-github", ());
        }
        _ => {}
    }
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
            // Native menu bar.
            let menu = build_menu(app.handle())?;
            app.set_menu(menu)?;
            let app_handle = app.handle().clone();
            app.on_menu_event(move |_app, event| {
                handle_menu_event(&app_handle, event.id().0.as_str());
            });

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
