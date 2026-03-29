import React, { startTransition, useDeferredValue, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Share,
  Platform,
  Pressable,
  RefreshControl,
  SafeAreaView,
  ScrollView,
  Text,
  useWindowDimensions,
  View,
} from "react-native";
import * as DocumentPicker from "expo-document-picker";
import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";

import { SettingsModal } from "./src/components/SettingsModal";
import { JobDetailPanel } from "./src/components/JobDetailPanel";
import { JobListPanel } from "./src/components/JobListPanel";
import { WorkspaceToolbar } from "./src/components/WorkspaceToolbar";
import { BUILD_TAG, currentWebBaseUrl, DEFAULT_CONFIG, normalizeBaseUrl } from "./src/constants";
import { deleteJob, fetchJob, fetchJobs, fetchResult, retryJob, saveResult, uploadPdf } from "./src/services/api";
import { clearDraft, loadConfig, loadDraft, persistConfig, persistDraft } from "./src/storage/config";
import { styles } from "./src/styles";
import type { AppConfig, Job, ResultPayload } from "./src/types";

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
  const [draftConfig, setDraftConfig] = useState<AppConfig>(DEFAULT_CONFIG);
  const [settingsVisible, setSettingsVisible] = useState(false);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [sortOrder, setSortOrder] = useState<"desc" | "asc">("desc");
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
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
  const visibleJobs = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase();
    return [...jobs]
      .filter((job) => (filterStatus === "all" ? true : job.status === filterStatus))
      .filter((job) => (normalizedQuery ? job.file_name.toLowerCase().includes(normalizedQuery) : true))
      .sort((left, right) => {
        const leftValue = new Date(left.updated_at || left.created_at).getTime();
        const rightValue = new Date(right.updated_at || right.created_at).getTime();
        return sortOrder === "desc" ? rightValue - leftValue : leftValue - rightValue;
      });
  }, [filterStatus, jobs, searchQuery, sortOrder]);
  const jobStats = useMemo(
    () => ({
      queued: jobs.filter((job) => job.status === "queued").length,
      processing: jobs.filter((job) => job.status === "processing").length,
      completed: jobs.filter((job) => job.status === "completed").length,
      failed: jobs.filter((job) => job.status === "failed").length,
    }),
    [jobs],
  );

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
        setDraftConfig(loaded);
      })
      .finally(() => setLoadingConfig(false));
  }, []);

  useEffect(() => {
    if (!loadingConfig) {
      void refreshJobsList();
    }
  }, [loadingConfig, config.baseUrl, config.apiKey]);

  useEffect(() => {
    if (selectedJobId) {
      void refreshSelectedJob(selectedJobId);
    }
  }, [selectedJobId]);

  useEffect(() => {
    if (!selectedJobId || !selectedJob) {
      return;
    }
    if (selectedJob.status !== "queued" && selectedJob.status !== "processing") {
      return;
    }
    const handle = setInterval(() => {
      void refreshSelectedJob(selectedJobId, false);
    }, 2500);
    return () => clearInterval(handle);
  }, [selectedJobId, selectedJob?.status]);

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

  async function refreshJobsList(cursor?: string | null, append = false): Promise<void> {
    try {
      append ? setBusy(true) : setRefreshing(true);
      const payload = await fetchJobs(config, cursor);
      setNotice(null);
      startTransition(() => {
        setJobs((current) => (append ? [...current, ...payload.items] : payload.items));
        setNextCursor(payload.next_cursor);
      });
    } catch (error) {
      showError("작업 목록을 불러오지 못했습니다.", error);
    } finally {
      setBusy(false);
      setRefreshing(false);
    }
  }

  async function refreshSelectedJob(jobId: string, syncResult = true): Promise<void> {
    try {
      const payload = await fetchJob(config, jobId);
      setNotice(null);
      const shouldLoadResult =
        payload.status === "completed" &&
        (syncResult || result?.job_id !== payload.job_id || selectedJob?.status !== "completed");
      startTransition(() => {
        setSelectedJob(payload);
        setJobs((current) => current.map((item) => (item.job_id === payload.job_id ? { ...item, ...payload } : item)));
      });
      if (shouldLoadResult) {
        const resultPayload = await fetchResult(config, jobId);
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

  async function handlePickPdf(): Promise<void> {
    try {
      const picked = await DocumentPicker.getDocumentAsync({
        type: "application/pdf",
        copyToCacheDirectory: true,
      });
      if (picked.canceled || !picked.assets.length) {
        return;
      }
      setBusy(true);
      setNotice("PDF 업로드 중...");
      const job = await uploadPdf(config, picked.assets[0]);
      startTransition(() => {
        setSelectedJobId(job.job_id);
        setSelectedJob(job);
        setResult(null);
        setEditorText("");
        setEditorSelection({ start: 0, end: 0 });
        setEditorFocusToken((current) => current + 1);
        setEditing(false);
      });
      await refreshJobsList();
    } catch (error) {
      showError("PDF 업로드에 실패했습니다.", error);
    } finally {
      setBusy(false);
    }
  }

  async function handleRetry(): Promise<void> {
    if (!selectedJobId) {
      return;
    }
    try {
      setBusy(true);
      const retried = await retryJob(config, selectedJobId);
      setNotice("작업을 다시 대기열에 넣었습니다.");
      startTransition(() => {
        setSelectedJob(retried);
        setResult(null);
        setEditorText("");
        setEditorSelection({ start: 0, end: 0 });
        setEditorFocusToken((current) => current + 1);
        setEditing(false);
      });
      await refreshJobsList();
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
    if (!hasUnsavedChanges) {
      setNotice("저장할 변경 사항이 없습니다.");
      return;
    }
    try {
      setBusy(true);
      await saveResult(config, selectedJobId, editorText);
      await clearDraft(selectedJobId);
      const updated = await fetchResult(config, selectedJobId);
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
    const action = async () => {
      try {
        setBusy(true);
        await deleteJob(config, selectedJobId);
        setJobs((current) => current.filter((job) => job.job_id !== selectedJobId));
        setSelectedJobId(null);
        setSelectedJob(null);
        setResult(null);
        setEditing(false);
        setNotice("작업을 삭제했습니다.");
      } catch (error) {
        showError("작업 삭제에 실패했습니다.", error);
      } finally {
        setBusy(false);
      }
    };

    if (Platform.OS === "web" && typeof window !== "undefined") {
      if (window.confirm("이 작업을 삭제하시겠습니까?")) {
        await action();
      }
      return;
    }

    Alert.alert("작업 삭제", "이 작업을 삭제하시겠습니까?", [
      { text: "취소", style: "cancel" },
      { text: "삭제", style: "destructive", onPress: () => void action() },
    ]);
  }

  async function handleSaveSettings(): Promise<void> {
    const next = {
      baseUrl: normalizeBaseUrl(draftConfig.baseUrl.trim().replace(/\/+$/, "")),
      apiKey: draftConfig.apiKey.trim(),
    };
    setConfig(next);
    setDraftConfig(next);
    setSettingsVisible(false);
    setNotice(`서버 설정을 저장했습니다: ${next.baseUrl}`);
    try {
      await persistConfig(next);
    } catch (error) {
      showError("서버 설정 저장에 실패했습니다.", error);
    }
  }

  async function handleUseCurrentHost(): Promise<void> {
    const next = {
      baseUrl: currentWebBaseUrl(),
      apiKey: config.apiKey,
    };
    setConfig(next);
    setDraftConfig(next);
    setSettingsVisible(false);
    setNotice(`현재 페이지 서버를 사용합니다: ${next.baseUrl}`);
    try {
      await persistConfig(next);
    } catch (error) {
      showError("현재 페이지 서버 적용에 실패했습니다.", error);
    }
  }

  const heroTitle = selectedJob?.status === "completed"
    ? result?.meta.title || selectedJob.file_name
    : "정부 보도자료를 모바일에서 바로 변환";
  const showListPanel = !isCompactLayout || !selectedJobId;
  const showDetailPanel = !isCompactLayout || !!selectedJobId;

  if (loadingConfig) {
    return (
      <SafeAreaView style={styles.loadingShell}>
        <ActivityIndicator size="large" color="#b75e1f" />
        <Text style={styles.loadingLabel}>GovPress Mobile 준비 중</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.backgroundOrbA} />
      <View style={styles.backgroundOrbB} />
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={[
          styles.scrollContent,
          isTabletLayout && styles.scrollContentTablet,
          isWideLayout && styles.scrollContentDesktop,
        ]}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => void refreshJobsList()} />}
      >
        <View style={[styles.heroCard, isWideLayout && styles.heroCardDesktop]}>
          <Text style={styles.eyebrow}>GovPress Mobile MVP</Text>
          <Text style={styles.heroTitle}>{heroTitle}</Text>
          <Text style={styles.heroSubtitle}>
            PDF 업로드, 변환 상태 확인, Markdown 검토와 수정, 공유까지 한 흐름으로 처리합니다.
          </Text>
          {notice ? <Text style={styles.noticeBox}>{notice}</Text> : null}
        </View>

        <WorkspaceToolbar
          currentServer={config.baseUrl}
          isWideLayout={isWideLayout}
          stats={jobStats}
          onOpenSettings={() => setSettingsVisible(true)}
          onPickPdf={() => void handlePickPdf()}
          onRefresh={() => void refreshJobsList()}
          onUseCurrentHost={Platform.OS === "web" ? () => void handleUseCurrentHost() : undefined}
        />

        <View style={[styles.sectionRow, isWideLayout && styles.sectionRowDesktop]}>
          {showListPanel ? (
            <JobListPanel
              busy={busy}
              filterStatus={filterStatus}
              isWideLayout={isWideLayout}
              jobs={visibleJobs}
              nextCursor={nextCursor}
              searchQuery={searchQuery}
              selectedJobId={selectedJobId}
              sortOrder={sortOrder}
              onChangeFilterStatus={setFilterStatus}
              onChangeSearchQuery={setSearchQuery}
              onLoadMore={(cursor) => void refreshJobsList(cursor, true)}
              onSelectJob={(jobId) => {
                confirmDiscardChanges(() => {
                  setSelectedJobId(jobId);
                  setActiveTab("preview");
                  setEditing(false);
                });
              }}
              onToggleSortOrder={() => setSortOrder((current) => (current === "desc" ? "asc" : "desc"))}
            />
          ) : null}

          {showDetailPanel ? (
            <JobDetailPanel
              activeTab={activeTab}
              editorSelection={editorSelection}
              editorFocusToken={editorFocusToken}
              hasUnsavedChanges={hasUnsavedChanges}
              editing={editing}
              editorText={editorText}
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
                  setSelectedJob(null);
                  setResult(null);
                  setActiveTab("preview");
                  setEditing(false);
                });
              }}
              onChangeEditorText={setEditorText}
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
              onToggleEditing={() => setEditing((current) => !current)}
            />
          ) : null}
        </View>
      </ScrollView>

      <SettingsModal
        visible={settingsVisible}
        draft={draftConfig}
        onChange={setDraftConfig}
        onClose={() => setSettingsVisible(false)}
        onSave={() => void handleSaveSettings()}
      />

      {busy ? (
        <View style={styles.busyOverlay}>
          <ActivityIndicator size="large" color="#fff7ee" />
        </View>
      ) : null}

      <View pointerEvents="none" style={styles.buildBadge}>
        <Text style={styles.buildBadgeText}>{BUILD_TAG}</Text>
      </View>
    </SafeAreaView>
  );
}
