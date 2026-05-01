#!/usr/bin/env node
// Post-export step for `expo export --platform web`.
// Injects PWA head tags (manifest, theme-color, apple-* meta) into the freshly
// generated dist/index.html. Manifest, service worker, and icons are already
// copied from mobile/public/ to dist/ by Expo's exporter, so we only patch HTML.

const fs = require("node:fs");
const path = require("node:path");

const DIST_INDEX = path.resolve(__dirname, "..", "dist", "index.html");

const HEAD_INJECTION = `
    <link rel="manifest" href="./manifest.webmanifest">
    <meta name="theme-color" content="#143e70">
    <link rel="icon" type="image/png" sizes="32x32" href="./icons/favicon-32.png?v=20260501-logo4">
    <link rel="apple-touch-icon" href="./icons/apple-touch-icon.png?v=20260501-logo4">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="읽힘">
    <meta name="application-name" content="읽힘">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="format-detection" content="telephone=no">
`;

const SW_REGISTER = `
    <script>
      if ("serviceWorker" in navigator) {
        window.addEventListener("load", function () {
          navigator.serviceWorker.register("./sw.js?v=20260501-logo4").catch(function (error) {
            console.warn("[pwa] service worker register failed:", error);
          });
        });
      }
    </script>
`;

function main() {
  if (!fs.existsSync(DIST_INDEX)) {
    console.error(`[postexport-pwa] missing ${DIST_INDEX}; did expo export run?`);
    process.exit(1);
  }
  let html = fs.readFileSync(DIST_INDEX, "utf8");

  if (!html.includes('rel="manifest"')) {
    if (html.includes("</head>")) {
      html = html.replace("</head>", `${HEAD_INJECTION}  </head>`);
    } else {
      console.warn("[postexport-pwa] no </head> tag found; head injection skipped");
    }
  }

  if (!html.includes("serviceWorker.register")) {
    if (html.includes("</body>")) {
      html = html.replace("</body>", `${SW_REGISTER}  </body>`);
    } else {
      console.warn("[postexport-pwa] no </body> tag found; SW registration skipped");
    }
  }

  fs.writeFileSync(DIST_INDEX, html, "utf8");
  console.log("[postexport-pwa] patched", DIST_INDEX);
}

main();
