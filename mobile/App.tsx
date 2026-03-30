import React, { startTransition, useDeferredValue, useEffect, useMemo, useState } from "react";
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
import { TurnstileGate } from "./src/components/TurnstileGate";
import { WorkspaceToolbar } from "./src/components/WorkspaceToolbar";
import { DEFAULT_CONFIG } from "./src/constants";
import { fetchJob, fetchResult, retryJob, saveResult, uploadPdf } from "./src/services/api";
import { clearDraft, loadConfig, loadDraft, persistDraft } from "./src/storage/config";
import { styles } from "./src/styles";
import type { AppConfig, Job, ResultPayload } from "./src/types";

type WebUploadAsset = DocumentPicker.DocumentPickerAsset & { file?: File };

type EditorSelection = {
  start: number;
  end: number;
};

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
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [result, setResult] = useState<ResultPayload | null>(null);
  const [editorText, setEditorText] = useState("");
  const deferredEditorText = useDeferredValue(editorText);
  const [activeTab, setActiveTab] = useState<"preview" | "markdown" | "diff">("preview");
  const [editorSelection, setEditorSelection] = useState<EditorSelection>({ start: 0, end: 0 });
  const [editorFocusToken, setEditorFocusToken] = useState(0);
  const [loadingConfig, setLoadingConfig] = useState(true);
  const [busy, setBusy] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [editing, setEditing] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [infoVisible, setInfoVisible] = useState(false);
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
  const [turnstileRefreshNonce, setTurnstileRefreshNonce] = useState(0);
  const [turnstileExecuteNonce, setTurnstileExecuteNonce] = useState(0);
  const [pendingPdfPick, setPendingPdfPick] = useState(false);
  const [pendingDroppedAsset, setPendingDroppedAsset] = useState<WebUploadAsset | null>(null);
  const [draftHydratedJobId, setDraftHydratedJobId] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const selectedResultText = useMemo(() => {
    if (!result) {
      return "";
    }
    return editing ? deferredEditorText : result.markdown || "";
  }, [deferredEditorText, editing, result]);
  const hasUnsavedChanges = editing && editorText !== (result?.markdown || "");
  const sectionHeadings = useMemo(() => extractSectionHeadings(editorText), [editorText]);
  function showError(title: string, error: unknown): void {
    const message = error instanceof Error ? error.message : String(error);
    setNotice(`${title}: ${message}`);
    if (Platform.OS !== "web") {
      Alert.alert(title, message);
    }
  }

  useEffect(() => {
    loadConfig()
      .then((loaded) => {
        setConfig(loaded);
      })
      .finally(() => setLoadingConfig(false));
  }, []);

  useEffect(() => {
    if (!loadingConfig && selectedJobId && currentEditToken && !selectedJobId.startsWith("local-md-")) {
      void refreshSelectedJob(selectedJobId, currentEditToken);
    }
  }, [loadingConfig, config.baseUrl, config.apiKey]);

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
    if (selectedJobId && currentEditToken && !selectedJobId.startsWith("local-md-")) {
      void refreshSelectedJob(selectedJobId, currentEditToken);
    }
  }, [selectedJobId, currentEditToken]);

  useEffect(() => {
    if (!selectedJobId || !currentEditToken || selectedJobId.startsWith("local-md-") || !selectedJob) {
      return;
    }
    if (selectedJob.status !== "queued" && selectedJob.status !== "processing") {
      return;
    }
    const handle = setInterval(() => {
      void refreshSelectedJob(selectedJobId, currentEditToken, false);
    }, 2500);
    return () => clearInterval(handle);
  }, [selectedJobId, currentEditToken, selectedJob?.status]);

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
    if (!notice) {
      return;
    }
    if (notice === "PDF 업로드 중...") {
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
        if (draft && draft !== result.markdown) {
          setEditorText(draft);
          setEditing(true);
          setNotice("임시 저장된 편집본을 복원했습니다.");
        }
      })
      .finally(() => setDraftHydratedJobId(selectedJobId));
  }, [draftHydratedJobId, result, selectedJobId]);

  async function refreshSelectedJob(jobId: string, editToken: string, syncResult = true): Promise<void> {
    try {
      const payload = await fetchJob(config, jobId, editToken);
      setNotice(null);
      const shouldLoadResult =
        payload.status === "completed" &&
        (syncResult || result?.job_id !== payload.job_id || selectedJob?.status !== "completed");
      startTransition(() => {
        setSelectedJob(payload);
      });
      if (shouldLoadResult) {
        const resultPayload = await fetchResult(config, jobId, editToken);
        startTransition(() => {
          setResult(resultPayload);
          setEditorText(resultPayload.markdown || "");
          setEditorSelection({ start: 0, end: 0 });
          setEditorFocusToken((current) => current + 1);
        });
      }
    } catch (error) {
      showError("작업 상태를 불러오지 못했습니다.", error);
    }
  }

  async function openLocalMarkdown(asset: DocumentPicker.DocumentPickerAsset): Promise<void> {
    const webFile = (asset as DocumentPicker.DocumentPickerAsset & { file?: File }).file;
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
      setEditorText(markdown);
      setEditorSelection({ start: 0, end: 0 });
      setEditing(false);
      setActiveTab("preview");
    });
    setNotice("Markdown 문서를 열었습니다.");
  }

  async function handleSelectedAsset(asset: WebUploadAsset): Promise<void> {
    try {
      const lowerName = asset.name.toLowerCase();
      if (lowerName.endsWith(".md")) {
        await openLocalMarkdown(asset);
        return;
      }
      if (!lowerName.endsWith(".pdf")) {
        setNotice("PDF 또는 Markdown 파일만 열 수 있습니다.");
        return;
      }
      setBusy(true);
      setNotice("PDF 업로드 중...");
      const job = await uploadPdf(config, asset, turnstileToken);
      setTurnstileToken(null);
      setPendingPdfPick(false);
      setTurnstileRefreshNonce((current) => current + 1);
      startTransition(() => {
        setSelectedJobId(job.job_id);
        setCurrentEditToken(job.edit_token);
        setSelectedJob(job);
        setResult(null);
        setEditorText("");
        setEditorSelection({ start: 0, end: 0 });
        setEditorFocusToken((current) => current + 1);
        setEditing(false);
      });
      await refreshSelectedJob(job.job_id, job.edit_token, false);
    } catch (error) {
      setPendingPdfPick(false);
      showError("PDF 업로드에 실패했습니다.", error);
    } finally {
      setBusy(false);
    }
  }

  async function handlePickPdf(): Promise<void> {
    if (Platform.OS === "web" && config.turnstileSiteKey && !turnstileToken) {
      setPendingPdfPick(true);
      setTurnstileExecuteNonce((current) => current + 1);
      return;
    }
    const picked = await DocumentPicker.getDocumentAsync({
      type: Platform.OS === "web" ? [".pdf", ".md"] : ["application/pdf", "text/markdown"],
      copyToCacheDirectory: true,
    });
    if (picked.canceled || !picked.assets.length) {
      return;
    }
    await handleSelectedAsset(picked.assets[0]);
  }

  function handleDropFile(file: File): void {
    const droppedAsset: WebUploadAsset = {
      name: file.name,
      uri: URL.createObjectURL(file),
      size: file.size,
      mimeType: file.type || undefined,
      lastModified: file.lastModified,
      file,
    };
    if (config.turnstileSiteKey && !turnstileToken) {
      setPendingDroppedAsset(droppedAsset);
      setTurnstileExecuteNonce((current) => current + 1);
      return;
    }
    void handleSelectedAsset(droppedAsset);
  }

  useEffect(() => {
    if (!pendingPdfPick || !turnstileToken) {
      return;
    }
    setPendingPdfPick(false);
    void handlePickPdf();
  }, [pendingPdfPick, turnstileToken]);

  useEffect(() => {
    if (!pendingDroppedAsset || !turnstileToken) {
      return;
    }
    const nextAsset = pendingDroppedAsset;
    setPendingDroppedAsset(null);
    void handleSelectedAsset(nextAsset);
  }, [pendingDroppedAsset, turnstileToken]);

  async function handleRetry(): Promise<void> {
    if (!selectedJobId || !currentEditToken) {
      return;
    }
    try {
      setBusy(true);
      const retried = await retryJob(config, selectedJobId, currentEditToken);
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

  async function handleSaveEdit(): Promise<void> {
    if (!selectedJobId) {
      return;
    }
    if (selectedJobId.startsWith("local-md-")) {
      const nextMarkdown = editorText;
      setResult((current) => (current ? { ...current, markdown: nextMarkdown } : current));
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
      await saveResult(config, selectedJobId, editorText, currentEditToken);
      await clearDraft(selectedJobId);
      const updated = await fetchResult(config, selectedJobId, currentEditToken);
      setNotice("수정본을 저장했습니다.");
      startTransition(() => {
        setResult(updated);
        setEditorText(updated.markdown || "");
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

  function handleDiscardEdit(): void {
    setEditorText(result?.markdown || "");
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
    if (!result?.markdown || !selectedJob) {
      return;
    }
    try {
      const shareBody = `# ${result.meta.title || selectedJob.file_name}\n\n${result.markdown}`;
      if (Platform.OS === "web" && navigator.share) {
        await navigator.share({
          title: result.meta.title || selectedJob.file_name,
          text: shareBody,
        });
        return;
      }
      if (Platform.OS !== "web") {
        await Share.share({
          title: result.meta.title || selectedJob.file_name,
          message: shareBody,
        });
        return;
      }
      const outputName = selectedJob.file_name.replace(/\.pdf$/i, ".md");
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
    if ((!editorText && !result?.markdown) || !selectedJob) {
      setNotice("저장할 Markdown이 없습니다.");
      return;
    }
    const content = editorText || result?.markdown || "";
    const outputName = selectedJob.file_name.replace(/\.pdf$/i, ".md");

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
    if (!result?.markdown || !selectedJob) {
      return;
    }
    const shareBody = `# ${result.meta.title || selectedJob.file_name}\n\n${result.markdown}`;
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

  function handleToggleDarkMode(): void {
    setIsDarkMode((current) => !current);
  }

  const showDetailPanel = true;
  const currentDocumentName = selectedJob?.file_name || result?.meta.source_file_name || null;
  const isPdfPickReady = true;
  const isPdfVerificationPending = !!config.turnstileSiteKey && !turnstileToken;

  if (loadingConfig) {
    return (
      <SafeAreaView style={styles.loadingShell}>
        <ActivityIndicator size="large" color="#b75e1f" />
        <Text style={styles.loadingLabel}>GovPress Mobile 준비 중</Text>
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
            isCompactLayout={isCompactLayout}
            isDarkMode={isDarkMode}
            isPdfPickReady={isPdfPickReady}
            isPdfVerificationPending={isPdfVerificationPending}
            editing={editing}
            activeTab={activeTab}
            onChangeTab={setActiveTab}
            onCopyMarkdown={() => void handleCopyMarkdown()}
            onDiscardEdit={handleDiscardEdit}
            onOpenInfo={handleOpenInfo}
            onPickPdf={() => void handlePickPdf()}
            onSaveEdit={() => void handleSaveEdit()}
            onSaveMarkdownFile={() => void handleSaveMarkdownFile()}
            onShareMarkdown={() => void handleShareMarkdown()}
            onToggleDarkMode={handleToggleDarkMode}
          />
          {notice ? <Text style={[styles.noticeBox, isDarkMode && styles.noticeBoxDark]}>{notice}</Text> : null}
          {config.turnstileSiteKey ? (
            <TurnstileGate
              isDarkMode={isDarkMode}
              siteKey={config.turnstileSiteKey || ""}
              refreshNonce={turnstileRefreshNonce}
              executeNonce={turnstileExecuteNonce}
              onTokenChange={setTurnstileToken}
            />
          ) : null}
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
            sectionHeadings={sectionHeadings}
            showBackButton={isCompactLayout}
            result={result}
            selectedJob={selectedJob}
            selectedResultText={selectedResultText}
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
            onChangeEditorText={setEditorText}
            onChangeSelection={setEditorSelection}
            onChangeTab={setActiveTab}
            onDropFile={handleDropFile}
            onDiscardEdit={handleDiscardEdit}
            onDeleteJob={() => void handleDeleteJob()}
            onCopyMarkdown={() => void handleCopyMarkdown()}
            onJumpToSection={(index) => {
              setEditorSelection({ start: index, end: index });
              setActiveTab("markdown");
              setEditing(true);
              setEditorFocusToken((current) => current + 1);
            }}
            onPickPdf={() => void handlePickPdf()}
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
            onToggleEditing={() => setEditing((current) => !current)}
          />
        ) : null}
      </ScrollView>

      <Modal visible={infoVisible} animationType="fade" transparent onRequestClose={() => setInfoVisible(false)}>
        <View style={styles.modalBackdrop}>
          <View style={styles.infoModalCard}>
            <Text style={styles.modalTitle}>정부 보도자료 Markdown 편집기</Text>
            <Text style={styles.modalHint}>
              PDF로 배포되는 정부 보도자료를 Markdown으로 바꾸고, 바로 수정하고, 저장할 수 있도록 만든 웹 도구입니다.
            </Text>
            <View style={styles.infoMetaList}>
              <View style={styles.infoMetaRow}>
                <Text style={styles.infoMetaLabel}>대상 문서</Text>
                <Text style={styles.infoMetaValue}>정부 보도자료 PDF, Markdown</Text>
              </View>
              <View style={styles.infoMetaRow}>
                <Text style={styles.infoMetaLabel}>주요 기능</Text>
                <Text style={styles.infoMetaValue}>PDF 변환, Markdown 편집, 미리보기, 저장</Text>
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
              <Pressable onPress={() => setInfoVisible(false)} style={styles.primaryButton}>
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
    </SafeAreaView>
  );
}
