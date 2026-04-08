import { Platform } from "react-native";

import type { AppConfig, JobStatus } from "./types";

export const STORAGE_KEYS = {
  baseUrl: "govpress.mobile.baseUrl",
  apiKey: "govpress.mobile.apiKey",
  draftPrefix: "govpress.mobile.draft",
} as const;

export const BUILD_TAG = "mobile-web-2026-04-08-serverw";

export const SERVER_FALLBACK_TIMEOUT_MS = 8000;

export const SERVER_PRESETS = [
  { key: "serverV", label: "서버V", shortLabel: "서버V", url: "https://api2.govpress.cloud" },
  { key: "serverW", label: "서버W", shortLabel: "서버W", url: "https://api4.govpress.cloud" },
  { key: "serverH", label: "서버H", shortLabel: "서버H", url: "https://api.govpress.cloud" },
] as const;

export function isHostedWeb(): boolean {
  return Platform.OS === "web" && typeof window !== "undefined" && window.location.hostname.endsWith("github.io");
}

export function defaultBaseUrl(): string {
  if (Platform.OS === "web" && typeof window !== "undefined") {
    if (isHostedWeb()) {
      return SERVER_PRESETS.find((preset) => preset.key === "serverW")?.url || SERVER_PRESETS[0].url;
    }
    return `${window.location.protocol}//${window.location.hostname}:8013`;
  }
  return "http://127.0.0.1:8012";
}

export function normalizeBaseUrl(baseUrl: string | null): string {
  const fallback = defaultBaseUrl();
  const value = (baseUrl || "").trim();
  if (!value) {
    return fallback;
  }
  if (Platform.OS === "web") {
    try {
      const parsed = new URL(value);
      if (parsed.hostname === "127.0.0.1" || parsed.hostname === "localhost") {
        return fallback;
      }
    } catch {
      return fallback;
    }
  }
  return value;
}

export function currentWebBaseUrl(): string {
  return defaultBaseUrl();
}

export function getServerLabel(baseUrl: string): string {
  return SERVER_PRESETS.find((preset) => preset.url === baseUrl)?.shortLabel || baseUrl;
}

export function getFallbackBaseUrls(baseUrl: string): string[] {
  return baseUrl.trim() ? [baseUrl.trim()] : [defaultBaseUrl()];
}

export const DEFAULT_CONFIG: AppConfig = {
  baseUrl: defaultBaseUrl(),
  apiKey: process.env.EXPO_PUBLIC_GOVPRESS_API_KEY || "898afed2d0b3560ff1e53d3b02fc120bfc23712a951952a7",
};

export const STATUS_COPY: Record<JobStatus, string> = {
  queued: "대기 중",
  processing: "변환 중",
  completed: "완료",
  failed: "실패",
};

export const STATUS_TONE: Record<JobStatus, string> = {
  queued: "#c97316",
  processing: "#0f6f6f",
  completed: "#1f6a3d",
  failed: "#a63838",
};
