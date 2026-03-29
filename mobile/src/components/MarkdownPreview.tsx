import React, { useMemo, useState } from "react";
import { Image, LayoutChangeEvent, Linking, Platform, ScrollView, Text, View } from "react-native";

import { styles } from "../styles";

type TableAlign = "left" | "center" | "right";

type Block =
  | { type: "heading"; level: number; text: string }
  | { type: "paragraph"; text: string }
  | { type: "blockquote"; paragraphs: string[] }
  | { type: "list_item"; ordered: boolean; level: number; text: string; orderIndex: number }
  | { type: "checklist_item"; checked: boolean; level: number; text: string }
  | { type: "image"; alt: string; src: string }
  | { type: "table"; headers: string[]; aligns: TableAlign[]; rows: string[][] }
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

function textAlignStyle(align: TableAlign) {
  if (align === "center") {
    return styles.markdownTableTextCenter;
  }
  if (align === "right") {
    return styles.markdownTableTextRight;
  }
  return styles.markdownTableTextLeft;
}

function getListBullet(level: number, ordered: boolean, itemIndex: number): string {
  if (ordered) {
    return `${itemIndex + 1}.`;
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

  while (index < lines.length) {
    const rawLine = lines[index];
    const trimmed = rawLine.trim();

    if (!trimmed) {
      index += 1;
      continue;
    }

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

    if (/^>\s?/.test(trimmed)) {
      const quoteLines: string[] = [];
      while (index < lines.length && /^>\s?/.test(lines[index].trim())) {
        quoteLines.push(lines[index].trim().replace(/^>\s?/, ""));
        index += 1;
      }
      const paragraphs: string[] = [];
      let paragraphBuffer: string[] = [];
      for (const line of quoteLines) {
        if (!line.trim()) {
          if (paragraphBuffer.length) {
            paragraphs.push(paragraphBuffer.join(" "));
            paragraphBuffer = [];
          }
          continue;
        }
        paragraphBuffer.push(line);
      }
      if (paragraphBuffer.length) {
        paragraphs.push(paragraphBuffer.join(" "));
      }
      blocks.push({ type: "blockquote", paragraphs: paragraphs.length ? paragraphs : [""] });
      continue;
    }

    const imageMatch = trimmed.match(/^!\[([^\]]*)\]\(([^)]+)\)$/);
    if (imageMatch) {
      blocks.push({ type: "image", alt: imageMatch[1].trim(), src: imageMatch[2].trim() });
      index += 1;
      continue;
    }

    if (trimmed.includes("|") && index + 1 < lines.length && isTableDivider(lines[index + 1].trim())) {
      const headers = splitTableRow(trimmed);
      const aligns = parseTableAlignments(lines[index + 1].trim());
      const rows: string[][] = [];
      index += 2;
      while (index < lines.length) {
        const candidate = lines[index].trim();
        if (!candidate || !candidate.includes("|")) {
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
          blocks.push({
            type: "list_item",
            ordered: true,
            level,
            text: candidate.replace(/^\d+\.\s+/, "").trim(),
            orderIndex,
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

    if (/^>\s?/.test(trimmed)) {
      while (index < lines.length && /^>\s?/.test(lines[index].trim())) {
        advanceLine(lines[index]);
      }
      ranges.push({ start: blockStart, end: offset });
      continue;
    }

    if (trimmed.includes("|") && index + 1 < lines.length && isTableDivider(lines[index + 1].trim())) {
      advanceLine(rawLine);
      advanceLine(lines[index]);
      while (index < lines.length) {
        const candidate = lines[index].trim();
        if (!candidate || !candidate.includes("|")) {
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

  function handleBlockLayout(blockIndex: number, event: LayoutChangeEvent): void {
    onBlockLayout?.(blockIndex, event.nativeEvent.layout.y);
  }

  if (!blocks.length) {
    return <Text style={[styles.previewEmpty, isDarkMode && styles.previewEmptyDark]}>표시할 Markdown 내용이 없습니다.</Text>;
  }

  return (
    <View style={styles.markdownPreview}>
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
            <View key={key} style={[styles.markdownQuote, isDarkMode && styles.markdownQuoteDark, blockHighlightStyle]} onLayout={(event) => handleBlockLayout(blockIndex, event)}>
              {block.paragraphs.map((paragraph, paragraphIndex) => (
                <View
                  key={`${key}-paragraph-${paragraphIndex}`}
                  style={paragraphIndex > 0 ? styles.markdownQuoteParagraph : undefined}
                >
                  {renderInlineMarkdown(paragraph, [styles.markdownQuoteText, isDarkMode && styles.markdownQuoteTextDark] as unknown as object, `${key}-${paragraphIndex}`, isDarkMode)}
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
                  {getListBullet(block.level, block.ordered, block.orderIndex)}
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

        if (block.type === "table") {
          const columnCount = Math.max(
            block.headers.length,
            block.aligns.length,
            ...block.rows.map((row) => row.length),
          );
          return (
            <View key={key} style={blockHighlightStyle} onLayout={(event) => handleBlockLayout(blockIndex, event)}>
              <ScrollView
                horizontal
                showsHorizontalScrollIndicator
                style={styles.markdownTableWrap}
                contentContainerStyle={styles.markdownTableScrollContent}
              >
                <View style={[styles.markdownTable, isDarkMode && styles.markdownTableDark]}>
                  <View style={[styles.markdownTableRow, isDarkMode && styles.markdownTableRowDark, styles.markdownTableHeaderRow, isDarkMode && styles.markdownTableHeaderRowDark]}>
                    {Array.from({ length: columnCount }).map((_, columnIndex) => (
                      <View
                        key={`${key}-header-${columnIndex}`}
                        style={[
                          styles.markdownTableCell,
                            styles.markdownTableHeaderCell,
                            isDarkMode && styles.markdownTableCellDark,
                            isDarkMode && styles.markdownTableHeaderCellDark,
                            columnIndex === columnCount - 1 && styles.markdownTableCellLast,
                          ]}
                        >
                        {renderInlineMarkdown(
                          block.headers[columnIndex] || "",
                          [styles.markdownTableHeaderText, isDarkMode && styles.markdownTableHeaderTextDark, textAlignStyle(block.aligns[columnIndex] || "left")] as unknown as object,
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
                            isDarkMode && styles.markdownTableCellDark,
                            columnIndex === columnCount - 1 && styles.markdownTableCellLast,
                          ]}
                        >
                          {renderInlineMarkdown(
                            row[columnIndex] || "",
                            [styles.markdownTableCellText, isDarkMode && styles.markdownTableCellTextDark, textAlignStyle(block.aligns[columnIndex] || "left")] as unknown as object,
                            `${key}-${rowIndex}-${columnIndex}`,
                            isDarkMode,
                          )}
                        </View>
                      ))}
                    </View>
                  ))}
                </View>
              </ScrollView>
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
