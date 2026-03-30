import React, { useEffect, useRef, useState } from "react";
import { Platform, Pressable, ScrollView, Text, View } from "react-native";

import { styles } from "../styles";

type Props = {
  isDarkMode?: boolean;
  isCompactLayout?: boolean;
  onPickPdf?: () => void;
  onDropFile?: (file: File) => void;
};

export function EmptyDetailState({ isDarkMode = false, isCompactLayout = false, onPickPdf, onDropFile }: Props) {
  const [isDragActive, setIsDragActive] = useState(false);
  const dropZoneRef = useRef<View>(null);
  // Keep latest callback in a ref so event listeners don't need to be re-attached on every render
  const onDropFileRef = useRef(onDropFile);
  onDropFileRef.current = onDropFile;

  useEffect(() => {
    if (Platform.OS !== "web" || typeof window === "undefined") {
      return;
    }
    const preventBrowserDrop = (event: DragEvent) => {
      event.preventDefault();
    };
    window.addEventListener("dragover", preventBrowserDrop);
    window.addEventListener("drop", preventBrowserDrop);
    return () => {
      window.removeEventListener("dragover", preventBrowserDrop);
      window.removeEventListener("drop", preventBrowserDrop);
    };
  }, []);

  // Attach drag event listeners directly to the DOM node.
  // React Native's Pressable does not forward onDragOver/onDrop props to the DOM,
  // so spreading them as JSX props has no effect on web.
  useEffect(() => {
    if (Platform.OS !== "web" || typeof window === "undefined") {
      return;
    }
    const el = dropZoneRef.current as unknown as HTMLElement;
    if (!el) {
      return;
    }
    function handleDragOver(event: DragEvent) {
      event.preventDefault();
      event.stopPropagation();
      setIsDragActive(true);
    }
    function handleDragEnter(event: DragEvent) {
      event.preventDefault();
      event.stopPropagation();
      setIsDragActive(true);
    }
    function handleDragLeave(event: DragEvent) {
      event.preventDefault();
      event.stopPropagation();
      setIsDragActive(false);
    }
    function handleDrop(event: DragEvent) {
      event.preventDefault();
      event.stopPropagation();
      setIsDragActive(false);
      const file = event.dataTransfer?.files?.[0];
      if (file) {
        onDropFileRef.current?.(file);
      }
    }
    el.addEventListener("dragover", handleDragOver);
    el.addEventListener("dragenter", handleDragEnter);
    el.addEventListener("dragleave", handleDragLeave);
    el.addEventListener("drop", handleDrop);
    return () => {
      el.removeEventListener("dragover", handleDragOver);
      el.removeEventListener("dragenter", handleDragEnter);
      el.removeEventListener("dragleave", handleDragLeave);
      el.removeEventListener("drop", handleDrop);
    };
  }, []);

  return (
    <View style={[styles.stateCardNeutral, isDarkMode && styles.stateCardNeutralDark]}>
      <Pressable
        ref={dropZoneRef}
        onPress={onPickPdf}
        style={[
          styles.emptyDropZone,
          styles.emptyDropZoneSingleColumn,
          isDarkMode && styles.emptyDropZoneDark,
          isDragActive && styles.emptyDropZoneActive,
          isDarkMode && isDragActive && styles.emptyDropZoneActiveDark,
        ]}
      >
        <Text style={[styles.emptyDropZoneIcon, isDarkMode && styles.emptyDropZoneIconDark]}>⬆</Text>
        <Text style={[styles.emptyDropZoneTitle, isDarkMode && styles.emptyDropZoneTitleDark]}>
          PDF 또는 Markdown 파일을 여기로 끌어놓으세요
        </Text>
        <Text style={[styles.emptyDropZoneBody, isDarkMode && styles.emptyDropZoneBodyDark]}>
          PDF로 제공되는 정부 보도자료를 Markdown으로 바꿉니다. 파일을 올리면 자동으로 변환하고, 결과를 바로 수정하거나 저장할 수 있습니다.
        </Text>
        <View style={[styles.emptyDropZoneBadge, isDarkMode && styles.emptyDropZoneBadgeDark]}>
          <Text style={[styles.emptyDropZoneBadgeText, isDarkMode && styles.emptyDropZoneBadgeTextDark]}>
            Drag & Drop Upload
          </Text>
        </View>
      </Pressable>

      <View style={[styles.emptyDetailDivider, isDarkMode && styles.emptyDetailDividerDark]} />

      <Text style={[styles.markdownIntroTitle, isDarkMode && styles.markdownIntroTitleDark]}>
        Markdown은 문서를 간단한 기호로 적는 방식입니다.
      </Text>
      <Text style={[styles.stateBody, isDarkMode && styles.stateBodyDark]}>
        같은 내용을 복잡한 서식 없이 작성해도 제목, 목록, 강조 같은 모양으로 바로 보여줄 수 있습니다.
      </Text>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.emptyExampleTableScroll}
        style={styles.emptyExampleTableScrollWrap}
      >
        <View style={[styles.emptyExampleTable, isDarkMode && styles.emptyExampleTableDark]}>
          <View style={[styles.emptyExampleRow, styles.emptyExampleHeaderRow, isDarkMode && styles.emptyExampleHeaderRowDark]}>
            <View style={[styles.emptyExampleCell, styles.emptyExampleHeaderCell, isDarkMode && styles.emptyExampleCellDark]}>
              <Text style={[styles.emptyExampleHeaderText, isDarkMode && styles.emptyExampleHeaderTextDark]}>구분</Text>
            </View>
            <View style={[styles.emptyExampleCell, styles.emptyExampleHeaderCell, isDarkMode && styles.emptyExampleCellDark]}>
              <Text style={[styles.emptyExampleHeaderText, isDarkMode && styles.emptyExampleHeaderTextDark]}>소스</Text>
            </View>
            <View style={[styles.emptyExampleCell, styles.emptyExampleHeaderCell, styles.emptyExampleCellLast, isDarkMode && styles.emptyExampleCellDark]}>
              <Text style={[styles.emptyExampleHeaderText, isDarkMode && styles.emptyExampleHeaderTextDark]}>미리보기</Text>
            </View>
          </View>
          <View style={[styles.emptyExampleRow, isDarkMode && styles.emptyExampleRowDark]}>
            <View style={[styles.emptyExampleCell, isDarkMode && styles.emptyExampleCellDark]}>
              <Text style={[styles.emptyExampleLabel, isDarkMode && styles.emptyExampleLabelDark]}>제목</Text>
            </View>
            <View style={[styles.emptyExampleCell, isDarkMode && styles.emptyExampleCellDark]}>
              <Text style={[styles.emptyExampleCode, isDarkMode && styles.emptyExampleCodeDark]}># 보도자료 제목</Text>
            </View>
            <View style={[styles.emptyExampleCell, styles.emptyExampleCellLast, isDarkMode && styles.emptyExampleCellDark]}>
              <Text style={[styles.emptyExamplePreviewTitle, isDarkMode && styles.emptyExamplePreviewTitleDark]}>보도자료 제목</Text>
            </View>
          </View>
          <View style={[styles.emptyExampleRow, isDarkMode && styles.emptyExampleRowDark]}>
            <View style={[styles.emptyExampleCell, isDarkMode && styles.emptyExampleCellDark]}>
              <Text style={[styles.emptyExampleLabel, isDarkMode && styles.emptyExampleLabelDark]}>목록</Text>
            </View>
            <View style={[styles.emptyExampleCell, isDarkMode && styles.emptyExampleCellDark]}>
              <Text style={[styles.emptyExampleCode, isDarkMode && styles.emptyExampleCodeDark]}>- 주요 내용</Text>
            </View>
            <View style={[styles.emptyExampleCell, styles.emptyExampleCellLast, isDarkMode && styles.emptyExampleCellDark]}>
              <Text style={[styles.emptyExamplePreviewText, isDarkMode && styles.emptyExamplePreviewTextDark]}>• 주요 내용</Text>
            </View>
          </View>
          <View style={[styles.emptyExampleRow, isDarkMode && styles.emptyExampleRowDark]}>
            <View style={[styles.emptyExampleCell, isDarkMode && styles.emptyExampleCellDark]}>
              <Text style={[styles.emptyExampleLabel, isDarkMode && styles.emptyExampleLabelDark]}>강조</Text>
            </View>
            <View style={[styles.emptyExampleCell, isDarkMode && styles.emptyExampleCellDark]}>
              <Text style={[styles.emptyExampleCode, isDarkMode && styles.emptyExampleCodeDark]}>**중요 문장**</Text>
            </View>
            <View style={[styles.emptyExampleCell, styles.emptyExampleCellLast, isDarkMode && styles.emptyExampleCellDark]}>
              <Text style={[styles.emptyExamplePreviewText, styles.emptyExamplePreviewStrong, isDarkMode && styles.emptyExamplePreviewTextDark]}>중요 문장</Text>
            </View>
          </View>
          <View style={[styles.emptyExampleRow, isDarkMode && styles.emptyExampleRowDark]}>
            <View style={[styles.emptyExampleCell, isDarkMode && styles.emptyExampleCellDark]}>
              <Text style={[styles.emptyExampleLabel, isDarkMode && styles.emptyExampleLabelDark]}>인용</Text>
            </View>
            <View style={[styles.emptyExampleCell, isDarkMode && styles.emptyExampleCellDark]}>
              <Text style={[styles.emptyExampleCode, isDarkMode && styles.emptyExampleCodeDark]}>{"> 안내 문구"}</Text>
            </View>
            <View style={[styles.emptyExampleCell, styles.emptyExampleCellLast, isDarkMode && styles.emptyExampleCellDark]}>
              <Text style={[styles.emptyExamplePreviewQuote, isDarkMode && styles.emptyExamplePreviewQuoteDark]}>안내 문구</Text>
            </View>
          </View>
          <View style={[styles.emptyExampleRow, styles.emptyExampleRowLast, isDarkMode && styles.emptyExampleRowDark]}>
            <View style={[styles.emptyExampleCell, isDarkMode && styles.emptyExampleCellDark]}>
              <Text style={[styles.emptyExampleLabel, isDarkMode && styles.emptyExampleLabelDark]}>가로줄</Text>
            </View>
            <View style={[styles.emptyExampleCell, isDarkMode && styles.emptyExampleCellDark]}>
              <Text style={[styles.emptyExampleCode, isDarkMode && styles.emptyExampleCodeDark]}>---</Text>
            </View>
            <View style={[styles.emptyExampleCell, styles.emptyExampleCellLast, isDarkMode && styles.emptyExampleCellDark]}>
              <View style={[styles.emptyExamplePreviewRule, isDarkMode && styles.emptyExamplePreviewRuleDark]} />
            </View>
          </View>
        </View>
      </ScrollView>
    </View>
  );
}
