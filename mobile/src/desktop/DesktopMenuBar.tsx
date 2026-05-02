import { useCallback, useEffect, useRef, useState } from "react";
import { Platform, Pressable, StyleSheet, Text, View } from "react-native";

import { isTauriRuntime } from "../platform/fileio";

type MenuEntry =
  | { kind: "item"; id: string; label: string; shortcut?: string }
  | { kind: "separator"; id: string };

const MENU_ENTRIES: MenuEntry[] = [
  { kind: "item", id: "menu://open-file", label: "열기...", shortcut: "Ctrl+O" },
  { kind: "item", id: "menu://open-briefings", label: "정책브리핑 열기...", shortcut: "Ctrl+B" },
  { kind: "separator", id: "sep1" },
  { kind: "item", id: "menu://save-file", label: "Markdown 저장...", shortcut: "Ctrl+S" },
  { kind: "item", id: "menu://copy-markdown", label: "Markdown 클립보드 복사", shortcut: "Ctrl+Shift+C" },
  { kind: "separator", id: "sep2" },
  { kind: "item", id: "menu://reload", label: "새로 고침", shortcut: "Ctrl+R" },
  { kind: "item", id: "menu://about", label: "정보" },
  { kind: "item", id: "menu://open-github", label: "GitHub 저장소 열기" },
  { kind: "separator", id: "sep3" },
  { kind: "item", id: "menu:quit", label: "종료" },
];

async function dispatch(id: string): Promise<void> {
  if (id === "menu:quit") {
    try {
      const win = await import("@tauri-apps/api/window");
      await win.getCurrentWindow().close();
    } catch (error) {
      console.warn("[DesktopMenuBar] quit failed:", error);
    }
    return;
  }
  try {
    const event = await import("@tauri-apps/api/event");
    await event.emit(id);
  } catch (error) {
    console.warn(`[DesktopMenuBar] emit ${id} failed:`, error);
  }
}

