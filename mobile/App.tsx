import React, { startTransition, useDeferredValue, useEffect, useMemo, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Linking,
  Modal,
  Share,
  Platform,
  Pressable,
  SafeAreaView,
  ScrollView,
  Text,
  TextInput,
  useWindowDimensions,
  View,
} from "react-native";
import * as DocumentPicker from "expo-document-picker";
import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";

import { JobDetailPanel } from "./src/components/JobDetailPanel";
import { SettingsModal } from "./src/components/SettingsModal";
import { WorkspaceToolbar } from "./src/components/WorkspaceToolbar";
import {
  DEFAULT_CONFIG,
  getServerLabel,
  isHostedWeb,
  SERVER_FALLBACK_TIMEOUT_MS,
  SERVER_PRESETS,
} from "./src/constants";
import {
  ApiError,
  fetchJob,
  fetchResult,
  fetchTodayPolicyBriefingsDirect,
  fetchTodayPolicyBriefings,
  importPolicyBriefing,
  retryJob,
  saveResult,
  uploadPdf,
} from "./src/services/api";
import { clearDraft, loadConfig, loadDraft, persistConfig, persistDraft } from "./src/storage/config";
import { styles } from "./src/styles";
import type {
  AppConfig,
  HwpxTableMode,
  Job,
  PolicyBriefingItem,
  ResultPayload,
  ResultVariant,
} from "./src/types";

type EditorSelection = {
  start: number;
  end: number;
};

type RecentJobEntry = {
  jobId: string;
  editToken: string | null;
  fileName: string;
  baseUrl: string;
  loadedAt: number;
};

type WebDropAsset = DocumentPicker.DocumentPickerAsset & { file?: File };
type PendingLandingAction = {
  type: "open-picker" | "open-policy-briefings";
  requestedAt: number;
};

type PolicyBriefingServerStatus = {
  key: string;
  label: string;
  url: string;
  anyFetchFailure: boolean;
  servedStale: boolean;
  warning: string | null;
  error: string | null;
  lastRefreshedAt: string | null;
};

type PolicyBriefingServerHealthStatus = {
  key: string;
  label: string;
  url: string;
  ok: boolean;
  detail: string;
};

const LANDING_ACTION_STORAGE_KEY = "govpress:landing-action";
const LANDING_UPLOAD_DB = "govpress-landing";
const LANDING_UPLOAD_STORE = "pending-uploads";
const LANDING_UPLOAD_KEY = "pending-file";
const POLICY_BRIEFING_UPSTREAM_FAILURE_MESSAGE =
  "정책브리핑 제공기관 API 응답이 지연되거나 장애 상태입니다. 잠시 후 다시 시도해 주세요.";

function normalizePolicyBriefingStatusMessage(message: string): string {
  const lowered = message.toLowerCase();
  if (
    lowered.includes("load failed") ||
    lowered.includes("failed to fetch") ||
    lowered.includes("signal is aborted") ||
    lowered.includes("aborterror") ||
    lowered.includes("bad gateway") ||
    lowered.includes("timed out") ||
    lowered.includes("timeout") ||
    lowered.includes("network")
  ) {
    return POLICY_BRIEFING_UPSTREAM_FAILURE_MESSAGE;
  }
  return message;
}

function formatProbeError(error: unknown): string {
  if (error instanceof DOMException && error.name === "AbortError") {
    return "timeout";
  }
  if (error instanceof Error) {
    const message = error.message.trim();
    return message || error.name || "fetch failed";
  }
  return String(error || "fetch failed");
}

function isRetryableProbeFailure(detail: string): boolean {
  const lowered = detail.toLowerCase();
  return (
    lowered.includes("timeout") ||
    lowered.includes("timed out") ||
    lowered.includes("abort") ||
    lowered.includes("fetch") ||
    lowered.includes("load failed") ||
    lowered.includes("network")
  );
}

