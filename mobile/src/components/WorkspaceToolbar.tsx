import React from "react";
import { Image, Platform, Pressable, Text, View } from "react-native";

import { styles } from "../styles";

type Props = {
  currentDocumentName: string | null;
  hasResult: boolean;
  isWideLayout: boolean;
  isDarkMode: boolean;
  isPdfPickReady: boolean;
  editing: boolean;
  onDiscardEdit: () => void;
  onOpenLanding: () => void;
  onOpenInfo: () => void;
  onPickPdf: () => void;
  onOpenPolicyBriefings: () => void;
  onSaveMarkdownFile: () => void;
  onToggleDarkMode: () => void;
};

const webTitle = (label: string) => (Platform.OS === "web" ? { title: label } : {});

export function WorkspaceToolbar({
  currentDocumentName,
  hasResult,
  isWideLayout,
  isDarkMode,
  isPdfPickReady,
  editing,
  onDiscardEdit,
  onOpenLanding,
  onOpenInfo,
  onPickPdf,
  onOpenPolicyBriefings,
  onSaveMarkdownFile,
  onToggleDarkMode,
}: Props) {
  const infoIconUri = "https://thumb.mt.co.kr/cdn-cgi/image/f=avif/21/2025/06/2025061011200349911_1.jpg";

  return (
    <View style={[styles.workspaceToolbar, isDarkMode && styles.workspaceToolbarDark]}>

      {/* ── Brand ── */}
      <Pressable
        onPress={onOpenLanding}
        accessibilityRole="link"
        accessibilityLabel="읽힘 랜딩페이지로 이동"
        {...webTitle("읽힘 랜딩페이지로 이동")}
      >
        <Text style={[styles.tbarBrand, isDarkMode && styles.tbarBrandDark]}>읽힘</Text>
      </Pressable>
      <Text style={[styles.tbarSep, isDarkMode && styles.tbarSepDark]}>|</Text>

      {/* ── Document name ── */}
      {currentDocumentName ? (
        <Text
          style={[styles.tbarDocName, isDarkMode && styles.tbarDocNameDark]}
          numberOfLines={1}
        >
          {currentDocumentName}
        </Text>
      ) : null}

      {/* ── Spacer: pushes all action buttons to the right ── */}
      <View style={styles.tbarSpacer} />

      {/* ── Primary action: convert file ── */}
      <Pressable
        style={[
          styles.tbarBtn,
          styles.tbarBtnPrimary,
          !isPdfPickReady && styles.tbarBtnDisabled,
        ]}
        onPress={onPickPdf}
        accessibilityLabel="변환"
        {...webTitle("변환")}
      >
        <Text style={styles.tbarBtnLabelPrimary}>⬆ 변환</Text>
      </Pressable>

      {/* ── Policy briefings ── */}
      <Pressable
        style={[styles.tbarBtn, isDarkMode && styles.tbarBtnDark]}
        onPress={onOpenPolicyBriefings}
        accessibilityLabel="보도자료"
        {...webTitle("보도자료")}
      >
        <Text style={[styles.tbarBtnLabel, isDarkMode && styles.tbarBtnLabelDark]}>
          ☰ 보도자료
        </Text>
      </Pressable>

      {/* ── Save MD ── */}
      {hasResult ? (
        <Pressable
          style={[styles.tbarBtn, isDarkMode && styles.tbarBtnDark, styles.tbarBtnPrimary]}
          onPress={onSaveMarkdownFile}
          accessibilityLabel="Markdown 저장하기"
          {...webTitle("Markdown 저장하기")}
        >
          <Text style={styles.tbarBtnLabelPrimary}>💾 저장</Text>
        </Pressable>
      ) : null}

      {/* ── Discard edit (desktop only, when editing) ── */}
      {editing && isWideLayout ? (
        <Pressable
          style={[styles.tbarIconBtn, isDarkMode && styles.tbarIconBtnDark]}
          onPress={onDiscardEdit}
          accessibilityLabel="변경 되돌리기"
          {...webTitle("변경 되돌리기")}
        >
          <Text style={[styles.tbarIconLabel, isDarkMode && styles.tbarIconLabelDark]}>↺</Text>
        </Pressable>
      ) : null}

      {/* ── Dark mode toggle (desktop) ── */}
      {isWideLayout ? (
        <Pressable
          style={[styles.tbarIconBtn, isDarkMode && styles.tbarIconBtnDark]}
          onPress={onToggleDarkMode}
          accessibilityLabel={isDarkMode ? "라이트 모드" : "다크 모드"}
          {...webTitle(isDarkMode ? "라이트 모드" : "다크 모드")}
        >
          <Text style={[styles.tbarIconLabel, isDarkMode && styles.tbarIconLabelDark]}>
            {isDarkMode ? "☀" : "☾"}
          </Text>
        </Pressable>
      ) : null}

      {/* ── Info ── */}
      <Pressable
        style={[styles.tbarIconBtn, isDarkMode && styles.tbarIconBtnDark]}
        onPress={onOpenInfo}
        accessibilityLabel="정보"
        {...webTitle("정보")}
      >
        <View style={styles.utilityInfoCrop}>
          <Image source={{ uri: infoIconUri }} style={styles.utilityInfoImage} />
        </View>
      </Pressable>
    </View>
  );
}
