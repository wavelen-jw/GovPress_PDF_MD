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
  useWindowDimensions,
  View,
} from "react-native";
import * as DocumentPicker from "expo-document-picker";
import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";

import { JobDetailPanel } from "./src/components/JobDetailPanel";
import { SettingsModal } from "./src/components/SettingsModal";
import { WorkspaceToolbar } from "./src/components/WorkspaceToolbar";
import { DEFAULT_CONFIG, getServerLabel } from "./src/constants";
import {
  ApiError,
  fetchJob,
  fetchResult,
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

type WebDropAsset = DocumentPicker.DocumentPickerAsset & { file?: File };

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
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [infoVisible, setInfoVisible] = useState(false);
  const [policyBriefingVisible, setPolicyBriefingVisible] = useState(false);
  const [hwpxTableMode, setHwpxTableMode] = useState<HwpxTableMode>("text");
  const [selectedTableMode, setSelectedTableMode] = useState<HwpxTableMode>("text");
  const [loadedTableMode, setLoadedTableMode] = useState<HwpxTableMode>("text");
  const [draftHydratedJobId, setDraftHydratedJobId] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [policyBriefings, setPolicyBriefings] = useState<PolicyBriefingItem[]>([]);
  const [policyBriefingLoading, setPolicyBriefingLoading] = useState(false);
  const [importingNewsItemId, setImportingNewsItemId] = useState<string | null>(null);
  const [desktopSplitRatio, setDesktopSplitRatio] = useState(0.5);
  const [dragOverlayVisible, setDragOverlayVisible] = useState(false);
  const jobRefreshSeqRef = useRef(0);
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

    function hasSupportedFiles(event: DragEvent): boolean {
      const files = Array.from(event.dataTransfer?.files || []);
      return files.some((file) => isSupportedFile(file));
    }

    const handleDragEnter = (event: DragEvent) => {
      if (!hasSupportedFiles(event)) {
        return;
      }
      event.preventDefault();
      dragDepth += 1;
      setDragOverlayVisible(true);
    };

    const handleDragOver = (event: DragEvent) => {
      if (!hasSupportedFiles(event)) {
        return;
      }
      event.preventDefault();
      if (event.dataTransfer) {
        event.dataTransfer.dropEffect = "copy";
      }
    };

    const handleDragLeave = (event: DragEvent) => {
      if (!hasSupportedFiles(event)) {
        return;
      }
      event.preventDefault();
      dragDepth = Math.max(0, dragDepth - 1);
      if (dragDepth === 0) {
        setDragOverlayVisible(false);
      }
    };

    const handleDrop = (event: DragEvent) => {
      if (!hasSupportedFiles(event)) {
        return;
      }
      event.preventDefault();
      dragDepth = 0;
      setDragOverlayVisible(false);
      const file = Array.from(event.dataTransfer?.files || []).find((candidate) => isSupportedFile(candidate));
      if (!file) {
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

    window.addEventListener("dragenter", handleDragEnter);
    window.addEventListener("dragover", handleDragOver);
    window.addEventListener("dragleave", handleDragLeave);
    window.addEventListener("drop", handleDrop);
    return () => {
      window.removeEventListener("dragenter", handleDragEnter);
      window.removeEventListener("dragover", handleDragOver);
      window.removeEventListener("dragleave", handleDragLeave);
      window.removeEventListener("drop", handleDrop);
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
    });
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
      });
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
    try {
      const payload = await fetchTodayPolicyBriefings(config);
      setPolicyBriefings(payload.items);
      setNotice(`정책브리핑 목록을 갱신했습니다. 누적 HWPX 기사 ${payload.items.length}건을 불러왔습니다.`);
    } catch (error) {
      showError("오늘자 정책브리핑을 불러오지 못했습니다.", error);
    } finally {
      setPolicyBriefingLoading(false);
    }
  }

  async function handleImportPolicyBriefing(item: PolicyBriefingItem): Promise<void> {
    setImportingNewsItemId(item.news_item_id);
    setBusy(true);
    setNotice("정책브리핑 HWPX를 가져오는 중...");
    try {
      const imported = await importPolicyBriefing(config, item.news_item_id);
      startTransition(() => {
        setPolicyBriefingVisible(false);
        setSelectedJobId(imported.job_id);
        setCurrentEditToken(imported.edit_token);
        setSelectedJob(imported);
        setResult(null);
        setLoadedTableMode("text");
        setSelectedTableMode("text");
        setEditorText("");
        setEditorSelection({ start: 0, end: 0 });
        setEditorFocusToken((current) => current + 1);
        setEditing(false);
        setActiveTab("preview");
      });
      await refreshSelectedJob(imported.job_id, imported.edit_token, false);
    } catch (error) {
      showError("정책브리핑 보도자료를 가져오지 못했습니다.", error);
    } finally {
      setImportingNewsItemId(null);
      setBusy(false);
    }
  }

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

  const showDetailPanel = true;
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
      <View style={styles.backgroundOrbA} />
      <View style={styles.backgroundOrbB} />
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={[
          styles.scrollContent,
          isTabletLayout && styles.scrollContentTablet,
          isWideLayout && styles.scrollContentDesktop,
        ]}
      >
        <View style={styles.toolbarShell}>
          <WorkspaceToolbar
            currentDocumentName={currentDocumentName}
            hasResult={!!(selectedJob?.status === "completed" && result)}
            hasUnsavedChanges={hasUnsavedChanges}
            isWideLayout={isWideLayout}
            isTabletLayout={isTabletLayout}
            isDarkMode={isDarkMode}
            isPdfPickReady={isPdfPickReady}
            selectedTableMode={selectedTableMode}
            htmlVariantState={htmlVariantState}
            editing={editing}
            onCopyMarkdown={() => void handleCopyMarkdown()}
            onDiscardEdit={handleDiscardEdit}
            onOpenInfo={handleOpenInfo}
            onPickPdf={() => void handlePickPdf()}
            onOpenPolicyBriefings={() => void handleOpenPolicyBriefings()}
            onChangeSelectedTableMode={(mode) => void handleChangeSelectedTableMode(mode)}
            onSaveEdit={() => void handleSaveEdit()}
            onSaveMarkdownFile={() => void handleSaveMarkdownFile()}
            onShareMarkdown={() => void handleShareMarkdown()}
            onToggleDarkMode={handleToggleDarkMode}
          />
          {notice ? <Text style={[styles.noticeBox, isDarkMode && styles.noticeBoxDark]}>{notice}</Text> : null}
        </View>

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
            showBackButton={isCompactLayout}
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
          />
        ) : null}
      </ScrollView>

      <Modal visible={infoVisible} animationType="fade" transparent onRequestClose={() => setInfoVisible(false)}>
        <View style={styles.modalBackdrop}>
          <View style={styles.infoModalCard}>
            <Text style={styles.modalTitle}>정부 보고서 Markdown 편집기</Text>
            <Text style={styles.modalHint}>
              HWPX, PDF로 만들어진 정부 보고서를 Markdown으로 바꾸고, 바로 수정하고, 저장할 수 있도록 만든 웹 도구입니다.
            </Text>
            <View style={styles.infoMetaList}>
              <View style={styles.infoMetaRow}>
                <Text style={styles.infoMetaLabel}>대상 문서</Text>
                <Text style={styles.infoMetaValue}>정부 보고서 HWPX, PDF, Markdown</Text>
              </View>
              <View style={styles.infoMetaRow}>
                <Text style={styles.infoMetaLabel}>주요 기능</Text>
                <Text style={styles.infoMetaValue}>HWPX, PDF → Markdown 변환, 편집, 저장</Text>
              </View>
              <View style={styles.infoMetaRow}>
                <Text style={styles.infoMetaLabel}>GitHub 저장소</Text>
                <Pressable onPress={handleOpenGithub}>
                  <Text style={styles.infoMetaLink}>wavelen-jw/GovPress_PDF_MD</Text>
                </Pressable>
              </View>
            </View>
            <View style={styles.infoCapabilityList}>
              <View style={styles.infoCapabilityRow}>
                <Text style={[styles.infoCapabilityBadge, styles.infoCapabilityGood]}>잘함</Text>
                <Text style={styles.infoCapabilityText}>보도자료 PDF를 Markdown 초안으로 변환하고 바로 수정하기</Text>
              </View>
              <View style={styles.infoCapabilityRow}>
                <Text style={[styles.infoCapabilityBadge, styles.infoCapabilityLearning]}>학습중</Text>
                <Text style={styles.infoCapabilityText}>문서 구조를 더 정확하게 이해하고 표기 방식을 자연스럽게 정리하기</Text>
              </View>
              <View style={styles.infoCapabilityRow}>
                <Text style={[styles.infoCapabilityBadge, styles.infoCapabilityBad]}>못함</Text>
                <Text style={styles.infoCapabilityText}>모든 문서를 완벽하게 자동 변환하거나 복잡한 보고서 서식을 그대로 재현하기</Text>
              </View>
            </View>
            <Text style={styles.modalHint}>
              변환 결과는 초안입니다. 공개 전에는 문장, 표, 목록, 링크를 한 번 더 확인하는 것을 권장합니다.
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
            <Text style={styles.modalTitle}>오늘자 정책브리핑 보도자료</Text>
            <Text style={styles.modalHint}>
              정책브리핑 보도자료 API에서 오늘 등록된 HWPX 첨부 기사를 불러옵니다. 선택하면 서버가 원문을 내려받아 기존 변환 파이프라인으로 처리합니다.
            </Text>
            <View style={styles.policyBriefingMetaRow}>
              <Text style={styles.policyBriefingMetaText}>대상: 오늘 게시된 HWPX 포함 기사</Text>
              <Text style={styles.policyBriefingMetaText}>{policyBriefings.length}건</Text>
            </View>
            <ScrollView style={styles.policyBriefingList} contentContainerStyle={styles.policyBriefingListContent}>
              {policyBriefingLoading ? (
                <View style={styles.policyBriefingEmptyState}>
                  <ActivityIndicator size="small" color="#7b664f" />
                  <Text style={styles.emptyState}>목록을 불러오는 중입니다.</Text>
                </View>
              ) : null}
              {!policyBriefingLoading && !policyBriefings.length ? (
                <View style={styles.policyBriefingEmptyState}>
                  <Text style={styles.emptyState}>오늘자 HWPX 보도자료가 없거나 불러오기에 실패했습니다.</Text>
                </View>
              ) : null}
              {!policyBriefingLoading
                ? policyBriefings.map((item) => {
                    const active = importingNewsItemId === item.news_item_id;
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
                            {item.department} · {item.file_name}
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
                  })
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
