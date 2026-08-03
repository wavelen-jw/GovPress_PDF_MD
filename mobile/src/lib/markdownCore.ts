export type MarkdownTableAlign = "left" | "center" | "right";

export type MarkdownQuoteChild =
  | { type: "quote_text"; paragraphs: string[] }
  | {
      type: "quote_list_item";
      ordered: boolean;
      level: number;
      visualLevel?: number;
      text: string;
      orderIndex: number;
      orderNumber?: number;
    }
  | {
      type: "quote_table";
      headers: string[];
      aligns: MarkdownTableAlign[];
      rows: string[][];
    }
  | { type: "blockquote"; children: MarkdownQuoteChild[]; level: number };

export type MarkdownBlock =
  | { type: "heading"; level: number; text: string }
  | { type: "paragraph"; text: string }
  | { type: "blockquote"; children: MarkdownQuoteChild[]; level: number }
  | {
      type: "list_item";
      ordered: boolean;
      level: number;
      visualLevel?: number;
      text: string;
      orderIndex: number;
      orderNumber?: number;
    }
  | { type: "checklist_item"; checked: boolean; level: number; text: string }
  | { type: "image"; alt: string; src: string }
  | {
      type: "table";
      headers: string[];
      aligns: MarkdownTableAlign[];
      rows: string[][];
    }
  | { type: "html_table"; headers: string[]; rows: string[][]; rawHtml: string }
  | { type: "rule" }
  | { type: "code"; language: string | null; lines: string[] };

const MAX_ORDERED_LIST_NUMBER = 17;

function isEscaped(value: string, index: number): boolean {
  let slashCount = 0;
  for (let cursor = index - 1; cursor >= 0 && value[cursor] === "\\"; cursor -= 1) {
    slashCount += 1;
  }
  return slashCount % 2 === 1;
}

function hasClosingBacktick(value: string, startIndex: number): boolean {
  for (let index = startIndex + 1; index < value.length; index += 1) {
    if (value[index] === "`" && !isEscaped(value, index)) return true;
  }
  return false;
}

