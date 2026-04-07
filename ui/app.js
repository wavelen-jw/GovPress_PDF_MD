/* GovPress PDF MD – frontend logic */
'use strict';

// ── HTML Sanitizer ─────────────────────────────────────────
// Python 쪽에서 1차 제거 후, JS에서 2차로 DOM 파싱 기반 검증.
// javascript:/data:/vbscript: URL과 on* 이벤트 핸들러를 제거한다.
const _UNSAFE_URL_RE = /^\s*(?:javascript|data|vbscript)\s*:/i;
function sanitizeHtml(html) {
  const tmp = document.createElement('div');
  tmp.innerHTML = html;
  tmp.querySelectorAll('*').forEach(el => {
    for (const attr of Array.from(el.attributes)) {
      if (/^on\w+$/i.test(attr.name)) {
        el.removeAttribute(attr.name);
      } else if (['href', 'src', 'action'].includes(attr.name.toLowerCase())) {
        if (_UNSAFE_URL_RE.test(attr.value)) {
          el.setAttribute(attr.name, '#');
        }
      }
    }
    if (/^(script|iframe|object|embed|form)$/i.test(el.tagName)) {
      el.remove();
    }
  });
  return tmp.innerHTML;
}

// ── State ──────────────────────────────────────────────────
// All mutable UI state lives here. Read via state.*, mutate via the
// setFile/setHasContent/setFollowCursor helpers so side-effects stay central.
const state = {
  currentFile:  '',   // basename shown in status bar
  currentPath:  '',   // full save path (for tooltip / future use)
  isDirty:      false,
  hasContent:   false,
  previewTimer: null,
  followCursor: true,
};
const PREVIEW_DEBOUNCE_MS = 250;

// ── DOM refs ───────────────────────────────────────────────
const editor       = document.getElementById('editor');
const previewContent = document.getElementById('preview-content');
const welcome      = document.getElementById('welcome');
const dropOverlay  = document.getElementById('drop-overlay');
const statusFile   = document.getElementById('status-file');
const statusMsg    = document.getElementById('status-msg');
const btnSave      = document.getElementById('btn-save');
const btnCopy      = document.getElementById('btn-copy');
const divider      = document.getElementById('divider');
const main         = document.getElementById('main');

// ── State helpers ──────────────────────────────────────────
// Centralise all side-effects that accompany state changes.

function setStatus(msg, type = '') {
  statusMsg.textContent = msg;
  statusMsg.className = type;
}

function setFileLabel(name, dirty, fullPath = '') {
  state.currentFile = name || '';
  state.currentPath = fullPath || name || '';
  state.isDirty = !!dirty;
  statusFile.textContent = name ? `${name}${dirty ? '  ●' : ''}` : '';
  statusFile.title = fullPath || name || '';  // tooltip shows full save path
}

function setHasContent(yes) {
  state.hasContent = yes;
  btnSave.disabled = !yes;
  btnCopy.disabled = !yes;
  welcome.style.display = yes ? 'none' : '';
}

function setFollowCursor(on) {
  state.followCursor = on;
  document.getElementById('follow-cursor').checked = on;
  setStatus(on ? '커서 동기화 켜짐' : '커서 동기화 꺼짐');
}

// ── pywebview API readiness ────────────────────────────────
let _apiReady = (typeof pywebview !== 'undefined' && pywebview.api);

window.addEventListener('pywebviewready', () => {
  _apiReady = true;
  console.log('[GovPress] pywebview API ready');
  pywebview.api.get_version().then(v => {
    document.getElementById('modal-version').textContent = 'v' + v;
  }).catch(() => {});
});

function ensureApi() {
  if (typeof pywebview !== 'undefined' && pywebview.api) {
    _apiReady = true;
    return true;
  }
  setStatus('API 초기화 대기 중… 잠시 후 다시 시도하세요', 'err');
  console.error('[GovPress] pywebview.api not available');
  return false;
}

// ── PDF/HWPX open ──────────────────────────────────────────
document.getElementById('btn-open').addEventListener('click', openPDF);
function openPDF() {
  if (!ensureApi()) return;
  try {
    setStatus('PDF/HWPX 선택 중…', 'busy');
    pywebview.api.open_pdf_dialog();
  } catch (e) {
    setStatus('PDF/HWPX 열기 실패: ' + e.message, 'err');
    console.error('[GovPress] open_pdf_dialog error:', e);
  }
}

// ── MD open ────────────────────────────────────────────────
document.getElementById('btn-open-md').addEventListener('click', openMD);
function openMD() {
  if (!ensureApi()) return;
  try {
    setStatus('MD 선택 중…', 'busy');
    pywebview.api.open_md_dialog();
  } catch (e) {
    setStatus('MD 열기 실패: ' + e.message, 'err');
    console.error('[GovPress] open_md_dialog error:', e);
  }
}

