// Browser/PWA implementation of the fileio abstraction.
// Mirrors the previous inline web behavior in App.tsx (handleSaveMarkdownFile,
// handleShareMarkdown, handleCopyMarkdown, openLocalMarkdown).
//
// Metro's web bundler resolves `import "./fileio"` to this file (.web.ts wins
// over .ts on the web platform) — and the Tauri desktop build is also a web
// bundle. So this module is responsible for runtime-dispatching to the Tauri
// implementation when __TAURI_INTERNALS__ is present. Statically importing
// fileio.tauri here ensures its code (and the "drain_pending_files" / drag-
// drop wiring) actually ships in the bundle.

import type {
  ExternalFileOpenHandler,
  FileIoImpl,
  PickFileOptions,
  PickedAsset,
  SaveFileResult,
  ShareFileOptions,
  Unsubscribe,
} from "./fileio";
import * as tauriImpl from "./fileio.tauri";

type ShowSaveFilePicker = (options: {
  suggestedName?: string;
  types?: { description?: string; accept: Record<string, string[]> }[];
}) => Promise<{ createWritable: () => Promise<{ write: (data: BlobPart) => Promise<void>; close: () => Promise<void> }> }>;

declare global {
  interface Window {
    showSaveFilePicker?: ShowSaveFilePicker;
  }
}

function pickViaInputElement(options: PickFileOptions): Promise<PickedAsset | null> {
  return new Promise((resolve) => {
    if (typeof document === "undefined") {
      resolve(null);
      return;
    }
    const input = document.createElement("input");
    input.type = "file";
    input.accept = options.extensions.map((ext) => `.${ext.replace(/^\./, "")}`).join(",");
    input.style.position = "fixed";
    input.style.left = "-1000px";
    input.style.top = "-1000px";
    let settled = false;
    input.addEventListener(
      "change",
      () => {
        settled = true;
        const file = input.files && input.files[0];
        document.body.removeChild(input);
        if (!file) {
          resolve(null);
          return;
        }
        resolve({
          uri: URL.createObjectURL(file),
          name: file.name,
          mimeType: file.type || undefined,
          size: file.size,
          file,
          lastModified: file.lastModified,
        });
      },
      { once: true },
    );
    // Some browsers fire focus on the window when the picker is closed; if no
    // file gets selected within a generous timeout, give up so the promise
    // doesn't hang forever.
    window.addEventListener(
      "focus",
      () => {
        setTimeout(() => {
          if (!settled) {
            settled = true;
            if (input.parentNode) document.body.removeChild(input);
            resolve(null);
          }
        }, 1000);
      },
      { once: true },
    );
    document.body.appendChild(input);
    input.click();
  });
}

const webImpl: FileIoImpl = {
  async pickFileForOpen(options) {
    return pickViaInputElement(options);
  },

  async readFileAsText(asset) {
    if (asset.file) {
      return asset.file.text();
    }
    const response = await fetch(asset.uri);
    return response.text();
  },

  async saveTextFileAs(suggestedName, content, mimeType): Promise<SaveFileResult> {
    if (typeof window === "undefined") {
      return { ok: false, cancelled: false, error: new Error("not running in a browser") };
    }
    if (typeof window.showSaveFilePicker === "function") {
      try {
        const handle = await window.showSaveFilePicker({
          suggestedName,
          types: [
            {
              description: "Markdown",
              accept: { [mimeType]: [`.${suggestedName.split(".").pop() || "md"}`] },
            },
          ],
        });
        const writable = await handle.createWritable();
        await writable.write(content);
        await writable.close();
        return { ok: true };
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return { ok: false, cancelled: true };
        }
        return { ok: false, cancelled: false, error };
      }
    }
    // Fallback: anchor download
    try {
      const blob = new Blob([content], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = suggestedName;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      setTimeout(() => URL.revokeObjectURL(url), 0);
      return { ok: true };
    } catch (error) {
      return { ok: false, cancelled: false, error };
    }
  },

  async shareTextFile(options: ShareFileOptions): Promise<boolean> {
    if (
      typeof navigator !== "undefined" &&
      typeof navigator.share === "function" &&
      typeof File !== "undefined"
    ) {
      try {
        const file = new File([options.content], options.fileName, { type: options.mimeType });
        // Some platforms (mobile Safari) only support text-only share; try files first.
        if (typeof (navigator as Navigator & { canShare?: (data: ShareData) => boolean }).canShare === "function") {
          const canShare = (navigator as Navigator & { canShare: (data: ShareData) => boolean }).canShare({
            files: [file],
            title: options.dialogTitle,
          });
          if (!canShare) {
            await navigator.share({ title: options.dialogTitle, text: options.content });
            return true;
          }
        }
        await navigator.share({
          title: options.dialogTitle,
          files: [file],
        } as ShareData);
        return true;
      } catch {
        // fall through to clipboard
      }
    }
    return webImpl.copyTextToClipboard(options.content);
  },

  async copyTextToClipboard(text: string): Promise<boolean> {
    if (typeof navigator === "undefined" || !navigator.clipboard) {
      return false;
    }
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      return false;
    }
  },

  onExternalFileOpen(_handler: ExternalFileOpenHandler): Unsubscribe {
    // Browser PWA has no equivalent to OS file association beyond the future
    // launch_handler manifest entry, which is out of scope here.
    return () => {};
  },
};

export function isTauriRuntime(): boolean {
  return (
    typeof window !== "undefined" &&
    (window as unknown as { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__ !== undefined
  );
}

// Each export checks at call-time so the same JS bundle works for both PWA
// (browser) and Tauri (desktop webview) without a build-time switch. Bind the
// pair eagerly (`isTauriRuntime()` is stable for the app lifetime) for a
// micro-optimization and to make it obvious in the bundle which impl is live.
const impl: FileIoImpl = isTauriRuntime() ? tauriImpl : webImpl;

export const pickFileForOpen: FileIoImpl["pickFileForOpen"] = (options) => impl.pickFileForOpen(options);
export const readFileAsText: FileIoImpl["readFileAsText"] = (asset) => impl.readFileAsText(asset);
export const saveTextFileAs: FileIoImpl["saveTextFileAs"] = (suggestedName, content, mimeType) =>
  impl.saveTextFileAs(suggestedName, content, mimeType);
export const shareTextFile: FileIoImpl["shareTextFile"] = (options) => impl.shareTextFile(options);
export const copyTextToClipboard: FileIoImpl["copyTextToClipboard"] = (text) => impl.copyTextToClipboard(text);
export const onExternalFileOpen: FileIoImpl["onExternalFileOpen"] = (handler) => impl.onExternalFileOpen(handler);
