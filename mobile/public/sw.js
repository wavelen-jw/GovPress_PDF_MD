// 읽힘 PWA service worker
// Strategy:
//   - App shell (HTML/JS/CSS, manifest, icons) → cache-first, refresh in background.
//   - All API calls (/v1/*) → network-only. Conversion needs the live server; never serve stale.
//   - Other GET requests → network-first with cache fallback (covers static assets fetched at runtime).
// Bumping CACHE_VERSION invalidates old caches on next activate.

const CACHE_VERSION = "v6";
const APP_SHELL_CACHE = `readhim-app-shell-${CACHE_VERSION}`;
const RUNTIME_CACHE = `readhim-runtime-${CACHE_VERSION}`;
const SHARED_MARKDOWN_URL = "./shared-markdown";

const APP_SHELL_URLS = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/icon-192-maskable.png",
  "./icons/icon-512-maskable.png",
  "./icons/apple-touch-icon.png",
  "./icons/favicon-32.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(APP_SHELL_CACHE).then((cache) =>
      cache.addAll(APP_SHELL_URLS).catch((error) => {
        console.warn("[sw] app shell precache partial failure:", error);
      }),
    ),
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== APP_SHELL_CACHE && key !== RUNTIME_CACHE)
          .map((key) => caches.delete(key)),
      ),
    ),
  );
  self.clients.claim();
});

function isApiRequest(url) {
  return url.pathname.startsWith("/v1/") || url.pathname === "/health";
}

function isShareTargetRequest(url) {
  return url.searchParams.get("shareTarget") === "1";
}

function isSharedMarkdownRequest(url) {
  return url.pathname.endsWith("/shared-markdown");
}

function isAppShellRequest(request, url) {
  if (request.mode === "navigate") {
    return true;
  }
  const path = url.pathname;
  return (
    path.endsWith("/") ||
    path.endsWith("/index.html") ||
    path.endsWith("/manifest.webmanifest") ||
    path.includes("/icons/")
  );
}

self.addEventListener("fetch", (event) => {
  const request = event.request;
  let url;
  try {
    url = new URL(request.url);
  } catch {
    return;
  }

  if (request.method === "POST" && isShareTargetRequest(url)) {
    event.respondWith(handleShareTargetPost(request));
    return;
  }

  if (request.method !== "GET") {
    return;
  }

  if (isApiRequest(url)) {
    return;
  }

  if (isSharedMarkdownRequest(url)) {
    event.respondWith(caches.match(SHARED_MARKDOWN_URL).then((cached) => cached || Response.error()));
    return;
  }

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(APP_SHELL_CACHE).then((cache) => cache.put(request, copy)).catch(() => {});
          return response;
        })
        .catch(() => caches.match("./index.html").then((cached) => cached || Response.error())),
    );
    return;
  }

  if (isAppShellRequest(request, url)) {
    event.respondWith(
      caches.match(request).then((cached) => {
        const network = fetch(request)
          .then((response) => {
            const copy = response.clone();
            caches.open(APP_SHELL_CACHE).then((cache) => cache.put(request, copy)).catch(() => {});
            return response;
          })
          .catch(() => cached || Response.error());
        return cached || network;
      }),
    );
    return;
  }

  if (url.origin === self.location.origin) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response && response.ok) {
            const copy = response.clone();
            caches.open(RUNTIME_CACHE).then((cache) => cache.put(request, copy)).catch(() => {});
          }
          return response;
        })
        .catch(() => caches.match(request).then((cached) => cached || Response.error())),
    );
  }
});

async function handleShareTargetPost(request) {
  const formData = await request.formData();
  const sharedFiles = formData.getAll("shared_files");
  const sharedFile = sharedFiles.find((value) => value instanceof File);
  const sharedText = formData.get("shared_text");
  const sharedTitle = formData.get("shared_title");

  let body = "";
  let fileName = "shared.md";
  if (sharedFile) {
    body = await sharedFile.text();
    fileName = sharedFile.name || fileName;
  } else if (typeof sharedText === "string" && sharedText.trim()) {
    body = sharedText;
    fileName = typeof sharedTitle === "string" && sharedTitle.trim() ? `${sharedTitle.trim()}.md` : fileName;
  }

  if (body) {
    const cache = await caches.open(RUNTIME_CACHE);
    await cache.put(
      SHARED_MARKDOWN_URL,
      new Response(body, {
        headers: {
          "content-type": "text/markdown; charset=utf-8",
          "x-readhim-file-name": encodeURIComponent(fileName),
        },
      }),
    );
  }

  return Response.redirect("./?editor=1&sharedFile=1", 303);
}

self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});
