import React, { useEffect } from "react";
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
  onTokenChange: (token: string | null) => void;
};

export function TurnstileGate({ isDarkMode = false, siteKey, onTokenChange }: Props): React.JSX.Element | null {
  useEffect(() => {
    if (Platform.OS !== "web" || typeof window === "undefined" || !siteKey) {
      return;
    }

    const scriptId = "cloudflare-turnstile-script";
    const containerId = "govpress-turnstile";
    let widgetId: string | null = null;

    function renderWidget() {
      if (!window.turnstile) {
        return;
      }
      const container = document.getElementById(containerId);
      if (!container || container.childNodes.length > 0) {
        return;
      }
      widgetId = window.turnstile.render(`#${containerId}`, {
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
      if (widgetId && window.turnstile?.remove) {
        window.turnstile.remove(widgetId);
      }
    };
  }, [onTokenChange, siteKey]);

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
