// iOS/Android implementation. Wraps expo-document-picker, expo-file-system
// and expo-sharing. Same call sites as the previous inline App.tsx code.

import * as DocumentPicker from "expo-document-picker";
import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";

import type {
  ExternalFileOpenHandler,
  FileIoImpl,
  PickFileOptions,
  PickedAsset,
  SaveFileResult,
  ShareFileOptions,
  Unsubscribe,
} from "./fileio";

function toPickedAsset(asset: DocumentPicker.DocumentPickerAsset): PickedAsset {
  return {
    uri: asset.uri,
    name: asset.name,
    mimeType: asset.mimeType ?? undefined,
    size: asset.size ?? undefined,
    lastModified: (asset as { lastModified?: number }).lastModified,
  };
}

function joinCachePath(fileName: string): string {
  const dir = FileSystem.cacheDirectory ?? "";
  return `${dir.replace(/\/$/, "")}/${fileName}`;
}

const nativeImpl: FileIoImpl = {
  async pickFileForOpen(options: PickFileOptions): Promise<PickedAsset | null> {
    const types =
      options.mimeTypes && options.mimeTypes.length > 0
        ? [...options.mimeTypes]
        : options.extensions.map((ext) => `.${ext.replace(/^\./, "")}`);
    const result = await DocumentPicker.getDocumentAsync({
      type: types,
      copyToCacheDirectory: true,
    });
    if (result.canceled || !result.assets.length) {
      return null;
    }
    return toPickedAsset(result.assets[0]);
  },

  async readFileAsText(asset: PickedAsset): Promise<string> {
    return FileSystem.readAsStringAsync(asset.uri, {
      encoding: FileSystem.EncodingType.UTF8,
    });
  },

  async saveTextFileAs(suggestedName, content, mimeType): Promise<SaveFileResult> {
    try {
      const outputPath = joinCachePath(suggestedName);
      await FileSystem.writeAsStringAsync(outputPath, content, {
        encoding: FileSystem.EncodingType.UTF8,
      });
      const available = await Sharing.isAvailableAsync();
      if (!available) {
        return { ok: true };
      }
      await Sharing.shareAsync(outputPath, {
        mimeType,
        dialogTitle: "저장",
      });
      return { ok: true };
    } catch (error) {
      return { ok: false, cancelled: false, error };
    }
  },

  async shareTextFile(options: ShareFileOptions): Promise<boolean> {
    try {
      const outputPath = joinCachePath(options.fileName);
      await FileSystem.writeAsStringAsync(outputPath, options.content, {
        encoding: FileSystem.EncodingType.UTF8,
      });
      const available = await Sharing.isAvailableAsync();
      if (!available) {
        return false;
      }
      await Sharing.shareAsync(outputPath, {
        mimeType: options.mimeType,
        dialogTitle: options.dialogTitle,
      });
      return true;
    } catch {
      return false;
    }
  },

  async copyTextToClipboard(_text: string): Promise<boolean> {
    // expo-clipboard is not currently a dependency; native clipboard support
    // for Markdown is a Phase 3 follow-up.
    return false;
  },

  onExternalFileOpen(_handler: ExternalFileOpenHandler): Unsubscribe {
    // iOS/Android file association via expo-linking belongs in Phase 3.
    return () => {};
  },
};

export const pickFileForOpen = nativeImpl.pickFileForOpen;
export const readFileAsText = nativeImpl.readFileAsText;
export const saveTextFileAs = nativeImpl.saveTextFileAs;
export const shareTextFile = nativeImpl.shareTextFile;
export const copyTextToClipboard = nativeImpl.copyTextToClipboard;
export const onExternalFileOpen = nativeImpl.onExternalFileOpen;

// React Native (iOS/Android) is never the Tauri webview. Mirrored here so
// the same import surface works regardless of which platform variant Metro
// resolves "./fileio" to.
export function isTauriRuntime(): boolean {
  return false;
}
