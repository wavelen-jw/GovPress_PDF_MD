import React from "react";
import { ScrollView, Text, View } from "react-native";

import { styles } from "../styles";

export function EmptyDetailState({ isDarkMode = false }: { isDarkMode?: boolean }) {
  return (
    <View style={[styles.stateCardNeutral, isDarkMode && styles.stateCardNeutralDark]}>
      <View style={[styles.emptyDropZone, isDarkMode && styles.emptyDropZoneDark]}>
        <Text style={[styles.emptyDropZoneEyebrow, isDarkMode && styles.emptyDropZoneEyebrowDark]}>DRAG AND DROP</Text>
        <Text style={[styles.emptyDropZoneTitle, isDarkMode && styles.emptyDropZoneTitleDark]}>파일을 여기로 끌어 놓아 바로 변환하세요</Text>
      </View>
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
