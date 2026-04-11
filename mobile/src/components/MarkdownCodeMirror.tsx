import React, { useEffect, useRef } from "react";

import CodeMirror from "@uiw/react-codemirror";
import { EditorSelection } from "@codemirror/state";
import { HighlightStyle, syntaxHighlighting } from "@codemirror/language";
import { markdown } from "@codemirror/lang-markdown";
import { EditorView, type ViewUpdate } from "@codemirror/view";
import { dracula } from "@uiw/codemirror-theme-dracula";
import { tags as t } from "@lezer/highlight";

type Props = {
  value: string;
  onChange: (value: string) => void;
  onSelectionChange?: (selection: { start: number; end: number }) => void;
  selection?: { start: number; end: number };
  focusToken?: number;
  height?: string;
};

const appTheme = EditorView.theme({
  "&": {
    backgroundColor: "transparent",
    height: "100%",
  },
  ".cm-scroller": {
    fontFamily: '"D2Coding","Fira Code","Consolas",monospace',
    fontSize: "13px",
    lineHeight: "22px",
    overflowX: "hidden",
    overflowY: "auto",
  },
  ".cm-gutters": {
    backgroundColor: "transparent",
    borderRight: "1px solid rgba(255,255,255,0.1)",
    color: "rgba(255,255,255,0.26)",
  },
  ".cm-lineNumbers .cm-gutterElement": {
    paddingRight: "8px",
  },
  ".cm-content": {
    color: "#f8f8f2",
    caretColor: "#f8f8f2",
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
  },
  ".cm-cursor, .cm-dropCursor": {
    borderLeftColor: "#ff79c6",
  },
  ".cm-selectionBackground, &.cm-focused .cm-selectionBackground, ::selection": {
    backgroundColor: "rgba(255, 121, 198, 0.22)",
  },
  ".cm-activeLine": { backgroundColor: "rgba(255,255,255,0.06)" },
  ".cm-activeLineGutter": { backgroundColor: "rgba(255,255,255,0.06)" },
  ".cm-matchingBracket": {
    backgroundColor: "rgba(139, 233, 253, 0.16)",
    color: "#8be9fd",
  },
});

const markdownHighlightStyle = HighlightStyle.define([
  { tag: t.heading1, color: "#ff79c6", fontWeight: "800" },
  { tag: [t.heading2, t.heading3], color: "#ffb86c", fontWeight: "800" },
  { tag: [t.heading4, t.heading5, t.heading6], color: "#ffd37a", fontWeight: "700" },
  { tag: [t.strong], color: "#ff6e9f", fontWeight: "800" },
  { tag: [t.emphasis], color: "#8be9fd", fontStyle: "italic" },
  { tag: [t.strikethrough], color: "#7f8fa6", textDecoration: "line-through" },
  { tag: [t.link, t.url], color: "#50fa7b", textDecoration: "underline" },
  { tag: [t.monospace, t.literal], color: "#f1fa8c" },
  { tag: [t.quote], color: "#bd93f9" },
  { tag: [t.list, t.separator], color: "#ffb86c" },
  { tag: [t.keyword], color: "#bd93f9" },
  { tag: [t.atom, t.bool], color: "#8be9fd" },
  { tag: [t.string], color: "#f1fa8c" },
  { tag: [t.number], color: "#ffb86c" },
  { tag: [t.comment], color: "#6272a4", fontStyle: "italic" },
]);

const fileDropBlocker = EditorView.domEventHandlers({
  dragover: (event) => {
    if (!event.dataTransfer?.files?.length) {
      return false;
    }
    event.preventDefault();
    return true;
  },
  drop: (event) => {
    if (!event.dataTransfer?.files?.length) {
      return false;
    }
    event.preventDefault();
    return true;
  },
});

export function MarkdownCodeMirror({
  value,
  onChange,
  onSelectionChange,
  selection,
  focusToken,
  height = "100%",
}: Props) {
  const viewRef = useRef<EditorView | null>(null);

  useEffect(() => {
    const view = viewRef.current;
    if (!view || !selection) {
      return;
    }
    const currentSelection = view.state.selection.main;
    if (currentSelection.from === selection.start && currentSelection.to === selection.end) {
      return;
    }
    view.dispatch({
      selection: EditorSelection.create([
        EditorSelection.range(selection.start, selection.end),
      ]),
      scrollIntoView: true,
    });
  }, [selection?.end, selection?.start]);

  useEffect(() => {
    if (!viewRef.current) {
      return;
    }
    viewRef.current.focus();
  }, [focusToken]);

  function handleUpdate(viewUpdate: ViewUpdate): void {
    if (!onSelectionChange) {
      return;
    }
    if (!viewUpdate.selectionSet && !viewUpdate.docChanged) {
      return;
    }
    const main = viewUpdate.state.selection.main;
    onSelectionChange({ start: main.from, end: main.to });
  }

  return (
    <CodeMirror
      value={value}
      height={height}
      theme={dracula}
      extensions={[markdown(), syntaxHighlighting(markdownHighlightStyle), EditorView.lineWrapping, appTheme, fileDropBlocker]}
      onChange={onChange}
      onUpdate={handleUpdate}
      onCreateEditor={(view) => {
        viewRef.current = view;
      }}
      style={{
        fontSize: 13,
        fontFamily: '"D2Coding","Fira Code","Consolas",monospace',
        flex: 1,
        minHeight: 0,
      }}
      basicSetup={{
        lineNumbers: true,
        foldGutter: false,
        dropCursor: false,
        allowMultipleSelections: false,
        indentOnInput: false,
      }}
    />
  );
}
