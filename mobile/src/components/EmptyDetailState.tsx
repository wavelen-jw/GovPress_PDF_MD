import React from "react";
import { Text, View } from "react-native";

import { styles } from "../styles";

export function EmptyDetailState() {
  return (
    <View style={styles.stateCardNeutral}>
      <Text style={styles.stateEyebrow}>선택 대기</Text>
      <Text style={styles.stateTitle}>작업을 선택하면 오른쪽에서 바로 검토를 이어갈 수 있습니다.</Text>
      <Text style={styles.stateBody}>
        최근 작업에서 문서를 고르거나 새 PDF를 업로드하면 상태, 결과 미리보기, Markdown 편집이 이 패널에 순서대로 표시됩니다.
      </Text>
      <View style={styles.emptyDetailChecklist}>
        <Text style={styles.emptyDetailChecklistItem}>1. 왼쪽 목록에서 기존 작업을 선택합니다.</Text>
        <Text style={styles.emptyDetailChecklistItem}>2. 완료된 작업은 바로 미리보기와 차이 보기로 이동합니다.</Text>
        <Text style={styles.emptyDetailChecklistItem}>3. 새 문서는 상단 업로드 버튼으로 추가합니다.</Text>
      </View>
    </View>
  );
}
