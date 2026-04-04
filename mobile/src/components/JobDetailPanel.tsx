import React, { useEffect, useMemo, useRef } from "react";
import { ActivityIndicator, Pressable, ScrollView, Text, TextInput, View } from "react-native";

import { styles } from "../styles";
import type { Job, ResultPayload } from "../types";
import { EmptyDetailState } from "./EmptyDetailState";
import { MarkdownPreview, parseMarkdownBlockRanges } from "./MarkdownPreview";

type Props = {
  activeTab: "preview" | "markdown";
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
  result: ResultPayload | null;
  selectedJob: Job | null;
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
  onToggleEditing: () => void;
};

export function JobDetailPanel({
  activeTab,
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
  result,
  selectedJob,
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
  onToggleEditing,
}: Props) {
  const editorRef = useRef<TextInput | null>(null);
  const previewScrollRef = useRef<ScrollView | null>(null);
  const previewBlockPositionsRef = useRef<Record<number, number>>({});
  const previewViewportHeightRef = useRef(0);
  const previewScrollYRef = useRef(0);
  const pendingMessage = selectedJob?.status === "queued"
    ? "대기열에 등록됐습니다. 워커가 파일을 가져가면 자동으로 변환을 시작합니다."
    : "PDF 구조를 분석하고 Markdown 초안을 생성하는 중입니다.";
  const activePreviewBlockIndex = useMemo(() => {
    if (!editorText) {
      return -1;
    }
    const ranges = parseMarkdownBlockRanges(editorText);
    if (!ranges.length) {
      return -1;
    }
    const cursor = editorSelection.start;
    const matchedIndex = ranges.findIndex((range) => cursor >= range.start && cursor <= range.end);
    if (matchedIndex >= 0) {
      return matchedIndex;
    }
    return ranges.findIndex((range) => cursor < range.start);
  }, [editorSelection.start, editorText]);
  useEffect(() => {
    if (!editing) {
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

  return (
    <View style={[styles.columnWide, isWideLayout && styles.detailColumnDesktop]}>
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
                <View style={[styles.detailStickyShell, isWideLayout && styles.detailStickyShellDesktop]}>
                  {!isWideLayout ? (
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
                  <View style={styles.editorSplitLayout}>
                    <View style={[styles.editorPanel, isDarkMode && styles.editorPanelDark]}>
                      <Text style={[styles.previewLabel, isDarkMode && styles.previewLabelDark]}>편집기</Text>
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
                    </View>
                    <View style={[styles.previewPanel, styles.previewPanelDesktop, styles.previewPanelSplit, isDarkMode && styles.previewPanelDark]}>
                      <Text style={[styles.previewLabel, isDarkMode && styles.previewLabelDark]}>미리보기</Text>
                      <View style={styles.splitPanelBody}>
                        <ScrollView
                          ref={previewScrollRef}
                          style={[styles.previewScroll, styles.previewScrollDesktop]}
                          contentContainerStyle={styles.previewScrollContent}
                          onLayout={(event) => {
                            previewViewportHeightRef.current = event.nativeEvent.layout.height;
                          }}
                          onScroll={(event) => {
                            previewScrollYRef.current = event.nativeEvent.contentOffset.y;
                          }}
                          scrollEventThrottle={16}
                        >
                          <MarkdownPreview
                            markdown={editing ? editorText : selectedResultText}
                            isDarkMode={isDarkMode}
                            activeBlockIndex={activePreviewBlockIndex}
                            onBlockLayout={handlePreviewBlockLayout}
                          />
                        </ScrollView>
                      </View>
                    </View>
                  </View>
                ) : isTabletLayout ? (
                  <View style={styles.editorStackLayout}>
                    {editing ? (
                      <View style={[styles.editorPanel, styles.editorPanelTablet, isDarkMode && styles.editorPanelDark]}>
                        <Text style={[styles.previewLabel, isDarkMode && styles.previewLabelDark]}>편집기</Text>
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
                      </View>
                    ) : null}
                    <View style={[styles.previewPanel, styles.previewPanelTablet, isDarkMode && styles.previewPanelDark]}>
                      <Text style={[styles.previewLabel, isDarkMode && styles.previewLabelDark]}>
                        미리보기
                      </Text>
                      <View style={styles.splitPanelBody}>
                        <ScrollView
                          ref={previewScrollRef}
                          style={[styles.previewScroll, styles.previewScrollTablet]}
                          contentContainerStyle={styles.previewScrollContent}
                          onLayout={(event) => {
                            previewViewportHeightRef.current = event.nativeEvent.layout.height;
                          }}
                          onScroll={(event) => {
                            previewScrollYRef.current = event.nativeEvent.contentOffset.y;
                          }}
                          scrollEventThrottle={16}
                        >
                          <MarkdownPreview
                            markdown={editing ? editorText : selectedResultText}
                            isDarkMode={isDarkMode}
                            activeBlockIndex={activePreviewBlockIndex}
                            onBlockLayout={handlePreviewBlockLayout}
                          />
                        </ScrollView>
                      </View>
                    </View>
                  </View>
                ) : (
                  <>
                    {editing && activeTab === "markdown" ? (
                      <View style={[styles.editorPanel, styles.editorPanelMobile, isDarkMode && styles.editorPanelDark]}>
                        <Text style={[styles.previewLabel, isDarkMode && styles.previewLabelDark]}>편집기</Text>
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
                      </View>
                    ) : (
                    <View style={[styles.previewPanel, styles.previewPanelMobile, isDarkMode && styles.previewPanelDark]}>
                      <Text style={[styles.previewLabel, isDarkMode && styles.previewLabelDark]}>
                        미리보기
                      </Text>
                      <ScrollView
                        ref={previewScrollRef}
                        style={[styles.previewScroll, styles.previewScrollMobile]}
                        contentContainerStyle={styles.previewScrollContent}
                        onLayout={(event) => {
                          previewViewportHeightRef.current = event.nativeEvent.layout.height;
                        }}
                        onScroll={(event) => {
                          previewScrollYRef.current = event.nativeEvent.contentOffset.y;
                        }}
                        scrollEventThrottle={16}
                      >
                        <MarkdownPreview
                          markdown={editing ? editorText : selectedResultText}
                          isDarkMode={isDarkMode}
                          activeBlockIndex={activePreviewBlockIndex}
                          onBlockLayout={handlePreviewBlockLayout}
                        />
                      </ScrollView>
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
