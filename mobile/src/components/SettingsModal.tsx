import React, { useEffect, useMemo, useState } from "react";
import { ActivityIndicator, Modal, Pressable, Text, View } from "react-native";

import { PRIMARY_SERVER_KEY, SERVER_FALLBACK_TIMEOUT_MS, SERVER_PRESETS } from "../constants";
import { styles } from "../styles";
import type { AppConfig } from "../types";

type ServerKey = (typeof SERVER_PRESETS)[number]["key"];
type ServerProbeResult = {
  ok: boolean;
  detail: string;
};

function isRetryableProbeFailure(detail: string): boolean {
  const lowered = detail.toLowerCase();
  return (
    lowered.includes("timeout") ||
    lowered.includes("timed out") ||
    lowered.includes("abort") ||
    lowered.includes("fetch") ||
    lowered.includes("load failed") ||
    lowered.includes("network")
  );
}

function formatProbeError(error: unknown): string {
  if (error instanceof DOMException && error.name === "AbortError") {
    return "timeout";
  }
  if (error instanceof Error) {
    const message = error.message.trim();
    return message || error.name || "fetch failed";
  }
  return String(error || "fetch failed");
}

async function probeServerApiReachability(url: string, apiKey: string, timeoutMs: number): Promise<ServerProbeResult> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${url}/v1/policy-briefings/today?date=2026-04-08&_t=${Date.now()}`, {
      signal: controller.signal,
      cache: "no-store",
      headers: apiKey.trim() ? { "X-API-Key": apiKey.trim() } : undefined,
    });
    if (response.ok) {
      return { ok: true, detail: `API HTTP ${response.status}` };
    }
    return { ok: false, detail: `API HTTP ${response.status}` };
  } catch (error) {
    return { ok: false, detail: formatProbeError(error) };
  } finally {
    clearTimeout(timeout);
  }
}

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
  const [serverDetails, setServerDetails] = useState<Record<ServerKey, string>>({
    serverV: "",
    serverW: "",
    serverH: "",
  });
  const [checkingStatus, setCheckingStatus] = useState(false);
  const [lastCheckedAt, setLastCheckedAt] = useState<string>("");

  const selectedKey = useMemo<ServerKey>(() => {
    return SERVER_PRESETS.find((preset) => preset.url === draft.baseUrl)?.key || PRIMARY_SERVER_KEY;
  }, [draft.baseUrl]);

  async function probeServerHealth(url: string, apiKey: string, timeoutMs: number): Promise<ServerProbeResult> {
    const attempts = 3;
    let lastFailure = "unknown";
    for (let attempt = 0; attempt < attempts; attempt += 1) {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), timeoutMs);
      try {
        const response = await fetch(`${url}/health?_t=${Date.now()}_${attempt}`, {
          signal: controller.signal,
          cache: "no-store",
        });
        if (response.ok) {
          return { ok: true, detail: `HTTP ${response.status}` };
        }
        lastFailure = `HTTP ${response.status}`;
        if (attempt === attempts - 1) {
          return { ok: false, detail: lastFailure };
        }
      } catch (error) {
        lastFailure = formatProbeError(error);
        if (attempt === attempts - 1) {
          break;
        }
      } finally {
        clearTimeout(timeout);
      }
    }
    if (isRetryableProbeFailure(lastFailure)) {
      const apiResult = await probeServerApiReachability(url, apiKey, timeoutMs);
      if (apiResult.ok) {
        return apiResult;
      }
    }
    return { ok: false, detail: lastFailure };
  }

  async function refreshServerStatuses(cancelledRef?: { current: boolean }) {
    setCheckingStatus(true);
    setServerStatus({
      serverV: null,
      serverW: null,
      serverH: null,
    });
    setServerDetails({
      serverV: "",
      serverW: "",
      serverH: "",
    });
    const results = await Promise.all(
      SERVER_PRESETS.map(async (preset) => {
        const result = await probeServerHealth(preset.url, draft.apiKey, SERVER_FALLBACK_TIMEOUT_MS);
        return { key: preset.key, ...result };
      }),
    );
    if (cancelledRef?.current) {
      return;
    }
    setServerStatus({
      serverV: results.find((item) => item.key === "serverV")?.ok ?? null,
      serverW: results.find((item) => item.key === "serverW")?.ok ?? null,
      serverH: results.find((item) => item.key === "serverH")?.ok ?? null,
    });
    setServerDetails({
      serverV: results.find((item) => item.key === "serverV")?.detail ?? "",
      serverW: results.find((item) => item.key === "serverW")?.detail ?? "",
      serverH: results.find((item) => item.key === "serverH")?.detail ?? "",
    });
    setLastCheckedAt(new Date().toLocaleTimeString("ko-KR", { hour12: false }));
    setCheckingStatus(false);
  }

  useEffect(() => {
    if (!visible) {
      return;
    }

    const cancelled = { current: false };
    void refreshServerStatuses(cancelled);

    return () => {
      cancelled.current = true;
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
          <Text style={styles.modalHint}>
            여기 표시되는 색상은 서버의 기본 `/health` 응답 기준이며, 정책브리핑 제공기관 상태와는 별도입니다.
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
                    <Text style={styles.settingsStatusText}>
                      {serverStatus[preset.key] === true
                        ? `정상 · ${serverDetails[preset.key]}`
                        : serverStatus[preset.key] === false
                          ? `실패 · ${serverDetails[preset.key]}`
                          : "확인 중"}
                    </Text>
                  </View>
                </Pressable>
              );
            })}
          </View>
          <Text style={styles.modalHint}>기본 서버 2초 내 무응답 시 대체 서버로 자동 전환됩니다.</Text>
          <View style={styles.settingsStatusBox}>
            {checkingStatus ? <ActivityIndicator size="small" color="#7b664f" /> : <View style={styles.settingsStatusSpacer} />}
            <Pressable onPress={() => void refreshServerStatuses()} style={styles.secondaryButton}>
              <Text style={styles.secondaryButtonLabel}>다시 점검</Text>
            </Pressable>
            <Text style={styles.settingsStatusText}>
              {checkingStatus ? "서버 상태 재점검 중" : lastCheckedAt ? `마지막 점검 ${lastCheckedAt}` : "아직 점검 전"}
            </Text>
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
