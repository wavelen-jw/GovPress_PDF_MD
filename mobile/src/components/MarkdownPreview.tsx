import React, { useMemo, useState } from "react";
import { Image, LayoutChangeEvent, Linking, Platform, ScrollView, Text, View, type ViewStyle } from "react-native";

import { styles } from "../styles";

type TableAlign = "left" | "center" | "right";

type TableColumnWidth = {
  minWidth: number;
  preferredWidth: number;
  flexGrow: number;
};

type Block =
  | { type: "heading"; level: number; text: string }
  | { type: "paragraph"; text: string }
  | { type: "blockquote"; paragraphs: string[]; level: number }
  | { type: "list_item"; ordered: boolean; level: number; text: string; orderIndex: number; orderNumber?: number }
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

function splitTableRow(line: string): string[] {
  return line
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => cell.trim().replace(/<br\s*\/?>/gi, "\n"));
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
}: {
  html: string;
  isDarkMode?: boolean;
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

function renderInlineMarkdown(text: string, textStyle: object, keyPrefix: string, isDarkMode = false) {
  const pattern = /(\*\*[^*]+\*\*|~~[^~]+~~|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g;
  const matches = text.split(pattern).filter(Boolean);

  return (
    <Text style={textStyle}>
      {matches.map((part, index) => {
        const key = `${keyPrefix}-${index}`;
        if (/^\*\*[^*]+\*\*$/.test(part)) {
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
        return <Text key={key}>{part}</Text>;
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
      level === 1 && styles.markdownHeading1,
      level === 2 && styles.markdownHeading2,
      level >= 3 && styles.markdownHeading3,
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

  while (index < lines.length) {
    const rawLine = lines[index];
    const trimmed = rawLine.trim();

    if (!trimmed) {
      blankRun += 1;
      if (blankRun >= 2) {
        orderedSequenceByLevel.clear();
      }
      index += 1;
      continue;
    }

    blankRun = 0;

    const codeFenceMatch = trimmed.match(/^```([\w-]+)?$/);
    if (codeFenceMatch) {
      const codeLines: string[] = [];
      const language = codeFenceMatch[1] || null;
      index += 1;
      while (index < lines.length && !/^```/.test(lines[index].trim())) {
        codeLines.push(lines[index]);
        index += 1;
      }
      if (index < lines.length) {
        index += 1;
      }
      blocks.push({ type: "code", language, lines: codeLines });
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
      const quotedHtml = quoteLines.join("\n").trim();
      if (/<table\b[\s\S]*<\/table>/i.test(quotedHtml) || /^<table\b/i.test(quotedHtml) || /^<tr\b/i.test(quotedHtml)) {
        const parsed = parseHtmlTableBlock(quotedHtml);
        if (parsed) {
          blocks.push({ type: "html_table", headers: parsed.headers, rows: parsed.rows, rawHtml: parsed.rawHtml });
          continue;
        }
      }
      const paragraphs: string[] = [];
      let paragraphBuffer: string[] = [];
      for (const line of quoteLines) {
        if (!line.trim()) {
          if (paragraphBuffer.length) {
            paragraphs.push(paragraphBuffer.join("\n"));
            paragraphBuffer = [];
          }
          continue;
        }
        paragraphBuffer.push(line);
      }
      if (paragraphBuffer.length) {
        paragraphs.push(paragraphBuffer.join("\n"));
      }
      blocks.push({ type: "blockquote", paragraphs: paragraphs.length ? paragraphs : [""], level: quoteLevel });
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

    if (/^[-*]\s+\[( |x|X)\]\s+/.test(trimmed)) {
      while (index < lines.length) {
        const rawCandidate = lines[index];
        const candidate = rawCandidate.trim();
        const match = candidate.match(/^[-*]\s+\[( |x|X)\]\s+(.*)$/);
        if (!match) {
          break;
        }
        const indent = rawCandidate.match(/^\s*/)?.[0].length || 0;
        const level = Math.min(3, Math.floor(indent / 2));
        blocks.push({
          type: "checklist_item",
          checked: match[1].toLowerCase() === "x",
          level,
          text: match[2].trim(),
        });
        index += 1;
      }
      continue;
    }

    if (/^[-*]\s+/.test(trimmed) || /^\d+\.\s+/.test(trimmed)) {
      const ordered = /^\d+\.\s+/.test(trimmed);
      let orderIndex = 0;
      while (index < lines.length) {
        const rawCandidate = lines[index];
        const candidate = rawCandidate.trim();
        const indent = rawCandidate.match(/^\s*/)?.[0].length || 0;
        const level = Math.min(3, Math.floor(indent / 2));
        if (ordered && /^\d+\.\s+/.test(candidate)) {
          const orderedMatch = candidate.match(/^(\d+)\.\s+(.*)$/);
          if (!orderedMatch) {
            break;
          }
          for (const existingLevel of [...orderedSequenceByLevel.keys()]) {
            if (existingLevel > level) {
              orderedSequenceByLevel.delete(existingLevel);
            }
          }
          const sourceNumber = Number(orderedMatch[1]);
          const previousNumber = orderedSequenceByLevel.get(level);
          // Reset counter when source restarts from 1 (new section), otherwise increment from previous
          const isNewSequence = sourceNumber === 1 && previousNumber !== undefined && previousNumber > 1;
          if (isNewSequence) {
            orderedSequenceByLevel.delete(level);
          }
          const orderNumber = !isNewSequence && previousNumber !== undefined ? previousNumber + 1 : sourceNumber;
          orderedSequenceByLevel.set(level, orderNumber);
          blocks.push({
            type: "list_item",
            ordered: true,
            level,
            text: orderedMatch[2].trim(),
            orderIndex,
            orderNumber,
          });
          orderIndex += 1;
          index += 1;
          continue;
        }
        if (!ordered && /^[-*]\s+/.test(candidate)) {
          blocks.push({
            type: "list_item",
            ordered: false,
            level,
            text: candidate.replace(/^[-*]\s+/, "").trim(),
            orderIndex,
          });
          index += 1;
          continue;
        }
        break;
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
        /^[-*]\s+\[( |x|X)\]\s+/.test(candidate) ||
        /^[-*]\s+/.test(candidate) ||
        /^\d+\.\s+/.test(candidate) ||
        /^(-{3,}|\*{3,}|_{3,})$/.test(candidate) ||
        /^```/.test(candidate)
      ) {
        break;
      }
      paragraphLines.push(candidate);
      index += 1;
    }
    blocks.push({ type: "paragraph", text: paragraphLines.join(" ") });
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

    if (/^```([\w-]+)?$/.test(trimmed)) {
      advanceLine(rawLine);
      while (index < lines.length && !/^```/.test(lines[index].trim())) {
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

    if (/^[-*]\s+\[( |x|X)\]\s+/.test(trimmed)) {
      while (index < lines.length && /^[-*]\s+\[( |x|X)\]\s+/.test(lines[index].trim())) {
        const itemStart = currentLineStart();
        advanceLine(lines[index]);
        ranges.push({ start: itemStart, end: offset });
      }
      continue;
    }

    if (/^[-*]\s+/.test(trimmed) || /^\d+\.\s+/.test(trimmed)) {
      const ordered = /^\d+\.\s+/.test(trimmed);
      while (index < lines.length) {
        const candidate = lines[index].trim();
        if (ordered ? /^\d+\.\s+/.test(candidate) : /^[-*]\s+/.test(candidate)) {
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
        /^(#{1,6})\s+/.test(candidate) ||
        /^>\s?/.test(candidate) ||
        /^!\[([^\]]*)\]\(([^)]+)\)$/.test(candidate) ||
        /^<table\b/i.test(candidate) ||
        (candidate.includes("|") && index + 1 < lines.length && isTableDivider(lines[index + 1].trim())) ||
        /^[-*]\s+\[( |x|X)\]\s+/.test(candidate) ||
        /^[-*]\s+/.test(candidate) ||
        /^\d+\.\s+/.test(candidate) ||
        /^(-{3,}|\*{3,}|_{3,})$/.test(candidate) ||
        /^```/.test(candidate)
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
    level >= 3 && styles.markdownHeading3,
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
  const blocks = parseMarkdown(markdown);
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
                  block.level === 1 && styles.markdownHeading1,
                  block.level === 2 && styles.markdownHeading2,
                  block.level >= 3 && styles.markdownHeading3,
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
                block.level > 0 && { marginLeft: block.level * 18 },
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
                          const headingMatch = quoteLine.trim().match(/^(#{1,6})\s+(.*)$/);
                          if (headingMatch) {
                            return renderHeadingMarkdown(
                              headingMatch[2].trim(),
                              headingMatch[1].length,
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
                  block.level > 0 && { marginLeft: block.level * 18 },
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
                  block.level > 0 && { marginLeft: block.level * 18 },
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
          const columnWidths = computeTableColumnWidths(block.headers, block.rows, columnCount);
          const tableMinimumWidth = columnWidths.reduce((sum, column) => sum + column.minWidth, 0);
          const needsHorizontalScroll =
            columnCount >= 5 && containerWidth > 0 && tableMinimumWidth > containerWidth - 12;

          if (block.type === "html_table" && Platform.OS === "web") {
            return (
              <View key={key} style={blockHighlightStyle} onLayout={(event) => handleBlockLayout(blockIndex, event)}>
                <HtmlTableFrame html={block.rawHtml} isDarkMode={isDarkMode} />
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
