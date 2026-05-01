import React, { useMemo, useState } from "react";
import { Image, LayoutChangeEvent, Linking, Platform, ScrollView, Text, View, type ViewStyle } from "react-native";

import { styles } from "../styles";

type TableAlign = "left" | "center" | "right";

type TableColumnWidth = {
  minWidth: number;
  preferredWidth: number;
  flexGrow: number;
};

type ListItem = {
  children: Block[];
  checked?: boolean;
};

type Block =
  | { type: "heading"; level: number; text: string }
  | { type: "paragraph"; text: string }
  | { type: "blockquote"; children: Block[]; level: number }
  | { type: "list"; ordered: boolean; level: number; start?: number; loose: boolean; items: ListItem[] }
  | { type: "image"; alt: string; src: string }
  | { type: "table"; headers: string[]; aligns: TableAlign[]; rows: string[][] }
  | { type: "html_table"; headers: string[]; rows: string[][]; rawHtml: string }
  | { type: "rule" }
  | { type: "code"; language: string | null; lines: string[] };

export type MarkdownBlockRange = {
  start: number;
  end: number;
};

const MARKDOWN_INDENT_UNIT = 16;

function markdownIndent(level: number): ViewStyle {
  return { marginLeft: MARKDOWN_INDENT_UNIT * (Math.max(0, level) + 1) };
}

function markdownListIndent(level: number, inQuote: boolean): ViewStyle {
  if (inQuote) {
    return { marginLeft: MARKDOWN_INDENT_UNIT * Math.max(0, level) };
  }
  return markdownIndent(level);
}

function isEscaped(value: string, index: number): boolean {
  let slashCount = 0;
  for (let cursor = index - 1; cursor >= 0 && value[cursor] === "\\"; cursor -= 1) {
    slashCount += 1;
  }
  return slashCount % 2 === 1;
}

function splitTableRow(line: string): string[] {
  let source = line.trim();
  if (source.startsWith("|")) {
    source = source.slice(1);
  }
  if (source.endsWith("|") && !isEscaped(source, source.length - 1)) {
    source = source.slice(0, -1);
  }

  const cells: string[] = [];
  let current = "";
  let inCode = false;
  for (let index = 0; index < source.length; index += 1) {
    const char = source[index];
    if (char === "`" && !isEscaped(source, index)) {
      inCode = !inCode;
    }
    if (char === "|" && !inCode && !isEscaped(source, index)) {
      cells.push(current);
      current = "";
      continue;
    }
    current += char;
  }
  cells.push(current);

  return cells.map((cell) => cell.trim().replace(/\\\|/g, "|").replace(/<br\s*\/?>/gi, "\n"));
}

function isTableDivider(line: string): boolean {
  const cells = splitTableRow(line);
  return cells.length > 0 && cells.every((cell) => /^:?-{3,}:?$/.test(cell));
}

function parseTableAlignments(line: string): TableAlign[] {
  return splitTableRow(line).map((cell) => {
    const trimmed = cell.trim();
    const starts = trimmed.startsWith(":");
    const ends = trimmed.endsWith(":");
    if (starts && ends) {
      return "center";
    }
    if (ends) {
      return "right";
    }
    return "left";
  });
}

function estimateColumnCharacterWidth(value: string): number {
  return value
    .split("\n")
    .map((part) => part.trim().length)
    .reduce((max, current) => Math.max(max, current), 0);
}

function computeTableColumnWidths(headers: string[], rows: string[][], columnCount: number): TableColumnWidth[] {
  const minimum = 84;
  const maximum = 240;

  return Array.from({ length: columnCount }).map((_, columnIndex) => {
    const samples = [headers[columnIndex] || "", ...rows.map((row) => row[columnIndex] || "")];
    const maxChars = samples.reduce((max, cell) => Math.max(max, estimateColumnCharacterWidth(cell)), 0);
    const normalizedChars = Math.max(6, Math.min(36, maxChars));
    return {
      minWidth: minimum,
      preferredWidth: Math.min(maximum, Math.max(minimum, Math.round(normalizedChars * 9 + 28))),
      flexGrow: normalizedChars,
    };
  });
}

function decodeHtmlEntities(text: string): string {
  return text
    .replace(/&nbsp;/gi, " ")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/&amp;/gi, "&")
    .replace(/&quot;/gi, '"')
    .replace(/&#39;/gi, "'");
}

function stripHtmlTags(text: string): string {
  return decodeHtmlEntities(text.replace(/<br\s*\/?>/gi, "\n").replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim());
}

function extractHtmlTableCells(rowHtml: string, tagName: "th" | "td"): string[] {
  const pattern = new RegExp(`<${tagName}\\b[^>]*>([\\s\\S]*?)<\\/${tagName}>`, "gi");
  const cells: string[] = [];
  let match = pattern.exec(rowHtml);
  while (match) {
    cells.push(stripHtmlTags(match[1]));
    match = pattern.exec(rowHtml);
  }
  return cells;
}

function parseHtmlTableBlock(tableHtml: string): { headers: string[]; rows: string[][]; rawHtml: string } | null {
  const rowPattern = /<tr\b[^>]*>([\s\S]*?)<\/tr>/gi;
  const rows: string[][] = [];
  let headers: string[] = [];
  let rowMatch = rowPattern.exec(tableHtml);

  while (rowMatch) {
    const rowHtml = rowMatch[1];
    const headerCells = extractHtmlTableCells(rowHtml, "th");
    const bodyCells = extractHtmlTableCells(rowHtml, "td");

    if (!headers.length && headerCells.length) {
      headers = headerCells;
    } else if (bodyCells.length) {
      rows.push(bodyCells);
    } else if (headerCells.length) {
      rows.push(headerCells);
    }

    rowMatch = rowPattern.exec(tableHtml);
  }

  if (!headers.length && rows.length) {
    headers = rows.shift() || [];
  }

  if (!headers.length) {
    return null;
  }

  return { headers, rows, rawHtml: tableHtml };
}