function parseAtxHeadingLine(line: string): { level: number; text: string } | null {
  const match = line.trim().match(/^(#{1,6})(?:[ \t]+|$)(.*)$/);
  if (!match) return null;
  return {
    level: match[1].length,
    text: match[2].replace(/[ \t]+#+[ \t]*$/, "").trim(),
  };
}

function matchOrderedListMarker(line: string): RegExpMatchArray | null {
  const match = line.match(/^(\d+)\.\s+(.*)$/);
  if (!match) return null;
  const markerNumber = Number(match[1]);
  return Number.isInteger(markerNumber) && markerNumber >= 1 && markerNumber <= MAX_ORDERED_LIST_NUMBER
    ? match
    : null;
}

function isOrderedListLine(line: string): boolean {
  return matchOrderedListMarker(line) !== null;
}

function isSubtitleDashLine(
  line: string,
  blockCount: number,
  previousBlockType?: MarkdownBlock["type"],
): boolean {
  return (
    blockCount <= 2 &&
    (previousBlockType === "heading" || previousBlockType === "paragraph") &&
    /^-\s+\S/.test(line) &&
    !/^-\s+\[( |x|X)\]\s+/.test(line)
  );
}

function hasHardLineBreakSuffix(line: string): boolean {
  return /[ \t]{2,}$/.test(line) || /(?<!\\)\\$/.test(line);
}

function stripHardLineBreakSuffix(line: string): string {
  if (/[ \t]{2,}$/.test(line)) return line.replace(/[ \t]+$/, "");
  if (/(?<!\\)\\$/.test(line)) return line.replace(/\\$/, "");
  return line;
}

function joinMarkdownInlineLines(lines: string[]): string {
  if (!lines.length) return "";
  let result = stripHardLineBreakSuffix(lines[0]);
  for (let index = 1; index < lines.length; index += 1) {
    result += hasHardLineBreakSuffix(lines[index - 1]) ? "<br>" : " ";
    result += stripHardLineBreakSuffix(lines[index]);
  }
  return result;
}

function splitTableRow(line: string): string[] {
  let source = line.trim();
  if (source.startsWith("|")) source = source.slice(1);
  if (source.endsWith("|") && !isEscaped(source, source.length - 1)) source = source.slice(0, -1);
  const cells: string[] = [];
  let current = "";
  let inCode = false;
  for (let index = 0; index < source.length; index += 1) {
    const character = source[index];
    if (character === "`" && !isEscaped(source, index)) {
      if (inCode || hasClosingBacktick(source, index)) inCode = !inCode;
    }
    if (character === "|" && !inCode && !isEscaped(source, index)) {
      cells.push(current.trim());
      current = "";
    } else current += character;
  }
  cells.push(current.trim());
  return cells.map((cell) => cell.replace(/\\\|/g, "|").replace(/<br\s*\/?>/gi, "\n"));
}

function isTableDivider(line: string): boolean {
  const cells = splitTableRow(line);
  return cells.length > 0 && cells.every((cell) => /^:?-{3,}:?$/.test(cell.trim()));
}

function parseTableAlignments(line: string): MarkdownTableAlign[] {
  return splitTableRow(line).map((cell) => {
    const trimmed = cell.trim();
    if (trimmed.startsWith(":") && trimmed.endsWith(":")) return "center";
    if (trimmed.endsWith(":")) return "right";
    return "left";
  });
}

function decodeHtmlEntities(text: string): string {
  return text
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/&quot;/gi, '"')
    .replace(/&#39;/gi, "'");
}

function stripHtmlTags(text: string): string {
  return decodeHtmlEntities(
    text.replace(/<br\s*\/?>/gi, "\n").replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim(),
  );
}

function extractHtmlTableCells(rowHtml: string, tagName: "th" | "td"): string[] {
  const cells: string[] = [];
  const expression = new RegExp(`<${tagName}\\b[^>]*>([\\s\\S]*?)<\\/${tagName}>`, "gi");
  let match: RegExpExecArray | null;
  while ((match = expression.exec(rowHtml)) !== null) cells.push(stripHtmlTags(match[1]));
  return cells;
}

function parseHtmlTableBlock(
  tableHtml: string,
): { headers: string[]; rows: string[][]; rawHtml: string } | null {
  const rowPattern = /<tr\b[^>]*>([\s\S]*?)<\/tr>/gi;
  const rows: string[][] = [];
  let headers: string[] = [];
  let rowMatch = rowPattern.exec(tableHtml);
  while (rowMatch) {
    const headerCells = extractHtmlTableCells(rowMatch[1], "th");
    const bodyCells = extractHtmlTableCells(rowMatch[1], "td");
    if (!headers.length && headerCells.length) headers = headerCells;
    else if (bodyCells.length) rows.push(bodyCells);
    else if (headerCells.length) rows.push(headerCells);
    rowMatch = rowPattern.exec(tableHtml);
  }
  if (!headers.length && rows.length) headers = rows.shift() || [];
  return headers.length ? { headers, rows, rawHtml: tableHtml } : null;
}

function parseQuoteListMarker(line: string): {
  ordered: boolean;
  level: number;
  text: string;
  orderNumber?: number;
} | null {
  const unordered = line.match(/^(\s*)([+])\s+(.*)$/);
  if (unordered) {
    return {
      ordered: false,
      level: Math.min(3, Math.floor(unordered[1].length / 2)),
      text: stripHardLineBreakSuffix(unordered[3]).trimEnd(),
    };
  }
  const ordered = line.match(/^(\s*)(\d+)\.\s+(.*)$/);
  if (ordered) {
    const orderNumber = Number(ordered[2]);
    if (!Number.isInteger(orderNumber) || orderNumber < 1 || orderNumber > MAX_ORDERED_LIST_NUMBER) return null;
    return {
      ordered: true,
      level: Math.min(3, Math.floor(ordered[1].length / 2)),
      text: stripHardLineBreakSuffix(ordered[3]).trimEnd(),
      orderNumber,
    };
  }
  return null;
}

function parseQuoteChildren(lines: string[]): MarkdownQuoteChild[] {
  const children: MarkdownQuoteChild[] = [];
  let index = 0;
  let paragraphBuffer: string[] = [];
  let paragraphs: string[] = [];
  let quoteOrderIndex = 0;
  const flushParagraph = () => {
    if (paragraphBuffer.length) {
      paragraphs.push(joinMarkdownInlineLines(paragraphBuffer));
      paragraphBuffer = [];
    }
  };
  const flushText = () => {
    flushParagraph();
    if (paragraphs.length) {
      children.push({ type: "quote_text", paragraphs });
      paragraphs = [];
    }
  };
  while (index < lines.length) {
    const line = lines[index];
    const nestedStartMatch = line.match(/^(\s*)>\s?(.*)$/);
    if (nestedStartMatch) {
      flushText();
      const nestedLevel = Math.min(4, Math.floor(nestedStartMatch[1].length / 2));
      const nestedLines: string[] = [];
      while (index < lines.length) {
        const nested = lines[index].match(/^(\s*)>\s?(.*)$/);
        if (!nested || Math.min(4, Math.floor(nested[1].length / 2)) !== nestedLevel) break;
        nestedLines.push(nested[2]);
        index += 1;
      }
      children.push({ type: "blockquote", children: parseQuoteChildren(nestedLines), level: nestedLevel });
      continue;
    }
    if (line.trim().includes("|") && index + 1 < lines.length && isTableDivider(lines[index + 1].trim())) {
      flushText();
      const headers = splitTableRow(line.trim());
      const aligns = parseTableAlignments(lines[index + 1].trim());
      const rows: string[][] = [];
      index += 2;
      while (index < lines.length && lines[index].trim() && lines[index].includes("|")) {
        rows.push(splitTableRow(lines[index].trim()));
        index += 1;
      }
      children.push({ type: "quote_table", headers, aligns, rows });
      continue;
    }
    const marker = parseQuoteListMarker(line);
    if (marker) {
      flushText();
      const itemLines = [marker.text];
      index += 1;
      while (index < lines.length) {
        const continuation = lines[index];
        if (!continuation.trim() || continuation.match(/^(\s*)>\s?(.*)$/) || parseQuoteListMarker(continuation)) break;
        if ((continuation.match(/^\s*/)?.[0].length ?? 0) < 2) break;
        itemLines.push(stripHardLineBreakSuffix(continuation.trim()).trimEnd());
        index += 1;
      }
      children.push({
        type: "quote_list_item",
        ordered: marker.ordered,
        level: marker.level,
        text: itemLines.join("<br>"),
        orderIndex: quoteOrderIndex,
        orderNumber: marker.orderNumber,
      });
      quoteOrderIndex += 1;
      continue;
    }
    if (!line.trim()) {
      flushParagraph();
      paragraphs.push("");
      index += 1;
      continue;
    }
    paragraphBuffer.push(line);
    index += 1;
  }
  flushText();
  return children.length ? children : [{ type: "quote_text", paragraphs: [""] }];
}

export function parseMarkdown(markdown: string): MarkdownBlock[] {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const blocks: MarkdownBlock[] = [];
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
    const previousBlockType = blocks[blocks.length - 1]?.type;
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
      index += 1;
      while (index < lines.length && !lines[index].trim().startsWith(fence)) {
        codeLines.push(lines[index]);
        index += 1;
      }
      if (index < lines.length) index += 1;
      resetListContext();
      blocks.push({ type: "code", language: codeFenceMatch[2] || null, lines: codeLines });
      continue;
    }
    const headingMatch = parseAtxHeadingLine(trimmed);
    if (headingMatch) {
      resetListContext();
      blocks.push({ type: "heading", ...headingMatch });
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
      const quoteLevel = Math.min(4, Math.floor(quoteStartMatch[1].length / 2));
      const quoteLines: string[] = [];
      while (index < lines.length) {
        const current = lines[index].match(/^(\s*)>\s?(.*)$/);
        if (!current || Math.min(4, Math.floor(current[1].length / 2)) !== quoteLevel) break;
        quoteLines.push(current[2]);
        index += 1;
      }
      const quotedHtml = quoteLines.join("\n").trim();
      if (/<table\b[\s\S]*<\/table>/i.test(quotedHtml) || /^<(?:table|tr)\b/i.test(quotedHtml)) {
        const parsed = parseHtmlTableBlock(quotedHtml);
        if (parsed) {
          blocks.push({ type: "html_table", ...parsed });
          continue;
        }
      }
      blocks.push({ type: "blockquote", children: parseQuoteChildren(quoteLines), level: quoteLevel });
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
      blocks.push(
        parsed
          ? { type: "html_table", ...parsed }
          : { type: "paragraph", text: stripHtmlTags(inlineHtmlTableMatch[0]) },
      );
      index += 1;
      continue;
    }
    if (/^<(?:table|tr)\b/i.test(trimmed)) {
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
      const rawHtml = htmlLines.join("\n");
      const parsed = parseHtmlTableBlock(rawHtml);
      blocks.push(parsed ? { type: "html_table", ...parsed } : { type: "paragraph", text: stripHtmlTags(rawHtml) });
      continue;
    }
    if (trimmed.includes("|") && index + 1 < lines.length && isTableDivider(lines[index + 1].trim())) {
      resetListContext();
      const headers = splitTableRow(trimmed);
      const aligns = parseTableAlignments(lines[index + 1]);
      const rows: string[][] = [];
      index += 2;
      while (index < lines.length) {
        const candidate = lines[index].trim();
        if (!candidate) {
          if (index + 1 < lines.length && lines[index + 1].trim().startsWith("|")) {
            index += 1;
            continue;
          }
          break;
        }
        if (!candidate.includes("|")) break;
        rows.push(splitTableRow(candidate));
        index += 1;
      }
      blocks.push({ type: "table", headers, aligns, rows });
      continue;
    }
    if (isSubtitleDashLine(trimmed, blocks.length, previousBlockType)) {
      blocks.push({ type: "paragraph", text: stripHardLineBreakSuffix(trimmed) });
      index += 1;
      continue;
    }
    if (/^[-*+]\s+\[( |x|X)\]\s+/.test(trimmed)) {
      resetListContext();
      while (index < lines.length) {
        const rawCandidate = lines[index];
        const match = rawCandidate.trim().match(/^[-*+]\s+\[( |x|X)\]\s+(.*)$/);
        if (!match) break;
        const indent = rawCandidate.match(/^\s*/)?.[0].length ?? 0;
        blocks.push({
          type: "checklist_item",
          checked: match[1].toLowerCase() === "x",
          level: Math.min(3, Math.floor(indent / 2)),
          text: stripHardLineBreakSuffix(match[2].trimEnd()),
        });
        index += 1;
      }
      continue;
    }
    if (/^[-*+]\s+/.test(trimmed) || isOrderedListLine(trimmed)) {
      const ordered = isOrderedListLine(trimmed);
      let orderIndex = 0;
      while (index < lines.length) {
        const rawCandidate = lines[index];
        const candidate = rawCandidate.trim();
        const level = Math.min(3, Math.floor((rawCandidate.match(/^\s*/)?.[0].length ?? 0) / 2));
        if (ordered && isOrderedListLine(candidate)) {
          const match = matchOrderedListMarker(candidate);
          if (!match) break;
          for (const existingLevel of [...orderedSequenceByLevel.keys()]) {
            if (existingLevel > level) orderedSequenceByLevel.delete(existingLevel);
          }
          const sourceNumber = Number(match[1]);
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
          blocks.push({
            type: "list_item",
            ordered: false,
            level,
            visualLevel: level,
            text: stripHardLineBreakSuffix(rawCandidate.replace(/^(\s*[-*+]\s+)/, "")).trimEnd(),
            orderIndex,
          });
          index += 1;
          continue;
        }
        break;
      }
      if (!ordered) resetListContext();
      continue;
    }
    const paragraphLines: string[] = [];
    while (index < lines.length) {
      const rawCandidate = lines[index];
      const candidate = rawCandidate.trim();
      if (
        !candidate ||
        parseAtxHeadingLine(candidate) ||
        /^\s*>\s?/.test(rawCandidate) ||
        /^!\[([^\]]*)\]\(([^)]+)\)$/.test(candidate) ||
        /^<(?:table|tr)\b/i.test(candidate) ||
        (candidate.includes("|") && index + 1 < lines.length && isTableDivider(lines[index + 1].trim())) ||
        /^[-*+]\s+\[( |x|X)\]\s+/.test(candidate) ||
        (/^[-*+]\s+/.test(candidate) && !isSubtitleDashLine(candidate, blocks.length, previousBlockType)) ||
        isOrderedListLine(candidate) ||
        /^(-{3,}|\*{3,}|_{3,})$/.test(candidate) ||
        /^(```|~~~)/.test(candidate)
      ) break;
      paragraphLines.push(rawCandidate);
      index += 1;
    }
    resetListContext();
    blocks.push({ type: "paragraph", text: joinMarkdownInlineLines(paragraphLines).trim() });
  }
  return blocks;
}
