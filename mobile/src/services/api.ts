import { Platform } from "react-native";
import * as DocumentPicker from "expo-document-picker";

import type { AppConfig, CleanupPayload, Job, ResultPayload } from "../types";

function buildHeaders(config: AppConfig, contentType?: string): Record<string, string> {
  const headers: Record<string, string> = {};
  if (contentType) {
    headers["Content-Type"] = contentType;
  }
  if (config.apiKey.trim()) {
    headers["X-API-Key"] = config.apiKey.trim();
  }
  return headers;
}

async function fetchJson<T>(config: AppConfig, path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${config.baseUrl}${path}`, {
    ...init,
    headers: {
      ...buildHeaders(config),
      ...(init?.headers as Record<string, string> | undefined),
    },
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function fetchJobs(
  config: AppConfig,
  cursor?: string | null,
  status?: string | null,
): Promise<{ items: Job[]; next_cursor: string | null }> {
  const params = new URLSearchParams({ limit: "12" });
  if (cursor) {
    params.set("cursor", cursor);
  }
  if (status) {
    params.set("status", status);
  }
  return fetchJson(config, `/v1/jobs?${params.toString()}`);
}

export async function fetchJob(config: AppConfig, jobId: string): Promise<Job> {
  return fetchJson(config, `/v1/jobs/${jobId}`);
}

export async function fetchResult(config: AppConfig, jobId: string): Promise<ResultPayload> {
  return fetchJson(config, `/v1/jobs/${jobId}/result`);
}

export async function uploadPdf(config: AppConfig, asset: DocumentPicker.DocumentPickerAsset): Promise<Job> {
  const form = new FormData();
  form.append("source", "mobile");
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

  const response = await fetch(`${config.baseUrl}/v1/jobs`, {
    method: "POST",
    headers: buildHeaders(config),
    body: form,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Upload failed: ${response.status}`);
  }
  return (await response.json()) as Job;
}

export async function retryJob(config: AppConfig, jobId: string): Promise<Job> {
  return fetchJson(config, `/v1/jobs/${jobId}/retry`, { method: "POST" });
}

export async function saveResult(config: AppConfig, jobId: string, markdown: string): Promise<void> {
  await fetchJson(config, `/v1/jobs/${jobId}/result`, {
    method: "PATCH",
    headers: buildHeaders(config, "application/json"),
    body: JSON.stringify({ markdown }),
  });
}

export async function deleteJob(config: AppConfig, jobId: string): Promise<void> {
  const response = await fetch(`${config.baseUrl}/v1/jobs/${jobId}`, {
    method: "DELETE",
    headers: buildHeaders(config),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Delete failed: ${response.status}`);
  }
}

export async function cleanupJobs(
  config: AppConfig,
  olderThanDays: number,
  statuses: string[],
): Promise<CleanupPayload> {
  const params = new URLSearchParams({ older_than_days: String(olderThanDays) });
  statuses.forEach((status) => params.append("statuses", status));
  return fetchJson(config, `/v1/jobs/cleanup?${params.toString()}`, {
    method: "POST",
  });
}