async function probeServerApiReachability(
  url: string,
  apiKey: string,
  timeoutMs: number,
): Promise<{ ok: boolean; detail: string }> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${url}/v1/policy-briefings/today?date=2026-04-08&_t=${Date.now()}`, {
      signal: controller.signal,
      cache: "no-store",
      headers: apiKey.trim() ? { "X-API-Key": apiKey.trim() } : undefined,
    });
    if (response.ok) {
      return { ok: true, detail: `API HTTP ${response.status}` };
    }
    return { ok: false, detail: `API HTTP ${response.status}` };
  } catch (error) {
    return { ok: false, detail: formatProbeError(error) };
  } finally {
    clearTimeout(timeout);
  }
}

async function probeServerHealthStatus(
  url: string,
  apiKey: string,
  timeoutMs: number,
): Promise<{ ok: boolean; detail: string }> {
  const attempts = 3;
  let lastFailure = "unknown";
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(`${url}/health?_t=${Date.now()}_${attempt}`, {
        signal: controller.signal,
        cache: "no-store",
      });
      if (response.ok) {
        return { ok: true, detail: `HTTP ${response.status}` };
      }
      lastFailure = `HTTP ${response.status}`;
      if (attempt === attempts - 1) {
        break;
      }
    } catch (error) {
      lastFailure = formatProbeError(error);
      if (attempt === attempts - 1) {
        break;
      }
    } finally {
      clearTimeout(timeout);
    }
  }
  if (isRetryableProbeFailure(lastFailure)) {
    const apiResult = await probeServerApiReachability(url, apiKey, timeoutMs);
    if (apiResult.ok) {
      return apiResult;
    }
  }
  return { ok: false, detail: lastFailure };
}

function consumeLandingAction(): PendingLandingAction | null {
  if (Platform.OS !== "web" || typeof window === "undefined") {
    return null;
  }
  const serialized = window.sessionStorage.getItem(LANDING_ACTION_STORAGE_KEY);
  if (!serialized) {
    return null;
  }
  window.sessionStorage.removeItem(LANDING_ACTION_STORAGE_KEY);
  try {
    return JSON.parse(serialized) as PendingLandingAction;
  } catch {
    return null;
  }
}

function openLandingUploadDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = window.indexedDB.open(LANDING_UPLOAD_DB, 1);
    request.onupgradeneeded = () => {
      const database = request.result;
      if (!database.objectStoreNames.contains(LANDING_UPLOAD_STORE)) {
        database.createObjectStore(LANDING_UPLOAD_STORE);
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error ?? new Error("indexedDB open failed"));
  });
}

async function readPendingLandingFile(): Promise<File | null> {
  if (Platform.OS !== "web" || typeof window === "undefined" || !window.indexedDB) {
    return null;
  }

  const database = await openLandingUploadDatabase();
  try {
    const entry = await new Promise<unknown>((resolve, reject) => {
      const transaction = database.transaction(LANDING_UPLOAD_STORE, "readwrite");
      const store = transaction.objectStore(LANDING_UPLOAD_STORE);
      const request = store.get(LANDING_UPLOAD_KEY);

      request.onsuccess = () => {
        store.delete(LANDING_UPLOAD_KEY);
        resolve(request.result);
      };
      request.onerror = () => reject(request.error ?? new Error("indexedDB read failed"));
    });

    if (!entry || typeof entry !== "object") {
      return null;
    }

    const pending = entry as {
      file?: Blob;
      name?: string;
      type?: string;
      lastModified?: number;
    };

    if (!pending.file) {
      return null;
    }

    if (pending.file instanceof File) {
      return pending.file;
    }

    return new File([pending.file], pending.name || "upload.bin", {
      type: pending.type || pending.file.type || "application/octet-stream",
      lastModified: pending.lastModified || Date.now(),
    });
  } finally {
    database.close();
  }
}

function findLineStart(text: string, index: number): number {
  const newlineIndex = text.lastIndexOf("\n", Math.max(0, index - 1));
  return newlineIndex === -1 ? 0 : newlineIndex + 1;
}

function findLineEnd(text: string, index: number): number {
  const newlineIndex = text.indexOf("\n", index);
  return newlineIndex === -1 ? text.length : newlineIndex;
}

function extractSectionHeadings(markdown: string): Array<{ title: string; index: number }> {
  const headings: Array<{ title: string; index: number }> = [];
  const pattern = /^(#{1,6})\s+(.+)$/gm;
  let match = pattern.exec(markdown);
  while (match) {
    headings.push({ title: match[2].trim(), index: match.index });
    match = pattern.exec(markdown);
  }
  return headings;
}

function dedupePolicyBriefings(items: PolicyBriefingItem[]): PolicyBriefingItem[] {
  const seen = new Set<string>();
  const deduped: PolicyBriefingItem[] = [];
  for (const item of items) {
    if (seen.has(item.news_item_id)) {
      continue;
    }
    seen.add(item.news_item_id);
    deduped.push(item);
  }
  return deduped;
}

export default function App(): React.JSX.Element {
  const { width } = useWindowDimensions();
  const isWideLayout = width >= 980;
  const isTabletLayout = width >= 720;
  const isCompactLayout = width < 720;
  const [config, setConfig] = useState<AppConfig>(DEFAULT_CONFIG);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [currentEditToken, setCurrentEditToken] = useState<string | null>(null);
  const [selectedJobBaseUrl, setSelectedJobBaseUrl] = useState<string>(DEFAULT_CONFIG.baseUrl);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [result, setResult] = useState<ResultPayload | null>(null);
  const [editorText, setEditorText] = useState("");
  const deferredEditorText = useDeferredValue(editorText);
  const [activeTab, setActiveTab] = useState<"preview" | "markdown">("preview");
  const [editorSelection, setEditorSelection] = useState<EditorSelection>({ start: 0, end: 0 });
  const [editorFocusToken, setEditorFocusToken] = useState(0);
  const [loadingConfig, setLoadingConfig] = useState(true);
  const [settingsVisible, setSettingsVisible] = useState(false);
  const [configDraft, setConfigDraft] = useState<AppConfig>(DEFAULT_CONFIG);
  const [busy, setBusy] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [editing, setEditing] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [infoVisible, setInfoVisible] = useState(false);
  const [policyBriefingVisible, setPolicyBriefingVisible] = useState(false);
  const [policyBriefingStatusVisible, setPolicyBriefingStatusVisible] = useState(false);
  const [hwpxTableMode, setHwpxTableMode] = useState<HwpxTableMode>("text");
  const [selectedTableMode, setSelectedTableMode] = useState<HwpxTableMode>("text");
  const [loadedTableMode, setLoadedTableMode] = useState<HwpxTableMode>("text");
  const [draftHydratedJobId, setDraftHydratedJobId] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [policyBriefings, setPolicyBriefings] = useState<PolicyBriefingItem[]>([]);
  const [policyBriefingLoading, setPolicyBriefingLoading] = useState(false);
  const [policyBriefingError, setPolicyBriefingError] = useState<string | null>(null);
  const [policyBriefingWarning, setPolicyBriefingWarning] = useState<string | null>(null);
  const [policyBriefingLastRefreshedAt, setPolicyBriefingLastRefreshedAt] = useState<string | null>(null);
  const [policyBriefingServedStale, setPolicyBriefingServedStale] = useState(false);
  const [policyBriefingAnyFetchFailure, setPolicyBriefingAnyFetchFailure] = useState(false);
  const [policyBriefingServerStatuses, setPolicyBriefingServerStatuses] = useState<PolicyBriefingServerStatus[]>([]);
  const [policyBriefingServerHealthStatuses, setPolicyBriefingServerHealthStatuses] = useState<
    PolicyBriefingServerHealthStatus[]
  >([]);
  const [policyBriefingQuery, setPolicyBriefingQuery] = useState("");
  const [importingNewsItemId, setImportingNewsItemId] = useState<string | null>(null);
  const [desktopSplitRatio, setDesktopSplitRatio] = useState(0.5);
  const [dragOverlayVisible, setDragOverlayVisible] = useState(false);
  const [mobileShowList, setMobileShowList] = useState(false);
  const [recentJobs, setRecentJobs] = useState<RecentJobEntry[]>([]);
  const jobRefreshSeqRef = useRef(0);
  const landingIntentHandledRef = useRef(false);
  const selectedJobConfig = useMemo<AppConfig>(() => {
    const baseUrl = selectedJobBaseUrl || config.baseUrl;
    return { ...config, baseUrl };
  }, [config, selectedJobBaseUrl]);
  const selectedVariant = useMemo<ResultVariant>(() => {
    if (!result) {
      return { markdown: null, html_preview: null };
    }
    if (result.table_variants) {
      return result.table_variants[selectedTableMode] || { markdown: result.markdown, html_preview: result.html_preview };
    }
    if (selectedTableMode === loadedTableMode) {
      return { markdown: result.markdown, html_preview: result.html_preview };
    }
    return { markdown: null, html_preview: null };
  }, [loadedTableMode, result, selectedTableMode]);
  const selectedResultText = useMemo(() => {
    if (!selectedVariant.markdown) {
      return "";
    }
    return editing ? deferredEditorText : selectedVariant.markdown;
  }, [deferredEditorText, editing, selectedVariant.markdown]);
  const hasUnsavedChanges = editing && editorText !== (selectedVariant.markdown || "");
  const previewMarkdown = useMemo(() => {
    if (editing || hasUnsavedChanges) {
      return editorText;
    }
    return selectedResultText;
  }, [editing, hasUnsavedChanges, editorText, selectedResultText]);
  const hasAsyncTableVariants = !!result?.table_variants;
  const policyBriefingStatusSummary = useMemo(() => {
    if (policyBriefingLoading) {
      return "정책브리핑 API 상태를 확인 중입니다.";
    }
    if (policyBriefingError) {
      return policyBriefingError;
    }
    if (policyBriefingAnyFetchFailure) {
      return "최근 5일 조회 중 일부 날짜 요청이 실패했습니다.";
    }
    if (policyBriefingServedStale) {
      return "캐시된 정책브리핑 목록이 제공되었습니다.";
    }
    if (policyBriefingWarning) {
      return policyBriefingWarning;
    }
    return "정책브리핑 API 상태가 정상입니다.";
  }, [
    policyBriefingAnyFetchFailure,
    policyBriefingError,
    policyBriefingLoading,
    policyBriefingServedStale,
    policyBriefingWarning,
  ]);
  const htmlVariantState: "ready" | "pending" | "unavailable" = useMemo(() => {
    if (!selectedJob || !selectedJob.file_name.toLowerCase().endsWith(".hwpx")) {
      return "unavailable";
    }
    if (!result) {
      return "pending";
    }
    if (result.table_variants) {
      return result.table_variants.html?.markdown ? "ready" : "pending";
    }
    return loadedTableMode === "html" ? "ready" : "unavailable";
  }, [loadedTableMode, result, selectedJob]);
  const needsHtmlVariant =
    !!selectedJob &&
    selectedJob.file_name.toLowerCase().endsWith(".hwpx") &&
    hasAsyncTableVariants &&
    htmlVariantState === "pending";
  const sectionHeadings = useMemo(() => extractSectionHeadings(editorText), [editorText]);

  const groupedPolicyBriefings = useMemo(() => {
    const q = policyBriefingQuery.trim().toLowerCase();
    const filtered = q
      ? policyBriefings.filter(
          (item) =>
            item.title.toLowerCase().includes(q) ||
            item.department.toLowerCase().includes(q),
        )
      : policyBriefings;
    const groups = new Map<string, PolicyBriefingItem[]>();
    for (const item of filtered) {
      const key = item.approve_date.substring(0, 10); // "MM/DD/YYYY"
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key)!.push(item);
    }
    return Array.from(groups.entries()).sort((a, b) => {
      // Sort desc: parse MM/DD/YYYY → sortable string YYYY/MM/DD
      const toSortable = (s: string) => `${s.slice(6)}/${s.slice(0, 5)}`;
      return toSortable(b[0]).localeCompare(toSortable(a[0]));
    });
  }, [policyBriefings, policyBriefingQuery]);

  function showError(title: string, error: unknown): void {
    const message = error instanceof Error ? error.message : String(error);
    setNotice(`${title}: ${message}`);
    if (Platform.OS !== "web") {
      Alert.alert(title, message);
    }
  }

  function invalidateJobRefreshes(): void {
    jobRefreshSeqRef.current += 1;
  }

  function addToRecentJobs(jobId: string, editToken: string | null, fileName: string, baseUrl: string): void {
    setRecentJobs((prev) => {
      const filtered = prev.filter((e) => e.jobId !== jobId);
      return [{ jobId, editToken, fileName, baseUrl, loadedAt: Date.now() }, ...filtered].slice(0, 8);
    });
  }

  function formatRelativeTime(ts: number): string {
    const diff = Math.floor((Date.now() - ts) / 1000);
    if (diff < 60) return "방금";
    if (diff < 3600) return `${Math.floor(diff / 60)}분 전`;
    const d = new Date(ts);
    return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  }

  function formatKoreanDate(mmddyyyy: string): string {
    // Input: "MM/DD/YYYY"
    const parts = mmddyyyy.split("/");
    if (parts.length < 3) return mmddyyyy;
    const [mm, dd, yyyy] = parts.map(Number);
    const d = new Date(yyyy, mm - 1, dd);
    const days = ["일", "월", "화", "수", "목", "금", "토"];
    return `${yyyy}년 ${mm}월 ${dd}일 (${days[d.getDay()]})`;
  }

  function formatPolicyBriefingTime(approveDate: string): string {
    const match = approveDate.match(/\b(\d{2}):(\d{2})(?::\d{2})?\b/);
    if (!match) return "";
    return `${match[1]}:${match[2]}`;
  }

  useEffect(() => {
    loadConfig()
      .then((loaded) => {
        setConfig(loaded);
        setConfigDraft(loaded);
        setSelectedJobBaseUrl(loaded.baseUrl);
      })
      .finally(() => setLoadingConfig(false));
  }, []);

  useEffect(() => {
    if (Platform.OS !== "web" || typeof document === "undefined") {
      return;
    }

    const fontLinkId = "pretendard-gov-font-link";
    const fontStyleId = "pretendard-gov-font-style";

    if (!document.getElementById(fontLinkId)) {
      const link = document.createElement("link");
      link.id = fontLinkId;
      link.rel = "stylesheet";
      link.crossOrigin = "anonymous";
      link.href =
        "https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard-gov.min.css";
      document.head.appendChild(link);
    }

    if (!document.getElementById(fontStyleId)) {
      const style = document.createElement("style");
      style.id = fontStyleId;
      style.textContent = `
        :root {
          color-scheme: light;
          --govpress-scrollbar-track: #f4eadc;
          --govpress-scrollbar-thumb: #ccb89d;
          --govpress-scrollbar-thumb-hover: #b89f7f;
        }
        html[data-theme="dark"] {
          color-scheme: dark;
          --govpress-scrollbar-track: #2d241e;
          --govpress-scrollbar-thumb: #6a5848;
          --govpress-scrollbar-thumb-hover: #816c59;
        }
        html, body, input, textarea, button, select {
          font-family: "Pretendard GOV Variable", "Pretendard GOV", -apple-system, BlinkMacSystemFont, system-ui, Roboto, "Helvetica Neue", "Segoe UI", "Apple SD Gothic Neo", "Noto Sans KR", "Malgun Gothic", sans-serif;
        }
        input:focus, textarea:focus, button:focus {
          outline: none;
          box-shadow: none;
        }
        * {
          scrollbar-color: var(--govpress-scrollbar-thumb) var(--govpress-scrollbar-track);
        }
        *::-webkit-scrollbar {
          width: 12px;
          height: 12px;
        }
        *::-webkit-scrollbar-track {
          background: var(--govpress-scrollbar-track);
        }
        *::-webkit-scrollbar-thumb {
          background: var(--govpress-scrollbar-thumb);
          border-radius: 999px;
          border: 3px solid var(--govpress-scrollbar-track);
        }
        *::-webkit-scrollbar-thumb:hover {
          background: var(--govpress-scrollbar-thumb-hover);
        }
      `;
      document.head.appendChild(style);
    }
  }, []);

  useEffect(() => {
    if (Platform.OS !== "web" || typeof document === "undefined") {
      return;
    }
    document.documentElement.setAttribute("data-theme", isDarkMode ? "dark" : "light");
  }, [isDarkMode]);

  useEffect(() => {
    if (!editing || !selectedJobId) {
      return;
    }
    const handle = setTimeout(() => {
      void persistDraft(selectedJobId, editorText);
    }, 500);
    return () => clearTimeout(handle);
  }, [editing, selectedJobId, editorText]);

  useEffect(() => {
    if (Platform.OS !== "web" || !editing || !hasUnsavedChanges || typeof window === "undefined") {
      return;
    }
    const handler = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [editing, hasUnsavedChanges]);

  useEffect(() => {
    if (Platform.OS !== "web" || typeof window === "undefined") {
      return;
    }

    let dragDepth = 0;

    function isSupportedFile(file: File | null | undefined): boolean {
      if (!file) {
        return false;
      }
      const name = file.name.toLowerCase();
      return name.endsWith(".pdf") || name.endsWith(".hwpx") || name.endsWith(".md");
    }

    function hasFilePayload(event: DragEvent): boolean {
      const transfer = event.dataTransfer;
      if (!transfer) {
        return false;
      }
      if (Array.from(transfer.files || []).length > 0) {
        return true;
      }
      if (Array.from(transfer.items || []).some((item) => item.kind === "file")) {
        return true;
      }
      if (Array.from(transfer.types || []).includes("Files")) {
        return true;
      }
      return false;
    }

    function hasSupportedFiles(event: DragEvent): boolean {
      const transfer = event.dataTransfer;
      if (!transfer) {
        return false;
      }
      const files = Array.from(transfer.files || []);
      if (files.some((file) => isSupportedFile(file))) {
        return true;
      }
      const items = Array.from(transfer.items || []);
      const hasUnknownFilePayload = items.some((item) => item.kind === "file" && !(item.type || "").trim());
      if (hasUnknownFilePayload || Array.from(transfer.types || []).includes("Files")) {
        return true;
      }
      return items.some((item) => {
        if (item.kind !== "file") {
          return false;
        }
        const type = (item.type || "").toLowerCase();
        return type === "application/pdf" || type.includes("hwpx") || type === "text/markdown" || type === "text/plain";
      });
    }

    const handleDragEnter = (event: DragEvent) => {
      if (!hasFilePayload(event)) {
        return;
      }
      event.preventDefault();
      event.stopPropagation();
      dragDepth += 1;
      setDragOverlayVisible(hasSupportedFiles(event));
    };

    const handleDragOver = (event: DragEvent) => {
      if (!hasFilePayload(event)) {
        return;
      }
      event.preventDefault();
      event.stopPropagation();
      if (event.dataTransfer) {
        event.dataTransfer.dropEffect = hasSupportedFiles(event) ? "copy" : "none";
      }
    };

    const handleDragLeave = (event: DragEvent) => {
      if (!hasFilePayload(event)) {
        return;
      }
      event.preventDefault();
      event.stopPropagation();
      dragDepth = Math.max(0, dragDepth - 1);
      if (dragDepth === 0) {
        setDragOverlayVisible(false);
      }
    };

    const handleDrop = (event: DragEvent) => {
      if (!hasFilePayload(event)) {
        return;
      }
      event.preventDefault();
      event.stopPropagation();
      dragDepth = 0;
      setDragOverlayVisible(false);
      const file = Array.from(event.dataTransfer?.files || []).find((candidate) => isSupportedFile(candidate));
      if (!file) {
        setNotice("PDF, HWPX, Markdown 파일만 업로드할 수 있습니다.");
        return;
      }
      const asset: WebDropAsset = {
        uri: window.URL.createObjectURL(file),
        mimeType: file.type || undefined,
        name: file.name,
        size: file.size,
        file,
        lastModified: file.lastModified,
      };
      void handleSelectedAsset(asset);
    };

    window.addEventListener("dragenter", handleDragEnter, true);
    window.addEventListener("dragover", handleDragOver, true);
    window.addEventListener("dragleave", handleDragLeave, true);
    window.addEventListener("drop", handleDrop, true);
    return () => {
      window.removeEventListener("dragenter", handleDragEnter, true);
      window.removeEventListener("dragover", handleDragOver, true);
      window.removeEventListener("dragleave", handleDragLeave, true);
      window.removeEventListener("drop", handleDrop, true);
    };
  }, [config, hwpxTableMode]);

  useEffect(() => {
    if (!notice) {
      return;
    }
    if (notice === "PDF 업로드 중..." || notice === "HWPX 업로드 중...") {
      return;
    }
    const timer = setTimeout(() => {
      setNotice((current) => (current === notice ? null : current));
    }, 2200);
    return () => clearTimeout(timer);
  }, [notice]);

  useEffect(() => {
    if (!selectedJobId || !result || draftHydratedJobId === selectedJobId) {
      return;
    }
    loadDraft(selectedJobId)
      .then((draft) => {
        if (draft && draft !== selectedVariant.markdown) {
          setEditorText(draft);
          setEditing(true);
          setNotice("임시 저장된 편집본을 복원했습니다.");
        }
      })
      .finally(() => setDraftHydratedJobId(selectedJobId));
  }, [draftHydratedJobId, result, selectedJobId, selectedVariant.markdown]);

  useEffect(() => {
    if (!result || editing) {
      return;
    }
    setEditorText(selectedVariant.markdown || "");
  }, [editing, result, selectedVariant.markdown]);

  async function refreshSelectedJob(
    jobId: string,
    editToken: string,
    syncResult = true,
    suppressErrors = false,
    baseUrl = selectedJobBaseUrl || config.baseUrl,
  ): Promise<ResultPayload | null> {
    const refreshSeq = ++jobRefreshSeqRef.current;
    try {
      const jobConfig = { ...config, baseUrl };
      const payload = await fetchJob(jobConfig, jobId, editToken);
      if (refreshSeq !== jobRefreshSeqRef.current) {
        return null;
      }
      setNotice(null);
      const shouldLoadResult =
        payload.status === "completed" &&
        (syncResult || result?.job_id !== payload.job_id || selectedJob?.status !== "completed");
      startTransition(() => {
        setSelectedJob(payload);
      });
      if (shouldLoadResult) {
        try {
          const resultPayload = await fetchResult(jobConfig, jobId, editToken);
          if (refreshSeq !== jobRefreshSeqRef.current) {
            return null;
          }
          const isNewJob = result?.job_id !== payload.job_id;
          startTransition(() => {
            setResult(resultPayload);
            if (isNewJob) {
              setLoadedTableMode(payload.file_name.toLowerCase().endsWith(".hwpx") ? hwpxTableMode : "text");
              setSelectedTableMode("text");
              setEditorText(resultPayload.markdown || "");
              setEditorSelection({ start: 0, end: 0 });
              setEditorFocusToken((current) => current + 1);
            }
          });
          return resultPayload;
        } catch (error) {
          if (error instanceof ApiError && error.status === 404) {
            if (refreshSeq !== jobRefreshSeqRef.current) {
              return null;
            }
            startTransition(() => {
              setSelectedJobId(null);
              setSelectedJob(null);
              setResult(null);
              setEditorText("");
              setEditing(false);
              setNotice(null);
            });
            return null;
          }
          throw error;
        }
      }
      return null;
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        if (refreshSeq !== jobRefreshSeqRef.current) {
          return null;
        }
        if (selectedJobId === jobId) {
          startTransition(() => {
            setSelectedJobId(null);
            setSelectedJob(null);
            setResult(null);
            setEditorText("");
            setEditing(false);
            setNotice(null);
          });
        }
        return null;
      }
      if (!suppressErrors) {
        showError("작업 상태를 불러오지 못했습니다.", error);
      }
    }
    return null;
  }

  useEffect(() => {
    if (!selectedJobId || !currentEditToken || selectedJobId.startsWith("local-md-")) {
      return;
    }

    const shouldPollJob = selectedJob?.status === "queued" || selectedJob?.status === "processing";
    const shouldPollResult = selectedJob?.status === "completed" && !result;

    if (!shouldPollJob && !shouldPollResult) {
      return;
    }

    const interval = setInterval(() => {
      void refreshSelectedJob(selectedJobId, currentEditToken, shouldPollResult, true, selectedJobBaseUrl || config.baseUrl);
    }, 2000);

    return () => clearInterval(interval);
  }, [config.baseUrl, currentEditToken, result, selectedJob?.status, selectedJobBaseUrl, selectedJobId]);

  async function openLocalMarkdown(asset: DocumentPicker.DocumentPickerAsset): Promise<void> {
    const webFile = (asset as WebDropAsset).file;
    let markdown = "";

    if (Platform.OS === "web") {
      if (webFile) {
        markdown = await webFile.text();
      } else {
        const response = await fetch(asset.uri);
        markdown = await response.text();
      }
    } else {
      markdown = await FileSystem.readAsStringAsync(asset.uri, {
        encoding: FileSystem.EncodingType.UTF8,
      });
    }

    const localJobId = `local-md-${Date.now()}`;
    const localJob: Job = {
      job_id: localJobId,
      status: "completed",
      file_name: asset.name,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    const localResult: ResultPayload = {
      job_id: localJobId,
      status: "completed",
      markdown,
      html_preview: null,
      table_variants: {
        text: { markdown, html_preview: null },
        html: { markdown, html_preview: null },
      },
      meta: {
        title: asset.name.replace(/\.md$/i, ""),
        department: null,
        source_file_name: asset.name,
      },
    };
    startTransition(() => {
      setSelectedJobId(localJobId);
      setCurrentEditToken(null);
      setSelectedJob(localJob);
      setResult(localResult);
      setLoadedTableMode("text");
      setSelectedTableMode("text");
      setEditorText(markdown);
      setEditorSelection({ start: 0, end: 0 });
      setEditing(false);
      setActiveTab("preview");
      setMobileShowList(false);
    });
    addToRecentJobs(localJobId, null, asset.name, config.baseUrl);
    setNotice("Markdown 문서를 열었습니다.");
  }

  async function handleSelectedAsset(asset: DocumentPicker.DocumentPickerAsset): Promise<void> {
    const lowerName = asset.name.toLowerCase();
    if (lowerName.endsWith(".md")) {
      await openLocalMarkdown(asset);
      return;
    }
    if (!lowerName.endsWith(".pdf") && !lowerName.endsWith(".hwpx")) {
      setNotice("PDF, HWPX 또는 Markdown 파일만 열 수 있습니다.");
      return;
    }
    setBusy(true);
    setNotice(lowerName.endsWith(".hwpx") ? "HWPX 업로드 중..." : "PDF 업로드 중...");
    try {
      const { job, resolvedBaseUrl } = await uploadPdf(config, asset, hwpxTableMode);
      if (resolvedBaseUrl !== config.baseUrl) {
        const nextConfig = { ...config, baseUrl: resolvedBaseUrl };
        invalidateJobRefreshes();
        await persistConfig(nextConfig);
        startTransition(() => {
          setConfig(nextConfig);
          setConfigDraft(nextConfig);
        });
        setNotice(`${getServerLabel(resolvedBaseUrl)}로 자동 전환했습니다.`);
      }
      startTransition(() => {
        setSelectedJobId(job.job_id);
        setCurrentEditToken(job.edit_token);
        setSelectedJob(job);
        setSelectedJobBaseUrl(resolvedBaseUrl);
        setResult(null);
        setLoadedTableMode(hwpxTableMode);
        setSelectedTableMode("text");
        setEditorText("");
        setEditorSelection({ start: 0, end: 0 });
        setEditorFocusToken((current) => current + 1);
        setEditing(false);
        setActiveTab("preview");
        setMobileShowList(false);
      });
      addToRecentJobs(job.job_id, job.edit_token, job.file_name, resolvedBaseUrl);
      await refreshSelectedJob(job.job_id, job.edit_token, false, false, resolvedBaseUrl);
    } catch (error) {
      showError("파일 업로드에 실패했습니다.", error);
    } finally {
      setBusy(false);
    }
  }

  async function handlePickPdf(): Promise<void> {
    try {
      const picked = await DocumentPicker.getDocumentAsync({
        type:
          Platform.OS === "web"
            ? [".pdf", ".hwpx", ".md"]
            : ["application/pdf", "application/octet-stream", "text/markdown"],
        copyToCacheDirectory: true,
      });
      if (picked.canceled || !picked.assets.length) {
        return;
      }
      await handleSelectedAsset(picked.assets[0]);
    } catch (error) {
      showError("파일 업로드에 실패했습니다.", error);
    }
  }

  async function handleOpenPolicyBriefings(): Promise<void> {
    setPolicyBriefingVisible(true);
    setPolicyBriefingLoading(true);
    setPolicyBriefingError(null);
    setPolicyBriefingWarning(null);
    setPolicyBriefingLastRefreshedAt(null);
    setPolicyBriefingServedStale(false);
    setPolicyBriefingAnyFetchFailure(false);
    setPolicyBriefingServerStatuses([]);
    setPolicyBriefingServerHealthStatuses([]);
    setPolicyBriefingQuery("");
    try {
      const today = new Date();
      const dates = Array.from({ length: 5 }, (_, i) => {
        const d = new Date(today);
        d.setDate(d.getDate() - i);
        return d.toISOString().slice(0, 10); // YYYY-MM-DD
      });
      const [healthStatusResults, directStatusResults] = await Promise.all([
        Promise.all(
          SERVER_PRESETS.map(async (preset) => {
            const result = await probeServerHealthStatus(preset.url, config.apiKey, SERVER_FALLBACK_TIMEOUT_MS);
            return {
              key: preset.key,
              label: preset.label,
              url: preset.url,
              ok: result.ok,
              detail: result.detail,
            } satisfies PolicyBriefingServerHealthStatus;
          }),
        ),
        Promise.all(
          SERVER_PRESETS.map(async (preset) => {
            const results = await Promise.allSettled(
              dates.map((date) => fetchTodayPolicyBriefingsDirect({ ...config, baseUrl: preset.url }, preset.url, date)),
            );
            const failures: string[] = [];
            const warnings: string[] = [];
            const refreshTimes: string[] = [];
            let servedStale = false;
            for (const r of results) {
              if (r.status === "fulfilled") {
                if (r.value.served_stale) {
                  servedStale = true;
                }
                if (r.value.warning) {
                  warnings.push(normalizePolicyBriefingStatusMessage(r.value.warning));
                }
                if (r.value.last_refreshed_at) {
                  refreshTimes.push(r.value.last_refreshed_at);
                }
              } else {
                failures.push(
                  normalizePolicyBriefingStatusMessage(r.reason instanceof Error ? r.reason.message : String(r.reason)),
                );
              }
            }
            const freshest = refreshTimes.sort().at(-1) || null;
            const error = failures[0] || null;
            const warning = warnings[0] || null;
            return {
              key: preset.key,
              label: preset.label,
              url: preset.url,
              anyFetchFailure: failures.length > 0,
              servedStale,
              warning,
              error,
              lastRefreshedAt: freshest,
            } satisfies PolicyBriefingServerStatus;
          }),
        ),
      ]);
      setPolicyBriefingServerHealthStatuses(healthStatusResults);
      setPolicyBriefingServerStatuses(directStatusResults);
      const results = await Promise.allSettled(
        dates.map((date) => fetchTodayPolicyBriefings(config, date)),
      );
      const allItems: PolicyBriefingItem[] = [];
      const failures: string[] = [];
      const warnings: string[] = [];
      const refreshTimes: string[] = [];
      let servedStale = false;
      for (const r of results) {
        if (r.status === "fulfilled") {
          allItems.push(...r.value.items);
          if (r.value.served_stale) {
            servedStale = true;
          }
          if (r.value.warning) {
            warnings.push(normalizePolicyBriefingStatusMessage(r.value.warning));
          }
          if (r.value.last_refreshed_at) {
            refreshTimes.push(r.value.last_refreshed_at);
          }
        } else {
          failures.push(
            normalizePolicyBriefingStatusMessage(r.reason instanceof Error ? r.reason.message : String(r.reason)),
          );
        }
      }
      const dedupedItems = dedupePolicyBriefings(allItems);
      setPolicyBriefingAnyFetchFailure(failures.length > 0);
      if (dedupedItems.length === 0 && failures.length > 0) {
        const providerIssue = failures.find((message) => message.includes("제공기관 API"));
        const failureMessage = providerIssue || failures[0];
        setPolicyBriefings([]);
        setPolicyBriefingError(failureMessage);
        setPolicyBriefingServedStale(false);
        return;
      }
      setPolicyBriefings(dedupedItems);
      setPolicyBriefingError(null);
      setPolicyBriefingServedStale(servedStale);
      const freshest = refreshTimes.sort().at(-1) || null;
      setPolicyBriefingLastRefreshedAt(freshest);
      const failureWarning =
        failures.find((message) => message.includes("제공기관 API")) ||
        failures.find((message) => message.includes("정책브리핑 목록 요청에 실패했습니다.")) ||
        failures[0] ||
        null;
      const warningMessage =
        warnings.find((message) => message.includes("제공기관 API")) ||
        warnings[0] ||
        failureWarning;
      setPolicyBriefingWarning(warningMessage);
      setNotice(warningMessage ? null : `정책브리핑 목록 갱신 완료 — ${dedupedItems.length}건`);
    } catch (error) {
      showError("정책브리핑을 불러오지 못했습니다.", error);
    } finally {
      setPolicyBriefingLoading(false);
    }
  }

  async function handleImportPolicyBriefing(item: PolicyBriefingItem): Promise<void> {
    setImportingNewsItemId(item.news_item_id);
    setBusy(true);
    setNotice("정책브리핑 HWPX를 가져오는 중...");
    try {
      const { payload: imported, resolvedBaseUrl } = await importPolicyBriefing(config, item.news_item_id);
      if (resolvedBaseUrl !== config.baseUrl) {
        const nextConfig = { ...config, baseUrl: resolvedBaseUrl };
        invalidateJobRefreshes();
        await persistConfig(nextConfig);
        startTransition(() => {
          setConfig(nextConfig);
          setConfigDraft(nextConfig);
        });
        setNotice(`${getServerLabel(resolvedBaseUrl)}로 자동 전환했습니다.`);
      }
      startTransition(() => {
        setPolicyBriefingVisible(false);
        setSelectedJobId(imported.job_id);
        setCurrentEditToken(imported.edit_token);
        setSelectedJob(imported);
        setSelectedJobBaseUrl(resolvedBaseUrl);
        setResult(null);
        setLoadedTableMode("text");
        setSelectedTableMode("text");
        setEditorText("");
        setEditorSelection({ start: 0, end: 0 });
        setEditorFocusToken((current) => current + 1);
        setEditing(false);
        setActiveTab("preview");
        setMobileShowList(false);
      });
      addToRecentJobs(imported.job_id, imported.edit_token, imported.file_name, resolvedBaseUrl);
      await refreshSelectedJob(imported.job_id, imported.edit_token, false, false, resolvedBaseUrl);
    } catch (error) {
      showError("정책브리핑 보도자료를 가져오지 못했습니다.", error);
    } finally {
      setImportingNewsItemId(null);
      setBusy(false);
    }
  }

  useEffect(() => {
    if (Platform.OS !== "web" || loadingConfig || landingIntentHandledRef.current || typeof window === "undefined") {
      return;
    }

    landingIntentHandledRef.current = true;

    const params = new URLSearchParams(window.location.search);
    const wantsEditor = params.get("editor") === "1";
    const queryIntent = params.get("intent");
    const pendingAction =
      queryIntent === "policy-briefings"
        ? { type: "open-policy-briefings" as const, requestedAt: Date.now() }
        : consumeLandingAction();

    if (
      isHostedWeb() &&
      !wantsEditor &&
      !queryIntent &&
      !pendingAction &&
      /^\/GovPress_PDF_MD\/app\/?$/.test(window.location.pathname)
    ) {
      window.location.replace("/GovPress_PDF_MD/landing.html");
      return;
    }

    if (queryIntent) {
      params.delete("intent");
      const nextSearch = params.toString();
      const nextUrl = `${window.location.pathname}${nextSearch ? `?${nextSearch}` : ""}${window.location.hash}`;
      window.history.replaceState({}, "", nextUrl);
    }

    if (!pendingAction) {
      return;
    }
    const action = pendingAction;

    async function hydrateLandingIntent(): Promise<void> {
      if (action.type === "open-policy-briefings") {
        await handleOpenPolicyBriefings();
        return;
      }

      const file = await readPendingLandingFile();
      if (!file) {
        await handlePickPdf();
        return;
      }

      const asset: WebDropAsset = {
        uri: window.URL.createObjectURL(file),
        mimeType: file.type || undefined,
        name: file.name,
        size: file.size,
        file,
        lastModified: file.lastModified,
      };
      await handleSelectedAsset(asset);
    }

    void hydrateLandingIntent();
  }, [loadingConfig]);

  async function handleRetry(): Promise<void> {
    if (!selectedJobId || !currentEditToken) {
      return;
    }
    try {
      setBusy(true);
      const retried = await retryJob(selectedJobConfig, selectedJobId, currentEditToken);
      setNotice("작업을 다시 대기열에 넣었습니다.");
      startTransition(() => {
        setSelectedJob(retried);
        setResult(null);
        setEditorText("");
        setEditorSelection({ start: 0, end: 0 });
        setEditorFocusToken((current) => current + 1);
        setEditing(false);
      });
    } catch (error) {
      showError("재시도에 실패했습니다.", error);
    } finally {
      setBusy(false);
    }
  }

  async function handleChangeSelectedTableMode(mode: HwpxTableMode): Promise<void> {
    if (editing && hasUnsavedChanges) {
      setNotice("표 버전을 바꾸려면 먼저 저장하거나 되돌리세요.");
      return;
    }

    if (mode === "html" && selectedJobId && currentEditToken && !selectedJobId.startsWith("local-md-")) {
      setRefreshing(true);
      try {
        const refreshed = await refreshSelectedJob(selectedJobId, currentEditToken, true);
        const latest = refreshed ?? result;
        const htmlReady = !!latest?.table_variants?.html?.markdown;
        setSelectedTableMode(htmlReady ? "html" : "text");
        setHwpxTableMode(htmlReady ? "html" : "text");
        setNotice(htmlReady ? "HTML 표 버전을 불러왔습니다." : "HTML 표 결과를 아직 준비 중입니다. 잠시 후 다시 시도하세요.");
      } finally {
        setRefreshing(false);
      }
      return;
    }

    setHwpxTableMode(mode);
    setSelectedTableMode(mode);
  }

  async function handleSaveEdit(): Promise<void> {
    if (!selectedJobId) {
      return;
    }
    if (selectedJobId.startsWith("local-md-")) {
      const nextMarkdown = editorText;
      setResult((current) => (
        current
          ? {
              ...current,
              markdown: nextMarkdown,
              table_variants: {
                text: { markdown: nextMarkdown, html_preview: current.table_variants.text.html_preview },
                html: { markdown: nextMarkdown, html_preview: current.table_variants.html.html_preview },
              },
            }
          : current
      ));
      setEditing(false);
      setNotice("편집 내용을 적용했습니다. 필요하면 MD 저장으로 내려받으세요.");
      return;
    }
    if (!hasUnsavedChanges) {
      setNotice("저장할 변경 사항이 없습니다.");
      return;
    }
    try {
      setBusy(true);
      if (!currentEditToken) {
        setNotice("이 작업에 대한 접근 토큰이 없습니다.");
        return;
      }
      await saveResult(selectedJobConfig, selectedJobId, editorText, currentEditToken);
      await clearDraft(selectedJobId);
      const updated = await fetchResult(selectedJobConfig, selectedJobId, currentEditToken);
      setNotice("수정본을 저장했습니다.");
      startTransition(() => {
        setResult(updated);
        setEditorText(updated.table_variants?.[selectedTableMode]?.markdown || updated.markdown || "");
        setEditorSelection({ start: 0, end: 0 });
        setEditorFocusToken((current) => current + 1);
        setEditing(false);
      });
    } catch (error) {
      showError("수정본 저장에 실패했습니다.", error);
    } finally {
      setBusy(false);
    }
  }

  function handleEditorTextChange(value: string): void {
    if (!editing) {
      setEditing(true);
    }
    setEditorText(value);
  }

  function handleDiscardEdit(): void {
    setEditorText(selectedVariant.markdown || "");
    setEditorSelection({ start: 0, end: 0 });
    setEditorFocusToken((current) => current + 1);
    if (selectedJobId) {
      void clearDraft(selectedJobId);
    }
    setNotice("저장된 Markdown으로 되돌렸습니다.");
  }

  function applyEditorAction(action: "heading" | "heading2" | "heading3" | "bold" | "italic" | "bullet" | "number" | "quote" | "table" | "tableRow"): void {
    const start = editorSelection.start;
    const end = editorSelection.end;
    const selected = editorText.slice(start, end);

    if (action === "bold" || action === "italic") {
      const wrapper = action === "bold" ? "**" : "*";
      const fallback = action === "bold" ? "강조 텍스트" : "기울임 텍스트";
      const wrappedSelection = `${wrapper}${selected}${wrapper}`;
      if (selected && editorText.slice(start - wrapper.length, end + wrapper.length) === wrappedSelection) {
        const next = `${editorText.slice(0, start - wrapper.length)}${selected}${editorText.slice(end + wrapper.length)}`;
        setEditorText(next);
        setEditorSelection({ start: start - wrapper.length, end: end - wrapper.length });
        return;
      }
      if (selected.startsWith(wrapper) && selected.endsWith(wrapper) && selected.length > wrapper.length * 2) {
        const unwrapped = selected.slice(wrapper.length, -wrapper.length);
        const next = `${editorText.slice(0, start)}${unwrapped}${editorText.slice(end)}`;
        setEditorText(next);
        setEditorSelection({ start, end: start + unwrapped.length });
        return;
      }
      const value = selected || fallback;
      const next = `${editorText.slice(0, start)}${wrapper}${value}${wrapper}${editorText.slice(end)}`;
      if (selected) {
        setEditorText(next);
        setEditorSelection({ start, end: start + wrapper.length + value.length + wrapper.length });
        setEditorFocusToken((current) => current + 1);
      } else {
        const cursor = start + wrapper.length + value.length + wrapper.length;
        setEditorText(next);
        setEditorSelection({ start: cursor, end: cursor });
        setEditorFocusToken((current) => current + 1);
      }
      return;
    }

    if (action === "table") {
      const lineStart = findLineStart(editorText, start);
      const prefix = lineStart > 0 && editorText[lineStart - 1] !== "\n" ? "\n" : "";
      const snippet = `${prefix}| 항목 | 내용 |\n| --- | --- |\n| 예시 | 값 |\n`;
      const next = `${editorText.slice(0, lineStart)}${snippet}${editorText.slice(end)}`;
      const cursor = lineStart + snippet.length;
      setEditorText(next);
      setEditorSelection({ start: cursor, end: cursor });
      setEditorFocusToken((current) => current + 1);
      return;
    }

    if (action === "tableRow") {
      const lineStart = findLineStart(editorText, start);
      const lineEnd = findLineEnd(editorText, start);
      const currentLine = editorText.slice(lineStart, lineEnd);
      if (!currentLine.includes("|")) {
        setNotice("표 내부에서만 행 추가를 사용할 수 있습니다.");
        return;
      }
      const cellCount = Math.max(2, currentLine.split("|").length - 2);
      const row = `| ${Array.from({ length: cellCount }).map(() => "").join(" | ")} |\n`;
      const next = `${editorText.slice(0, lineEnd + (lineEnd < editorText.length ? 1 : 0))}${row}${editorText.slice(lineEnd + (lineEnd < editorText.length ? 1 : 0))}`;
      const cursor = lineEnd + (lineEnd < editorText.length ? 1 : 0) + row.length;
      setEditorText(next);
      setEditorSelection({ start: cursor, end: cursor });
      setEditorFocusToken((current) => current + 1);
      return;
    }

    const lineStart = findLineStart(editorText, start);
    const lineEnd = findLineEnd(editorText, Math.max(end, start));
    const block = editorText.slice(lineStart, lineEnd);
    const lines = block ? block.split("\n") : [""];
    const prefix = action === "heading"
      ? "# "
      : action === "heading2"
        ? "## "
        : action === "heading3"
          ? "### "
          : action === "bullet"
            ? "- "
            : action === "number"
              ? "1. "
              : "> ";
    const allPrefixed = lines.every((line) => line.startsWith(prefix));
    const replaced = lines
      .map((line, index) => {
        if (allPrefixed) {
          return line.slice(prefix.length);
        }
        if (action === "number") {
          return `${index + 1}. ${line.replace(/^\d+\.\s+/, "")}`;
        }
        return `${prefix}${line}`;
      })
      .join("\n");
    const next = `${editorText.slice(0, lineStart)}${replaced}${editorText.slice(lineEnd)}`;
    const cursor = lineStart + replaced.length;
    setEditorText(next);
    setEditorSelection({ start: cursor, end: cursor });
    setEditorFocusToken((current) => current + 1);
  }

  function confirmDiscardChanges(action: () => void): void {
    if (!hasUnsavedChanges) {
      action();
      return;
    }

    if (Platform.OS === "web" && typeof window !== "undefined") {
      if (window.confirm("저장되지 않은 변경 사항이 있습니다. 계속하시겠습니까?")) {
        action();
      }
      return;
    }

    Alert.alert(
      "편집 중인 내용이 있습니다",
      "저장되지 않은 변경 사항이 있습니다. 계속하시겠습니까?",
      [
        { text: "취소", style: "cancel" },
        { text: "계속", style: "destructive", onPress: action },
      ],
    );
  }

  async function handleShareMarkdown(): Promise<void> {
    if (!selectedVariant.markdown || !selectedJob) {
      return;
    }
    try {
      const documentTitle = result?.meta.title || selectedJob.file_name;
      const shareBody = `# ${documentTitle}\n\n${selectedVariant.markdown}`;
      if (Platform.OS === "web" && navigator.share) {
        await navigator.share({
          title: documentTitle,
          text: shareBody,
        });
        return;
      }
      if (Platform.OS !== "web") {
        await Share.share({
          title: documentTitle,
          message: shareBody,
        });
        return;
      }
      const outputName = selectedJob.file_name.replace(/\.(pdf|hwpx)$/i, ".md");
      const outputPath = `${FileSystem.cacheDirectory}${outputName}`;
      await FileSystem.writeAsStringAsync(outputPath, shareBody, {
        encoding: FileSystem.EncodingType.UTF8,
      });
      if (!(await Sharing.isAvailableAsync())) {
        showError("공유를 지원하지 않습니다.", "이 기기에서는 공유 기능을 사용할 수 없습니다.");
        return;
      }
      await Sharing.shareAsync(outputPath, {
        mimeType: "text/markdown",
        dialogTitle: "Markdown 공유",
      });
    } catch (error) {
      showError("공유에 실패했습니다.", error);
    }
  }

  async function handleSaveMarkdownFile(): Promise<void> {
    if ((!editorText && !selectedVariant.markdown) || !selectedJob) {
      setNotice("저장할 Markdown이 없습니다.");
      return;
    }
    const content = editorText || selectedVariant.markdown || "";
    const outputName = selectedJob.file_name.replace(/\.(pdf|hwpx)$/i, ".md");

    try {
      if (Platform.OS === "web" && typeof window !== "undefined") {
        const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
        const url = window.URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = outputName.endsWith(".md") ? outputName : `${outputName}.md`;
        anchor.click();
        window.URL.revokeObjectURL(url);
        setNotice("Markdown 파일을 저장했습니다.");
        return;
      }

      const outputPath = `${FileSystem.cacheDirectory}${outputName}`;
      await FileSystem.writeAsStringAsync(outputPath, content, {
        encoding: FileSystem.EncodingType.UTF8,
      });
      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(outputPath, {
          mimeType: "text/markdown",
          dialogTitle: "Markdown 저장",
        });
      }
    } catch (error) {
      showError("Markdown 저장에 실패했습니다.", error);
    }
  }

  async function handleCopyMarkdown(): Promise<void> {
    if (!selectedVariant.markdown || !selectedJob) {
      return;
    }
    const shareBody = `# ${result?.meta.title || selectedJob.file_name}\n\n${selectedVariant.markdown}`;
    if (Platform.OS === "web" && typeof navigator !== "undefined" && navigator.clipboard) {
      await navigator.clipboard.writeText(shareBody);
      setNotice("Markdown를 클립보드에 복사했습니다.");
      return;
    }
    setNotice("이 환경에서는 클립보드 복사를 지원하지 않습니다.");
  }

  async function handleDeleteJob(): Promise<void> {
    if (!selectedJobId) {
      return;
    }
    setSelectedJobId(null);
    setCurrentEditToken(null);
    setSelectedJobBaseUrl(config.baseUrl);
    setSelectedJob(null);
    setResult(null);
    setEditorText("");
    setEditing(false);
    setNotice(selectedJobId.startsWith("local-md-") ? "로컬 Markdown 문서를 닫았습니다." : "현재 작업 화면을 닫았습니다.");
  }

  function handleOpenGithub(): void {
    void Linking.openURL("https://github.com/wavelen-jw/GovPress_PDF_MD");
  }

  function handleOpenInfo(): void {
    setInfoVisible(true);
  }

  function handleOpenSettings(): void {
    setConfigDraft(config);
    setSettingsVisible(true);
  }

  async function handleSaveSettings(): Promise<void> {
    const next = {
      ...configDraft,
      baseUrl: configDraft.baseUrl.trim(),
      apiKey: configDraft.apiKey.trim(),
    };
    invalidateJobRefreshes();
    await persistConfig(next);
    setConfig(next);
    setSelectedJobBaseUrl(next.baseUrl);
    setNotice(null);
    setSettingsVisible(false);
  }

  function handleToggleDarkMode(): void {
    setIsDarkMode((current) => !current);
  }

  const showDetailPanel = isWideLayout || !mobileShowList;
  const currentDocumentName = selectedJob?.file_name || result?.meta.source_file_name || null;
  const isPdfPickReady = true;

  if (loadingConfig) {
    return (
      <SafeAreaView style={styles.loadingShell}>
        <ActivityIndicator size="large" color="#b75e1f" />
        <Text style={styles.loadingLabel}>정부 보고서.Markdown 준비 중</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.safeArea, isDarkMode && styles.safeAreaDark]}>
      {/* Fixed top toolbar — outside ScrollView so it stays pinned */}
      <View style={styles.toolbarShell}>
        <WorkspaceToolbar
          currentDocumentName={currentDocumentName}
          hasResult={!!(selectedJob?.status === "completed" && result)}
          isWideLayout={isWideLayout}
          isDarkMode={isDarkMode}
          isPdfPickReady={isPdfPickReady}
          editing={editing}
          onDiscardEdit={handleDiscardEdit}
          onOpenInfo={handleOpenInfo}
          onPickPdf={() => void handlePickPdf()}
          onOpenPolicyBriefings={() => void handleOpenPolicyBriefings()}
          onSaveMarkdownFile={() => void handleSaveMarkdownFile()}
          onToggleDarkMode={handleToggleDarkMode}
        />
        {notice ? <Text style={[styles.noticeBox, isDarkMode && styles.noticeBoxDark]}>{notice}</Text> : null}
      </View>

      {isWideLayout ? (
        <View
          style={[
            styles.desktopContentShell,
            isDarkMode && styles.scrollContentDark,
          ]}
        >
          {showDetailPanel ? (
            <JobDetailPanel
              activeTab={activeTab}
              editorSelection={editorSelection}
              editorFocusToken={editorFocusToken}
            hasUnsavedChanges={hasUnsavedChanges}
            isDarkMode={isDarkMode}
            editing={editing}
            editorText={editorText}
            isTabletLayout={isTabletLayout}
            isCompactLayout={isCompactLayout}
            isWideLayout={isWideLayout}
            desktopSplitRatio={desktopSplitRatio}
            sectionHeadings={sectionHeadings}
            showBackButton={false}
            hideTopTabs={!isWideLayout}
            result={result}
            selectedJob={selectedJob}
            selectedResultText={previewMarkdown}
            onApplyEditorAction={applyEditorAction}
            onBack={() => {
                confirmDiscardChanges(() => {
                  setSelectedJobId(null);
                  setCurrentEditToken(null);
                  setSelectedJob(null);
                  setResult(null);
                  setActiveTab("preview");
                setEditing(false);
              });
            }}
            onChangeEditorText={handleEditorTextChange}
            onChangeSelection={setEditorSelection}
            onChangeTab={setActiveTab}
            onDiscardEdit={handleDiscardEdit}
            onDeleteJob={() => void handleDeleteJob()}
            onCopyMarkdown={() => void handleCopyMarkdown()}
            onJumpToSection={(index) => {
              setEditorSelection({ start: index, end: index });
              setActiveTab("markdown");
              setEditing(true);
              setEditorFocusToken((current) => current + 1);
            }}
            onRequestToggleEditing={() => {
              if (editing) {
                confirmDiscardChanges(() => {
                  setEditing(false);
                  setEditorText(result?.markdown || "");
                });
                return;
              }
              setEditing(true);
              setActiveTab("markdown");
              setEditorFocusToken((current) => current + 1);
            }}
            onRetry={() => void handleRetry()}
            onSaveEdit={() => void handleSaveEdit()}
            onShareMarkdown={() => void handleShareMarkdown()}
            onResizeDesktopSplit={setDesktopSplitRatio}
            onToggleEditing={() => setEditing((current) => !current)}
            onHandleDroppedAsset={(asset) => {
              void handleSelectedAsset(asset);
            }}
          />
          ) : null}
        </View>
      ) : (
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={[
            styles.scrollContent,
            isTabletLayout && styles.scrollContentTablet,
            isDarkMode && styles.scrollContentDark,
          ]}
        >
          {showDetailPanel ? (
              <JobDetailPanel
                activeTab={activeTab}
                editorSelection={editorSelection}
                editorFocusToken={editorFocusToken}
              hasUnsavedChanges={hasUnsavedChanges}
              isDarkMode={isDarkMode}
              editing={editing}
              editorText={editorText}
              isTabletLayout={isTabletLayout}
              isCompactLayout={isCompactLayout}
              isWideLayout={isWideLayout}
              desktopSplitRatio={desktopSplitRatio}
              sectionHeadings={sectionHeadings}
              showBackButton={false}
              hideTopTabs={!isWideLayout}
              result={result}
              selectedJob={selectedJob}
              selectedResultText={previewMarkdown}
              onApplyEditorAction={applyEditorAction}
              onBack={() => {
                  confirmDiscardChanges(() => {
                    setSelectedJobId(null);
                    setCurrentEditToken(null);
                    setSelectedJob(null);
                    setResult(null);
                    setActiveTab("preview");
                  setEditing(false);
                });
              }}
              onChangeEditorText={handleEditorTextChange}
              onChangeSelection={setEditorSelection}
              onChangeTab={setActiveTab}
              onDiscardEdit={handleDiscardEdit}
              onDeleteJob={() => void handleDeleteJob()}
              onCopyMarkdown={() => void handleCopyMarkdown()}
              onJumpToSection={(index) => {
                setEditorSelection({ start: index, end: index });
                setActiveTab("markdown");
                setEditing(true);
                setEditorFocusToken((current) => current + 1);
              }}
              onRequestToggleEditing={() => {
                if (editing) {
                  confirmDiscardChanges(() => {
                    setEditing(false);
                    setEditorText(result?.markdown || "");
                  });
                  return;
                }
                setEditing(true);
                setActiveTab("markdown");
                setEditorFocusToken((current) => current + 1);
              }}
              onRetry={() => void handleRetry()}
              onSaveEdit={() => void handleSaveEdit()}
              onShareMarkdown={() => void handleShareMarkdown()}
              onResizeDesktopSplit={setDesktopSplitRatio}
              onToggleEditing={() => setEditing((current) => !current)}
              onHandleDroppedAsset={(asset) => {
                void handleSelectedAsset(asset);
              }}
            />
          ) : null}
          {!isWideLayout && mobileShowList ? (
            <View style={[styles.mobileListPanel, isDarkMode && styles.mobileListPanelDark]}>
              <Text style={[styles.mobileListTitle, isDarkMode && styles.mobileListTitleDark]}>변환 기록</Text>
              {recentJobs.length === 0 ? (
                <Text style={[styles.mobileListHint, isDarkMode && styles.mobileListHintDark]}>
                  아직 변환한 문서가 없습니다.{"\n"}⬆ 변환 버튼으로 시작하세요.
                </Text>
              ) : (
                recentJobs.map((entry) => {
                  const isActive = entry.jobId === selectedJobId;
                  return (
                    <Pressable
                      key={entry.jobId}
                      style={[styles.recentJobRow, isDarkMode && styles.recentJobRowDark, isActive && styles.recentJobRowActive]}
                      onPress={() => {
                        if (isActive) {
                          setMobileShowList(false);
                          setActiveTab("preview");
                          return;
                        }
                        startTransition(() => {
                          setSelectedJobId(entry.jobId);
                          setCurrentEditToken(entry.editToken);
                          setSelectedJobBaseUrl(entry.baseUrl);
                          setResult(null);
                          setEditorText("");
                          setSelectedTableMode("text");
                          setEditing(false);
                          setActiveTab("preview");
                          setMobileShowList(false);
                        });
                        if (entry.editToken) {
                          void refreshSelectedJob(entry.jobId, entry.editToken, false, false, entry.baseUrl);
                        }
                      }}
                    >
                      <View style={styles.recentJobIndicator}>
                        <View style={[styles.recentJobDot, isActive && styles.recentJobDotActive]} />
                      </View>
                      <View style={styles.recentJobInfo}>
                        <Text style={[styles.recentJobName, isDarkMode && styles.recentJobNameDark]} numberOfLines={1}>
                          {entry.fileName}
                        </Text>
                        <Text style={[styles.recentJobTime, isDarkMode && styles.recentJobTimeDark]}>
                          {formatRelativeTime(entry.loadedAt)}
                        </Text>
                      </View>
                    </Pressable>
                  );
                })
              )}
            </View>
          ) : null}
        </ScrollView>
      )}


      {/* ── Mobile bottom tab bar ── */}
      {!isWideLayout ? (() => {
        const mobileActiveTab = (!selectedJob || mobileShowList) ? "list" : activeTab === "markdown" ? "markdown" : "preview";
        const tabs = [
          { key: "list",     icon: "⊞", label: "목록" },
          { key: "markdown", icon: "≡", label: "편집" },
          { key: "preview",  icon: "◎", label: "미리보기" },
        ] as const;
        return (
          <View style={[styles.bottomTabBar, isDarkMode && styles.bottomTabBarDark]}>
            {tabs.map((tab) => {
              const active = tab.key === mobileActiveTab;
              return (
                <Pressable
                  key={tab.key}
                  style={[styles.bottomTab, active && styles.bottomTabActive]}
                  onPress={() => {
                    if (tab.key === "list") {
                      setMobileShowList(true);
                    } else if (tab.key === "markdown") {
                      setMobileShowList(false);
                      if (!editing) {
                        setEditing(true);
                        setEditorFocusToken((t) => t + 1);
                      }
                      setActiveTab("markdown");
                    } else {
                      setMobileShowList(false);
                      setActiveTab("preview");
                    }
                  }}
                >
                  <Text style={[styles.bottomTabIcon, isDarkMode && styles.bottomTabIconDark, active && styles.bottomTabIconActive]}>{tab.icon}</Text>
                  <Text style={[styles.bottomTabLabel, isDarkMode && styles.bottomTabLabelDark, active && styles.bottomTabLabelActive]}>{tab.label}</Text>
                </Pressable>
              );
            })}
          </View>
        );
      })() : null}

      <Modal visible={infoVisible} animationType="fade" transparent onRequestClose={() => setInfoVisible(false)}>
        <View style={styles.modalBackdrop}>
          <View style={styles.infoModalCard}>
            <Text style={styles.infoEyebrow}>Government Document Converter</Text>
            <Text style={styles.modalTitle}>읽힘</Text>
            <Text style={styles.modalHint}>
              정부문서가 막힌 곳에서, 사람과 AI 모두 통하게 한다.
            </Text>
            <View style={styles.infoMetaList}>
              <View style={styles.infoMetaRow}>
                <Text style={styles.infoMetaLabel}>GitHub</Text>
                <Pressable onPress={handleOpenGithub}>
                  <Text style={styles.infoMetaLink}>wavelen-jw/GovPress_PDF_MD</Text>
                </Pressable>
              </View>
            </View>
            <Text style={styles.modalHint}>
              변환 결과는 초안입니다. 공개 전에는 제목, 표, 목록, 숫자, 링크를 한 번 더 확인하는 것이 좋습니다.
            </Text>
            <Text style={styles.infoQuote}>
              이 도구는 개발자가 아닌 공무원이 AI를 활용하여 업무에 도움이 되는 도구를 만드는 '행정안전부 AI 챔피언' 교육과정을 통해 만들어졌습니다.
            </Text>
            <View style={styles.modalActions}>
              <Pressable onPress={() => void handleOpenSettings()} style={styles.secondaryButton}>
                <Text style={styles.secondaryButtonLabel}>서버 설정</Text>
              </Pressable>
              <Pressable onPress={() => setInfoVisible(false)} style={styles.primaryButton}>
                <Text style={styles.primaryButtonLabel}>닫기</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>

      <SettingsModal
        visible={settingsVisible}
        draft={configDraft}
        onChange={setConfigDraft}
        onClose={() => setSettingsVisible(false)}
        onSave={() => void handleSaveSettings()}
      />

      <Modal visible={policyBriefingVisible} animationType="slide" transparent onRequestClose={() => setPolicyBriefingVisible(false)}>
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <View style={styles.policyBriefingHeader}>
              <Text style={styles.modalTitle}>정책브리핑 보도자료</Text>
              <Pressable
                onPress={() => setPolicyBriefingStatusVisible(true)}
                style={styles.policyBriefingStatusInlineRow}
              >
                <Text style={styles.policyBriefingMetaText}>{policyBriefings.length}건 · 최근 5일</Text>
                <Text style={styles.policyBriefingMetaText}>|</Text>
                <Text style={styles.policyBriefingMetaText}>문체부 API</Text>
                <View
                  style={[
                    styles.policyBriefingStatusDot,
                    policyBriefingLoading
                      ? styles.policyBriefingStatusDotChecking
                      : policyBriefingError || policyBriefingAnyFetchFailure || policyBriefingServedStale || policyBriefingWarning
                        ? styles.policyBriefingStatusDotDegraded
                        : styles.policyBriefingStatusDotHealthy,
                  ]}
                />
              </Pressable>
            </View>
            {/* Search bar */}
            <View style={styles.policyBriefingSearchRow}>
              <TextInput
                style={styles.policyBriefingSearchInput}
                placeholder="제목 또는 보도기관 검색…"
                placeholderTextColor="rgba(255,255,255,0.28)"
                value={policyBriefingQuery}
                onChangeText={setPolicyBriefingQuery}
                autoCorrect={false}
                autoCapitalize="none"
                clearButtonMode="while-editing"
              />
            </View>
            <ScrollView style={styles.policyBriefingList} contentContainerStyle={styles.policyBriefingListContent}>
              {policyBriefingLoading ? (
                <View style={styles.policyBriefingEmptyState}>
                  <ActivityIndicator size="small" color="#7b664f" />
                  <Text style={styles.emptyState}>목록을 불러오는 중입니다.</Text>
                </View>
              ) : null}
              {!policyBriefingLoading && groupedPolicyBriefings.length === 0 ? (
                <View style={styles.policyBriefingEmptyState}>
                  <Text style={styles.emptyState}>
                    {policyBriefingQuery
                      ? "검색 결과가 없습니다."
                      : policyBriefingError || "HWPX 보도자료가 없거나 불러오기에 실패했습니다."}
                  </Text>
                </View>
              ) : null}
              {!policyBriefingLoading
                ? groupedPolicyBriefings.map(([dateKey, items]) => (
                    <View key={dateKey}>
                      <View style={styles.policyBriefingDateSep}>
                        <View style={styles.policyBriefingDateLine} />
                        <Text style={styles.policyBriefingDateLabel}>{formatKoreanDate(dateKey)}</Text>
                        <View style={styles.policyBriefingDateLine} />
                      </View>
                      {items.map((item) => {
                        const active = importingNewsItemId === item.news_item_id;
                        const approvedTime = formatPolicyBriefingTime(item.approve_date);
                        return (
                          <Pressable
                            key={item.news_item_id}
                            style={styles.policyBriefingRow}
                            onPress={() => void handleImportPolicyBriefing(item)}
                            disabled={!!importingNewsItemId}
                          >
                            <View style={styles.policyBriefingRowBody}>
                              <Text style={styles.policyBriefingTitle}>{item.title}</Text>
                              <Text style={styles.policyBriefingMetaText}>
                                {item.department}
                                {approvedTime ? ` · ${approvedTime}` : ""}
                                {" · "}
                                {item.file_name}
                              </Text>
                              {item.has_appendix_hwpx ? (
                                <Text style={styles.policyBriefingAppendix}>별첨 HWPX 포함</Text>
                              ) : null}
                            </View>
                            <View style={styles.policyBriefingRowAction}>
                              {active ? <ActivityIndicator size="small" color="#7b664f" /> : <Text style={styles.loadMoreLabel}>불러오기</Text>}
                            </View>
                          </Pressable>
                        );
                      })}
                    </View>
                  ))
                : null}
            </ScrollView>
            <View style={styles.modalActions}>
              <Pressable onPress={() => setPolicyBriefingVisible(false)} style={styles.secondaryButton}>
                <Text style={styles.secondaryButtonLabel}>닫기</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>

      <Modal
        visible={policyBriefingStatusVisible}
        animationType="fade"
        transparent
        onRequestClose={() => setPolicyBriefingStatusVisible(false)}
      >
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>정책브리핑 API 상태</Text>
            <Text style={styles.modalHint}>
              서버 연결 상태와 정책브리핑 제공기관 조회 상태를 구분해서 보여줍니다.
            </Text>
            <View style={styles.resultMetaCard}>
              <Text style={styles.resultMetaEyebrow}>정책브리핑 현재 상태</Text>
              <Text style={styles.resultMetaBody}>{policyBriefingStatusSummary}</Text>
            </View>
            <View style={styles.resultMetaCard}>
              <Text style={styles.resultMetaEyebrow}>최근 5일 조회</Text>
              <Text style={styles.resultMetaBody}>
                {policyBriefingAnyFetchFailure ? "일부 날짜 요청 실패" : "실패 없음"}
              </Text>
              <Text style={styles.resultMetaBody}>
                {policyBriefingServedStale ? "캐시 제공됨" : "실시간 응답"}
              </Text>
              <Text style={styles.resultMetaBody}>
                {policyBriefingLastRefreshedAt
                  ? `마지막 갱신: ${policyBriefingLastRefreshedAt}`
                  : "마지막 갱신 시각 없음"}
              </Text>
            </View>
            {policyBriefingServerHealthStatuses.length > 0 ? (
              <View style={styles.resultMetaCard}>
                <Text style={styles.resultMetaEyebrow}>서버 연결 상태 (/health)</Text>
                <Text style={styles.resultMetaBody}>
                  이 표시는 각 서버의 기본 API 연결 상태만 나타냅니다.
                </Text>
                {policyBriefingServerHealthStatuses.map((status) => (
                  <View key={status.key} style={styles.resultMetaRow}>
                    <Text style={styles.resultMetaEyebrow}>
                      {status.label} · {status.ok ? "정상" : "실패"}
                    </Text>
                    <Text style={styles.resultMetaBody}>{status.ok ? `서버 응답 정상 · ${status.detail}` : status.detail}</Text>
                  </View>
                ))}
              </View>
            ) : null}
            {policyBriefingServerStatuses.length > 0 ? (
              <View style={styles.resultMetaCard}>
                <Text style={styles.resultMetaEyebrow}>서버별 정책브리핑 조회 상태</Text>
                {policyBriefingServerStatuses.map((status) => {
                  const statusLabel = status.error
                    ? "실패"
                    : status.anyFetchFailure
                      ? "부분 실패"
                      : status.servedStale || status.warning
                        ? "주의"
                        : "정상";
                  return (
                    <View key={status.key} style={styles.resultMetaRow}>
                      <Text style={styles.resultMetaEyebrow}>
                        {status.label} · {statusLabel}
                      </Text>
                      <Text style={styles.resultMetaBody}>
                        {status.error
                          ? status.error
                          : status.anyFetchFailure
                            ? "최근 5일 조회 중 일부 날짜 요청 실패"
                            : status.servedStale
                              ? "캐시 제공됨"
                              : status.warning || "정상"}
                      </Text>
                      <Text style={styles.resultMetaBody}>
                        {status.lastRefreshedAt
                          ? `마지막 갱신: ${status.lastRefreshedAt}`
                          : "마지막 갱신 시각 없음"}
                      </Text>
                    </View>
                  );
                })}
              </View>
            ) : null}
            {policyBriefingWarning ? (
              <View style={styles.resultMetaCard}>
                <Text style={styles.resultMetaEyebrow}>경고</Text>
                <Text style={styles.resultMetaBody}>{policyBriefingWarning}</Text>
              </View>
            ) : null}
            {policyBriefingError ? (
              <View style={styles.resultMetaCard}>
                <Text style={styles.resultMetaEyebrow}>오류</Text>
                <Text style={styles.resultMetaBody}>{policyBriefingError}</Text>
              </View>
            ) : null}
            <View style={styles.modalActions}>
              <Pressable onPress={() => setPolicyBriefingStatusVisible(false)} style={styles.primaryButton}>
                <Text style={styles.primaryButtonLabel}>닫기</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>

      {busy ? (
        <View style={styles.busyOverlay}>
          <ActivityIndicator size="large" color="#fff7ee" />
        </View>
      ) : null}

      {Platform.OS === "web" && dragOverlayVisible ? (
        <View pointerEvents="none" style={styles.dragOverlay}>
          <View style={styles.dragOverlayCard}>
            <Text style={styles.dragOverlayEyebrow}>DROP TO CONVERT</Text>
            <Text style={styles.dragOverlayTitle}>PDF, HWPX, Markdown 파일을 놓으세요</Text>
            <Text style={styles.dragOverlayBody}>드래그앤드롭으로 바로 업로드하고 결과를 편집기와 미리보기에서 확인할 수 있습니다.</Text>
          </View>
        </View>
      ) : null}
    </SafeAreaView>
  );
}
