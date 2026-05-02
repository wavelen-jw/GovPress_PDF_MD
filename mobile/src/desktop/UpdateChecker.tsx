import { useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { isTauriRuntime } from "../platform/fileio";

// `Update` from @tauri-apps/plugin-updater. Loaded lazily so the PWA bundle
// doesn't pull in updater client code at all.
type UpdateLike = {
  version: string;
  date?: string;
  body?: string;
  downloadAndInstall: (
    onEvent?: (event: { event: string; data?: { contentLength?: number } }) => void,
  ) => Promise<void>;
};

const CHECK_DELAY_MS = 3000;

export function UpdateChecker({ isDarkMode }: { isDarkMode?: boolean }): React.JSX.Element | null {
  const [update, setUpdate] = useState<UpdateLike | null>(null);
  const [installing, setInstalling] = useState(false);
  const [progress, setProgress] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (!isTauriRuntime()) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;
    timer = setTimeout(() => {
      void (async () => {
        try {
          const updater = await import("@tauri-apps/plugin-updater");
          const found = await updater.check();
          if (cancelled || !found) return;
          // Tauri 2's check() resolves to null when no update is available.
          // The returned object also has an `available` field on some
          // versions; treat any non-null result as "update found".
          setUpdate(found as unknown as UpdateLike);
        } catch (e) {
          console.warn("[UpdateChecker] check failed:", e);
        }
      })();
    }, CHECK_DELAY_MS);
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, []);

  if (!update || dismissed) return null;

  const onInstall = async () => {
    if (!update) return;
    setInstalling(true);
    setError(null);
    setProgress("다운로드 준비 중...");
    try {
      await update.downloadAndInstall((event) => {
        if (event.event === "Started") {
          const total = event.data?.contentLength;
          setProgress(total ? `다운로드 중 (${(total / 1024 / 1024).toFixed(1)} MB)` : "다운로드 중...");
        } else if (event.event === "Progress") {
          // Tauri emits frequent progress events; we show a single label
          // rather than a percentage to avoid re-render churn.
          setProgress("다운로드 중...");
        } else if (event.event === "Finished") {
          setProgress("설치 중...");
        }
      });
      setProgress("재시작 중...");
      const proc = await import("@tauri-apps/plugin-process");
      await proc.relaunch();
    } catch (e) {
      const msg = (e as Error)?.message ?? String(e);
      setError(msg);
      setInstalling(false);
      setProgress("");
    }
  };

  const dark = !!isDarkMode;

  return (
    <View
      style={[styles.backdrop, { position: "fixed" as unknown as "absolute" }]}
      pointerEvents="auto"
    >
      <View style={[styles.card, dark && styles.cardDark]}>
        <Text style={[styles.title, dark && styles.titleDark]}>새 버전이 있습니다</Text>
        <Text style={[styles.version, dark && styles.versionDark]}>v{update.version}</Text>
        {update.body ? (
          <Text style={[styles.body, dark && styles.bodyDark]} numberOfLines={8}>
            {update.body}
          </Text>
        ) : null}
        {progress ? (
          <Text style={[styles.progress, dark && styles.progressDark]}>{progress}</Text>
        ) : null}
        {error ? <Text style={styles.error}>오류: {error}</Text> : null}
        <View style={styles.actions}>
          <Pressable
            style={({ pressed }) => [
              styles.button,
              styles.buttonGhost,
              dark && styles.buttonGhostDark,
              pressed && !installing && styles.buttonGhostPressed,
              installing && styles.buttonDisabled,
            ]}
            onPress={() => setDismissed(true)}
            disabled={installing}
          >
            <Text style={[styles.buttonGhostText, dark && styles.buttonGhostTextDark]}>나중에</Text>
          </Pressable>
          <Pressable
            style={({ pressed }) => [
              styles.button,
              styles.buttonPrimary,
              pressed && !installing && styles.buttonPrimaryPressed,
              installing && styles.buttonDisabled,
            ]}
            onPress={onInstall}
            disabled={installing}
          >
            <Text style={styles.buttonPrimaryText}>{installing ? "설치 중..." : "지금 설치"}</Text>
          </Pressable>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(0, 0, 0, 0.45)",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 1000,
  },
  card: {
    width: 420,
    maxWidth: "90%",
    backgroundColor: "#ffffff",
    borderRadius: 10,
    padding: 24,
    shadowColor: "#000",
    shadowOpacity: 0.2,
    shadowRadius: 24,
    shadowOffset: { width: 0, height: 8 },
  },
  cardDark: {
    backgroundColor: "#27272a",
  },
  title: {
    fontSize: 16,
    fontWeight: "600",
    color: "#18181b",
    marginBottom: 4,
  },
  titleDark: {
    color: "#fafafa",
  },
  version: {
    fontSize: 13,
    color: "#71717a",
    marginBottom: 12,
  },
  versionDark: {
    color: "#a1a1aa",
  },
  body: {
    fontSize: 13,
    color: "#3f3f46",
    lineHeight: 18,
    marginBottom: 16,
  },
  bodyDark: {
    color: "#d4d4d8",
  },
  progress: {
    fontSize: 13,
    color: "#3f3f46",
    marginBottom: 12,
  },
  progressDark: {
    color: "#d4d4d8",
  },
  error: {
    fontSize: 13,
    color: "#dc2626",
    marginBottom: 12,
  },
  actions: {
    flexDirection: "row",
    justifyContent: "flex-end",
    gap: 8,
  },
  button: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 6,
    minWidth: 88,
    alignItems: "center",
  },
  buttonGhost: {
    backgroundColor: "transparent",
  },
  buttonGhostDark: {
    backgroundColor: "transparent",
  },
  buttonGhostPressed: {
    backgroundColor: "#f4f4f5",
  },
  buttonGhostText: {
    fontSize: 14,
    color: "#3f3f46",
  },
  buttonGhostTextDark: {
    color: "#d4d4d8",
  },
  buttonPrimary: {
    backgroundColor: "#b75e1f",
  },
  buttonPrimaryPressed: {
    backgroundColor: "#a04f17",
  },
  buttonPrimaryText: {
    fontSize: 14,
    color: "#ffffff",
    fontWeight: "500",
  },
  buttonDisabled: {
    opacity: 0.6,
  },
});
