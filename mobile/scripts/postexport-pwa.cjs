#!/usr/bin/env node
// Post-export step for `expo export --platform web`.
//
// Two modes:
//   default       — patches dist/index.html for PWA install (manifest link,
//                   theme-color, apple-* meta, inline service worker
//                   registration). Used by `npm run export:web`.
//   --desktop     — patches dist/index.html for the Tauri desktop wrapper.
//                   Skips SW registration (assets are bundled in the binary)
//                   and rewrites the absolute /GovPress_PDF_MD/app/_expo/...
//                   bundle path to a relative ./_expo/... path so the file
//                   resolves under tauri://localhost/.

const fs = require("node:fs");
const path = require("node:path");

const argv = process.argv.slice(2);
const desktopMode = argv.includes("--desktop");
const distArgIdx = argv.indexOf("--dist");
const distRel = distArgIdx >= 0 && argv[distArgIdx + 1] ? argv[distArgIdx + 1] : "dist";

const DIST_DIR = path.resolve(__dirname, "..", distRel);
const DIST_INDEX = path.join(DIST_DIR, "index.html");

const PWA_HEAD_INJECTION = `
    <link rel="manifest" href="./manifest.webmanifest">
    <meta name="theme-color" content="#b75e1f">
    <link rel="icon" type="image/png" sizes="32x32" href="./icons/favicon-32.png">
    <link rel="apple-touch-icon" href="./icons/apple-touch-icon.png">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="읽힘">
    <meta name="application-name" content="읽힘">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="format-detection" content="telephone=no">
`;

const PWA_SW_REGISTER = `
    <script>
      if (
        "serviceWorker" in navigator &&
        !location.protocol.startsWith("tauri")
      ) {
        window.addEventListener("load", function () {
          navigator.serviceWorker.register("./sw.js").catch(function (error) {
            console.warn("[pwa] service worker register failed:", error);
          });
        });
      }
    </script>
`;

function patchPwa(html) {
  let out = html;
  if (!out.includes('rel="manifest"')) {
    if (out.includes("</head>")) {
      out = out.replace("</head>", `${PWA_HEAD_INJECTION}  </head>`);
    } else {
      console.warn("[postexport-pwa] no </head> tag found; head injection skipped");
    }
  }
  if (!out.includes("serviceWorker.register")) {
    if (out.includes("</body>")) {
      out = out.replace("</body>", `${PWA_SW_REGISTER}  </body>`);
    } else {
      console.warn("[postexport-pwa] no </body> tag found; SW registration skipped");
    }
  }
  return out;
}

function patchDesktop(html) {
  // Rewrite absolute /GovPress_PDF_MD/app/_expo/... → ./_expo/... so the
  // bundle resolves under tauri://localhost/. Mirrors the python heredoc in
  // .github/workflows/pages.yml that performs the same rewrite for /app/
  // hosting on GitHub Pages.
  let out = html.replace(/(["'])\/GovPress_PDF_MD\/app\//g, "$1./");
  // Defensive: if any other absolute /GovPress_PDF_MD/... refs exist, drop
  // the prefix so they become relative too.
  out = out.replace(/(["'])\/GovPress_PDF_MD\//g, "$1./");
  return out;
}

function patchDesktopBundleAssets(distDir) {
  // Expo's Metro web bundler bakes `experiments.baseUrl` into the JS bundle
  // for dynamic chunk URLs (e.g. /GovPress_PDF_MD/app/_expo/static/js/web/
  // event-*.js). Under tauri://localhost those absolute paths 404, so we
  // strip the prefix from every text asset Tauri ships next to index.html.
  const exts = new Set([".js", ".css", ".map", ".html"]);
  const walk = (dir) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        walk(full);
        continue;
      }
      const ext = path.extname(entry.name).toLowerCase();
      if (!exts.has(ext)) continue;
      const original = fs.readFileSync(full, "utf8");
      if (!original.includes("/GovPress_PDF_MD/")) continue;
      // Keep absolute paths absolute (Tauri serves dist root at /). Match
      // only when the leading "/" is the very first slash of a URL path —
      // i.e. preceded by quote, paren, comma, equals, semicolon, whitespace,
      // or start of string. This skips github.com URLs (https://...) and
      // regex literals (which use escaped \/).
      const replaced = original.replace(
        /(^|[\s"'`,;=()])(\/GovPress_PDF_MD\/app\/)/g,
        "$1/",
      ).replace(
        /(^|[\s"'`,;=()])(\/GovPress_PDF_MD\/)/g,
        "$1/",
      );
      if (replaced !== original) {
        fs.writeFileSync(full, replaced, "utf8");
        console.log(`[postexport-pwa]   rewrote ${path.relative(distDir, full)}`);
      }
    }
  };
  walk(distDir);
}

function main() {
  if (!fs.existsSync(DIST_INDEX)) {
    console.error(`[postexport-pwa] missing ${DIST_INDEX}; did expo export run?`);
    process.exit(1);
  }
  let html = fs.readFileSync(DIST_INDEX, "utf8");
  html = desktopMode ? patchDesktop(html) : patchPwa(html);
  fs.writeFileSync(DIST_INDEX, html, "utf8");
  console.log(
    `[postexport-pwa] patched ${DIST_INDEX} (${desktopMode ? "desktop" : "pwa"} mode)`,
  );
  if (desktopMode) {
    patchDesktopBundleAssets(DIST_DIR);
  }
}

main();
