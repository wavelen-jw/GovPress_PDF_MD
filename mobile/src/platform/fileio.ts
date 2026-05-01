// Platform-specific file IO abstraction.
//
// Three implementations (selected at runtime, not at bundle time):
//   - fileio.web.ts:    File System Access API + showSaveFilePicker + clipboard
//   - fileio.native.ts: expo-document-picker + expo-file-system + expo-sharing
//   - fileio.tauri.ts:  @tauri-apps/plugin-{dialog,fs,clipboard-manager,deep-link}
//
// Tauri runs inside a webview where `Platform.OS === "web"` is true, so we
// detect Tauri first via `window.__TAURI_INTERNALS__` and fall back to the
// regular web/native dispatch otherwise.

import { Platform } from "react-native";

import * as nativeImpl from "./fileio.native";
import * as tauriImpl from "./fileio.tauri";
import * as webImpl from "./fileio.web";

export type PickedAsset = {
  uri: string;
  name: string;
  mimeType?: string;
  size?: number;
  file?: File;
  lastModified?: number;
};

export type PickFileOptions = {
  extensions: readonly string[];
  mimeTypes?: readonly string[];
};

export type SaveFileResult =
  | { ok: true; cancelled?: false }
  | { ok: false; cancelled: true }
  | { ok: false; cancelled?: false; error: unknown };

export type ShareFileOptions = {
  fileName: string;
  content: string;
  mimeType: string;
  dialogTitle?: string;
};

export type ExternalFileOpenHandler = (asset: PickedAsset) => void;
export type Unsubscribe = () => void;

export type FileIoImpl = {
  pickFileForOpen(options: PickFileOptions): Promise<PickedAsset | null>;
  readFileAsText(asset: PickedAsset): Promise<string>;
  saveTextFileAs(suggestedName: string, content: string, mimeType: string): Promise<SaveFileResult>;
  shareTextFile(options: ShareFileOptions): Promise<boolean>;
  copyTextToClipboard(text: string): Promise<boolean>;
  onExternalFileOpen(handler: ExternalFileOpenHandler): Unsubscribe;
};

export function isTauriRuntime(): boolean {
  return (
    typeof window !== "undefined" &&
    (window as unknown as { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__ !== undefined
  );
}

function selectImpl(): FileIoImpl {
  if (isTauriRuntime()) {
    return tauriImpl;
  }
  if (Platform.OS === "web") {
    return webImpl;
  }
  return nativeImpl;
}

const impl = selectImpl();

export const pickFileForOpen: FileIoImpl["pickFileForOpen"] = (options) =>
  impl.pickFileForOpen(options);
export const readFileAsText: FileIoImpl["readFileAsText"] = (asset) => impl.readFileAsText(asset);
export const saveTextFileAs: FileIoImpl["saveTextFileAs"] = (name, content, mime) =>
  impl.saveTextFileAs(name, content, mime);
export const shareTextFile: FileIoImpl["shareTextFile"] = (options) => impl.shareTextFile(options);
export const copyTextToClipboard: FileIoImpl["copyTextToClipboard"] = (text) =>
  impl.copyTextToClipboard(text);
export const onExternalFileOpen: FileIoImpl["onExternalFileOpen"] = (handler) =>
  impl.onExternalFileOpen(handler);
