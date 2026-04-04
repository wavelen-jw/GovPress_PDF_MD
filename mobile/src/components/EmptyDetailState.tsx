import React from "react";
import { ScrollView, Text, View } from "react-native";

import { styles } from "../styles";

export function EmptyDetailState({ isDarkMode = false }: { isDarkMode?: boolean }) {
  return (
    <View style={[styles.stateCardNeutral, isDarkMode && styles.stateCardNeutralDark]}>
      <Text style={[styles.stateTitle, isDarkMode && styles.stateTitleDark]}>PDF로 제공되는 정부 보도자료를 Markdown으로 바꿉니다.</Text>
      <Text style={[styles.stateBody, isDarkMode && styles.stateBodyDark]}>
        PDF를 열면 변환 결과가 이 화면에 바로 나타나고, 필요하면 내용을 수정해서 저장할 수 있습니다.
      </Text>
      <View style={styles.emptyDetailChecklist}>
        <Text style={[styles.emptyDetailChecklistItem, isDarkMode && styles.emptyDetailChecklistItemDark]}>1. 상단에서 PDF, HWPX 또는 Markdown 파일을 엽니다.</Text>
        <Text style={[styles.emptyDetailChecklistItem, isDarkMode && styles.emptyDetailChecklistItemDark]}>2. PDF는 자동으로 Markdown으로 변환됩니다.</Text>
        <Text style={[styles.emptyDetailChecklistItem, isDarkMode && styles.emptyDetailChecklistItemDark]}>3. 결과를 확인하고 바로 수정하거나 저장하면 됩니다.</Text>
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
      <Text style={[styles.stateBody, isDarkMode && styles.stateBodyDark]}>
        Markdown으로 바꾸면 별도 뷰어 프로그램이 없어도 웹브라우저나 일반 문서 편집기에서 읽기 쉽고, AI가 문서 구조를 이해하고 활용하기에도 더 적합합니다.
      </Text>
    </View>
  );
}
