import { Platform } from "react-native";
import * as SecureStore from "expo-secure-store";

import { DEFAULT_CONFIG, isHostedWeb, normalizeBaseUrl, STORAGE_KEYS } from "../constants";
import type { AppConfig } from "../types";

function draftStorageKey(jobId: string): string {
  return `${STORAGE_KEYS.draftPrefix}.${jobId}`;
}

export async function loadConfig(): Promise<AppConfig> {
  if (Platform.OS === "web" && typeof window !== "undefined") {
    const apiKey = isHostedWeb() ? DEFAULT_CONFIG.apiKey : (window.localStorage.getItem(STORAGE_KEYS.apiKey) || DEFAULT_CONFIG.apiKey);
    if (isHostedWeb()) {
      window.localStorage.removeItem(STORAGE_KEYS.apiKey);
    }
    return {
      baseUrl: normalizeBaseUrl(window.localStorage.getItem(STORAGE_KEYS.baseUrl)),
      apiKey,
      turnstileSiteKey: DEFAULT_CONFIG.turnstileSiteKey,
    };
  }

  const [baseUrl, apiKey] = await Promise.all([
    SecureStore.getItemAsync(STORAGE_KEYS.baseUrl),
    SecureStore.getItemAsync(STORAGE_KEYS.apiKey),
  ]);
  return {
    baseUrl: normalizeBaseUrl(baseUrl),
    apiKey: apiKey || DEFAULT_CONFIG.apiKey,
    turnstileSiteKey: DEFAULT_CONFIG.turnstileSiteKey,
  };
}

export async function persistConfig(config: AppConfig): Promise<void> {
  if (Platform.OS === "web" && typeof window !== "undefined") {
    window.localStorage.setItem(STORAGE_KEYS.baseUrl, config.baseUrl);
    if (isHostedWeb()) {
      window.localStorage.removeItem(STORAGE_KEYS.apiKey);
    } else {
      window.localStorage.setItem(STORAGE_KEYS.apiKey, config.apiKey);
    }
    return;
  }

  await Promise.all([
    SecureStore.setItemAsync(STORAGE_KEYS.baseUrl, config.baseUrl),
    SecureStore.setItemAsync(STORAGE_KEYS.apiKey, config.apiKey),
  ]);
}

export async function loadDraft(jobId: string): Promise<string | null> {
  const key = draftStorageKey(jobId);
  if (Platform.OS === "web" && typeof window !== "undefined") {
    return window.localStorage.getItem(key);
  }
  return SecureStore.getItemAsync(key);
}

export async function persistDraft(jobId: string, markdown: string): Promise<void> {
  const key = draftStorageKey(jobId);
  if (Platform.OS === "web" && typeof window !== "undefined") {
    window.localStorage.setItem(key, markdown);
    return;
  }
  await SecureStore.setItemAsync(key, markdown);
}

export async function clearDraft(jobId: string): Promise<void> {
  const key = draftStorageKey(jobId);
  if (Platform.OS === "web" && typeof window !== "undefined") {
    window.localStorage.removeItem(key);
    return;
  }
  await SecureStore.deleteItemAsync(key);
}