function onMdLoaded(payload) {
  const { markdown, filename, path } = payload;
  editor.value = markdown;
  setFileLabel(filename, false, path);
  setHasContent(true);
  setStatus('MD 열림', 'ok');
  schedulePreview();
}

// ── Conversion callbacks (called from Python) ──────────────
function onConversionSuccess(payload) {
  const { markdown, filename } = payload;
  editor.value = markdown;
  setFileLabel(filename, false);
  setHasContent(true);
  setStatus('변환 완료', 'ok');
  schedulePreview();
}

function onPdfDialogCancelled() {
  setStatus('준비');
}

function onConversionError(msg) {
  setStatus('변환 실패', 'err');
  showError(msg);
}

// ── Save ───────────────────────────────────────────────────
document.getElementById('btn-save').addEventListener('click', saveMarkdown);
async function saveMarkdown() {
  if (!state.hasContent) return;
  if (!ensureApi()) return;
  setStatus('저장 중…', 'busy');
  const result = await pywebview.api.save_markdown(editor.value);
  if (result.saved) {
    setFileLabel(result.name || result.path, false, result.path);
    setStatus('저장 완료', 'ok');
  } else if (result.error) {
    setStatus('저장 실패', 'err');
    showError(result.error);
  } else {
    setStatus('저장 취소');
  }
}

// ── Copy ───────────────────────────────────────────────────
document.getElementById('btn-copy').addEventListener('click', copyMarkdown);
async function copyMarkdown() {
  if (!state.hasContent) return;
  await navigator.clipboard.writeText(editor.value);
  setStatus('클립보드에 복사됨', 'ok');
  setTimeout(() => setStatus('준비'), 1500);
}

// ── Preview rendering ──────────────────────────────────────
editor.addEventListener('input', () => {
  pywebview.api.update_content(editor.value);
  setFileLabel(state.currentFile, true, state.currentPath);
  schedulePreview(true);
});

function schedulePreview(scrollToHighlight = false) {
  clearTimeout(state.previewTimer);
  state.previewTimer = setTimeout(() => renderPreview(scrollToHighlight), PREVIEW_DEBOUNCE_MS);
}

async function renderPreview(scrollToHighlight = false) {
  const content    = editor.value;
  const cursorLine = state.followCursor ? getCurrentLine() : null;
  const html = await pywebview.api.render_markdown(content, cursorLine);
  const safeHtml = sanitizeHtml(html);
  const scrollEl   = document.getElementById('preview-scroll');

  if (state.followCursor && scrollToHighlight) {
    previewContent.innerHTML = safeHtml;
    const highlight = previewContent.querySelector('.cursor-highlight');
    if (highlight) {
      highlight.scrollIntoView({ block: 'center', behavior: 'smooth' });
    }
  } else {
    const savedTop = scrollEl.scrollTop;
    previewContent.innerHTML = safeHtml;
    scrollEl.scrollTop = savedTop;
  }
}

function getCurrentLine() {
  const pos  = editor.selectionStart;
  const text = editor.value;
  const lineStart = text.lastIndexOf('\n', pos - 1) + 1;
  const lineEnd   = text.indexOf('\n', pos);
  return text.slice(lineStart, lineEnd === -1 ? text.length : lineEnd) || null;
}

// cursor sync toggle
document.getElementById('follow-cursor').addEventListener('change', e => {
  state.followCursor = e.target.checked;
  setStatus(state.followCursor ? '커서 동기화 켜짐' : '커서 동기화 꺼짐');
});

// ── View modes ─────────────────────────────────────────────
const modes = { source: 'btn-source', split: 'btn-split', preview: 'btn-preview' };
function setMode(mode) {
  document.body.className = `mode-${mode}`;
  Object.entries(modes).forEach(([m, id]) => {
    document.getElementById(id).classList.toggle('active', m === mode);
  });
  if (mode !== 'source') schedulePreview();
}
document.getElementById('btn-source').addEventListener('click',  () => setMode('source'));
document.getElementById('btn-split').addEventListener('click',   () => setMode('split'));
document.getElementById('btn-preview').addEventListener('click', () => setMode('preview'));

