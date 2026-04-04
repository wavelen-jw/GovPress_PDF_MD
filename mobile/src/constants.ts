import { Platform } from "react-native";

import type { AppConfig, JobStatus } from "./types";

export const STORAGE_KEYS = {
  baseUrl: "govpress.mobile.baseUrl",
  apiKey: "govpress.mobile.apiKey",
  draftPrefix: "govpress.mobile.draft",
} as const;

export const BUILD_TAG = "mobile-web-2026-03-29-2310-local";
const TURNSTILE_SITE_KEY_FALLBACK = "0x4AAAAAACxpgXbUmIjLt9ZH";

export function isHostedWeb(): boolean {
  return Platform.OS === "web" && typeof window !== "undefined" && window.location.hostname.endsWith("github.io");
}

export function defaultBaseUrl(): string {
  if (Platform.OS === "web" && typeof window !== "undefined") {
    if (isHostedWeb()) {
      return "https://api2.govpress.cloud";
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

export const DEFAULT_CONFIG: AppConfig = {
  baseUrl: defaultBaseUrl(),
  apiKey: "",
  turnstileSiteKey:
    process.env.EXPO_PUBLIC_CLOUDFLARE_TURNSTILE_SITE_KEY || TURNSTILE_SITE_KEY_FALLBACK,
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
