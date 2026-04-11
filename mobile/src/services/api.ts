import { Platform } from "react-native";
import * as DocumentPicker from "expo-document-picker";

import { getFallbackBaseUrls, SERVER_FALLBACK_TIMEOUT_MS } from "../constants";
import type {
  AppConfig,
  HwpxTableMode,
  Job,
  PolicyBriefingImportPayload,
  PolicyBriefingListPayload,
  ResultPayload,
  UploadResult,
} from "../types";

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function normalizePolicyBriefingFailure(message: string): string {
  const lowered = message.toLowerCase();
  if (
    lowered.includes("timed out") ||
    lowered.includes("timeout") ||
    lowered.includes("bad gateway")
  ) {
    return "정책브리핑 제공기관 API 응답이 지연되거나 장애 상태입니다. 잠시 후 다시 시도해 주세요.";
  }
  return message;
}

function buildHeaders(config: AppConfig, contentType?: string, editToken?: string | null): Record<string, string> {
  const headers: Record<string, string> = {};
  if (contentType) {
    headers["Content-Type"] = contentType;
  }
  if (config.apiKey.trim()) {
    headers["X-API-Key"] = config.apiKey.trim();
  }
  if (editToken?.trim()) {
    headers["X-Edit-Token"] = editToken.trim();
  }
  return headers;
}

async function fetchJson<T>(config: AppConfig, path: string, init?: RequestInit, editToken?: string | null): Promise<T> {
  const response = await fetch(`${config.baseUrl}${path}`, {
    ...init,
    headers: {
      ...buildHeaders(config, undefined, editToken),
      ...(init?.headers as Record<string, string> | undefined),
    },
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new ApiError(response.status, detail || `Request failed: ${response.status}`);
  }

  return (await response.json()) as T;
}

async function fetchWithTimeout(input: string, init: RequestInit, timeoutMs: number): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timeout);
  }
}

function isRetryableUploadError(error: unknown): boolean {
  if (!(error instanceof Error)) {
    return false;
  }
  if (error.name === "AbortError") {
    return true;
  }
  const message = error.message.toLowerCase();
  if (message.includes("network") || message.includes("fetch")) {
    return true;
  }
  // API key rejected by a specific server — fall back to next server
  if (message.includes("invalid api key") || message.includes("api key")) {
    return true;
  }
  return false;
}

function buildUploadBody(asset: DocumentPicker.DocumentPickerAsset, hwpxTableMode: HwpxTableMode): FormData {
  const form = new FormData();
  form.append("source", "mobile");
  form.append("hwpx_table_mode", hwpxTableMode);
  const webFile = (asset as DocumentPicker.DocumentPickerAsset & { file?: File }).file;
  if (Platform.OS === "web" && webFile) {
    form.append("file", webFile);
  } else {
    form.append("file", {
      uri: asset.uri,
      name: asset.name,
      type: asset.mimeType || "application/pdf",
    } as unknown as Blob);
  }
  return form;
}

export async function fetchJob(config: AppConfig, jobId: string, editToken: string): Promise<Job> {
  return fetchJson(config, `/v1/jobs/${jobId}`, undefined, editToken);
}

export async function fetchResult(config: AppConfig, jobId: string, editToken: string): Promise<ResultPayload> {
  return fetchJson(config, `/v1/jobs/${jobId}/result`, undefined, editToken);
}

export async function uploadPdf(
  config: AppConfig,
  asset: DocumentPicker.DocumentPickerAsset,
  hwpxTableMode: HwpxTableMode,
): Promise<UploadResult> {
  const attempts = getFallbackBaseUrls(config.baseUrl);
  const failures: string[] = [];

  for (const baseUrl of attempts) {
    try {
      const response = await fetchWithTimeout(`${baseUrl}/v1/jobs`, {
        method: "POST",
        headers: buildHeaders(config),
        body: buildUploadBody(asset, hwpxTableMode),
      }, SERVER_FALLBACK_TIMEOUT_MS);
      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || `Upload failed: ${response.status}`);
      }
      return {
        job: (await response.json()) as UploadResult["job"],
        resolvedBaseUrl: baseUrl,
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      failures.push(`${baseUrl}: ${message}`);
      if (!isRetryableUploadError(error)) {
        throw error;
      }
    }
  }

  throw new Error(`모든 서버 업로드에 실패했습니다. ${failures.join(" | ")}`);
}

export async function retryJob(config: AppConfig, jobId: string, editToken: string): Promise<Job> {
  return fetchJson(config, `/v1/jobs/${jobId}/retry`, { method: "POST" }, editToken);
}

export async function fetchTodayPolicyBriefings(config: AppConfig, date?: string): Promise<PolicyBriefingListPayload> {
  const path = date ? `/v1/policy-briefings/today?date=${date}` : "/v1/policy-briefings/today";
  const attempts = getFallbackBaseUrls(config.baseUrl);
  const failures: string[] = [];

  for (const baseUrl of attempts) {
    try {
      const response = await fetchWithTimeout(
        `${baseUrl}${path}`,
        {
          method: "GET",
          headers: buildHeaders(config),
        },
        SERVER_FALLBACK_TIMEOUT_MS,
      );
      if (!response.ok) {
        const detail = await response.text();
        throw new Error(normalizePolicyBriefingFailure(detail || `Request failed: ${response.status}`));
      }
      return (await response.json()) as PolicyBriefingListPayload;
    } catch (error) {
      const rawMessage = error instanceof Error ? error.message : String(error);
      const message = normalizePolicyBriefingFailure(rawMessage);
      failures.push(`${baseUrl}: ${message}`);
      if (!isRetryableUploadError(error)) {
        throw error;
      }
    }
  }

  throw new Error(`정책브리핑 목록 요청에 실패했습니다. ${failures.join(" | ")}`);
}

export async function importPolicyBriefing(config: AppConfig, newsItemId: string): Promise<PolicyBriefingImportPayload> {
  return fetchJson(config, "/v1/policy-briefings/import", {
    method: "POST",
    headers: buildHeaders(config, "application/json"),
    body: JSON.stringify({ news_item_id: newsItemId }),
  });
}

export async function saveResult(config: AppConfig, jobId: string, markdown: string, editToken: string): Promise<void> {
  await fetchJson(config, `/v1/jobs/${jobId}/result`, {
    method: "PATCH",
    headers: buildHeaders(config, "application/json", editToken),
    body: JSON.stringify({ markdown }),
  }, editToken);
}
