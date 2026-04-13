import React, { useEffect, useMemo, useState } from "react";
import { ActivityIndicator, Modal, Pressable, Text, View } from "react-native";

import { PRIMARY_SERVER_KEY, SERVER_FALLBACK_TIMEOUT_MS, SERVER_PRESETS } from "../constants";
import { styles } from "../styles";
import type { AppConfig } from "../types";

type ServerKey = (typeof SERVER_PRESETS)[number]["key"];

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
  const [serverStatus, setServerStatus] = useState<Record<ServerKey, boolean | null>>({
    serverV: null,
    serverW: null,
    serverH: null,
  });
  const [checkingStatus, setCheckingStatus] = useState(false);

  const selectedKey = useMemo<ServerKey>(() => {
    return SERVER_PRESETS.find((preset) => preset.url === draft.baseUrl)?.key || PRIMARY_SERVER_KEY;
  }, [draft.baseUrl]);

  useEffect(() => {
    if (!visible) {
      return;
    }

    let cancelled = false;
    setCheckingStatus(true);
    setServerStatus({
      serverV: null,
      serverW: null,
      serverH: null,
    });

    const probeAt = Date.now();

    void Promise.all(
      SERVER_PRESETS.map(async (preset) => {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), SERVER_FALLBACK_TIMEOUT_MS);
        try {
          const response = await fetch(`${preset.url}/health?_t=${probeAt}`, {
            signal: controller.signal,
            cache: "no-store",
          });
          return { key: preset.key, ok: response.ok };
        } catch {
          return { key: preset.key, ok: false };
        } finally {
          clearTimeout(timeout);
        }
      }),
    ).then((results) => {
      if (cancelled) {
        return;
      }
      setServerStatus({
        serverV: results.find((item) => item.key === "serverV")?.ok ?? null,
        serverW: results.find((item) => item.key === "serverW")?.ok ?? null,
        serverH: results.find((item) => item.key === "serverH")?.ok ?? null,
      });
      setCheckingStatus(false);
    });

    return () => {
      cancelled = true;
    };
  }, [visible]);

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.modalBackdrop}>
        <View style={styles.modalCard}>
          <Text style={styles.modalTitle}>서버 설정</Text>
          <Text style={styles.modalHint}>
            선택한 서버가 기본 서버가 되며, 다른 서버는 대체 서버로 사용합니다.
          </Text>
          <View style={styles.settingsPresetGroup}>
            {SERVER_PRESETS.map((preset) => {
              const active = selectedKey === preset.key;
              return (
                <Pressable
                  key={preset.key}
                  onPress={() => onChange({ ...draft, baseUrl: preset.url })}
                  style={[styles.settingsPresetButton, active && styles.settingsPresetButtonActive]}
                >
                  <View style={[styles.settingsPresetRadio, active && styles.settingsPresetRadioActive]} />
                  <View style={styles.settingsPresetContent}>
                    <View style={styles.settingsPresetTitleRow}>
                      <View
                        style={[
                          styles.settingsStatusDot,
                          serverStatus[preset.key] === true && styles.settingsStatusDotUp,
                          serverStatus[preset.key] === false && styles.settingsStatusDotDown,
                          serverStatus[preset.key] === null && styles.settingsStatusDotUnknown,
                        ]}
                      />
                      <Text style={[styles.settingsPresetLabel, active && styles.settingsPresetLabelActive]}>{preset.label}</Text>
                      <Text style={[styles.settingsPresetBadge, active && styles.settingsPresetBadgeActive]}>
                        {active ? "기본" : "대체"}
                      </Text>
                    </View>
                    <Text style={[styles.settingsPresetUrl, active && styles.settingsPresetUrlActive]}>{preset.url}</Text>
                  </View>
                </Pressable>
              );
            })}
          </View>
          <Text style={styles.modalHint}>기본 서버 2초 내 무응답 시 대체 서버로 자동 전환됩니다.</Text>
          <View style={styles.settingsStatusBox}>
            {checkingStatus ? <ActivityIndicator size="small" color="#7b664f" /> : <View style={styles.settingsStatusSpacer} />}
          </View>
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