// ── Keyboard shortcuts ──────────────────────────────────────
document.addEventListener('keydown', e => {
  const ctrl = e.ctrlKey || e.metaKey;
  if (ctrl && e.key === 'o') { e.preventDefault(); openPDF(); }
  if (ctrl && e.key === 'm') { e.preventDefault(); openMD(); }
  if (ctrl && e.key === 's') { e.preventDefault(); saveMarkdown(); }
  if (ctrl && e.shiftKey && e.key === 'C') { e.preventDefault(); copyMarkdown(); }
  if (ctrl && e.key === '1') { e.preventDefault(); setMode('source'); }
  if (ctrl && e.key === '2') { e.preventDefault(); setMode('split'); }
  if (ctrl && e.key === '3') { e.preventDefault(); setMode('preview'); }
  if (ctrl && e.shiftKey && e.key === 'F') {
    e.preventDefault();
    setFollowCursor(!state.followCursor);
  }
  if (e.key === 'Escape') closeModal();
});

// Tab key in editor → insert spaces
editor.addEventListener('keydown', e => {
  if (e.key === 'Tab') {
    e.preventDefault();
    const s = editor.selectionStart, end = editor.selectionEnd;
    editor.value = editor.value.substring(0, s) + '    ' + editor.value.substring(end);
    editor.selectionStart = editor.selectionEnd = s + 4;
  }
});

// ── Resizable divider ──────────────────────────────────────
(function () {
  let dragging = false, startX = 0, startLeft = 0;

  divider.addEventListener('mousedown', e => {
    dragging  = true;
    startX    = e.clientX;
    startLeft = document.getElementById('editor-pane').getBoundingClientRect().width;
    divider.classList.add('dragging');
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  });

  document.addEventListener('mousemove', e => {
    if (!dragging) return;
    const totalW  = main.getBoundingClientRect().width - divider.offsetWidth;
    const newLeft = Math.min(Math.max(startLeft + (e.clientX - startX), 180), totalW - 180);
    const pct     = (newLeft / totalW * 100).toFixed(2);
    document.getElementById('editor-pane').style.flex  = `0 0 ${pct}%`;
    document.getElementById('preview-pane').style.flex = `0 0 ${100 - parseFloat(pct)}%`;
  });

  document.addEventListener('mouseup', () => {
    if (!dragging) return;
    dragging = false;
    divider.classList.remove('dragging');
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  });
})();

// ── Drag-and-drop PDF/HWPX ─────────────────────────────────
let _dragCounter = 0;

document.addEventListener('dragenter', e => {
  if (!hasConvertibleDocument(e)) return;
  e.preventDefault();
  _dragCounter++;
  dropOverlay.classList.add('visible');
});
document.addEventListener('dragover',  e => { if (hasConvertibleDocument(e)) e.preventDefault(); });
document.addEventListener('dragleave', () => {
  _dragCounter--;
  if (_dragCounter <= 0) { _dragCounter = 0; dropOverlay.classList.remove('visible'); }
});
document.addEventListener('drop', e => {
  e.preventDefault();
  _dragCounter = 0;
  dropOverlay.classList.remove('visible');

  const file = e.dataTransfer && e.dataTransfer.files[0];
  const name = file && file.name.toLowerCase();
  if (!file || (!name.endsWith('.pdf') && !name.endsWith('.hwpx'))) return;

  // Chromium (Edge WebView2) exposes file.path
  const path = file.path || '';
  if (path) {
    setStatus('변환 중…', 'busy');
    pywebview.api.convert_pdf(path);
  } else {
    // fallback: open dialog
    openPDF();
  }
});

function hasConvertibleDocument(e) {
  const items = e.dataTransfer && e.dataTransfer.items;
  if (!items) return false;
  for (const item of items) {
    if (item.kind !== 'file') continue;
    // item.type is often empty in WebView2/Edge for local files (HWPX reports as
    // application/zip or empty). Accept PDF, known HWPX MIME types, or unknown; reject
    // only when a clearly non-document type is explicit.
    if (!item.type || item.type === 'application/pdf' ||
        item.type === 'application/hwpx' || item.type === 'application/zip') return true;
  }
  return false;
}

// ── Error dialog (simple alert fallback) ───────────────────
function showError(msg) {
  if (pywebview && pywebview.api && pywebview.api.show_error) {
    pywebview.api.show_error(msg);
  } else {
    alert(msg);
  }
}

// ── Info modal ─────────────────────────────────────────────
const modalBackdrop = document.getElementById('modal-backdrop');

document.getElementById('btn-info').addEventListener('click', openModal);
document.getElementById('modal-close').addEventListener('click', closeModal);
modalBackdrop.addEventListener('click', e => {
  if (e.target === modalBackdrop) closeModal();
});

function openModal()  { modalBackdrop.classList.add('open'); }
function closeModal() { modalBackdrop.classList.remove('open'); }

// ── Init ───────────────────────────────────────────────────
setHasContent(false);
setMode('split');
