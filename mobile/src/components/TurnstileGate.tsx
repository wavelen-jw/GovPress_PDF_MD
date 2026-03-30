import React, { useEffect, useRef } from "react";
import { Platform, View } from "react-native";

declare global {
  interface Window {
    turnstile?: {
      render: (container: string | HTMLElement, options: Record<string, unknown>) => string;
      remove?: (widgetId: string) => void;
      reset?: (widgetId?: string) => void;
    };
  }
}

type Props = {
  isDarkMode?: boolean;
  siteKey: string;
  refreshNonce?: number;
  onTokenChange: (token: string | null) => void;
};

export function TurnstileGate({ isDarkMode = false, siteKey, refreshNonce = 0, onTokenChange }: Props): React.JSX.Element | null {
  const widgetIdRef = useRef<string | null>(null);
  useEffect(() => {
    if (Platform.OS !== "web" || typeof window === "undefined" || !siteKey) {
      return;
    }

    const scriptId = "cloudflare-turnstile-script";
    const containerId = "govpress-turnstile";

    function renderWidget() {
      if (!window.turnstile) {
        return;
      }
      const container = document.getElementById(containerId);
      if (!container || container.childNodes.length > 0) {
        return;
      }
      widgetIdRef.current = window.turnstile.render(`#${containerId}`, {
        sitekey: siteKey,
        appearance: "interaction-only",
        callback: (token: string) => onTokenChange(token),
        "expired-callback": () => onTokenChange(null),
        "error-callback": () => onTokenChange(null),
      });
    }

    const existing = document.getElementById(scriptId) as HTMLScriptElement | null;
    if (existing) {
      renderWidget();
    } else {
      const script = document.createElement("script");
      script.id = scriptId;
      script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
      script.async = true;
      script.defer = true;
      script.onload = renderWidget;
      document.head.appendChild(script);
    }

    return () => {
      if (widgetIdRef.current && window.turnstile?.remove) {
        window.turnstile.remove(widgetIdRef.current);
        widgetIdRef.current = null;
      }
    };
  }, [onTokenChange, siteKey]);

  useEffect(() => {
    if (Platform.OS !== "web" || typeof window === "undefined") {
      return;
    }
    if (!refreshNonce) {
      return;
    }
    if (widgetIdRef.current && window.turnstile?.reset) {
      onTokenChange(null);
      window.turnstile.reset(widgetIdRef.current);
    }
  }, [onTokenChange, refreshNonce]);

  if (Platform.OS !== "web" || !siteKey) {
    return null;
  }

  return (
    <View
      style={{
        position: "absolute",
        width: 1,
        height: 1,
        overflow: "hidden",
        opacity: 0,
        pointerEvents: "none",
      }}
    >
      <View nativeID="govpress-turnstile" />
    </View>
  );
}
