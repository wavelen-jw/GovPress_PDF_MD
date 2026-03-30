import React from "react";
import { ActivityIndicator, Image, Platform, Pressable, Text, View } from "react-native";

import { styles } from "../styles";

type Props = {
  currentDocumentName: string | null;
  hasResult: boolean;
  hasUnsavedChanges: boolean;
  isWideLayout: boolean;
  isCompactLayout: boolean;
  isDarkMode: boolean;
  isPdfPickReady: boolean;
  isPdfVerificationPending: boolean;
  editing: boolean;
  activeTab: "preview" | "markdown" | "diff";
  onChangeTab: (value: "preview" | "markdown" | "diff") => void;
  onCopyMarkdown: () => void;
  onDiscardEdit: () => void;
  onOpenInfo: () => void;
  onPickPdf: () => void;
  onSaveEdit: () => void;
  onSaveMarkdownFile: () => void;
  onShareMarkdown: () => void;
  onToggleDarkMode: () => void;
};

export function WorkspaceToolbar({
  currentDocumentName,
  hasResult,
  hasUnsavedChanges,
  isWideLayout,
  isCompactLayout,
  isDarkMode,
  isPdfPickReady,
  isPdfVerificationPending,
  editing,
  activeTab,
  onChangeTab,
  onCopyMarkdown,
  onDiscardEdit,
  onOpenInfo,
  onPickPdf,
  onSaveEdit,
  onSaveMarkdownFile,
  onShareMarkdown,
  onToggleDarkMode,
}: Props) {
  const infoIconUri = "https://thumb.mt.co.kr/cdn-cgi/image/f=avif/21/2025/06/2025061011200349911_1.jpg";
  const pickPdfLabel = "📄 PDF 열기";
  const saveMdLabel = "💾 저장하기";
  const copyLabel = isWideLayout ? "⧉" : "⧉ 복사";
  const discardLabel = "↺";
  const saveEditLabel = isWideLayout ? "💾 저장" : "💾 저장";
  const shareLabel = isWideLayout ? "⇪" : "⇪ 공유";
  const webTitle = (label: string) => (Platform.OS === "web" ? { title: label } : {});
  const toolbarDocumentText = currentDocumentName || "PDF 또는 Markdown 파일을 열어 작업을 시작하세요.";

  return (
    <View style={[styles.workspaceToolbar, isWideLayout && styles.workspaceToolbarDesktop, isDarkMode && styles.workspaceToolbarDark]}>
      <View style={styles.workspaceToolbarBar}>
        <View style={[styles.workspaceToolbarTopRow, isWideLayout && styles.workspaceToolbarTopRowDesktop]}>
          <View style={styles.workspaceToolbarBrand}>
            <Text style={[styles.workspaceToolbarTitle, isDarkMode && styles.workspaceToolbarTitleDark]}>정부 보도자료.Markdown</Text>
          </View>
          <View style={styles.workspaceToolbarCluster}>
            <View style={styles.workspaceToolbarActions}>
              {editing && isWideLayout ? (
                <Pressable style={styles.primaryButton} onPress={onSaveEdit} accessibilityLabel="편집 저장" {...webTitle("편집 저장")}>
                  <Text style={[styles.primaryButtonLabel, !hasUnsavedChanges && styles.disabledButtonLabel]}>{saveEditLabel}</Text>
                </Pressable>
              ) : null}
            </View>
            <View style={styles.workspaceToolbarUtility}>
              <View style={styles.workspaceToolbarPrimaryUtility}>
                <Pressable
                  style={[
                    isPdfPickReady
                      ? hasResult
                        ? [styles.secondaryButton, isDarkMode && styles.secondaryButtonDark]
                        : styles.primaryButton
                      : [styles.secondaryButton, styles.toolbarDisabledButton, isDarkMode && styles.secondaryButtonDark],
                    isPdfVerificationPending && styles.toolbarPendingButton,
                  ]}
                  onPress={onPickPdf}
                  accessibilityLabel="PDF 열기"
                  {...webTitle("PDF 열기")}
                >
                  <Text
                    style={[
                      isPdfPickReady
                        ? hasResult
                          ? [styles.secondaryButtonLabel, isDarkMode && styles.secondaryButtonLabelDark]
                          : styles.primaryButtonLabel
                        : [styles.secondaryButtonLabel, styles.toolbarDisabledButtonLabel, isDarkMode && styles.secondaryButtonLabelDark],
                      isPdfVerificationPending && styles.toolbarPendingLabel,
                    ]}
                  >
                    {pickPdfLabel}
                  </Text>
                  {isPdfVerificationPending ? (
                    <View style={styles.toolbarPendingOverlay}>
                      <ActivityIndicator size="small" color={isDarkMode ? "#f2e2d0" : "#fffaf4"} />
                    </View>
                  ) : null}
                </Pressable>
                <Pressable
                  style={hasResult ? styles.primaryButton : [styles.secondaryButton, isDarkMode && styles.secondaryButtonDark]}
                  onPress={onSaveMarkdownFile}
                  accessibilityLabel="Markdown 저장하기"
                  {...webTitle("Markdown 저장하기")}
                >
                  <Text
                    style={
                      hasResult
                        ? styles.primaryButtonLabel
                        : [styles.secondaryButtonLabel, isDarkMode && styles.secondaryButtonLabelDark]
                    }
                  >
                    {saveMdLabel}
                  </Text>
                </Pressable>
                {hasResult && isWideLayout ? (
                  <View style={[styles.workspaceToolbarInlineDivider, isDarkMode && styles.workspaceToolbarInlineDividerDark]} />
                ) : null}
                {hasResult && isWideLayout ? (
                  <View style={styles.workspaceTabsRow}>
                    {(isWideLayout
                      ? [
                          { key: "preview", label: "미리보기" },
                          { key: "diff", label: "차이 보기" },
                        ]
                      : [
                          { key: "preview", label: "미리보기" },
                          { key: "markdown", label: "Markdown" },
                          { key: "diff", label: "차이 보기" },
                        ]).map((tab) => {
                      const active = tab.key === activeTab;
                      return (
                        <Pressable
                          key={tab.key}
                          style={[styles.workspaceTabButton, isDarkMode && styles.workspaceTabButtonDark, active && styles.workspaceTabButtonActive]}
                          onPress={() => onChangeTab(tab.key as "preview" | "markdown" | "diff")}
                          accessibilityLabel={tab.label}
                          {...webTitle(tab.label)}
                        >
                          <Text style={[styles.workspaceTabLabel, isDarkMode && styles.workspaceTabLabelDark, active && styles.workspaceTabLabelActive]}>{tab.label}</Text>
                        </Pressable>
                      );
                    })}
                  </View>
                ) : null}
                {editing && isWideLayout ? (
                  <Pressable
                    style={[styles.utilityButton, styles.utilityIconButton, isDarkMode && styles.utilityButtonDark]}
                    onPress={onDiscardEdit}
                    accessibilityLabel="변경 되돌리기"
                    {...webTitle("변경 되돌리기")}
                  >
                    <Text style={[styles.utilityButtonLabel, styles.utilityIconLabel, isDarkMode && styles.utilityButtonLabelDark]}>{discardLabel}</Text>
                  </Pressable>
                ) : null}
                {hasResult ? (
                  <Pressable
                    style={[styles.utilityButton, styles.utilityIconButton, isDarkMode && styles.utilityButtonDark]}
                    onPress={onCopyMarkdown}
                    accessibilityLabel="Markdown 복사"
                    {...webTitle("Markdown 복사")}
                  >
                    <Text style={[styles.utilityButtonLabel, styles.utilityIconLabel, isDarkMode && styles.utilityButtonLabelDark]}>{copyLabel}</Text>
                  </Pressable>
                ) : null}
                {hasResult ? (
                  <Pressable
                    style={[styles.utilityButton, styles.utilityIconButton, isDarkMode && styles.utilityButtonDark]}
                    onPress={onShareMarkdown}
                    accessibilityLabel="Markdown 공유"
                    {...webTitle("Markdown 공유")}
                  >
                    <Text style={[styles.utilityButtonLabel, styles.utilityIconLabel, isDarkMode && styles.utilityButtonLabelDark]}>{shareLabel}</Text>
                  </Pressable>
                ) : null}
              </View>
              <View style={[styles.workspaceToolbarSecondaryUtility, isDarkMode && styles.workspaceToolbarSecondaryUtilityDark]}>
                {!isCompactLayout ? (
                  <Pressable
                    style={[styles.utilityButton, styles.utilityIconButton, isDarkMode && styles.utilityButtonDark]}
                    onPress={onToggleDarkMode}
                    accessibilityLabel={isDarkMode ? "라이트 모드" : "다크 모드"}
                    {...webTitle(isDarkMode ? "라이트 모드" : "다크 모드")}
                  >
                    <Text style={[styles.utilityButtonLabel, styles.utilityIconLabel, isDarkMode && styles.utilityButtonLabelDark]}>{isDarkMode ? "☀" : "☾"}</Text>
                  </Pressable>
                ) : null}
                <Pressable
                  style={[styles.utilityButton, styles.utilityIconButton, isDarkMode && styles.utilityButtonDark]}
                  onPress={onOpenInfo}
                  accessibilityLabel="정보"
                  {...webTitle("정보")}
                >
                  <View style={styles.utilityInfoCrop}>
                    <Image source={{ uri: infoIconUri }} style={styles.utilityInfoImage} />
                  </View>
                </Pressable>
              </View>
            </View>
          </View>
        </View>
        <View style={styles.workspaceToolbarDocumentRow}>
          <Text style={[styles.workspaceToolbarDocument, isDarkMode && styles.workspaceToolbarDocumentDark]} numberOfLines={1}>
            {toolbarDocumentText}
          </Text>
        </View>
      </View>
    </View>
  );
}