function buildHtmlTableDocument(tableHtml: string, isDarkMode: boolean, frameId: string): string {
  const background = isDarkMode ? "#241d18" : "#fffdf8";
  const foreground = isDarkMode ? "#f3e5d4" : "#2f2318";
  const border = isDarkMode ? "#5d4b3d" : "#d8c4ab";
  const headerBackground = isDarkMode ? "#3b3028" : "#f4e6d3";
  const cellBackground = isDarkMode ? "#2d241f" : "#fffdf8";

  return `<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      :root {
        color-scheme: ${isDarkMode ? "dark" : "light"};
      }
      html, body {
        margin: 0;
        padding: 0;
        background: ${background};
        color: ${foreground};
        font-family: "Pretendard GOV Variable", "Pretendard GOV", -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
      }
      body {
        padding: 0;
      }
      table {
        width: 100%;
        border-collapse: collapse;
        table-layout: auto;
        background: ${cellBackground};
      }
      th, td {
        border: 1px solid ${border};
        padding: 10px 12px;
        vertical-align: top;
        text-align: left;
        line-height: 1.5;
        font-size: 14px;
        word-break: break-word;
        white-space: pre-wrap;
      }
      th {
        background: ${headerBackground};
        font-weight: 700;
      }
    </style>
  </head>
  <body>
    ${tableHtml}
    <script>
      (function() {
        function postHeight() {
          var height = Math.max(
            document.body ? document.body.scrollHeight : 0,
            document.documentElement ? document.documentElement.scrollHeight : 0
          );
          window.parent.postMessage({ source: "govpress-html-table", id: "${frameId}", height: height }, "*");
        }
        window.addEventListener("load", postHeight);
        window.addEventListener("resize", postHeight);
        postHeight();
      })();
    </script>
  </body>
</html>`;
}

function HtmlTableFrame({
  html,
  isDarkMode = false,
  minWidth,
}: {
  html: string;
  isDarkMode?: boolean;
  minWidth?: number;
}) {
  const frameId = useMemo(() => `govpress-table-${Math.random().toString(36).slice(2)}`, []);
  const [height, setHeight] = useState(160);

  if (Platform.OS !== "web" || typeof window === "undefined") {
    return null;
  }

  React.useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (
        !event.data ||
        typeof event.data !== "object" ||
        event.data.source !== "govpress-html-table" ||
        event.data.id !== frameId
      ) {
        return;
      }
      const nextHeight = Number(event.data.height);
      if (Number.isFinite(nextHeight) && nextHeight > 0) {
        setHeight(Math.max(120, Math.ceil(nextHeight)));
      }
    };

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [frameId]);

  return (
    <View style={[styles.markdownHtmlFrameWrap, isDarkMode && styles.markdownHtmlFrameWrapDark]}>
      {React.createElement("iframe", {
        key: frameId,
        title: frameId,
        srcDoc: buildHtmlTableDocument(html, isDarkMode, frameId),
        style: {
          width: minWidth ? `${Math.max(minWidth, 320)}px` : "100%",
          height,
          border: "0",
          display: "block",
          backgroundColor: isDarkMode ? "#241d18" : "#fffdf8",
        },
        sandbox: "allow-scripts",
      })}
    </View>
  );
}

function textAlignStyle(align: TableAlign) {
  if (align === "center") {
    return styles.markdownTableTextCenter;
  }
  if (align === "right") {
    return styles.markdownTableTextRight;
  }
  return styles.markdownTableTextLeft;
}

function getListBullet(level: number, ordered: boolean, itemIndex: number, orderNumber?: number): string {
  if (ordered) {
    return `${orderNumber ?? itemIndex + 1}.`;
  }
  if (level <= 0) {
    return "•";
  }
  if (level === 1) {
    return "-";
  }
  return "◦";
}

function getListMarker(line: string) {
  return line.match(/^(\s*)((?:[-+])|(?:\d+\.))\s+(?:\[( |x|X)\]\s+)?(.*)$/);
}

