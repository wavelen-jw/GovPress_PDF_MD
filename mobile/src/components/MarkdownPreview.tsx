import React, { useMemo, useState } from "react";
import { Image, LayoutChangeEvent, Linking, Platform, ScrollView, Text, View, type ViewStyle } from "react-native";

import { styles } from "../styles";

type TableAlign = "left" | "center" | "right";

type TableColumnWidth = {
  minWidth: number;
  preferredWidth: number;
  flexGrow: number;
};

type TableLayout = {
  columnWidths: TableColumnWidth[];
  needsHorizontalScroll: boolean;
  tableContentWidth: number;
};

type Block =
  | { type: "heading"; level: number; text: string }
  | { type: "paragraph"; text: string }
  | { type: "blockquote"; paragraphs: string[]; level: number }
  | { type: "list_item"; ordered: boolean; level: number; visualLevel?: number; text: string; orderIndex: number; orderNumber?: number }
  | { type: "checklist_item"; checked: boolean; level: number; text: string }
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
const MARKDOWN_LIST_BASE_INDENT = 8;
const MAX_ORDERED_LIST_NUMBER = 17;

function parseAtxHeadingLine(line: string): { level: number; text: string } | null {
  const match = line.trim().match(/^(#{1,6})(?:[ \t]+|$)(.*)$/);
  if (!match) {
    return null;
  }
  return {
    level: match[1].length,
    text: match[2].replace(/[ \t]+#+[ \t]*$/, "").trim(),
  };
}

function getHeadingLevelStyles(level: number) {
  return [
    level === 1 && styles.markdownHeading1,
    level === 2 && styles.markdownHeading2,
    level === 3 && styles.markdownHeading3,
    level === 4 && styles.markdownHeading4,
    level === 5 && styles.markdownHeading5,
    level >= 6 && styles.markdownHeading6,
  ];
}

function markdownIndent(level: number): ViewStyle {
  return { marginLeft: MARKDOWN_INDENT_UNIT * (Math.max(0, level) + 1) };
}

function listIndent(level: number, ordered: boolean): ViewStyle {
  const normalizedLevel = Math.max(0, level);
  return {
    marginLeft: MARKDOWN_LIST_BASE_INDENT + MARKDOWN_INDENT_UNIT * normalizedLevel,
  };
}

function checklistIndent(level: number): ViewStyle {
  return {
    marginLeft: MARKDOWN_LIST_BASE_INDENT + MARKDOWN_INDENT_UNIT * Math.max(0, level),
  };
}

function isEscaped(value: string, index: number): boolean {
  let slashCount = 0;
  for (let cursor = index - 1; cursor >= 0 && value[cursor] === "\\"; cursor -= 1) {
    slashCount += 1;
  }
  return slashCount % 2 === 1;
}

function hasClosingBacktick(value: string, startIndex: number): boolean {
  for (let index = startIndex + 1; index < value.length; index += 1) {
    if (value[index] === "`" && !isEscaped(value, index)) {
      return true;
    }
  }
  return false;
}

function matchOrderedListMarker(line: string): RegExpMatchArray | null {
  const match = line.match(/^(\d+)\.\s+(.*)$/);
  if (!match) {
    return null;
  }
  const markerNumber = Number(match[1]);
  if (!Number.isInteger(markerNumber) || markerNumber < 1 || markerNumber > MAX_ORDERED_LIST_NUMBER) {
    return null;
  }
  return match;
}

function isOrderedListLine(line: string): boolean {
  return matchOrderedListMarker(line) !== null;
}

function hasHardLineBreakSuffix(line: string): boolean {
  return /[ \t]{2,}$/.test(line) || /(?<!\\)\\$/.test(line);
}

function stripHardLineBreakSuffix(line: string): string {
  if (/[ \t]{2,}$/.test(line)) {
    return line.replace(/[ \t]+$/, "");
  }
  if (/(?<!\\)\\$/.test(line)) {
    return line.replace(/\\$/, "");
  }
  return line;
}

function joinMarkdownInlineLines(lines: string[]): string {
  if (!lines.length) {
    return "";
  }
  let result = stripHardLineBreakSuffix(lines[0]);
  for (let index = 1; index < lines.length; index += 1) {
    const previous = lines[index - 1];
    result += hasHardLineBreakSuffix(previous) ? "<br>" : " ";
    result += stripHardLineBreakSuffix(lines[index]);
  }
  return result;
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
      if (inCode || hasClosingBacktick(source, index)) {
        inCode = !inCode;
      }
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
    .map((part) =>
      Array.from(part.trim()).reduce((width, char) => {
        if (/[가-힣ㄱ-ㅎㅏ-ㅣ一-龥]/.test(char)) {
          return width + 1.65;
        }
        if (/[A-Z0-9]/.test(char)) {
          return width + 1.1;
        }
        return width + 0.8;
      }, 0),
    )
    .reduce((max, current) => Math.max(max, current), 0);
}

function computeTableColumnWidths(headers: string[], rows: string[][], columnCount: number): TableColumnWidth[] {
  const maximum = 280;

  return Array.from({ length: columnCount }).map((_, columnIndex) => {
    const samples = [headers[columnIndex] || "", ...rows.map((row) => row[columnIndex] || "")];
    const maxChars = samples.reduce((max, cell) => Math.max(max, estimateColumnCharacterWidth(cell)), 0);
    const normalizedChars = Math.max(3, Math.min(40, maxChars));
    const minimum = Math.min(112, Math.max(48, Math.round(normalizedChars * 8 + 20)));
    return {
      minWidth: minimum,
      preferredWidth: Math.min(maximum, Math.max(minimum, Math.round(normalizedChars * 8 + 36))),
      flexGrow: normalizedChars,
    };
  });
}

function computeTableLayout(headers: string[], rows: string[][], columnCount: number, containerWidth: number): TableLayout {
  const columnWidths = computeTableColumnWidths(headers, rows, columnCount);
  const availableTableWidth = containerWidth > 0 ? Math.max(0, containerWidth - 12) : 0;
  const tableContentWidth = columnWidths.reduce((sum, col) => sum + col.minWidth, 0);
  const needsHorizontalScroll = availableTableWidth > 0 && tableContentWidth > availableTableWidth;

  return {
    columnWidths,
    needsHorizontalScroll,
    tableContentWidth,
  };
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

  const frameWidth = minWidth ? Math.max(minWidth, 320) : undefined;

  return (
    <View
      style={[
        styles.markdownHtmlFrameWrap,
        frameWidth ? ({ width: frameWidth } satisfies ViewStyle) : undefined,
        isDarkMode && styles.markdownHtmlFrameWrapDark,
      ]}
    >
      {React.createElement("iframe", {
        key: frameId,
        title: frameId,
        srcDoc: buildHtmlTableDocument(html, isDarkMode, frameId),
        style: {
          width: "100%",
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

function openExternalLink(url: string): void {
  if (Platform.OS === "web" && typeof window !== "undefined") {
    window.open(url, "_blank", "noopener,noreferrer");
    return;
  }
  void Linking.openURL(url);
}

const MARKDOWN_ESCAPE_START = "\uE000";
const MARKDOWN_ESCAPE_END = "\uE001";
function protectMarkdownEscapes(text: string): { text: string; restore: (value: string) => string } {
  const escapedValues: string[] = [];
  const protectedText = text.replace(/\\([\\`*_[\]()>#+.!-])/g, (_, escaped: string) => {
    const index = escapedValues.push(escaped) - 1;
    return `${MARKDOWN_ESCAPE_START}${index}${MARKDOWN_ESCAPE_END}`;
  });
  const restore = (value: string) =>
    value.replace(new RegExp(`${MARKDOWN_ESCAPE_START}(\\d+)${MARKDOWN_ESCAPE_END}`, "g"), (_, rawIndex: string) => {
      return escapedValues[Number(rawIndex)] ?? "";
    });
  return { text: protectedText, restore };
}

function renderInlineMarkdownSegment(
  part: string,
  key: string,
  isDarkMode: boolean,
  restore: (value: string) => string,
  preserveAsteriskLiterals = false,
): React.ReactNode {
  const tagMatch = part.match(/^<(sup|sub|ins|u)>([\s\S]*?)<\/\1>$/i);
  if (tagMatch) {
    const tag = tagMatch[1].toLowerCase();
    const inner = restore(tagMatch[2]);
    const tagStyle =
      tag === "sup"
        ? [styles.markdownSuperscript, isDarkMode && styles.markdownSuperscriptDark]
        : tag === "sub"
          ? [styles.markdownSubscript, isDarkMode && styles.markdownSubscriptDark]
          : [styles.markdownUnderline, isDarkMode && styles.markdownUnderlineDark];
    return (
      <Text key={key} style={tagStyle}>
        {renderInlineMarkdown(inner, {}, `${key}-inner`, isDarkMode, { preserveAsteriskLiterals })}
      </Text>
    );
  }

  if (!preserveAsteriskLiterals && /^\*\*[^*]+\*\*$/.test(part)) {
    return (
      <Text key={key} style={[styles.markdownStrong, isDarkMode && styles.markdownStrongDark]}>
        {restore(part.slice(2, -2))}
      </Text>
    );
  }
  if (!preserveAsteriskLiterals && /^\*[^*]+\*$/.test(part)) {
    return (
      <Text key={key} style={styles.markdownEmphasis}>
        {restore(part.slice(1, -1))}
      </Text>
    );
  }
  if (/^~~[^~]+~~$/.test(part)) {
    return (
      <Text key={key} style={[styles.markdownStrike, isDarkMode && styles.markdownStrikeDark]}>
        {restore(part.slice(2, -2))}
      </Text>
    );
  }
  if (/^`[^`]+`$/.test(part)) {
    return <Text key={key}>{restore(part)}</Text>;
  }
  const linkMatch = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
  if (linkMatch) {
    const label = restore(linkMatch[1]);
    const href = restore(linkMatch[2]);
    return (
      <Text
        key={key}
        style={[styles.markdownLink, isDarkMode && styles.markdownLinkDark]}
        onPress={() => openExternalLink(href)}
      >
        {label}
      </Text>
    );
  }
  return <Text key={key}>{restore(part)}</Text>;
}

function renderInlineMarkdown(
  text: string,
  textStyle: object,
  keyPrefix: string,
  isDarkMode = false,
  options: { preserveAsteriskLiterals?: boolean } = {},
) {
  const { text: escapedText, restore } = protectMarkdownEscapes(text);
  const pattern = options.preserveAsteriskLiterals
    ? /(<(?:sup|sub|ins|u)>[\s\S]*?<\/(?:sup|sub|ins|u)>|~~[^~]+~~|`[^`]+`|\[[^\]]+\]\([^)]+\))/g
    : /(<(?:sup|sub|ins|u)>[\s\S]*?<\/(?:sup|sub|ins|u)>|\*\*[^*]+\*\*|~~[^~]+~~|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g;
  const lineParts = escapedText.split(/<br\s*\/?>/gi);

  return (
    <Text style={textStyle}>
      {lineParts.map((linePart, lineIndex) => {
        const matches = linePart.split(pattern).filter(Boolean);
        return (
          <React.Fragment key={`${keyPrefix}-line-${lineIndex}`}>
            {lineIndex > 0 ? "\n" : null}
            {matches.map((part, index) => {
              const key = `${keyPrefix}-${lineIndex}-${index}`;
              return renderInlineMarkdownSegment(part, key, isDarkMode, restore, options.preserveAsteriskLiterals);
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
  return renderInlineMarkdown(
    text,
    [
      useQuotePalette ? styles.markdownQuoteHeading : styles.markdownHeading,
      isDarkMode && (useQuotePalette ? styles.markdownQuoteHeadingDark : styles.markdownHeadingDark),
      ...getHeadingLevelStyles(level),
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

function parseMarkdown(markdown: string): Block[] {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const blocks: Block[] = [];
  let index = 0;
  let blankRun = 0;
  const orderedSequenceByLevel = new Map<number, number>();
  let lastOrderedListLevel: number | null = null;

  const resetListContext = () => {
    lastOrderedListLevel = null;
  };

  while (index < lines.length) {
    const rawLine = lines[index];
    const trimmed = rawLine.trim();

    if (!trimmed) {
      blankRun += 1;
      if (blankRun >= 2) {
        orderedSequenceByLevel.clear();
        resetListContext();
      }
      index += 1;
      continue;
    }

    blankRun = 0;

    const codeFenceMatch = trimmed.match(/^(```|~~~)([\w-]+)?$/);
    if (codeFenceMatch) {
      const codeLines: string[] = [];
      const fence = codeFenceMatch[1];
      const language = codeFenceMatch[2] || null;
      index += 1;
      while (index < lines.length && !lines[index].trim().startsWith(fence)) {
        codeLines.push(lines[index]);
        index += 1;
      }
      if (index < lines.length) {
        index += 1;
      }
      resetListContext();
      blocks.push({ type: "code", language, lines: codeLines });
      continue;
    }

    const headingMatch = parseAtxHeadingLine(trimmed);
    if (headingMatch) {
      resetListContext();
      blocks.push({
        type: "heading",
        level: headingMatch.level,
        text: headingMatch.text,
      });
      index += 1;
      continue;
    }

    if (/^(-{3,}|\*{3,}|_{3,})$/.test(trimmed)) {
      resetListContext();
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
      const quotedHtml = quoteLines.join("\n").trim();
      if (/<table\b[\s\S]*<\/table>/i.test(quotedHtml) || /^<table\b/i.test(quotedHtml) || /^<tr\b/i.test(quotedHtml)) {
        const parsed = parseHtmlTableBlock(quotedHtml);
        if (parsed) {
          resetListContext();
          blocks.push({ type: "html_table", headers: parsed.headers, rows: parsed.rows, rawHtml: parsed.rawHtml });
          continue;
        }
      }
      const paragraphs: string[] = [];
      let paragraphBuffer: string[] = [];
      for (const line of quoteLines) {
        if (!line.trim()) {
          if (paragraphBuffer.length) {
            paragraphs.push(joinMarkdownInlineLines(paragraphBuffer));
            paragraphBuffer = [];
          }
          continue;
        }
        paragraphBuffer.push(line);
      }
      if (paragraphBuffer.length) {
        paragraphs.push(joinMarkdownInlineLines(paragraphBuffer));
      }
      resetListContext();
      blocks.push({ type: "blockquote", paragraphs: paragraphs.length ? paragraphs : [""], level: quoteLevel });
      continue;
    }

    const imageMatch = trimmed.match(/^!\[([^\]]*)\]\(([^)]+)\)$/);
    if (imageMatch) {
      resetListContext();
      blocks.push({ type: "image", alt: imageMatch[1].trim(), src: imageMatch[2].trim() });
      index += 1;
      continue;
    }

    const inlineHtmlTableMatch = rawLine.match(/<table\b[\s\S]*<\/table>/i);
    if (inlineHtmlTableMatch) {
      resetListContext();
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
      resetListContext();
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
      resetListContext();
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

    if (/^[-*+]\s+\[( |x|X)\]\s+/.test(trimmed)) {
      resetListContext();
      while (index < lines.length) {
        const rawCandidate = lines[index];
        const candidate = rawCandidate.trim();
        const match = candidate.match(/^[-*+]\s+\[( |x|X)\]\s+(.*)$/);
        if (!match) {
          break;
        }
        const indent = rawCandidate.match(/^\s*/)?.[0].length || 0;
        const level = Math.min(3, Math.floor(indent / 2));
        const text = rawCandidate.replace(/^[-*+]\s+\[( |x|X)\]\s+/, "");
        blocks.push({
          type: "checklist_item",
          checked: match[1].toLowerCase() === "x",
          level,
          text: stripHardLineBreakSuffix(text.trimEnd()),
        });
        index += 1;
      }
      continue;
    }

    if (/^[-*+]\s+/.test(trimmed) || isOrderedListLine(trimmed)) {
      const ordered = isOrderedListLine(trimmed);
      const unorderedVisualOffset = !ordered && lastOrderedListLevel !== null ? lastOrderedListLevel + 1 : 0;
      let orderIndex = 0;
      while (index < lines.length) {
        const rawCandidate = lines[index];
        const candidate = rawCandidate.trim();
        const indent = rawCandidate.match(/^\s*/)?.[0].length || 0;
        const level = Math.min(3, Math.floor(indent / 2));
        if (ordered && isOrderedListLine(candidate)) {
          const orderedMatch = matchOrderedListMarker(candidate);
          if (!orderedMatch) {
            break;
          }
          for (const existingLevel of [...orderedSequenceByLevel.keys()]) {
            if (existingLevel > level) {
              orderedSequenceByLevel.delete(existingLevel);
            }
          }
          const sourceNumber = Number(orderedMatch[1]);
          orderedSequenceByLevel.set(level, sourceNumber);
          lastOrderedListLevel = level;
          blocks.push({
            type: "list_item",
            ordered: true,
            level,
            text: stripHardLineBreakSuffix(rawCandidate.replace(/^(\s*\d+\.\s+)/, "")).trimEnd(),
            orderIndex,
            orderNumber: sourceNumber,
          });
          orderIndex += 1;
          index += 1;
          continue;
        }
        if (!ordered && /^[-*+]\s+/.test(candidate)) {
          const rawText = rawCandidate.replace(/^(\s*[-*+]\s+)/, "");
          blocks.push({
            type: "list_item",
            ordered: false,
            level,
            visualLevel: level + unorderedVisualOffset,
            text: stripHardLineBreakSuffix(rawText).trimEnd(),
            orderIndex,
          });
          index += 1;
          continue;
        }
        break;
      }
      if (!ordered) {
        resetListContext();
      }
      continue;
    }

    const paragraphLines: string[] = [];
    while (index < lines.length) {
      const rawCandidate = lines[index];
      const candidate = rawCandidate.trim();
      if (!candidate) {
        break;
      }
      if (
        parseAtxHeadingLine(candidate) ||
        /^>\s?/.test(candidate) ||
        /^!\[([^\]]*)\]\(([^)]+)\)$/.test(candidate) ||
        /^<table\b/i.test(candidate) ||
        (candidate.includes("|") && index + 1 < lines.length && isTableDivider(lines[index + 1].trim())) ||
        /^[-*+]\s+\[( |x|X)\]\s+/.test(candidate) ||
        /^[-*+]\s+/.test(candidate) ||
        isOrderedListLine(candidate) ||
        /^(-{3,}|\*{3,}|_{3,})$/.test(candidate) ||
        /^(```|~~~)/.test(candidate)
      ) {
        break;
      }
      paragraphLines.push(rawCandidate);
      index += 1;
    }
    resetListContext();
    blocks.push({ type: "paragraph", text: joinMarkdownInlineLines(paragraphLines).trim() });
  }

  return blocks;
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderInlinePrintHtml(text: string, options: { preserveAsteriskLiterals?: boolean } = {}): string {
  const { text: escapedText, restore } = protectMarkdownEscapes(text);
  const pattern = options.preserveAsteriskLiterals
    ? /(<(?:sup|sub|ins|u)>[\s\S]*?<\/(?:sup|sub|ins|u)>|~~[^~]+~~|`[^`]+`|\[[^\]]+\]\([^)]+\))/g
    : /(<(?:sup|sub|ins|u)>[\s\S]*?<\/(?:sup|sub|ins|u)>|\*\*[^*]+\*\*|~~[^~]+~~|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g;

  return escapedText
    .split(/<br\s*\/?>/gi)
    .map((linePart) =>
      linePart
        .split(pattern)
        .filter(Boolean)
        .map((part) => {
          const tagMatch = part.match(/^<(sup|sub|ins|u)>([\s\S]*?)<\/\1>$/i);
          if (tagMatch) {
            const tag = tagMatch[1].toLowerCase() === "u" ? "ins" : tagMatch[1].toLowerCase();
            return `<${tag}>${renderInlinePrintHtml(restore(tagMatch[2]), options)}</${tag}>`;
          }
          if (!options.preserveAsteriskLiterals && /^\*\*[^*]+\*\*$/.test(part)) {
            return `<strong>${escapeHtml(restore(part.slice(2, -2)))}</strong>`;
          }
          if (!options.preserveAsteriskLiterals && /^\*[^*]+\*$/.test(part)) {
            return `<em>${escapeHtml(restore(part.slice(1, -1)))}</em>`;
          }
          if (/^~~[^~]+~~$/.test(part)) {
            return `<del>${escapeHtml(restore(part.slice(2, -2)))}</del>`;
          }
          if (/^`[^`]+`$/.test(part)) {
            return `<code>${escapeHtml(restore(part.slice(1, -1)))}</code>`;
          }
          const linkMatch = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
          if (linkMatch) {
            const label = escapeHtml(restore(linkMatch[1]));
            const href = escapeHtml(restore(linkMatch[2]));
            return `<a href="${href}">${label}</a>`;
          }
          return escapeHtml(restore(part));
        })
        .join(""),
    )
    .join("<br>");
}

function safeRawPrintHtml(html: string): string {
  return html
    .replace(/<script\b[\s\S]*?<\/script>/gi, "")
    .replace(/\son\w+=(?:"[^"]*"|'[^']*'|[^\s>]+)/gi, "");
}

function renderPrintBlockHtml(block: Block, blockIndex: number): string {
  const key = `block-${blockIndex}`;
  if (block.type === "heading") {
    const level = Math.max(1, Math.min(6, block.level));
    return `<h${level} class="md-heading md-heading-${level}" id="${key}">${renderInlinePrintHtml(block.text)}</h${level}>`;
  }
  if (block.type === "paragraph") {
    return `<p>${renderInlinePrintHtml(block.text)}</p>`;
  }
  if (block.type === "blockquote") {
    const marginClass = `indent-${Math.max(0, Math.min(4, block.level))}`;
    return `<blockquote class="${marginClass}">${block.paragraphs
      .map((paragraph) =>
        paragraph
          .split("\n")
          .map((quoteLine) => {
            const headingMatch = parseAtxHeadingLine(quoteLine);
            if (headingMatch) {
              const level = Math.max(1, Math.min(6, headingMatch.level));
              return `<h${level} class="md-heading md-heading-${level}">${renderInlinePrintHtml(headingMatch.text, { preserveAsteriskLiterals: true })}</h${level}>`;
            }
            return `<div>${renderInlinePrintHtml(quoteLine, { preserveAsteriskLiterals: true })}</div>`;
          })
          .join(""),
      )
      .join("")}</blockquote>`;
  }
  if (block.type === "list_item") {
    const visualLevel = block.visualLevel ?? block.level;
    const marker = escapeHtml(getListBullet(block.level, block.ordered, block.orderIndex, block.orderNumber));
    return `<div class="list-item indent-${Math.max(0, Math.min(4, visualLevel))}"><span class="marker">${marker}</span><div>${renderInlinePrintHtml(block.text)}</div></div>`;
  }
  if (block.type === "checklist_item") {
    const marker = block.checked ? "✓" : "";
    return `<div class="list-item indent-${Math.max(0, Math.min(4, block.level))}"><span class="checkbox">${marker}</span><div>${renderInlinePrintHtml(block.text)}</div></div>`;
  }
  if (block.type === "image") {
    return `<figure><img src="${escapeHtml(block.src)}" alt="${escapeHtml(block.alt)}">${block.alt ? `<figcaption>${escapeHtml(block.alt)}</figcaption>` : ""}</figure>`;
  }
  if (block.type === "table") {
    const columnCount = Math.max(block.headers.length, ...block.rows.map((row) => row.length));
    const header = `<tr>${Array.from({ length: columnCount })
      .map((_, index) => `<th>${renderInlinePrintHtml(block.headers[index] || "")}</th>`)
      .join("")}</tr>`;
    const rows = block.rows
      .map((row) => `<tr>${Array.from({ length: columnCount }).map((_, index) => `<td>${renderInlinePrintHtml(row[index] || "")}</td>`).join("")}</tr>`)
      .join("");
    return `<table>${header}${rows}</table>`;
  }
  if (block.type === "html_table") {
    return `<div class="table-wrap">${safeRawPrintHtml(block.rawHtml)}</div>`;
  }
  if (block.type === "rule") {
    return "<hr>";
  }
  if (block.type === "code") {
    return `<pre><code>${escapeHtml(block.lines.join("\n"))}</code></pre>`;
  }
  return "";
}

export function buildPrintDocumentHtml(markdown: string, title: string): string {
  const blocks = parseMarkdown(markdown);
  const body = blocks.map(renderPrintBlockHtml).join("\n");
  return `<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>${escapeHtml(title)}</title>
  <style>
    @page { margin: 14mm; }
    * { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; background: #fff; color: #2f2318; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Apple SD Gothic Neo", "Noto Sans KR", sans-serif; font-size: 16px; line-height: 1.62; }
    main { width: 100%; margin: 0; padding: 8px 0 0; background: #fff; border: 0; outline: 0; box-shadow: none; }
    h1, h2, h3, h4, h5, h6 { color: #7a3e12; margin: 0 0 12px; font-weight: 700; break-after: avoid; }
    h1 { font-size: 30px; line-height: 1.27; }
    h2 { font-size: 25px; line-height: 1.32; }
    h3 { font-size: 20px; line-height: 1.4; }
    h4 { font-size: 17px; line-height: 1.47; color: #8b5425; }
    h5 { font-size: 16px; line-height: 1.5; color: #8b5425; }
    h6 { font-size: 15px; line-height: 1.53; color: #8b5425; }
    p { margin: 0 0 12px; }
    a { color: #0f6f6f; text-decoration: underline; }
    code { font-family: "D2Coding", "Fira Code", Consolas, monospace; background: #f3ebe2; padding: 1px 4px; border-radius: 4px; }
    pre { white-space: pre-wrap; background: #f7efe6; padding: 12px; break-inside: avoid; }
    blockquote { margin: 0 0 12px; padding-left: 12px; border-left: 3px solid #c8a77d; color: #5c4632; break-inside: avoid; }
    blockquote > div + div { margin-top: 4px; }
    .list-item { display: flex; align-items: flex-start; gap: 8px; margin: 0 0 8px; }
    .marker { width: 24px; flex: 0 0 24px; text-align: right; color: #8b5425; }
    .checkbox { width: 18px; height: 18px; flex: 0 0 18px; margin-top: 4px; border: 1px solid #b5a695; border-radius: 4px; text-align: center; line-height: 16px; color: #0f6f6f; }
    .indent-0 { margin-left: 8px; }
    .indent-1 { margin-left: 24px; }
    .indent-2 { margin-left: 40px; }
    .indent-3 { margin-left: 56px; }
    .indent-4 { margin-left: 72px; }
    table { width: 100%; border-collapse: collapse; margin: 12px 0; break-inside: auto; }
    tr { break-inside: avoid; }
    th, td { border: 1px solid #ddd6cc; padding: 8px 10px; vertical-align: top; text-align: left; }
    th { background: #f4eadf; font-weight: 700; }
    figure { margin: 12px 0; break-inside: avoid; }
    img { display: block; max-width: 100%; height: auto; }
    figcaption { margin-top: 6px; color: #7c6a55; font-size: 13px; }
    hr { border: 0; border-top: 1px solid #d9c7ad; margin: 16px 0; }
    ins { text-decoration: underline; }
    sup { font-size: 0.7em; vertical-align: super; }
    sub { font-size: 0.7em; vertical-align: sub; }
  </style>
</head>
<body>
  <main>${body}</main>
  <script>
    window.addEventListener("load", () => {
      window.focus();
      window.print();
    });
  </script>
</body>
</html>`;
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

    const fenceMatch = trimmed.match(/^(```|~~~)([\w-]+)?$/);
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
      parseAtxHeadingLine(trimmed) ||
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

    if (/^[-*+]\s+\[( |x|X)\]\s+/.test(trimmed)) {
      while (index < lines.length && /^[-*+]\s+\[( |x|X)\]\s+/.test(lines[index].trim())) {
        const itemStart = currentLineStart();
        advanceLine(lines[index]);
        ranges.push({ start: itemStart, end: offset });
      }
      continue;
    }

    if (/^[-*+]\s+/.test(trimmed) || isOrderedListLine(trimmed)) {
      const ordered = isOrderedListLine(trimmed);
      while (index < lines.length) {
        const candidate = lines[index].trim();
        if (ordered ? isOrderedListLine(candidate) : /^[-*+]\s+/.test(candidate)) {
          const itemStart = currentLineStart();
          advanceLine(lines[index]);
          ranges.push({ start: itemStart, end: offset });
          continue;
        }
        break;
      }
      continue;
    }

    while (index < lines.length) {
      const candidate = lines[index].trim();
      if (
        !candidate ||
        parseAtxHeadingLine(candidate) ||
        /^>\s?/.test(candidate) ||
        /^!\[([^\]]*)\]\(([^)]+)\)$/.test(candidate) ||
        /^<table\b/i.test(candidate) ||
        (candidate.includes("|") && index + 1 < lines.length && isTableDivider(lines[index + 1].trim())) ||
        /^[-*+]\s+\[( |x|X)\]\s+/.test(candidate) ||
        /^[-*+]\s+/.test(candidate) ||
        isOrderedListLine(candidate) ||
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
      {blocks.map((block, blockIndex) => {
        const key = `${block.type}-${blockIndex}`;
        const isActive = blockIndex === activeBlockIndex;
        const blockHighlightStyle = isActive ? [styles.markdownActiveBlock, isDarkMode && styles.markdownActiveBlockDark] : undefined;

        if (block.type === "heading") {
          return (
            <View key={key} style={blockHighlightStyle} onLayout={(event) => handleBlockLayout(blockIndex, event)}>
              {renderInlineMarkdown(
                block.text,
                [
                  styles.markdownHeading,
                  isDarkMode && styles.markdownHeadingDark,
                  ...getHeadingLevelStyles(block.level),
                ] as unknown as object,
                key,
                isDarkMode,
              )}
            </View>
          );
        }

        if (block.type === "paragraph") {
          return (
            <View key={key} style={blockHighlightStyle} onLayout={(event) => handleBlockLayout(blockIndex, event)}>
              {renderInlineMarkdown(block.text, [styles.markdownParagraph, isDarkMode && styles.markdownParagraphDark] as unknown as object, key, isDarkMode)}
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
              onLayout={(event) => handleBlockLayout(blockIndex, event)}
              >
                {block.paragraphs.map((paragraph, paragraphIndex) => (
                  <View
                    key={`${key}-paragraph-${paragraphIndex}`}
                    style={paragraphIndex > 0 ? styles.markdownQuoteParagraph : undefined}
                  >
                    {paragraph.split("\n").map((quoteLine, quoteLineIndex) => (
                      <View
                        key={`${key}-paragraph-${paragraphIndex}-line-${quoteLineIndex}`}
                        style={quoteLineIndex > 0 ? styles.markdownQuoteLine : undefined}
                      >
                        {(() => {
                          const headingMatch = parseAtxHeadingLine(quoteLine);
                          if (headingMatch) {
                            return renderHeadingMarkdown(
                              headingMatch.text,
                              headingMatch.level,
                              `${key}-${paragraphIndex}-${quoteLineIndex}`,
                              isDarkMode,
                              true,
                            );
                          }

                          return renderInlineMarkdown(
                            quoteLine,
                            [styles.markdownQuoteText, isDarkMode && styles.markdownQuoteTextDark] as unknown as object,
                            `${key}-${paragraphIndex}-${quoteLineIndex}`,
                            isDarkMode,
                            { preserveAsteriskLiterals: true },
                          );
                        })()}
                      </View>
                    ))}
                  </View>
                ))}
              </View>
            );
        }

        if (block.type === "list_item") {
          return (
            <View key={key} style={[styles.markdownList, blockHighlightStyle]} onLayout={(event) => handleBlockLayout(blockIndex, event)}>
              <View
                style={[
                  styles.markdownListItem,
                  listIndent(block.visualLevel ?? block.level, block.ordered),
                ]}
              >
                <Text style={[styles.markdownListBullet, isDarkMode && styles.markdownListBulletDark]}>
                  {getListBullet(block.level, block.ordered, block.orderIndex, block.orderNumber)}
                </Text>
                <View style={styles.markdownListTextWrap}>
                  {renderInlineMarkdown(block.text, [styles.markdownListText, isDarkMode && styles.markdownListTextDark] as unknown as object, key, isDarkMode)}
                </View>
              </View>
            </View>
          );
        }

        if (block.type === "checklist_item") {
          return (
            <View key={key} style={[styles.markdownList, blockHighlightStyle]} onLayout={(event) => handleBlockLayout(blockIndex, event)}>
              <View
                style={[
                  styles.markdownListItem,
                  checklistIndent(block.level),
                ]}
              >
                <View style={[styles.markdownCheckbox, isDarkMode && styles.markdownCheckboxDark, block.checked && styles.markdownCheckboxChecked]}>
                  {block.checked ? <Text style={[styles.markdownCheckboxMark, isDarkMode && styles.markdownCheckboxMarkDark]}>✓</Text> : null}
                </View>
                <View style={styles.markdownListTextWrap}>
                  {renderInlineMarkdown(
                    block.text,
                    [styles.markdownListText, isDarkMode && styles.markdownListTextDark, block.checked && styles.markdownChecklistDone, block.checked && isDarkMode && styles.markdownChecklistDoneDark] as unknown as object,
                    key,
                    isDarkMode,
                  )}
                </View>
              </View>
            </View>
          );
        }

        if (block.type === "image") {
          return (
            <View key={key} style={blockHighlightStyle} onLayout={(event) => handleBlockLayout(blockIndex, event)}>
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
          const { columnWidths, needsHorizontalScroll, tableContentWidth } = computeTableLayout(
            block.headers,
            block.rows,
            columnCount,
            containerWidth,
          );

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
              <View key={key} style={blockHighlightStyle} onLayout={(event) => handleBlockLayout(blockIndex, event)}>
                <HtmlShell {...htmlShellProps}>
                  <HtmlTableFrame
                    html={block.rawHtml}
                    isDarkMode={isDarkMode}
                    minWidth={needsHorizontalScroll ? tableContentWidth : undefined}
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
            <View key={key} style={blockHighlightStyle} onLayout={(event) => handleBlockLayout(blockIndex, event)}>
              <TableShell {...tableShellProps}>
                <View
                  style={[
                    styles.markdownTable,
                    isDarkMode && styles.markdownTableDark,
                    needsHorizontalScroll && ({ width: tableContentWidth } satisfies ViewStyle),
                  ]}
                >
                  <View style={[styles.markdownTableRow, isDarkMode && styles.markdownTableRowDark, styles.markdownTableHeaderRow, isDarkMode && styles.markdownTableHeaderRowDark]}>
                    {Array.from({ length: columnCount }).map((_, columnIndex) => (
                      <View
                        key={`${key}-header-${columnIndex}`}
                        style={[
                          styles.markdownTableCell,
                          needsHorizontalScroll
                            ? ({ width: columnWidths[columnIndex].minWidth, minWidth: columnWidths[columnIndex].minWidth, flexGrow: 0 } satisfies ViewStyle)
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
                              ? ({ width: columnWidths[columnIndex].minWidth, minWidth: columnWidths[columnIndex].minWidth, flexGrow: 0 } satisfies ViewStyle)
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
          return <View key={key} style={[styles.markdownRule, isDarkMode && styles.markdownRuleDark, blockHighlightStyle]} onLayout={(event) => handleBlockLayout(blockIndex, event)} />;
        }

        return (
          <View key={key} style={[styles.markdownCodeBlock, blockHighlightStyle]} onLayout={(event) => handleBlockLayout(blockIndex, event)}>
            {block.language ? <Text style={styles.markdownCodeLanguage}>{block.language}</Text> : null}
            {block.lines.map((line, lineIndex) => (
              <Text key={`${key}-${lineIndex}`} style={styles.markdownCodeLine}>
                {line || " "}
              </Text>
            ))}
          </View>
        );
      })}
    </View>
  );
}
