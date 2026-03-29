import React, { useEffect, useRef } from "react";
import { ActivityIndicator, Pressable, ScrollView, Text, TextInput, View } from "react-native";

import { STATUS_COPY } from "../constants";
import { styles } from "../styles";
import type { Job, ResultPayload } from "../types";
import { formatDate } from "../utils/format";
import { detailBadgeStyle } from "../utils/statusStyles";
import { DiffPreview } from "./DiffPreview";
import { EmptyDetailState } from "./EmptyDetailState";
import { MarkdownPreview } from "./MarkdownPreview";
import { ResultTabs } from "./ResultTabs";

type Props = {
  activeTab: "preview" | "markdown" | "diff";
  editorSelection: { start: number; end: number };
  editorFocusToken: number;
  hasUnsavedChanges: boolean;
  editing: boolean;
  editorText: string;
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
  onChangeTab: (value: "preview" | "markdown" | "diff") => void;
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
  editing,
  editorText,
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
  const pendingMessage = selectedJob?.status === "queued"
    ? "대기열에 등록됐습니다. 워커가 파일을 가져가면 자동으로 변환을 시작합니다."
    : "PDF 구조를 분석하고 Markdown 초안을 생성하는 중입니다.";

  useEffect(() => {
    if (!editing) {
      return;
    }
    const handle = setTimeout(() => {
      editorRef.current?.focus();
    }, 0);
    return () => clearTimeout(handle);
  }, [editing, editorFocusToken]);

  return (
    <View style={[styles.columnWide, isWideLayout && styles.detailColumnDesktop]}>
      <View style={styles.sectionHeader}>
        <View style={styles.detailHeaderBar}>
          {showBackButton ? (
            <Pressable style={styles.backButton} onPress={onBack}>
              <Text style={styles.backButtonLabel}>목록으로</Text>
            </Pressable>
          ) : null}
          <Text style={styles.sectionTitle}>작업 상세</Text>
        </View>
        <Text style={styles.sectionMeta}>{selectedJob ? STATUS_COPY[selectedJob.status] : "선택 대기"}</Text>
      </View>
      <View style={[styles.panelLarge, isWideLayout && styles.panelLargeDesktop]}>
        {!selectedJob ? (
          <EmptyDetailState />
        ) : (
          <>
            <View style={styles.detailHeader}>
              <View>
                <Text style={styles.detailTitle}>{selectedJob.file_name}</Text>
                <Text style={styles.detailSub}>{formatDate(selectedJob.created_at)}</Text>
              </View>
              <Text style={detailBadgeStyle(selectedJob.status)}>{STATUS_COPY[selectedJob.status]}</Text>
            </View>

            {(selectedJob.status === "queued" || selectedJob.status === "processing") && (
              <View style={styles.stateCardProcessing}>
                <View style={styles.stateCardHeader}>
                  <ActivityIndicator color="#0f6f6f" />
                  <Text style={styles.stateEyebrow}>{selectedJob.status === "queued" ? "QUEUE" : "PROCESSING"}</Text>
                </View>
                <Text style={styles.stateTitle}>
                  {selectedJob.status === "queued" ? "서버 대기열에서 처리 순서를 기다리는 중입니다." : "변환 파이프라인이 실행 중입니다."}
                </Text>
                <Text style={styles.stateBody}>{pendingMessage}</Text>
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
              <View style={styles.stateCardError}>
                <Text style={styles.stateEyebrow}>FAILED</Text>
                <Text style={styles.stateTitle}>변환 중 문제가 발생했습니다.</Text>
                <Text style={styles.errorBody}>{selectedJob.error_message || "알 수 없는 오류"}</Text>
                <Pressable style={styles.primaryButton} onPress={onRetry}>
                  <Text style={styles.primaryButtonLabel}>다시 시도</Text>
                </Pressable>
              </View>
            )}

            {selectedJob.status === "completed" && result && (
              <>
                <View style={[styles.detailStickyShell, isWideLayout && styles.detailStickyShellDesktop]}>
                  <View style={[styles.detailTopCluster, isWideLayout && styles.detailTopClusterDesktop]}>
                    <View style={[styles.resultMetaCard, isWideLayout && styles.resultMetaCardDesktop]}>
                      <Text style={styles.resultMetaEyebrow}>변환 결과 요약</Text>
                      <Text style={styles.resultMetaTitle}>{result.meta.title || "제목 없음"}</Text>
                      <Text style={styles.resultMetaBody}>
                        부서: {result.meta.department || "미추출"}{"\n"}
                        원본: {result.meta.source_file_name}
                      </Text>
                    </View>
                    <View style={styles.detailControlsCluster}>
                      <View style={styles.detailActionsHeader}>
                        <Text style={styles.detailActionsTitle}>검토와 후속 작업</Text>
                        <Text style={styles.detailActionsHint}>탭으로 결과를 확인하고, 필요할 때만 편집이나 공유를 진행합니다.</Text>
                      </View>
                      <ResultTabs
                        tabs={[
                          { key: "preview", label: "미리보기" },
                          { key: "markdown", label: "Markdown" },
                          { key: "diff", label: "차이 보기" },
                        ]}
                        value={activeTab}
                        onChange={onChangeTab}
                      />
                      <View style={[styles.toolbar, !isWideLayout && styles.toolbarStack, isWideLayout && styles.toolbarDesktopCompact]}>
                        <Pressable style={styles.secondaryButton} onPress={onRequestToggleEditing}>
                          <Text style={styles.secondaryButtonLabel}>{editing ? "편집 닫기" : "수정"}</Text>
                        </Pressable>
                        <Pressable style={styles.secondaryButton} onPress={onCopyMarkdown}>
                          <Text style={styles.secondaryButtonLabel}>복사</Text>
                        </Pressable>
                        <Pressable style={styles.secondaryButton} onPress={onShareMarkdown}>
                          <Text style={styles.secondaryButtonLabel}>공유</Text>
                        </Pressable>
                        <Pressable style={styles.secondaryButton} onPress={onDeleteJob}>
                          <Text style={styles.secondaryButtonLabel}>삭제</Text>
                        </Pressable>
                        {editing ? (
                          <Pressable style={styles.secondaryButton} onPress={onDiscardEdit}>
                            <Text style={styles.secondaryButtonLabel}>되돌리기</Text>
                          </Pressable>
                        ) : null}
                        {editing ? (
                          <Pressable style={styles.primaryButton} onPress={onSaveEdit}>
                            <Text style={[styles.primaryButtonLabel, !hasUnsavedChanges && styles.disabledButtonLabel]}>저장</Text>
                          </Pressable>
                        ) : null}
                      </View>
                    </View>
                  </View>

                  {editing ? (
                    <View style={[styles.editNotice, hasUnsavedChanges ? styles.editNoticeDirty : styles.editNoticeClean]}>
                      <Text style={styles.editNoticeText}>
                        {hasUnsavedChanges ? "저장되지 않은 변경 사항이 있습니다." : "현재 편집 내용이 저장본과 같습니다."}
                      </Text>
                    </View>
                  ) : null}

                  {editing ? (
                    <>
                      <View style={[styles.editorToolbar, isWideLayout && styles.editorToolbarDesktop]}>
                        {[
                          {
                            title: "제목/강조",
                            actions: [
                              ["heading", "제목"],
                              ["heading2", "H2"],
                              ["heading3", "H3"],
                              ["bold", "굵게"],
                              ["italic", "기울임"],
                            ],
                          },
                          {
                            title: "목록/인용",
                            actions: [
                              ["bullet", "목록"],
                              ["number", "번호"],
                              ["quote", "인용"],
                            ],
                          },
                          {
                            title: "표",
                            actions: [
                              ["table", "표"],
                              ["tableRow", "행 추가"],
                            ],
                          },
                        ].map((group) => (
                          <View key={group.title} style={styles.editorToolGroup}>
                            {isWideLayout ? <Text style={styles.editorToolGroupLabel}>{group.title}</Text> : null}
                            <View style={styles.editorToolGroupButtons}>
                              {group.actions.map(([action, label]) => (
                                <Pressable
                                  key={action}
                                  style={styles.editorToolButton}
                                  onPress={() => onApplyEditorAction(action as "heading" | "heading2" | "heading3" | "bold" | "italic" | "bullet" | "number" | "quote" | "table" | "tableRow")}
                                >
                                  <Text style={styles.editorToolLabel}>{label}</Text>
                                </Pressable>
                              ))}
                            </View>
                          </View>
                        ))}
                      </View>

                      {sectionHeadings.length ? (
                        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.sectionJumpRow}>
                          {sectionHeadings.slice(0, 8).map((heading) => (
                            <Pressable
                              key={`${heading.index}-${heading.title}`}
                              style={styles.sectionJumpButton}
                              onPress={() => onJumpToSection(heading.index)}
                            >
                              <Text style={styles.sectionJumpLabel}>{heading.title}</Text>
                            </Pressable>
                          ))}
                        </ScrollView>
                      ) : null}
                    </>
                  ) : null}
                </View>

                {editing && isWideLayout ? (
                  <View style={styles.editorSplitLayout}>
                    <View style={styles.editorPanel}>
                      <Text style={styles.previewLabel}>Markdown 편집기</Text>
                      <TextInput
                        ref={editorRef}
                        value={editorText}
                        onChangeText={onChangeEditorText}
                        selection={editorSelection}
                        onSelectionChange={(event) => onChangeSelection(event.nativeEvent.selection)}
                        multiline
                        textAlignVertical="top"
                        style={[styles.editor, styles.editorDesktop]}
                      />
                    </View>
                    <View style={[styles.previewPanel, styles.previewPanelDesktop, styles.previewPanelSplit]}>
                      <Text style={styles.previewLabel}>
                        {activeTab === "preview" ? "렌더링용 텍스트 미리보기" : activeTab === "markdown" ? "Markdown 원문" : "원본 대비 수정 차이"}
                      </Text>
                      <ScrollView style={[styles.previewScroll, styles.previewScrollDesktop]}>
                        {activeTab === "preview" ? (
                          <MarkdownPreview markdown={selectedResultText} />
                        ) : activeTab === "diff" ? (
                          <DiffPreview original={result.markdown || ""} edited={editorText} />
                        ) : (
                          <Text style={styles.previewText}>{selectedResultText}</Text>
                        )}
                      </ScrollView>
                    </View>
                  </View>
                ) : (
                  <>
                    {editing ? (
                      <TextInput
                        ref={editorRef}
                        value={editorText}
                        onChangeText={onChangeEditorText}
                        selection={editorSelection}
                        onSelectionChange={(event) => onChangeSelection(event.nativeEvent.selection)}
                        multiline
                        textAlignVertical="top"
                        style={styles.editor}
                      />
                    ) : null}

                    <View style={[styles.previewPanel, isWideLayout && styles.previewPanelDesktop]}>
                      <Text style={styles.previewLabel}>
                        {activeTab === "preview" ? "렌더링용 텍스트 미리보기" : activeTab === "markdown" ? "Markdown 원문" : "원본 대비 수정 차이"}
                      </Text>
                      <ScrollView style={[styles.previewScroll, isWideLayout && styles.previewScrollDesktop]}>
                        {activeTab === "preview" ? (
                          <MarkdownPreview markdown={selectedResultText} />
                        ) : activeTab === "diff" ? (
                          <DiffPreview original={result.markdown || ""} edited={editorText} />
                        ) : (
                          <Text style={styles.previewText}>{selectedResultText}</Text>
                        )}
                      </ScrollView>
                    </View>
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
