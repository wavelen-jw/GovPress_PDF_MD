import React from "react";
import { Modal, Pressable, Text, TextInput, View } from "react-native";

import { styles } from "../styles";
import type { AppConfig } from "../types";

export function SettingsModal({
  visible,
  draft,
  onChange,
  onClose,
  onSave,
}: {
  visible: boolean;
  draft: AppConfig;
  onChange: (next: AppConfig) => void;
  onClose: () => void;
  onSave: () => void;
}) {
  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.modalBackdrop}>
        <View style={styles.modalCard}>
          <Text style={styles.modalTitle}>서버 설정</Text>
          <Text style={styles.modalHint}>GovPress API 주소와 선택적 API 키를 입력합니다.</Text>
          <TextInput
            value={draft.baseUrl}
            onChangeText={(baseUrl) => onChange({ ...draft, baseUrl })}
            autoCapitalize="none"
            autoCorrect={false}
            style={styles.input}
            placeholder="http://127.0.0.1:8012"
          />
          <TextInput
            value={draft.apiKey}
            onChangeText={(apiKey) => onChange({ ...draft, apiKey })}
            autoCapitalize="none"
            autoCorrect={false}
            style={styles.input}
            placeholder="선택: X-API-Key"
          />
          <View style={styles.modalActions}>
            <Pressable onPress={onClose} style={styles.secondaryButton}>
              <Text style={styles.secondaryButtonLabel}>닫기</Text>
            </Pressable>
            <Pressable onPress={onSave} style={styles.primaryButton}>
              <Text style={styles.primaryButtonLabel}>저장</Text>
            </Pressable>
          </View>
        </View>
      </View>
    </Modal>
  );
}
