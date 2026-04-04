import { Platform } from "react-native";
import * as DocumentPicker from "expo-document-picker";

import type { AppConfig, HwpxTableMode, Job, JobCreatePayload, ResultPayload } from "../types";

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
    throw new Error(detail || `Request failed: ${response.status}`);
  }

  return (await response.json()) as T;
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
  turnstileToken?: string | null,
): Promise<JobCreatePayload> {
  const form = new FormData();
  form.append("source", "mobile");
  form.append("hwpx_table_mode", hwpxTableMode);
  if (turnstileToken) {
    form.append("cf-turnstile-response", turnstileToken);
  }
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
  return (await response.json()) as JobCreatePayload;
}

export async function retryJob(config: AppConfig, jobId: string, editToken: string): Promise<Job> {
  return fetchJson(config, `/v1/jobs/${jobId}/retry`, { method: "POST" }, editToken);
}

export async function saveResult(config: AppConfig, jobId: string, markdown: string, editToken: string): Promise<void> {
  await fetchJson(config, `/v1/jobs/${jobId}/result`, {
    method: "PATCH",
    headers: buildHeaders(config, "application/json", editToken),
    body: JSON.stringify({ markdown }),
  }, editToken);
}
