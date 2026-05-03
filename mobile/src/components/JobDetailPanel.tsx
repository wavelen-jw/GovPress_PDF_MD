import React, { useDeferredValue, useEffect, useMemo, useRef, useState } from "react";
import { ActivityIndicator, Linking, Platform, Pressable, ScrollView, Text, TextInput, View } from "react-native";
import type { DocumentPickerAsset } from "expo-document-picker";

import { styles } from "../styles";
import type { Job, ResultPayload } from "../types";
import { EmptyDetailState } from "./EmptyDetailState";
import { MarkdownPreview, parseMarkdownBlockRanges } from "./MarkdownPreview";

type WebDropAsset = DocumentPickerAsset & { file?: File };

let MarkdownCodeMirror: React.ComponentType<{
  value: string;
  onChange: (value: string) => void;
  onSelectionChange?: (selection: { start: number; end: number }) => void;
  selection?: { start: number; end: number };
  focusToken?: number;
  height?: string;
  onHandleDroppedAsset?: (asset: WebDropAsset) => void;
}> | null = null;

if (Platform.OS === "web") {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  MarkdownCodeMirror = require("./MarkdownCodeMirror").MarkdownCodeMirror;
}

type Props = {
  activeTab: "preview" | "markdown";
  desktopSplitRatio: number;
  editorSelection: { start: number; end: number };
  editorFocusToken: number;
  hasUnsavedChanges: boolean;
  isDarkMode?: boolean;
  editing: boolean;
  editorText: string;
  isTabletLayout: boolean;
  isCompactLayout: boolean;
  isWideLayout: boolean;
  sectionHeadings: Array<{ title: string; index: number }>;
  showBackButton: boolean;
  hideTopTabs?: boolean;
  result: ResultPayload | null;
  selectedJob: Job | null;
  originalUrl?: string | null;
  selectedResultText: string;
  onApplyEditorAction: (action: "heading" | "heading2" | "heading3" | "bold" | "italic" | "bullet" | "number" | "quote" | "table" | "tableRow") => void;
  onBack: () => void;
  onChangeEditorText: (value: string) => void;
  onChangeSelection: (selection: { start: number; end: number }) => void;
  onChangeTab: (value: "preview" | "markdown") => void;
  onDiscardEdit: () => void;
  onDeleteJob: () => void;
  onCopyMarkdown: () => void;
  onJumpToSection: (index: number) => void;
  onRequestToggleEditing: () => void;
  onRetry: () => void;
  onSaveEdit: () => void;
  onShareMarkdown: () => void;
  onResizeDesktopSplit: (ratio: number) => void;
  onToggleEditing: () => void;
  onHandleDroppedAsset?: (asset: WebDropAsset) => void;
};