export function DesktopMenuBar({ isDarkMode }: { isDarkMode?: boolean }): React.JSX.Element | null {
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<View | null>(null);

  const handleSelect = useCallback((id: string) => {
    setOpen(false);
    void dispatch(id);
  }, []);

  // Keyboard shortcuts. The native menu used to provide these via accelerators;
  // now we register them ourselves on the document level so they work whether
  // the dropdown is open or not.
  useEffect(() => {
    if (Platform.OS !== "web" || typeof document === "undefined") return;
    const onKey = (e: KeyboardEvent) => {
      if (!(e.ctrlKey || e.metaKey)) return;
      const key = e.key.toLowerCase();
      let id: string | null = null;
      if (e.shiftKey && key === "c") id = "menu://copy-markdown";
      else if (!e.shiftKey && key === "o") id = "menu://open-file";
      else if (!e.shiftKey && key === "s") id = "menu://save-file";
      else if (!e.shiftKey && key === "b") id = "menu://open-briefings";
      else if (!e.shiftKey && key === "r") id = "menu://reload";
      if (id) {
        e.preventDefault();
        void dispatch(id);
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  // Close dropdown on outside click.
  useEffect(() => {
    if (!open || Platform.OS !== "web" || typeof document === "undefined") return;
    const onClick = (e: MouseEvent) => {
      const target = e.target as Node | null;
      const node = dropdownRef.current as unknown as HTMLElement | null;
      if (node && target && !node.contains(target)) {
        setOpen(false);
      }
    };
    // Defer to next tick so the click that opened the menu doesn't immediately close it.
    const t = setTimeout(() => document.addEventListener("mousedown", onClick), 0);
    return () => {
      clearTimeout(t);
      document.removeEventListener("mousedown", onClick);
    };
  }, [open]);

  if (!isTauriRuntime()) return null;

  const dark = !!isDarkMode;
  const navBack = () => {
    if (typeof window !== "undefined") window.history.back();
  };
  const navForward = () => {
    if (typeof window !== "undefined") window.history.forward();
  };

  // The whole bar acts as the OS title bar (decorations: false in
  // tauri.conf.json). Buttons are interactive; the empty middle region
  // carries the data-tauri-drag-region attribute so users can drag the
  // window from there. Window controls (min / max / close) live on the
  // far right and replace the OS-supplied ones we just hid.
  const minimizeWindow = async () => {
    try {
      const win = await import("@tauri-apps/api/window");
      await win.getCurrentWindow().minimize();
    } catch (e) {
      console.warn("[DesktopMenuBar] minimize failed:", e);
    }
  };
  const toggleMaximize = async () => {
    try {
      const win = await import("@tauri-apps/api/window");
      await win.getCurrentWindow().toggleMaximize();
    } catch (e) {
      console.warn("[DesktopMenuBar] toggleMaximize failed:", e);
    }
  };
  const closeWindow = async () => {
    try {
      const win = await import("@tauri-apps/api/window");
      await win.getCurrentWindow().close();
    } catch (e) {
      console.warn("[DesktopMenuBar] close failed:", e);
    }
  };

  return (
    <View style={[styles.bar, dark && styles.barDark]}>
      <Pressable
        style={({ pressed }) => [styles.iconButton, pressed && styles.iconButtonPressed, dark && styles.iconButtonDark]}
        onPress={() => setOpen((v) => !v)}
        accessibilityLabel="메뉴 열기"
        accessibilityRole="button"
      >
        <Text style={[styles.iconGlyph, dark && styles.iconGlyphDark]}>≡</Text>
      </Pressable>
      <Pressable
        style={({ pressed }) => [styles.iconButton, pressed && styles.iconButtonPressed, dark && styles.iconButtonDark]}
        onPress={navBack}
        accessibilityLabel="뒤로"
        accessibilityRole="button"
      >
        <Text style={[styles.iconGlyph, dark && styles.iconGlyphDark]}>←</Text>
      </Pressable>
      <Pressable
        style={({ pressed }) => [styles.iconButton, pressed && styles.iconButtonPressed, dark && styles.iconButtonDark]}
        onPress={navForward}
        accessibilityLabel="앞으로"
        accessibilityRole="button"
      >
        <Text style={[styles.iconGlyph, dark && styles.iconGlyphDark]}>→</Text>
      </Pressable>
      <View
        // RN Web converts dataSet keys to data-* attributes; Tauri's drag
        // region detector keys off the attribute presence.
        // @ts-expect-error -- web-only prop forwarded by react-native-web
        dataSet={{ tauriDragRegion: "" }}
        style={styles.dragArea}
      />
      <Pressable
        style={({ pressed }) => [styles.controlButton, pressed && styles.iconButtonPressed]}
        onPress={() => void minimizeWindow()}
        accessibilityLabel="창 최소화"
        accessibilityRole="button"
      >
        <Text style={[styles.controlGlyph, dark && styles.iconGlyphDark]}>—</Text>
      </Pressable>
      <Pressable
        style={({ pressed }) => [styles.controlButton, pressed && styles.iconButtonPressed]}
        onPress={() => void toggleMaximize()}
        accessibilityLabel="창 크기 전환"
        accessibilityRole="button"
      >
        <Text style={[styles.controlGlyph, dark && styles.iconGlyphDark]}>▢</Text>
      </Pressable>
      <Pressable
        style={({ pressed }) => [styles.controlButton, pressed && styles.controlButtonClosePressed]}
        onPress={() => void closeWindow()}
        accessibilityLabel="창 닫기"
        accessibilityRole="button"
      >
        {({ pressed }) => (
          <Text
            style={[
              styles.controlGlyph,
              styles.controlGlyphClose,
              dark && !pressed && styles.iconGlyphDark,
              pressed && styles.controlGlyphClosePressed,
            ]}
          >
            ✕
          </Text>
        )}
      </Pressable>
      {open ? (
        <View
          ref={(node) => {
            dropdownRef.current = node;
          }}
          style={[styles.dropdown, dark && styles.dropdownDark]}
        >
          {MENU_ENTRIES.map((entry) =>
            entry.kind === "separator" ? (
              <View key={entry.id} style={[styles.separator, dark && styles.separatorDark]} />
            ) : (
              <Pressable
                key={entry.id}
                style={({ pressed }) => [
                  styles.dropdownItem,
                  pressed && (dark ? styles.dropdownItemPressedDark : styles.dropdownItemPressed),
                ]}
                onPress={() => handleSelect(entry.id)}
              >
                <Text style={[styles.dropdownLabel, dark && styles.dropdownLabelDark]}>{entry.label}</Text>
                {entry.shortcut ? (
                  <Text style={[styles.dropdownShortcut, dark && styles.dropdownShortcutDark]}>{entry.shortcut}</Text>
                ) : null}
              </Pressable>
            ),
          )}
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  bar: {
    flexDirection: "row",
    alignItems: "center",
    height: 36,
    paddingHorizontal: 4,
    backgroundColor: "#f4f4f5",
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: "#d4d4d8",
    zIndex: 100,
  },
  barDark: {
    backgroundColor: "#18181b",
    borderBottomColor: "#3f3f46",
  },
  iconButton: {
    width: 32,
    height: 28,
    marginHorizontal: 1,
    borderRadius: 4,
    alignItems: "center",
    justifyContent: "center",
  },
  iconButtonPressed: {
    backgroundColor: "#e4e4e7",
  },
  iconButtonDark: {
    // base; pressed handled below via separate selector if needed
  },
  iconGlyph: {
    fontSize: 18,
    color: "#3f3f46",
    lineHeight: 20,
  },
  iconGlyphDark: {
    color: "#d4d4d8",
  },
  dragArea: {
    flex: 1,
    height: "100%",
    // Empty filler whose only purpose is to host the
    // data-tauri-drag-region attribute. Cursor stays default; the OS
    // window manager handles the drag once Tauri starts it.
  },
  controlButton: {
    width: 44,
    height: 36,
    alignItems: "center",
    justifyContent: "center",
  },
  controlButtonClosePressed: {
    backgroundColor: "#dc2626",
  },
  controlGlyph: {
    fontSize: 14,
    color: "#3f3f46",
    lineHeight: 16,
  },
  controlGlyphClose: {
    fontSize: 12,
  },
  controlGlyphClosePressed: {
    color: "#ffffff",
  },
  dropdown: {
    position: "absolute",
    top: 36,
    left: 4,
    minWidth: 240,
    backgroundColor: "#ffffff",
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "#d4d4d8",
    borderRadius: 6,
    paddingVertical: 4,
    shadowColor: "#000",
    shadowOpacity: 0.12,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 4 },
    elevation: 6,
    zIndex: 101,
  },
  dropdownDark: {
    backgroundColor: "#27272a",
    borderColor: "#3f3f46",
  },
  dropdownItem: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  dropdownItemPressed: {
    backgroundColor: "#e4e4e7",
  },
  dropdownItemPressedDark: {
    backgroundColor: "#3f3f46",
  },
  dropdownLabel: {
    fontSize: 14,
    color: "#18181b",
  },
  dropdownLabelDark: {
    color: "#fafafa",
  },
  dropdownShortcut: {
    fontSize: 12,
    color: "#71717a",
    marginLeft: 24,
  },
  dropdownShortcutDark: {
    color: "#a1a1aa",
  },
  separator: {
    height: StyleSheet.hairlineWidth,
    marginVertical: 4,
    backgroundColor: "#e4e4e7",
  },
  separatorDark: {
    backgroundColor: "#3f3f46",
  },
});