function isBlockStart(line: string, nextLine?: string): boolean {
  const trimmed = line.trim();
  return (
    /^(#{1,6})\s+/.test(trimmed) ||
    /^(\s*)>\s?/.test(line) ||
    /^!\[([^\]]*)\]\(([^)]+)\)$/.test(trimmed) ||
    /^<table\b/i.test(trimmed) ||
    (trimmed.includes("|") && !!nextLine && isTableDivider(nextLine.trim())) ||
    /^[-+]\s+\[( |x|X)\]\s+/.test(trimmed) ||
    /^(\d+\.|[-+])\s+/.test(trimmed) ||
    /^(-{3,}|\*{3,}|_{3,})$/.test(trimmed) ||
    /^(```|~~~)/.test(trimmed)
  );
}

function stripIndent(line: string, count: number): string {
  let remaining = count;
  let cursor = 0;
  while (cursor < line.length && remaining > 0) {
    if (line[cursor] === " ") {
      cursor += 1;
      remaining -= 1;
      continue;
    }
    if (line[cursor] === "\t") {
      cursor += 1;
      remaining -= 2;
      continue;
    }
    break;
  }
  return line.slice(cursor);
}

function parseInlineUrl(value: string): string {
  return value.replace(/[),.;:!?]+$/, "");
}

function openExternalLink(url: string): void {
  if (Platform.OS === "web" && typeof window !== "undefined") {
    window.open(url, "_blank", "noopener,noreferrer");
    return;
  }
  void Linking.openURL(url);
}

function renderInlineMarkdown(text: string, textStyle: object, keyPrefix: string, isDarkMode = false) {
  const pattern =
    /(\\[\\`*_[\]()>#+.!-]|!\[[^\]]*\]\([^)]+\)|\*\*\*[^*]+\*\*\*|___[^_]+___|\*\*[^*]+\*\*|__[^_]+__|~~[^~]+~~|\*[^*]+\*|_[^_]+_|`[^`]+`|\[[^\]]+\]\([^)]+\)|<https?:\/\/[^>\s]+>|https?:\/\/[^\s<]+)/g;
  const lineParts = text.split(/<br\s*\/?>/gi);

  return (
    <Text style={textStyle}>
      {lineParts.map((linePart, lineIndex) => {
        const matches = linePart.split(pattern).filter(Boolean);
        return (
          <React.Fragment key={`${keyPrefix}-line-${lineIndex}`}>
            {lineIndex > 0 ? "\n" : null}
            {matches.map((part, index) => {
              const key = `${keyPrefix}-${lineIndex}-${index}`;
              const escaped = part.match(/^\\([\\`*_[\]()>#+.!-])$/);
              if (escaped) {
                return <Text key={key}>{escaped[1]}</Text>;
              }
              if (/^(\*\*\*[^*]+\*\*\*|___[^_]+___)$/.test(part)) {
                return (
                  <Text key={key} style={[styles.markdownStrong, isDarkMode && styles.markdownStrongDark, styles.markdownEmphasis]}>
                    {part.slice(3, -3)}
                  </Text>
                );
              }
              if (/^\*\*[^*]+\*\*$/.test(part)) {
                return (
                  <Text key={key} style={[styles.markdownStrong, isDarkMode && styles.markdownStrongDark]}>
                    {part.slice(2, -2)}
                  </Text>
                );
              }
              if (/^__[^_]+__$/.test(part)) {
                return (
                  <Text key={key} style={[styles.markdownStrong, isDarkMode && styles.markdownStrongDark]}>
                    {part.slice(2, -2)}
                  </Text>
                );
              }
              if (/^\*[^*]+\*$/.test(part)) {
                return (
                  <Text key={key} style={styles.markdownEmphasis}>
                    {part.slice(1, -1)}
                  </Text>
                );
              }
              if (/^_[^_]+_$/.test(part)) {
                return (
                  <Text key={key} style={styles.markdownEmphasis}>
                    {part.slice(1, -1)}
                  </Text>
                );
              }
              if (/^~~[^~]+~~$/.test(part)) {
                return (
                  <Text key={key} style={[styles.markdownStrike, isDarkMode && styles.markdownStrikeDark]}>
                    {part.slice(2, -2)}
                  </Text>
                );
              }
              if (/^`[^`]+`$/.test(part)) {
                return (
                  <Text key={key} style={[styles.markdownInlineCode, isDarkMode && styles.markdownInlineCodeDark]}>
                    {part.slice(1, -1)}
                  </Text>
                );
              }
              const inlineImageMatch = part.match(/^!\[([^\]]*)\]\(([^)]+)\)$/);
              if (inlineImageMatch) {
                return (
                  <Text
                    key={key}
                    style={[styles.markdownLink, isDarkMode && styles.markdownLinkDark]}
                    onPress={() => openExternalLink(inlineImageMatch[2])}
                  >
                    {inlineImageMatch[1] || "이미지"}
                  </Text>
                );
              }
              const linkMatch = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
              if (linkMatch) {
                return (
                  <Text
                    key={key}
                    style={[styles.markdownLink, isDarkMode && styles.markdownLinkDark]}
                    onPress={() => openExternalLink(linkMatch[2])}
                  >
                    {linkMatch[1]}
                  </Text>
                );
              }
              const bracketAutolinkMatch = part.match(/^<(https?:\/\/[^>\s]+)>$/);
              if (bracketAutolinkMatch) {
                return (
                  <Text
                    key={key}
                    style={[styles.markdownLink, isDarkMode && styles.markdownLinkDark]}
                    onPress={() => openExternalLink(bracketAutolinkMatch[1])}
                  >
                    {bracketAutolinkMatch[1]}
                  </Text>
                );
              }
              if (/^https?:\/\/[^\s<]+$/.test(part)) {
                const url = parseInlineUrl(part);
                const suffix = part.slice(url.length);
                return (
                  <React.Fragment key={key}>
                    <Text style={[styles.markdownLink, isDarkMode && styles.markdownLinkDark]} onPress={() => openExternalLink(url)}>
                      {url}
                    </Text>
                    {suffix ? <Text>{suffix}</Text> : null}
                  </React.Fragment>
                );
              }
              return <Text key={key}>{part}</Text>;
            })}
          </React.Fragment>
        );
      })}
    </Text>
  );
}

function renderHeadingMarkdown(
  text: string,
  level: number,
  keyPrefix: string,
  isDarkMode = false,
  useQuotePalette = false,
) {
  const headingLevelStyle = [
    level === 1 && styles.markdownHeading1,
    level === 2 && styles.markdownHeading2,
    level === 3 && styles.markdownHeading3,
    level === 4 && styles.markdownHeading4,
    level >= 5 && styles.markdownHeading5,
  ];

  return renderInlineMarkdown(
    text,
    [
      useQuotePalette ? styles.markdownQuoteHeading : styles.markdownHeading,
      isDarkMode && (useQuotePalette ? styles.markdownQuoteHeadingDark : styles.markdownHeadingDark),
      ...headingLevelStyle,
    ] as unknown as object,
    keyPrefix,
    isDarkMode,
  );
}

function MarkdownImage({ alt, src, isDarkMode = false }: { alt: string; src: string; isDarkMode?: boolean }) {
  const [failed, setFailed] = useState(false);

  if (failed) {
    return (
      <View style={[styles.markdownImageFallback, isDarkMode && styles.markdownImageFallbackDark]}>
        <Text style={[styles.markdownImageFallbackTitle, isDarkMode && styles.markdownImageFallbackTitleDark]}>이미지를 불러오지 못했습니다.</Text>
        <Text style={[styles.markdownImageFallbackUrl, isDarkMode && styles.markdownImageFallbackUrlDark]}>{src}</Text>
        {alt ? <Text style={[styles.markdownImageCaption, isDarkMode && styles.markdownImageCaptionDark]}>{alt}</Text> : null}
      </View>
    );
  }

  return (
    <View style={styles.markdownImageWrap}>
      <Image source={{ uri: src }} style={styles.markdownImage} resizeMode="contain" onError={() => setFailed(true)} />
      {alt ? <Text style={[styles.markdownImageCaption, isDarkMode && styles.markdownImageCaptionDark]}>{alt}</Text> : null}
    </View>
  );
}

function parseMarkdown(markdown: string, depth = 0, preserveSoftBreaks = false): Block[] {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const blocks: Block[] = [];
  let index = 0;

  function parseListBlock(): Block | null {
    const firstMatch = getListMarker(lines[index]);
    if (!firstMatch) {
      return null;
    }
    const baseIndent = firstMatch[1].length;
    const ordered = /^\d+\.$/.test(firstMatch[2]);
    const start = ordered ? Number(firstMatch[2].slice(0, -1)) : undefined;
    const level = Math.min(3, Math.floor(baseIndent / 2));
    const items: ListItem[] = [];
    let loose = false;

    while (index < lines.length) {
      const match = getListMarker(lines[index]);
      if (!match) {
        break;
      }
      const indent = match[1].length;
      const marker = match[2];
      const currentOrdered = /^\d+\.$/.test(marker);
      if (indent !== baseIndent || currentOrdered !== ordered) {
        break;
      }

      const checked = match[3] ? match[3].toLowerCase() === "x" : undefined;
      const itemLines: string[] = [match[4]];
      let sawBlankLine = false;
      index += 1;
      while (index < lines.length) {
        const nextLine = lines[index];
        const nextMatch = getListMarker(nextLine);
        if (nextMatch && nextMatch[1].length === baseIndent && (/^\d+\.$/.test(nextMatch[2]) === ordered)) {
          break;
        }
        if (!nextLine.trim()) {
          loose = true;
          sawBlankLine = true;
          itemLines.push("");
          index += 1;
          continue;
        }
        const nextIndent = nextLine.match(/^\s*/)?.[0].length || 0;
        if (sawBlankLine && nextIndent <= baseIndent) {
          break;
        }
        if (nextIndent <= baseIndent && isBlockStart(nextLine, lines[index + 1])) {
          break;
        }
        sawBlankLine = false;
        itemLines.push(stripIndent(nextLine, baseIndent + 2));
        index += 1;
      }

      const childSource = itemLines.join("\n").trim();
      const children = childSource ? parseMarkdown(childSource, depth + 1, preserveSoftBreaks) : [{ type: "paragraph", text: "" } satisfies Block];
      items.push({ children, checked });
    }

    return { type: "list", ordered, level, start, loose, items };
  }

  while (index < lines.length) {
    const rawLine = lines[index];
    const trimmed = rawLine.trim();

    if (!trimmed) {
      index += 1;
      continue;
    }

    const codeFenceMatch = trimmed.match(/^(```|~~~)\s*([^`]*)$/);
    if (codeFenceMatch) {
      const codeLines: string[] = [];
      const fence = codeFenceMatch[1];
      const language = codeFenceMatch[2]?.trim().split(/\s+/)[0] || null;
      index += 1;
      while (index < lines.length && !lines[index].trim().startsWith(fence)) {
        codeLines.push(lines[index]);
        index += 1;
      }
      if (index < lines.length) {
        index += 1;
      }
      blocks.push({ type: "code", language, lines: codeLines });
      continue;
    }

    if (/^( {4}|\t)/.test(rawLine)) {
      const codeLines: string[] = [];
      while (index < lines.length) {
        if (!lines[index].trim()) {
          codeLines.push("");
          index += 1;
          continue;
        }
        if (!/^( {4}|\t)/.test(lines[index])) {
          break;
        }
        codeLines.push(stripIndent(lines[index], 4));
        index += 1;
      }
      blocks.push({ type: "code", language: null, lines: codeLines });
      continue;
    }

    const headingMatch = trimmed.match(/^(#{1,6})\s+(.*)$/);
    if (headingMatch) {
      blocks.push({
        type: "heading",
        level: headingMatch[1].length,
        text: headingMatch[2].trim(),
      });
      index += 1;
      continue;
    }

    if (index + 1 < lines.length && /^(=+|-+)\s*$/.test(lines[index + 1].trim()) && trimmed && !isBlockStart(rawLine, lines[index + 1])) {
      blocks.push({
        type: "heading",
        level: lines[index + 1].trim().startsWith("=") ? 1 : 2,
        text: trimmed,
      });
      index += 2;
      continue;
    }

    if (/^(-{3,}|\*{3,}|_{3,})$/.test(trimmed)) {
      blocks.push({ type: "rule" });
      index += 1;
      continue;
    }

    const quoteStartMatch = rawLine.match(/^(\s*)>\s?(.*)$/);
    if (quoteStartMatch) {
      const quoteIndent = quoteStartMatch[1].length;
      const quoteLevel = Math.min(4, Math.floor(quoteIndent / 2));
      const quoteLines: string[] = [];
      while (index < lines.length) {
        const currentRawLine = lines[index];
        const currentQuoteMatch = currentRawLine.match(/^(\s*)>\s?(.*)$/);
        if (!currentQuoteMatch) {
          break;
        }
        const leading = currentQuoteMatch[1].length;
        const currentLevel = Math.min(4, Math.floor(leading / 2));
        if (currentLevel !== quoteLevel) {
          break;
        }
        quoteLines.push(currentQuoteMatch[2]);
        index += 1;
      }
      const children = depth >= 8 ? [{ type: "paragraph", text: quoteLines.join("\n").trim() } satisfies Block] : parseMarkdown(quoteLines.join("\n"), depth + 1, true);
      blocks.push({ type: "blockquote", children: children.length ? children : [{ type: "paragraph", text: "" }], level: quoteLevel });
      continue;
    }

    const imageMatch = trimmed.match(/^!\[([^\]]*)\]\(([^)]+)\)$/);
    if (imageMatch) {
      blocks.push({ type: "image", alt: imageMatch[1].trim(), src: imageMatch[2].trim() });
      index += 1;
      continue;
    }

    const inlineHtmlTableMatch = rawLine.match(/<table\b[\s\S]*<\/table>/i);
    if (inlineHtmlTableMatch) {
      const parsed = parseHtmlTableBlock(inlineHtmlTableMatch[0]);
      if (parsed) {
        blocks.push({ type: "html_table", headers: parsed.headers, rows: parsed.rows, rawHtml: parsed.rawHtml });
      } else {
        blocks.push({ type: "paragraph", text: stripHtmlTags(inlineHtmlTableMatch[0]) });
      }
      index += 1;
      continue;
    }

    if (/^<table\b/i.test(trimmed) || /^<tr\b/i.test(trimmed)) {
      const htmlLines: string[] = [];
      while (index < lines.length) {
        htmlLines.push(lines[index].trim());
        if (/^<\/table>/i.test(lines[index].trim())) {
          index += 1;
          break;
        }
        index += 1;
      }
      const parsed = parseHtmlTableBlock(htmlLines.join("\n"));
      if (parsed) {
        blocks.push({ type: "html_table", headers: parsed.headers, rows: parsed.rows, rawHtml: parsed.rawHtml });
      } else {
        blocks.push({ type: "paragraph", text: stripHtmlTags(htmlLines.join(" ")) });
      }
      continue;
    }

    if (trimmed.includes("|") && index + 1 < lines.length && isTableDivider(lines[index + 1].trim())) {
      const headers = splitTableRow(trimmed);
      const aligns = parseTableAlignments(lines[index + 1].trim());
      const rows: string[][] = [];
      index += 2;
      while (index < lines.length) {
        const candidate = lines[index].trim();
        if (!candidate) {
          const nextCandidate = index + 1 < lines.length ? lines[index + 1].trim() : "";
          if (nextCandidate.startsWith("|")) {
            index += 1;
            continue;
          }
          break;
        }
        if (!candidate.includes("|")) {
          break;
        }
        rows.push(splitTableRow(candidate));
        index += 1;
      }
      blocks.push({ type: "table", headers, aligns, rows });
      continue;
    }

    if (getListMarker(rawLine)) {
      const listBlock = parseListBlock();
      if (listBlock) {
        blocks.push(listBlock);
      }
      continue;
    }

    const paragraphLines: string[] = [];
    while (index < lines.length) {
      const candidate = lines[index].trim();
      if (!candidate) {
        break;
      }
      if (
        /^(#{1,6})\s+/.test(candidate) ||
        /^>\s?/.test(candidate) ||
        /^!\[([^\]]*)\]\(([^)]+)\)$/.test(candidate) ||
        /^<table\b/i.test(candidate) ||
        (candidate.includes("|") && index + 1 < lines.length && isTableDivider(lines[index + 1].trim())) ||
        /^[-+]\s+\[( |x|X)\]\s+/.test(candidate) ||
        /^(\d+\.|[-+])\s+/.test(candidate) ||
        /^(-{3,}|\*{3,}|_{3,})$/.test(candidate) ||
        /^(```|~~~)/.test(candidate)
      ) {
        break;
      }
      paragraphLines.push(candidate);
      index += 1;
    }
    blocks.push({ type: "paragraph", text: paragraphLines.join(preserveSoftBreaks ? "\n" : " ") });
  }

  return blocks;
}

export function parseMarkdownBlockRanges(markdown: string): MarkdownBlockRange[] {
  const normalized = markdown.replace(/\r\n/g, "\n");
  const lines = normalized.split("\n");
  const ranges: MarkdownBlockRange[] = [];
  let index = 0;
  let offset = 0;

  const currentLineStart = () => offset;
  const advanceLine = (line: string) => {
    offset += line.length;
    if (index < lines.length - 1) {
      offset += 1;
    }
    index += 1;
  };

  while (index < lines.length) {
    const rawLine = lines[index];
    const trimmed = rawLine.trim();
    const blockStart = currentLineStart();

    if (!trimmed) {
      advanceLine(rawLine);
      continue;
    }

    const fenceMatch = trimmed.match(/^(```|~~~)\s*([\w-]+)?\s*$/);
    if (fenceMatch) {
      const fence = fenceMatch[1];
      advanceLine(rawLine);
      while (index < lines.length && !lines[index].trim().startsWith(fence)) {
        advanceLine(lines[index]);
      }
      if (index < lines.length) {
        advanceLine(lines[index]);
      }
      ranges.push({ start: blockStart, end: offset });
      continue;
    }

    if (
      /^(#{1,6})\s+/.test(trimmed) ||
      /^(-{3,}|\*{3,}|_{3,})$/.test(trimmed) ||
      /^!\[([^\]]*)\]\(([^)]+)\)$/.test(trimmed)
    ) {
      advanceLine(rawLine);
      ranges.push({ start: blockStart, end: offset });
      continue;
    }

    if (/^\s*>\s?/.test(rawLine)) {
      const quoteStartMatch = rawLine.match(/^(\s*)>\s?/);
      const quoteLevel = Math.min(4, Math.floor((quoteStartMatch?.[1].length || 0) / 2));
      while (index < lines.length) {
        const currentMatch = lines[index].match(/^(\s*)>\s?/);
        if (!currentMatch) {
          break;
        }
        const currentLevel = Math.min(4, Math.floor((currentMatch[1].length || 0) / 2));
        if (currentLevel !== quoteLevel) {
          break;
        }
        advanceLine(lines[index]);
      }
      ranges.push({ start: blockStart, end: offset });
      continue;
    }

    if (/^<table\b/i.test(trimmed) || /^<tr\b/i.test(trimmed) || /<table\b[\s\S]*<\/table>/i.test(rawLine)) {
      while (index < lines.length) {
        advanceLine(lines[index]);
        if (/^<\/table>/i.test(lines[index - 1].trim())) {
          break;
        }
      }
      ranges.push({ start: blockStart, end: offset });
      continue;
    }

    if (trimmed.includes("|") && index + 1 < lines.length && isTableDivider(lines[index + 1].trim())) {
      advanceLine(rawLine);
      advanceLine(lines[index]);
      while (index < lines.length) {
        const candidate = lines[index].trim();
        if (!candidate) {
          const nextCandidate = index + 1 < lines.length ? lines[index + 1].trim() : "";
          if (nextCandidate.startsWith("|")) {
            advanceLine(lines[index]);
            continue;
          }
          break;
        }
        if (!candidate.includes("|")) {
          break;
        }
        advanceLine(lines[index]);
      }
      ranges.push({ start: blockStart, end: offset });
      continue;
    }

    const listStart = getListMarker(rawLine);
    if (listStart) {
      const baseIndent = listStart[1].length;
      const ordered = /^\d+\.$/.test(listStart[2]);
      let sawBlankLine = false;
      while (index < lines.length) {
        const currentLine = lines[index];
        const currentMarker = getListMarker(currentLine);
        if (currentMarker) {
          const currentIndent = currentMarker[1].length;
          const currentOrdered = /^\d+\.$/.test(currentMarker[2]);
          if (currentIndent < baseIndent || (currentIndent === baseIndent && currentOrdered !== ordered)) {
            break;
          }
          advanceLine(lines[index]);
          continue;
        }
        if (!currentLine.trim()) {
          sawBlankLine = true;
          advanceLine(currentLine);
          continue;
        }
        const currentIndent = currentLine.match(/^\s*/)?.[0].length || 0;
        if (sawBlankLine && currentIndent <= baseIndent) {
          break;
        }
        if (currentIndent <= baseIndent && isBlockStart(currentLine, lines[index + 1])) {
          break;
        }
        sawBlankLine = false;
        advanceLine(currentLine);
      }
      ranges.push({ start: blockStart, end: offset });
      continue;
    }

    while (index < lines.length) {
      const candidate = lines[index].trim();
      if (
        !candidate ||
        /^(#{1,6})\s+/.test(candidate) ||
        /^>\s?/.test(candidate) ||
        /^!\[([^\]]*)\]\(([^)]+)\)$/.test(candidate) ||
        /^<table\b/i.test(candidate) ||
        (candidate.includes("|") && index + 1 < lines.length && isTableDivider(lines[index + 1].trim())) ||
        /^[-+]\s+\[( |x|X)\]\s+/.test(candidate) ||
        /^[-+]\s+/.test(candidate) ||
        /^\d+\.\s+/.test(candidate) ||
        /^(-{3,}|\*{3,}|_{3,})$/.test(candidate) ||
        /^(```|~~~)/.test(candidate)
      ) {
        break;
      }
      advanceLine(lines[index]);
    }
    ranges.push({ start: blockStart, end: offset });
  }

  return ranges;
}

function renderHeading(level: number, text: string, key: string) {
  const headingStyle = [
    styles.markdownHeading,
    level === 1 && styles.markdownHeading1,
    level === 2 && styles.markdownHeading2,
    level === 3 && styles.markdownHeading3,
    level === 4 && styles.markdownHeading4,
    level >= 5 && styles.markdownHeading5,
  ];
  return (
    <Text key={key} style={headingStyle}>
      {text}
    </Text>
  );
}

export function MarkdownPreview({
  markdown,
  isDarkMode = false,
  activeBlockIndex = -1,
  onBlockLayout,
}: {
  markdown: string;
  isDarkMode?: boolean;
  activeBlockIndex?: number;
  onBlockLayout?: (blockIndex: number, y: number) => void;
}) {
  const blocks = useMemo(() => parseMarkdown(markdown), [markdown]);
  const [containerWidth, setContainerWidth] = useState(0);

  function handleBlockLayout(blockIndex: number, event: LayoutChangeEvent): void {
    onBlockLayout?.(blockIndex, event.nativeEvent.layout.y);
  }

  function renderBlock(block: Block, blockIndex: number, key: string, options: { trackLayout?: boolean; inQuote?: boolean; listDepth?: number } = {}): React.ReactNode {
    const trackLayout = options.trackLayout ?? false;
    const inQuote = options.inQuote ?? false;
    const listDepth = options.listDepth ?? 0;
    const isActive = trackLayout && blockIndex === activeBlockIndex;
    const blockHighlightStyle = isActive ? [styles.markdownActiveBlock, isDarkMode && styles.markdownActiveBlockDark] : undefined;
    const layoutProps = trackLayout ? { onLayout: (event: LayoutChangeEvent) => handleBlockLayout(blockIndex, event) } : {};

    if (block.type === "heading") {
      return (
        <View key={key} style={blockHighlightStyle} {...layoutProps}>
          {renderHeadingMarkdown(block.text, block.level, key, isDarkMode, inQuote)}
        </View>
      );
    }

    if (block.type === "paragraph") {
      return (
        <View key={key} style={blockHighlightStyle} {...layoutProps}>
          {renderInlineMarkdown(
            block.text,
            [
              inQuote ? styles.markdownQuoteText : styles.markdownParagraph,
              isDarkMode && (inQuote ? styles.markdownQuoteTextDark : styles.markdownParagraphDark),
            ] as unknown as object,
            key,
            isDarkMode,
          )}
        </View>
      );
    }

    if (block.type === "blockquote") {
      return (
        <View
          key={key}
          style={[
            styles.markdownQuote,
            isDarkMode && styles.markdownQuoteDark,
            markdownIndent(block.level),
            blockHighlightStyle,
          ]}
          {...layoutProps}
        >
          {block.children.map((child, childIndex) =>
            renderBlock(child, childIndex, `${key}-quote-${childIndex}`, { inQuote: true, listDepth }),
          )}
        </View>
      );
    }

    if (block.type === "list") {
      const effectiveLevel = listDepth + block.level;
      if (inQuote && listDepth > 0) {
        return (
          <View key={key} style={[styles.markdownList, blockHighlightStyle]} {...layoutProps}>
            {block.items.map((item, itemIndex) => {
              const marker = typeof item.checked === "boolean"
                ? `- [${item.checked ? "x" : " "}]`
                : block.ordered
                  ? `${block.start ? block.start + itemIndex : itemIndex + 1}.`
                  : "-";
              const paragraphChildren = item.children.filter((child) => child.type === "paragraph") as Extract<Block, { type: "paragraph" }>[];
              const firstParagraph = paragraphChildren[0]?.text || "";
              const remainingChildren = firstParagraph
                ? item.children.filter((child) => child !== paragraphChildren[0])
                : item.children;

              return (
                <View key={`${key}-text-item-${itemIndex}`} style={markdownListIndent(effectiveLevel, true)}>
                  {renderInlineMarkdown(
                    `${marker}${firstParagraph ? ` ${firstParagraph}` : ""}`,
                    [
                      styles.markdownQuoteText,
                      isDarkMode && styles.markdownQuoteTextDark,
                      item.checked && styles.markdownChecklistDone,
                      item.checked && isDarkMode && styles.markdownChecklistDoneDark,
                    ] as unknown as object,
                    `${key}-text-item-${itemIndex}`,
                    isDarkMode,
                  )}
                  {remainingChildren.map((child, childIndex) =>
                    renderBlock(child, childIndex, `${key}-text-item-${itemIndex}-child-${childIndex}`, {
                      inQuote,
                      listDepth: effectiveLevel + 1,
                    }),
                  )}
                </View>
              );
            })}
          </View>
        );
      }
      return (
        <View key={key} style={[styles.markdownList, blockHighlightStyle]} {...layoutProps}>
          {block.items.map((item, itemIndex) => {
            const marker = getListBullet(effectiveLevel, block.ordered, itemIndex, block.start ? block.start + itemIndex : undefined);
            const paragraphChildren = item.children.filter((child) => child.type === "paragraph") as Extract<Block, { type: "paragraph" }>[];
            const compactParagraphOnly = item.children.length === 1 && paragraphChildren.length === 1;

            return (
              <View key={`${key}-item-${itemIndex}`} style={[styles.markdownListItem, markdownListIndent(effectiveLevel, inQuote)]}>
                {typeof item.checked === "boolean" ? (
                  <View style={[styles.markdownCheckbox, isDarkMode && styles.markdownCheckboxDark, item.checked && styles.markdownCheckboxChecked]}>
                    {item.checked ? <Text style={[styles.markdownCheckboxMark, isDarkMode && styles.markdownCheckboxMarkDark]}>✓</Text> : null}
                  </View>
                ) : (
                  <Text style={[styles.markdownListBullet, isDarkMode && styles.markdownListBulletDark]}>{marker}</Text>
                )}
                <View style={styles.markdownListTextWrap}>
                  {compactParagraphOnly
                    ? renderInlineMarkdown(
                        paragraphChildren[0].text,
                        [
                          inQuote ? styles.markdownQuoteText : styles.markdownListText,
                          isDarkMode && (inQuote ? styles.markdownQuoteTextDark : styles.markdownListTextDark),
                          item.checked && styles.markdownChecklistDone,
                          item.checked && isDarkMode && styles.markdownChecklistDoneDark,
                        ] as unknown as object,
                        `${key}-item-${itemIndex}`,
                        isDarkMode,
                      )
                    : item.children.map((child, childIndex) =>
                        renderBlock(child, childIndex, `${key}-item-${itemIndex}-child-${childIndex}`, {
                          inQuote,
                          listDepth: effectiveLevel + 1,
                        }),
                      )}
                </View>
              </View>
            );
          })}
        </View>
      );
    }

    if (block.type === "image") {
      return (
        <View key={key} style={blockHighlightStyle} {...layoutProps}>
          <MarkdownImage alt={block.alt} src={block.src} isDarkMode={isDarkMode} />
        </View>
      );
    }

    if (block.type === "table" || block.type === "html_table") {
      const aligns = block.type === "table" ? block.aligns : [];
      const columnCount = Math.max(
        block.headers.length,
        aligns.length,
        ...block.rows.map((row) => row.length),
      );
      const columnWidths = computeTableColumnWidths(block.headers, block.rows, columnCount);
      const tableMinimumWidth = columnWidths.reduce((sum, column) => sum + column.minWidth, 0);
      const needsHorizontalScroll =
        containerWidth > 0 && tableMinimumWidth > Math.max(0, containerWidth - 12);

      if (block.type === "html_table" && Platform.OS === "web") {
        const HtmlShell = needsHorizontalScroll ? ScrollView : View;
        const htmlShellProps = needsHorizontalScroll
          ? {
              horizontal: true,
              showsHorizontalScrollIndicator: true,
              style: styles.markdownTableWrap,
              contentContainerStyle: styles.markdownTableScrollContent,
            }
          : {
              style: styles.markdownTableWrap,
            };
        return (
          <View key={key} style={blockHighlightStyle} {...layoutProps}>
            <HtmlShell {...htmlShellProps}>
              <HtmlTableFrame
                html={block.rawHtml}
                isDarkMode={isDarkMode}
                minWidth={needsHorizontalScroll ? tableMinimumWidth : undefined}
              />
            </HtmlShell>
          </View>
        );
      }

      const TableShell = needsHorizontalScroll ? ScrollView : View;
      const tableShellProps = needsHorizontalScroll
        ? {
            horizontal: true,
            showsHorizontalScrollIndicator: true,
            style: styles.markdownTableWrap,
            contentContainerStyle: styles.markdownTableScrollContent,
          }
        : {
            style: styles.markdownTableWrap,
          };

      return (
        <View key={key} style={blockHighlightStyle} {...layoutProps}>
          <TableShell {...tableShellProps}>
            <View
              style={[
                styles.markdownTable,
                isDarkMode && styles.markdownTableDark,
                needsHorizontalScroll && { minWidth: tableMinimumWidth },
              ]}
            >
              <View style={[styles.markdownTableRow, isDarkMode && styles.markdownTableRowDark, styles.markdownTableHeaderRow, isDarkMode && styles.markdownTableHeaderRowDark]}>
                {Array.from({ length: columnCount }).map((_, columnIndex) => (
                  <View
                    key={`${key}-header-${columnIndex}`}
                    style={[
                      styles.markdownTableCell,
                      needsHorizontalScroll
                        ? ({ width: columnWidths[columnIndex].preferredWidth, minWidth: columnWidths[columnIndex].minWidth, flexGrow: 0 } satisfies ViewStyle)
                        : columnWidths[columnIndex],
                      styles.markdownTableHeaderCell,
                      isDarkMode && styles.markdownTableCellDark,
                      isDarkMode && styles.markdownTableHeaderCellDark,
                      columnIndex === columnCount - 1 && styles.markdownTableCellLast,
                    ]}
                  >
                    {renderInlineMarkdown(
                      block.headers[columnIndex] || "",
                      [styles.markdownTableHeaderText, isDarkMode && styles.markdownTableHeaderTextDark, textAlignStyle(aligns[columnIndex] || "left")] as unknown as object,
                      `${key}-header-${columnIndex}`,
                      isDarkMode,
                    )}
                  </View>
                ))}
              </View>
              {block.rows.map((row, rowIndex) => (
                <View
                  key={`${key}-row-${rowIndex}`}
                  style={[
                    styles.markdownTableRow,
                    isDarkMode && styles.markdownTableRowDark,
                    rowIndex === block.rows.length - 1 && styles.markdownTableRowLast,
                  ]}
                >
                  {Array.from({ length: columnCount }).map((_, columnIndex) => (
                    <View
                      key={`${key}-${rowIndex}-${columnIndex}`}
                      style={[
                        styles.markdownTableCell,
                        needsHorizontalScroll
                          ? ({ width: columnWidths[columnIndex].preferredWidth, minWidth: columnWidths[columnIndex].minWidth, flexGrow: 0 } satisfies ViewStyle)
                          : columnWidths[columnIndex],
                        isDarkMode && styles.markdownTableCellDark,
                        columnIndex === columnCount - 1 && styles.markdownTableCellLast,
                      ]}
                    >
                      {renderInlineMarkdown(
                        row[columnIndex] || "",
                        [styles.markdownTableCellText, isDarkMode && styles.markdownTableCellTextDark, textAlignStyle(aligns[columnIndex] || "left")] as unknown as object,
                        `${key}-${rowIndex}-${columnIndex}`,
                        isDarkMode,
                      )}
                    </View>
                  ))}
                </View>
              ))}
            </View>
          </TableShell>
        </View>
      );
    }

    if (block.type === "rule") {
      return <View key={key} style={[styles.markdownRule, isDarkMode && styles.markdownRuleDark, blockHighlightStyle]} {...layoutProps} />;
    }

    return (
      <View key={key} style={[styles.markdownCodeBlock, blockHighlightStyle]} {...layoutProps}>
        {block.language ? <Text style={styles.markdownCodeLanguage}>{block.language}</Text> : null}
        {block.lines.map((line, lineIndex) => (
          <Text key={`${key}-${lineIndex}`} style={styles.markdownCodeLine}>
            {line || " "}
          </Text>
        ))}
      </View>
    );
  }

  if (!blocks.length) {
    return <Text style={[styles.previewEmpty, isDarkMode && styles.previewEmptyDark]}>표시할 Markdown 내용이 없습니다.</Text>;
  }

  return (
    <View
      style={styles.markdownPreview}
      onLayout={(event) => {
        const nextWidth = Math.round(event.nativeEvent.layout.width);
        if (nextWidth > 0 && nextWidth !== containerWidth) {
          setContainerWidth(nextWidth);
        }
      }}
    >
      {blocks.map((block, blockIndex) => renderBlock(block, blockIndex, `${block.type}-${blockIndex}`, { trackLayout: true }))}
    </View>
  );
}