export function JobDetailPanel({
  activeTab,
  desktopSplitRatio,
  editorSelection,
  editorFocusToken,
  hasUnsavedChanges,
  isDarkMode,
  editing,
  editorText,
  isTabletLayout,
  isCompactLayout,
  isWideLayout,
  sectionHeadings,
  showBackButton,
  hideTopTabs,
  result,
  selectedJob,
  originalUrl,
  selectedResultText,
  onApplyEditorAction,
  onBack,
  onChangeEditorText,
  onChangeSelection,
  onChangeTab,
  onDiscardEdit,
  onDeleteJob,
  onCopyMarkdown,
  onJumpToSection,
  onRequestToggleEditing,
  onRetry,
  onSaveEdit,
  onShareMarkdown,
  onResizeDesktopSplit,
  onToggleEditing,
  onHandleDroppedAsset,
}: Props) {
  const editorRef = useRef<TextInput | null>(null);
  const splitLayoutRef = useRef<View | null>(null);
  const previewScrollRef = useRef<ScrollView | null>(null);
  const [editorContentHeight, setEditorContentHeight] = useState(0);
  const previewBlockPositionsRef = useRef<Record<number, number>>({});
  const previewViewportHeightRef = useRef(0);
  const previewScrollYRef = useRef(0);
  const previewMarkdown = useDeferredValue(selectedResultText);
  const openOriginalUrl = () => {
    if (!originalUrl) {
      return;
    }
    if (Platform.OS === "web" && typeof window !== "undefined") {
      window.open(originalUrl, "_blank", "noopener,noreferrer");
      return;
    }
    void Linking.openURL(originalUrl);
  };
  const renderPreviewHeader = () => (
    <View style={[styles.panelTabBar, isDarkMode ? styles.panelTabBarDark : styles.panelTabBarLight]}>
      <Text style={isDarkMode ? styles.panelTabLabelActive : styles.previewLabel}>미리보기</Text>
      <View style={styles.panelTabSpacer} />
      {originalUrl ? (
        <Pressable
          onPress={openOriginalUrl}
          style={styles.panelTabBtn}
          accessibilityRole="link"
          accessibilityLabel="정책브리핑 원문 열기"
        >
          <Text style={styles.panelTabBtnLabel}>원본</Text>
        </Pressable>
      ) : null}
    </View>
  );
  const previewBlockRanges = useMemo(() => {
    if (!previewMarkdown) {
      return [];
    }
    return parseMarkdownBlockRanges(previewMarkdown);
  }, [previewMarkdown]);
  const pendingMessage = selectedJob?.status === "queued"
    ? "대기열에 등록됐습니다. 워커가 파일을 가져가면 자동으로 변환을 시작합니다."
    : "PDF 구조를 분석하고 Markdown 초안을 생성하는 중입니다.";
  const activePreviewBlockIndex = useMemo(() => {
    if (!previewBlockRanges.length) {
      return -1;
    }
    const cursor = editorSelection.start;
    const matchedIndex = previewBlockRanges.findIndex((range) => cursor >= range.start && cursor <= range.end);
    if (matchedIndex >= 0) {
      return matchedIndex;
    }
    return previewBlockRanges.findIndex((range) => cursor < range.start);
  }, [editorSelection.start, previewBlockRanges]);
  useEffect(() => {
    if (!editing) {
      return;
    }
    if (Platform.OS === "web" && isDarkMode) {
      return;
    }
    const handle = setTimeout(() => {
      editorRef.current?.focus();
    }, 0);
    return () => clearTimeout(handle);
  }, [editing, editorFocusToken]);

  useEffect(() => {
    if (activePreviewBlockIndex < 0) {
      return;
    }
    const y = previewBlockPositionsRef.current[activePreviewBlockIndex];
    if (typeof y === "number") {
      const viewportHeight = previewViewportHeightRef.current;
      const currentScrollY = previewScrollYRef.current;
      const topThreshold = currentScrollY + 56;
      const bottomThreshold = currentScrollY + Math.max(120, viewportHeight - 120);
      if (!viewportHeight || y < topThreshold || y > bottomThreshold) {
        previewScrollRef.current?.scrollTo({ y: Math.max(0, y - 64), animated: true });
      }
    }
  }, [activePreviewBlockIndex, editorSelection.start]);

  function handlePreviewBlockLayout(blockIndex: number, y: number): void {
    previewBlockPositionsRef.current[blockIndex] = y;
  }

  function isSupportedDropFile(file: File | null | undefined): boolean {
    if (!file) {
      return false;
    }
    const name = file.name.toLowerCase();
    return name.endsWith(".pdf") || name.endsWith(".hwpx") || name.endsWith(".md");
  }

  function hasFileDropPayload(transfer: DataTransfer | null | undefined): boolean {
    if (!transfer) {
      return false;
    }
    if (Array.from(transfer.files || []).length > 0) {
      return true;
    }
    if (Array.from(transfer.items || []).some((item) => item.kind === "file")) {
      return true;
    }
    return Array.from(transfer.types || []).includes("Files");
  }

  function canAcceptDroppedFiles(transfer: DataTransfer | null | undefined): boolean {
    if (!transfer || !hasFileDropPayload(transfer)) {
      return false;
    }
    const files = Array.from(transfer.files || []) as File[];
    if (files.length === 0) {
      return true;
    }
    return files.some((file) => isSupportedDropFile(file));
  }

  const webPreviewDropProps = Platform.OS === "web" && onHandleDroppedAsset
    ? {
        onDragOver: (event: any) => {
          const transfer = event?.nativeEvent?.dataTransfer || event?.dataTransfer;
          if (!hasFileDropPayload(transfer)) {
            return;
          }
          event.preventDefault?.();
          event.stopPropagation?.();
          if (transfer) {
            transfer.dropEffect = canAcceptDroppedFiles(transfer) ? "copy" : "none";
          }
        },
        onDrop: (event: any) => {
          const transfer = event?.nativeEvent?.dataTransfer || event?.dataTransfer;
          const files = Array.from(transfer?.files || []) as File[];
          if (!files.length) {
            return;
          }
          event.preventDefault?.();
          event.stopPropagation?.();
          const file = files.find((candidate) => isSupportedDropFile(candidate));
          if (!file) {
            return;
          }
          onHandleDroppedAsset({
            uri: typeof window !== "undefined" ? window.URL.createObjectURL(file) : "",
            mimeType: file.type || "",
            name: file.name,
            size: file.size,
            file,
            lastModified: file.lastModified,
          } as WebDropAsset);
        },
      }
    : {};

  const webEditorDropProps = Platform.OS === "web" && onHandleDroppedAsset
    ? {
        onDragOver: (event: any) => {
          const transfer = event?.nativeEvent?.dataTransfer || event?.dataTransfer;
          if (!hasFileDropPayload(transfer)) {
            return;
          }
          event.preventDefault?.();
          event.stopPropagation?.();
          if (transfer) {
            transfer.dropEffect = canAcceptDroppedFiles(transfer) ? "copy" : "none";
          }
        },
        onDrop: (event: any) => {
          const transfer = event?.nativeEvent?.dataTransfer || event?.dataTransfer;
          const files = Array.from(transfer?.files || []) as File[];
          if (!files.length) {
            return;
          }
          event.preventDefault?.();
          event.stopPropagation?.();
          const file = files.find((candidate) => isSupportedDropFile(candidate));
          if (!file) {
            return;
          }
          onHandleDroppedAsset({
            uri: typeof window !== "undefined" ? window.URL.createObjectURL(file) : "",
            mimeType: file.type || "",
            name: file.name,
            size: file.size,
            file,
            lastModified: file.lastModified,
          } as WebDropAsset);
        },
      }
    : {};

  const webPanelDropProps = Platform.OS === "web" && onHandleDroppedAsset
    ? {
        onDragOver: (event: any) => {
          const transfer = event?.nativeEvent?.dataTransfer || event?.dataTransfer;
          if (!hasFileDropPayload(transfer)) {
            return;
          }
          event.preventDefault?.();
          event.stopPropagation?.();
          if (transfer) {
            transfer.dropEffect = canAcceptDroppedFiles(transfer) ? "copy" : "none";
          }
        },
        onDrop: (event: any) => {
          const transfer = event?.nativeEvent?.dataTransfer || event?.dataTransfer;
          const files = Array.from(transfer?.files || []) as File[];
          if (!files.length) {
            return;
          }
          event.preventDefault?.();
          event.stopPropagation?.();
          const file = files.find((candidate) => isSupportedDropFile(candidate));
          if (!file) {
            return;
          }
          onHandleDroppedAsset({
            uri: typeof window !== "undefined" ? window.URL.createObjectURL(file) : "",
            mimeType: file.type || "",
            name: file.name,
            size: file.size,
            file,
            lastModified: file.lastModified,
          } as WebDropAsset);
        },
      }
    : {};

  function clampDesktopRatio(next: number): number {
    return Math.min(0.72, Math.max(0.28, next));
  }

  function handleDesktopResize(event: { nativeEvent: { locationX: number; pageX: number } }): void {
    if (!isWideLayout) {
      return;
    }
    splitLayoutRef.current?.measureInWindow((x, _y, width) => {
      if (!width) {
        return;
      }
      const ratio = clampDesktopRatio((event.nativeEvent.pageX - x) / width);
      onResizeDesktopSplit(ratio);
    });
  }

  return (
    <View style={[styles.columnWide, isWideLayout && styles.detailColumnDesktop]} {...webPanelDropProps}>
      {showBackButton && !isCompactLayout ? (
        <View style={styles.sectionHeader}>
          <View style={styles.detailHeaderBar}>
            <Pressable style={styles.backButton} onPress={onBack}>
              <Text style={styles.backButtonLabel}>목록으로</Text>
            </Pressable>
          </View>
        </View>
      ) : null}
      <View style={[styles.panelLarge, isWideLayout && styles.panelLargeDesktop, isDarkMode && styles.panelLargeDark]}>
        {!selectedJob ? (
          <EmptyDetailState isDarkMode={isDarkMode} />
        ) : (
          <>
            {(selectedJob.status === "queued" || selectedJob.status === "processing") && (
              <View style={[styles.stateCardProcessing, isDarkMode && styles.stateCardProcessingDark]}>
                <View style={styles.stateCardHeader}>
                  <ActivityIndicator color="#0f6f6f" />
                  <Text style={[styles.stateEyebrow, isDarkMode && styles.stateEyebrowDark]}>{selectedJob.status === "queued" ? "QUEUE" : "PROCESSING"}</Text>
                </View>
                <Text style={[styles.stateTitle, isDarkMode && styles.stateTitleDark]}>
                  {selectedJob.status === "queued" ? "서버 대기열에서 처리 순서를 기다리는 중입니다." : "변환 파이프라인이 실행 중입니다."}
                </Text>
                <Text style={[styles.stateBody, isDarkMode && styles.stateBodyDark]}>{pendingMessage}</Text>
                <View style={[styles.progressSteps, !isWideLayout && styles.progressStepsStack]}>
                  <View style={[styles.progressStep, styles.progressStepActive]}>
                    <Text style={styles.progressStepLabel}>1. 업로드</Text>
                  </View>
                  <View
                    style={[
                      styles.progressStep,
                      selectedJob.status === "processing" ? styles.progressStepActive : styles.progressStepPending,
                    ]}
                  >
                    <Text style={styles.progressStepLabel}>2. 변환</Text>
                  </View>
                  <View style={[styles.progressStep, styles.progressStepPending]}>
                    <Text style={styles.progressStepLabel}>3. 결과 확인</Text>
                  </View>
                </View>
              </View>
            )}

            {selectedJob.status === "failed" && (
              <View style={[styles.stateCardError, isDarkMode && styles.stateCardErrorDark]}>
                <Text style={[styles.stateEyebrow, isDarkMode && styles.stateEyebrowDark]}>FAILED</Text>
                <Text style={[styles.stateTitle, isDarkMode && styles.stateTitleDark]}>변환 중 문제가 발생했습니다.</Text>
                <Text style={styles.errorBody}>{selectedJob.error_message || "알 수 없는 오류"}</Text>
                <Pressable style={styles.primaryButton} onPress={onRetry}>
                  <Text style={styles.primaryButtonLabel}>다시 시도</Text>
                </Pressable>
              </View>
            )}

            {selectedJob.status === "completed" && result && (
              <>
                <Text style={{ fontSize: 11, color: '#6b7280', textAlign: 'center', marginBottom: 8 }}>읽힘 AI로 구조화된 문서입니다</Text>
                <View style={[styles.detailStickyShell, isWideLayout && styles.detailStickyShellDesktop]}>
                  {!isWideLayout && !hideTopTabs ? (
                    <View style={styles.tabRow}>
                      {[
                        { key: "preview", label: "미리보기" },
                        { key: "markdown", label: "편집" },
                      ].map((tab) => {
                        const active = tab.key === activeTab;
                        return (
                          <Pressable
                            key={tab.key}
                            style={[styles.tabButton, isDarkMode && styles.tabButtonDark, active && styles.tabButtonActive]}
                            onPress={() => {
                              if (tab.key === "markdown") {
                                if (!editing) {
                                  onRequestToggleEditing();
                                }
                                onChangeTab("markdown");
                                return;
                              }
                              onChangeTab("preview");
                            }}
                          >
                            <Text style={[styles.tabLabel, isDarkMode && styles.tabLabelDark, active && styles.tabLabelActive]}>{tab.label}</Text>
                          </Pressable>
                        );
                      })}
                    </View>
                  ) : null}
                </View>

                {isWideLayout ? (
                  <View ref={splitLayoutRef} style={styles.editorSplitLayout}>
                    <View
                      style={[
                        styles.editorPanel,
                        styles.editorPanelDesktop,
                        isDarkMode && styles.editorPanelDark,
                        { flexBasis: `${desktopSplitRatio * 100}%` },
                      ]}
                    >
                      {/* Panel tab bar */}
                      {isDarkMode ? (
                        <View style={[styles.panelTabBar, styles.panelTabBarDark]}>
                          <Text style={styles.panelTabLabelActive}>Markdown</Text>
                          <View style={styles.panelTabSpacer} />
                          <Pressable style={styles.panelTabBtn} onPress={onCopyMarkdown}>
                            <Text style={styles.panelTabBtnLabel}>복사</Text>
                          </Pressable>
                          <Pressable style={styles.panelTabBtn} onPress={onShareMarkdown}>
                            <Text style={styles.panelTabBtnLabel}>공유</Text>
                          </Pressable>
                        </View>
                      ) : (
                        <Text style={[styles.previewLabel, isDarkMode && styles.previewLabelDark]}>편집기</Text>
                      )}
                      {/* Editor with line numbers */}
                      {isDarkMode && Platform.OS === "web" && MarkdownCodeMirror ? (
                        <View style={{ flex: 1, minHeight: 0 }} {...webEditorDropProps}>
                          <MarkdownCodeMirror
                            value={editorText}
                            onChange={onChangeEditorText}
                            onSelectionChange={onChangeSelection}
                            selection={editorSelection}
                            focusToken={editorFocusToken}
                            height="100%"
                            onHandleDroppedAsset={onHandleDroppedAsset}
                          />
                        </View>
                      ) : isDarkMode ? (
                        <ScrollView style={styles.editorScrollArea} contentContainerStyle={styles.editorScrollContent}>
                          <View style={styles.lineNumbersRow}>
                            <View style={styles.lineNumbersCol}>
                              {Array.from({ length: Math.max(1, (editorText.match(/\n/g) || []).length + 1) }, (_, i) => (
                                <Text key={i} style={styles.lineNumber}>{i + 1}</Text>
                              ))}
                            </View>
                            <TextInput
                              ref={editorRef}
                              value={editorText}
                              onChangeText={onChangeEditorText}
                              selection={editorSelection}
                              onSelectionChange={(event) => onChangeSelection(event.nativeEvent.selection)}
                              onContentSizeChange={(e) => {
                                const h = e.nativeEvent.contentSize.height;
                                if (h > 0) setEditorContentHeight(h);
                              }}
                              multiline
                              scrollEnabled={false}
                              textAlignVertical="top"
                              style={[styles.editorFlat, styles.editorFlatDark, editorContentHeight > 0 ? { height: editorContentHeight } : null]}
                            />
                          </View>
                        </ScrollView>
                      ) : (
                        <View style={styles.splitPanelBody}>
                          <TextInput
                            ref={editorRef}
                            value={editorText}
                            onChangeText={onChangeEditorText}
                            selection={editorSelection}
                            onSelectionChange={(event) => onChangeSelection(event.nativeEvent.selection)}
                            multiline
                            textAlignVertical="top"
                            style={[styles.editor, styles.editorDesktop, isDarkMode && styles.editorDark]}
                          />
                        </View>
                      )}
                      {/* Status bar */}
                      {isDarkMode ? (
                        <View style={[styles.panelStatusBar, styles.panelStatusBarDark]}>
                          <Text style={styles.panelStatusText}>줄 {(editorText.match(/\n/g) || []).length + 1}</Text>
                          <Text style={styles.panelStatusText}>·</Text>
                          <Text style={styles.panelStatusText}>UTF-8</Text>
                          <Text style={styles.panelStatusText}>·</Text>
                          <Text style={[styles.panelStatusText, styles.panelStatusSaved]}>
                            {hasUnsavedChanges ? "● 미저장" : "● 저장됨"}
                          </Text>
                        </View>
                      ) : null}
                    </View>
                    <View
                      style={styles.desktopResizeHandle}
                      onStartShouldSetResponder={() => true}
                      onMoveShouldSetResponder={() => true}
                      onResponderGrant={handleDesktopResize}
                      onResponderMove={handleDesktopResize}
                    >
                      <View style={[styles.desktopResizeTrack, isDarkMode && styles.desktopResizeTrackDark]} />
                    </View>
                    <View
                      style={[
                        styles.previewPanel,
                        styles.previewPanelDesktop,
                        styles.previewPanelSplit,
                        isDarkMode && styles.previewPanelDark,
                        { flexBasis: `${(1 - desktopSplitRatio) * 100}%` },
                      ]}
                      {...webPreviewDropProps}
                    >
                      {renderPreviewHeader()}
                      <ScrollView
                        ref={previewScrollRef}
                        style={[styles.previewScroll, styles.previewScrollDesktop]}
                        contentContainerStyle={[styles.previewScrollContent, isDarkMode && { padding: 16 }]}
                        onLayout={(event) => {
                          previewViewportHeightRef.current = event.nativeEvent.layout.height;
                        }}
                        onScroll={(event) => {
                          previewScrollYRef.current = event.nativeEvent.contentOffset.y;
                        }}
                        scrollEventThrottle={16}
                      >
                        {isDarkMode ? (
                          <View style={styles.previewCard}>
                            <MarkdownPreview
                              markdown={previewMarkdown}
                              isDarkMode={false}
                              activeBlockIndex={activePreviewBlockIndex}
                              onBlockLayout={handlePreviewBlockLayout}
                            />
                          </View>
                        ) : (
                          <MarkdownPreview
                            markdown={previewMarkdown}
                            isDarkMode={isDarkMode}
                            activeBlockIndex={activePreviewBlockIndex}
                            onBlockLayout={handlePreviewBlockLayout}
                          />
                        )}
                      </ScrollView>
                    </View>
                  </View>
                ) : isTabletLayout ? (
                  <View style={styles.editorStackLayout}>
                    {editing ? (
                      <View style={[styles.editorPanel, styles.editorPanelTablet, isDarkMode && styles.editorPanelDark]}>
                        {/* Panel tab bar */}
                        {isDarkMode ? (
                          <View style={[styles.panelTabBar, styles.panelTabBarDark]}>
                            <Text style={styles.panelTabLabelActive}>Markdown</Text>
                            <View style={styles.panelTabSpacer} />
                            <Pressable style={styles.panelTabBtn} onPress={onCopyMarkdown}>
                              <Text style={styles.panelTabBtnLabel}>복사</Text>
                            </Pressable>
                            <Pressable style={styles.panelTabBtn} onPress={onShareMarkdown}>
                              <Text style={styles.panelTabBtnLabel}>공유</Text>
                            </Pressable>
                          </View>
                        ) : (
                          <Text style={[styles.previewLabel, isDarkMode && styles.previewLabelDark]}>편집기</Text>
                        )}
                        {/* Editor with line numbers */}
                        {isDarkMode && Platform.OS === "web" && MarkdownCodeMirror ? (
                          <View style={{ flex: 1, minHeight: 0 }} {...webEditorDropProps}>
                            <MarkdownCodeMirror
                              value={editorText}
                              onChange={onChangeEditorText}
                              onSelectionChange={onChangeSelection}
                              selection={editorSelection}
                              focusToken={editorFocusToken}
                              height="100%"
                              onHandleDroppedAsset={onHandleDroppedAsset}
                            />
                          </View>
                        ) : isDarkMode ? (
                          <ScrollView style={styles.editorScrollArea} contentContainerStyle={styles.editorScrollContent}>
                            <View style={styles.lineNumbersRow}>
                              <View style={styles.lineNumbersCol}>
                                {Array.from({ length: Math.max(1, (editorText.match(/\n/g) || []).length + 1) }, (_, i) => (
                                  <Text key={i} style={styles.lineNumber}>{i + 1}</Text>
                                ))}
                              </View>
                              <TextInput
                                ref={editorRef}
                                value={editorText}
                                onChangeText={onChangeEditorText}
                                selection={editorSelection}
                                onSelectionChange={(event) => onChangeSelection(event.nativeEvent.selection)}
                                onContentSizeChange={(e) => {
                                  const h = e.nativeEvent.contentSize.height;
                                  if (h > 0) setEditorContentHeight(h);
                                }}
                                multiline
                                scrollEnabled={false}
                                textAlignVertical="top"
                                style={[styles.editorFlat, styles.editorFlatDark, editorContentHeight > 0 ? { height: editorContentHeight } : null]}
                              />
                            </View>
                          </ScrollView>
                        ) : (
                          <View style={styles.splitPanelBody}>
                            <TextInput
                              ref={editorRef}
                              value={editorText}
                              onChangeText={onChangeEditorText}
                              selection={editorSelection}
                              onSelectionChange={(event) => onChangeSelection(event.nativeEvent.selection)}
                              multiline
                              textAlignVertical="top"
                              style={[styles.editor, styles.editorTablet, isDarkMode && styles.editorDark]}
                            />
                          </View>
                        )}
                        {/* Status bar */}
                        {isDarkMode ? (
                          <View style={[styles.panelStatusBar, styles.panelStatusBarDark]}>
                            <Text style={styles.panelStatusText}>줄 {(editorText.match(/\n/g) || []).length + 1}</Text>
                            <Text style={styles.panelStatusText}>·</Text>
                            <Text style={styles.panelStatusText}>UTF-8</Text>
                            <Text style={styles.panelStatusText}>·</Text>
                            <Text style={[styles.panelStatusText, styles.panelStatusSaved]}>
                              {hasUnsavedChanges ? "● 미저장" : "● 저장됨"}
                            </Text>
                          </View>
                        ) : null}
                      </View>
                    ) : null}
                    <View style={[styles.previewPanel, styles.previewPanelTablet, isDarkMode && styles.previewPanelDark]}>
                      <View style={{ flex: 1 }} {...webPreviewDropProps}>
                      {renderPreviewHeader()}
                      <ScrollView
                        ref={previewScrollRef}
                        style={[styles.previewScroll, styles.previewScrollTablet]}
                        contentContainerStyle={[styles.previewScrollContent, isDarkMode && { padding: 16 }]}
                        onLayout={(event) => {
                          previewViewportHeightRef.current = event.nativeEvent.layout.height;
                        }}
                        onScroll={(event) => {
                          previewScrollYRef.current = event.nativeEvent.contentOffset.y;
                        }}
                        scrollEventThrottle={16}
                      >
                        {isDarkMode ? (
                          <View style={styles.previewCard}>
                            <MarkdownPreview
                              markdown={previewMarkdown}
                              isDarkMode={false}
                              activeBlockIndex={activePreviewBlockIndex}
                              onBlockLayout={handlePreviewBlockLayout}
                            />
                          </View>
                        ) : (
                          <MarkdownPreview
                            markdown={previewMarkdown}
                            isDarkMode={isDarkMode}
                            activeBlockIndex={activePreviewBlockIndex}
                            onBlockLayout={handlePreviewBlockLayout}
                          />
                        )}
                      </ScrollView>
                      </View>
                    </View>
                  </View>
                ) : (
                  <>
                    {editing && activeTab === "markdown" ? (
                      <View style={[styles.editorPanel, styles.editorPanelMobile, isDarkMode && styles.editorPanelDark]}>
                        {/* Panel tab bar */}
                        {isDarkMode ? (
                          <View style={[styles.panelTabBar, styles.panelTabBarDark]}>
                            <Text style={styles.panelTabLabelActive}>Markdown</Text>
                            <View style={styles.panelTabSpacer} />
                            <Pressable style={styles.panelTabBtn} onPress={onCopyMarkdown}>
                              <Text style={styles.panelTabBtnLabel}>복사</Text>
                            </Pressable>
                            <Pressable style={styles.panelTabBtn} onPress={onShareMarkdown}>
                              <Text style={styles.panelTabBtnLabel}>공유</Text>
                            </Pressable>
                          </View>
                        ) : (
                          <Text style={[styles.previewLabel, isDarkMode && styles.previewLabelDark]}>편집기</Text>
                        )}
                        {/* Editor with line numbers */}
                        {isDarkMode && Platform.OS === "web" && MarkdownCodeMirror ? (
                          <View style={{ flex: 1, minHeight: 0 }}>
                            <MarkdownCodeMirror
                              value={editorText}
                              onChange={onChangeEditorText}
                              onSelectionChange={onChangeSelection}
                              selection={editorSelection}
                              focusToken={editorFocusToken}
                              height="100%"
                            />
                          </View>
                        ) : isDarkMode ? (
                          <ScrollView style={styles.editorScrollArea} contentContainerStyle={styles.editorScrollContent}>
                            <View style={styles.lineNumbersRow}>
                              <View style={styles.lineNumbersCol}>
                                {Array.from({ length: Math.max(1, (editorText.match(/\n/g) || []).length + 1) }, (_, i) => (
                                  <Text key={i} style={styles.lineNumber}>{i + 1}</Text>
                                ))}
                              </View>
                              <TextInput
                                ref={editorRef}
                                value={editorText}
                                onChangeText={onChangeEditorText}
                                selection={editorSelection}
                                onSelectionChange={(event) => onChangeSelection(event.nativeEvent.selection)}
                                onContentSizeChange={(e) => {
                                  const h = e.nativeEvent.contentSize.height;
                                  if (h > 0) setEditorContentHeight(h);
                                }}
                                multiline
                                scrollEnabled={false}
                                textAlignVertical="top"
                                style={[styles.editorFlat, styles.editorFlatDark, editorContentHeight > 0 ? { height: editorContentHeight } : null]}
                              />
                            </View>
                          </ScrollView>
                        ) : (
                          <View style={styles.splitPanelBody}>
                            <TextInput
                              ref={editorRef}
                              value={editorText}
                              onChangeText={onChangeEditorText}
                              selection={editorSelection}
                              onSelectionChange={(event) => onChangeSelection(event.nativeEvent.selection)}
                              multiline
                              textAlignVertical="top"
                              style={[styles.editor, styles.editorMobile, isDarkMode && styles.editorDark]}
                            />
                          </View>
                        )}
                        {/* Status bar */}
                        {isDarkMode ? (
                          <View style={[styles.panelStatusBar, styles.panelStatusBarDark]}>
                            <Text style={styles.panelStatusText}>줄 {(editorText.match(/\n/g) || []).length + 1}</Text>
                            <Text style={styles.panelStatusText}>·</Text>
                            <Text style={styles.panelStatusText}>UTF-8</Text>
                            <Text style={styles.panelStatusText}>·</Text>
                            <Text style={[styles.panelStatusText, styles.panelStatusSaved]}>
                              {hasUnsavedChanges ? "● 미저장" : "● 저장됨"}
                            </Text>
                          </View>
                        ) : null}
                      </View>
                    ) : (
                    <View style={[styles.previewPanel, styles.previewPanelMobile, isDarkMode && styles.previewPanelDark]}>
                      <View style={{ flex: 1 }} {...webPreviewDropProps}>
                      {renderPreviewHeader()}
                      <ScrollView
                        ref={previewScrollRef}
                        style={[styles.previewScroll, styles.previewScrollMobile]}
                        contentContainerStyle={[styles.previewScrollContent, isDarkMode && { padding: 16 }]}
                        onLayout={(event) => {
                          previewViewportHeightRef.current = event.nativeEvent.layout.height;
                        }}
                        onScroll={(event) => {
                          previewScrollYRef.current = event.nativeEvent.contentOffset.y;
                        }}
                        scrollEventThrottle={16}
                      >
                        {isDarkMode ? (
                          <View style={styles.previewCard}>
                            <MarkdownPreview
                              markdown={previewMarkdown}
                              isDarkMode={false}
                              activeBlockIndex={activePreviewBlockIndex}
                              onBlockLayout={handlePreviewBlockLayout}
                            />
                          </View>
                        ) : (
                          <MarkdownPreview
                            markdown={previewMarkdown}
                            isDarkMode={isDarkMode}
                            activeBlockIndex={activePreviewBlockIndex}
                            onBlockLayout={handlePreviewBlockLayout}
                          />
                        )}
                      </ScrollView>
                      </View>
                    </View>
                    )}
                  </>
                )}
              </>
            )}
          </>
        )}
      </View>
    </View>
  );
}
