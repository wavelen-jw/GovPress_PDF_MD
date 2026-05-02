// Tauri 2 desktop implementation. Loads @tauri-apps/* lazily so that the
// Expo web/native bundlers don't fail when these packages are unavailable
// (e.g. iOS/Android EAS Build). All entry points are guarded with
// isTauriRuntime() so accidental invocation outside Tauri returns a no-op
// rather than crashing.

import type {
  ExternalFileOpenHandler,
  FileIoImpl,
  PickFileOptions,
  PickedAsset,
  SaveFileResult,
  ShareFileOptions,
  Unsubscribe,
} from "./fileio";

function inTauri(): boolean {
  return (
    typeof window !== "undefined" &&
    (window as unknown as { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__ !== undefined
  );
}

type DialogModule = typeof import("@tauri-apps/plugin-dialog");
type FsModule = typeof import("@tauri-apps/plugin-fs");
type ClipboardModule = typeof import("@tauri-apps/plugin-clipboard-manager");
type EventModule = typeof import("@tauri-apps/api/event");
type DeepLinkModule = typeof import("@tauri-apps/plugin-deep-link");

let dialogPromise: Promise<DialogModule> | null = null;
let fsPromise: Promise<FsModule> | null = null;
let clipboardPromise: Promise<ClipboardModule> | null = null;
let eventPromise: Promise<EventModule> | null = null;
let deepLinkPromise: Promise<DeepLinkModule> | null = null;

function loadDialog(): Promise<DialogModule> {
  if (!dialogPromise) dialogPromise = import("@tauri-apps/plugin-dialog");
  return dialogPromise;
}
function loadFs(): Promise<FsModule> {
  if (!fsPromise) fsPromise = import("@tauri-apps/plugin-fs");
  return fsPromise;
}
function loadClipboard(): Promise<ClipboardModule> {
  if (!clipboardPromise) clipboardPromise = import("@tauri-apps/plugin-clipboard-manager");
  return clipboardPromise;
}
function loadEvent(): Promise<EventModule> {
  if (!eventPromise) eventPromise = import("@tauri-apps/api/event");
  return eventPromise;
}
function loadDeepLink(): Promise<DeepLinkModule> {
  if (!deepLinkPromise) deepLinkPromise = import("@tauri-apps/plugin-deep-link");
  return deepLinkPromise;
}

function basename(filePath: string): string {
  const normalized = filePath.replace(/\\/g, "/");
  const idx = normalized.lastIndexOf("/");
  return idx >= 0 ? normalized.slice(idx + 1) : normalized;
}

function extensionOf(filePath: string): string {
  const name = basename(filePath);
  const idx = name.lastIndexOf(".");
  return idx > 0 ? name.slice(idx + 1).toLowerCase() : "";
}

function inferMimeType(ext: string): string | undefined {
  switch (ext) {
    case "md":
      return "text/markdown";
    case "pdf":
      return "application/pdf";
    case "hwpx":
      return "application/vnd.hancom.hwpx";
    default:
      return undefined;
  }
}

async function pathToPickedAsset(filePath: string): Promise<PickedAsset> {
  const fs = await loadFs();
  const bytes = await fs.readFile(filePath);
  const name = basename(filePath);
  const ext = extensionOf(name);
  const mimeType = inferMimeType(ext);
  // Construct a File so existing FormData / .text() consumers work unchanged.
  const blob = new Blob([new Uint8Array(bytes)], { type: mimeType ?? "application/octet-stream" });
  const file = new File([blob], name, { type: mimeType ?? "application/octet-stream" });
  return {
    uri: URL.createObjectURL(file),
    name,
    mimeType,
    size: file.size,
    file,
    lastModified: Date.now(),
  };
}

const tauriImpl: FileIoImpl = {
  async pickFileForOpen(options: PickFileOptions): Promise<PickedAsset | null> {
    if (!inTauri()) return null;
    const dialog = await loadDialog();
    const selected = await dialog.open({
      multiple: false,
      directory: false,
      filters: [
        {
          name: "Documents",
          extensions: options.extensions.map((ext) => ext.replace(/^\./, "")),
        },
      ],
    });
    if (!selected || Array.isArray(selected)) {
      const path = Array.isArray(selected) ? selected[0] : null;
      if (!path) return null;
      return pathToPickedAsset(path);
    }
    return pathToPickedAsset(selected as unknown as string);
  },

  async readFileAsText(asset: PickedAsset): Promise<string> {
    if (asset.file) {
      return asset.file.text();
    }
    const response = await fetch(asset.uri);
    return response.text();
  },

  async saveTextFileAs(suggestedName, content, mimeType): Promise<SaveFileResult> {
    if (!inTauri()) {
      return { ok: false, cancelled: false, error: new Error("not running in Tauri") };
    }
    try {
      const dialog = await loadDialog();
      const fs = await loadFs();
      const targetPath = await dialog.save({
        defaultPath: suggestedName,
        filters: [
          {
            name: mimeType,
            extensions: [suggestedName.split(".").pop() || "md"],
          },
        ],
      });
      if (!targetPath) {
        return { ok: false, cancelled: true };
      }
      await fs.writeTextFile(targetPath as string, content);
      return { ok: true };
    } catch (error) {
      return { ok: false, cancelled: false, error };
    }
  },

  async shareTextFile(options: ShareFileOptions): Promise<boolean> {
    // Desktop has no system share sheet; fall back to Save As dialog.
    const result = await tauriImpl.saveTextFileAs(options.fileName, options.content, options.mimeType);
    return result.ok;
  },

  async copyTextToClipboard(text: string): Promise<boolean> {
    if (!inTauri()) return false;
    try {
      const clipboard = await loadClipboard();
      await clipboard.writeText(text);
      return true;
    } catch {
      return false;
    }
  },

  onExternalFileOpen(handler: ExternalFileOpenHandler): Unsubscribe {
    if (!inTauri()) return () => {};

    let unsubscribed = false;
    const cleanups: Unsubscribe[] = [];

    async function deliver(filePath: string) {
      if (unsubscribed) return;
      try {
        const asset = await pathToPickedAsset(filePath);
        if (!unsubscribed) handler(asset);
      } catch (error) {
        console.warn("[fileio.tauri] external file open failed:", filePath, error);
      }
    }

    void (async () => {
      // Cold-start argv files: emitted in setup() before the React tree is
      // mounted, so a regular event.listen would miss them. Drain a Rust-
      // side queue instead.
      try {
        const { invoke } = await import("@tauri-apps/api/core");
        const pending = await invoke<string[]>("drain_pending_files");
        for (const arg of pending) {
          if (looksLikeOpenableFile(arg)) void deliver(arg);
        }
      } catch (error) {
        console.warn("[fileio.tauri] drain_pending_files failed:", error);
      }

      try {
        const event = await loadEvent();
        const argvUnlisten = await event.listen<string[]>("tauri://file-opened-from-argv", (e) => {
          for (const arg of e.payload) {
            if (looksLikeOpenableFile(arg)) {
              void deliver(arg);
            }
          }
        });
        const fileUnlisten = await event.listen<string>("tauri://file-opened", (e) => {
          if (typeof e.payload === "string") void deliver(e.payload);
        });
        // Native window drag-drop. Tauri 2 fires tauri://drag-drop with
        // { paths: string[], position } once dragDropEnabled is on (set in
        // tauri.conf.json). Browser-level dataTransfer events never fire
        // inside the webview when the OS handles the drop, so this is the
        // only delivery path.
        const dragUnlisten = await event.listen<{ paths?: string[] }>(
          "tauri://drag-drop",
          (e) => {
            const paths = e.payload && Array.isArray(e.payload.paths) ? e.payload.paths : [];
            for (const p of paths) {
              if (looksLikeOpenableFile(p)) void deliver(p);
            }
          },
        );
        cleanups.push(() => argvUnlisten());
        cleanups.push(() => fileUnlisten());
        cleanups.push(() => dragUnlisten());
      } catch (error) {
        console.warn("[fileio.tauri] event listen failed:", error);
      }
      try {
        const deepLink = await loadDeepLink();
        const off = await deepLink.onOpenUrl((urls) => {
          for (const url of urls) {
            const path = url.startsWith("file://") ? decodeURIComponent(url.slice("file://".length)) : url;
            if (looksLikeOpenableFile(path)) {
              void deliver(path);
            }
          }
        });
        cleanups.push(() => off());
      } catch (error) {
        console.warn("[fileio.tauri] deep-link subscribe failed:", error);
      }
    })();

    return () => {
      unsubscribed = true;
      for (const fn of cleanups) {
        try {
          fn();
        } catch {
          /* ignore */
        }
      }
    };
  },
};

function looksLikeOpenableFile(arg: string): boolean {
  const ext = extensionOf(arg);
  return ext === "md" || ext === "pdf" || ext === "hwpx";
}

export const pickFileForOpen = tauriImpl.pickFileForOpen;
export const readFileAsText = tauriImpl.readFileAsText;
export const saveTextFileAs = tauriImpl.saveTextFileAs;
export const shareTextFile = tauriImpl.shareTextFile;
export const copyTextToClipboard = tauriImpl.copyTextToClipboard;
export const onExternalFileOpen = tauriImpl.onExternalFileOpen;
