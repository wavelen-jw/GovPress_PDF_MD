import React, { useState } from "react";
import { Image, Linking, Platform, ScrollView, Text, View } from "react-native";

import { styles } from "../styles";

type TableAlign = "left" | "center" | "right";

type Block =
  | { type: "heading"; level: number; text: string }
  | { type: "paragraph"; text: string }
  | { type: "blockquote"; paragraphs: string[] }
  | { type: "list"; ordered: boolean; items: { level: number; text: string }[] }
  | { type: "checklist"; items: { checked: boolean; level: number; text: string }[] }
  | { type: "image"; alt: string; src: string }
  | { type: "table"; headers: string[]; aligns: TableAlign[]; rows: string[][] }
  | { type: "rule" }
  | { type: "code"; language: string | null; lines: string[] };

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

function openExternalLink(url: string): void {
  if (Platform.OS === "web" && typeof window !== "undefined") {
    window.open(url, "_blank", "noopener,noreferrer");
    return;
  }
  void Linking.openURL(url);
}

function renderInlineMarkdown(text: string, textStyle: object, keyPrefix: string) {
  const pattern = /(\*\*[^*]+\*\*|~~[^~]+~~|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g;
  const matches = text.split(pattern).filter(Boolean);

  return (
    <Text style={textStyle}>
      {matches.map((part, index) => {
        const key = `${keyPrefix}-${index}`;
        if (/^\*\*[^*]+\*\*$/.test(part)) {
          return (
            <Text key={key} style={styles.markdownStrong}>
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
            <Text key={key} style={styles.markdownStrike}>
              {part.slice(2, -2)}
            </Text>
          );
        }
        if (/^`[^`]+`$/.test(part)) {
          return (
            <Text key={key} style={styles.markdownInlineCode}>
              {part.slice(1, -1)}
            </Text>
          );
        }
        const linkMatch = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
        if (linkMatch) {
          return (
            <Text
              key={key}
              style={styles.markdownLink}
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

function MarkdownImage({ alt, src }: { alt: string; src: string }) {
  const [failed, setFailed] = useState(false);

  if (failed) {
    return (
      <View style={styles.markdownImageFallback}>
        <Text style={styles.markdownImageFallbackTitle}>이미지를 불러오지 못했습니다.</Text>
        <Text style={styles.markdownImageFallbackUrl}>{src}</Text>
        {alt ? <Text style={styles.markdownImageCaption}>{alt}</Text> : null}
      </View>
    );
  }

  return (
    <View style={styles.markdownImageWrap}>
      <Image source={{ uri: src }} style={styles.markdownImage} resizeMode="contain" onError={() => setFailed(true)} />
      {alt ? <Text style={styles.markdownImageCaption}>{alt}</Text> : null}
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
      const items: { checked: boolean; level: number; text: string }[] = [];
      while (index < lines.length) {
        const rawCandidate = lines[index];
        const candidate = rawCandidate.trim();
        const match = candidate.match(/^[-*]\s+\[( |x|X)\]\s+(.*)$/);
        if (!match) {
          break;
        }
        const indent = rawCandidate.match(/^\s*/)?.[0].length || 0;
        const level = Math.min(3, Math.floor(indent / 2));
        items.push({
          checked: match[1].toLowerCase() === "x",
          level,
          text: match[2].trim(),
        });
        index += 1;
      }
      blocks.push({ type: "checklist", items });
      continue;
    }

    if (/^[-*]\s+/.test(trimmed) || /^\d+\.\s+/.test(trimmed)) {
      const ordered = /^\d+\.\s+/.test(trimmed);
      const items: { level: number; text: string }[] = [];
      while (index < lines.length) {
        const rawCandidate = lines[index];
        const candidate = rawCandidate.trim();
        const indent = rawCandidate.match(/^\s*/)?.[0].length || 0;
        const level = Math.min(3, Math.floor(indent / 2));
        if (ordered && /^\d+\.\s+/.test(candidate)) {
          items.push({ level, text: candidate.replace(/^\d+\.\s+/, "").trim() });
          index += 1;
          continue;
        }
        if (!ordered && /^[-*]\s+/.test(candidate)) {
          items.push({ level, text: candidate.replace(/^[-*]\s+/, "").trim() });
          index += 1;
          continue;
        }
        break;
      }
      blocks.push({ type: "list", ordered, items });
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

export function MarkdownPreview({ markdown }: { markdown: string }) {
  const blocks = parseMarkdown(markdown);

  if (!blocks.length) {
    return <Text style={styles.previewEmpty}>표시할 Markdown 내용이 없습니다.</Text>;
  }

  return (
    <View style={styles.markdownPreview}>
      {blocks.map((block, blockIndex) => {
        const key = `${block.type}-${blockIndex}`;

        if (block.type === "heading") {
          return (
            <View key={key}>
              {renderInlineMarkdown(
                block.text,
                [
                  styles.markdownHeading,
                  block.level === 1 && styles.markdownHeading1,
                  block.level === 2 && styles.markdownHeading2,
                  block.level >= 3 && styles.markdownHeading3,
                ] as unknown as object,
                key,
              )}
            </View>
          );
        }

        if (block.type === "paragraph") {
          return <View key={key}>{renderInlineMarkdown(block.text, styles.markdownParagraph, key)}</View>;
        }

        if (block.type === "blockquote") {
          return (
            <View key={key} style={styles.markdownQuote}>
              {block.paragraphs.map((paragraph, paragraphIndex) => (
                <View
                  key={`${key}-paragraph-${paragraphIndex}`}
                  style={paragraphIndex > 0 ? styles.markdownQuoteParagraph : undefined}
                >
                  {renderInlineMarkdown(paragraph, styles.markdownQuoteText, `${key}-${paragraphIndex}`)}
                </View>
              ))}
            </View>
          );
        }

        if (block.type === "list") {
          return (
            <View key={key} style={styles.markdownList}>
              {block.items.map((item, itemIndex) => (
                <View
                  key={`${key}-${itemIndex}`}
                  style={[
                    styles.markdownListItem,
                    item.level > 0 && { marginLeft: item.level * 18 },
                  ]}
                >
                  <Text style={styles.markdownListBullet}>
                    {block.ordered ? `${itemIndex + 1}.` : "•"}
                  </Text>
                  <View style={styles.markdownListTextWrap}>
                    {renderInlineMarkdown(item.text, styles.markdownListText, `${key}-${itemIndex}`)}
                  </View>
                </View>
              ))}
            </View>
          );
        }

        if (block.type === "checklist") {
          return (
            <View key={key} style={styles.markdownList}>
              {block.items.map((item, itemIndex) => (
                <View
                  key={`${key}-${itemIndex}`}
                  style={[
                    styles.markdownListItem,
                    item.level > 0 && { marginLeft: item.level * 18 },
                  ]}
                >
                  <View style={[styles.markdownCheckbox, item.checked && styles.markdownCheckboxChecked]}>
                    {item.checked ? <Text style={styles.markdownCheckboxMark}>✓</Text> : null}
                  </View>
                  <View style={styles.markdownListTextWrap}>
                    {renderInlineMarkdown(
                      item.text,
                      [styles.markdownListText, item.checked && styles.markdownChecklistDone] as unknown as object,
                      `${key}-${itemIndex}`,
                    )}
                  </View>
                </View>
              ))}
            </View>
          );
        }

        if (block.type === "image") {
          return <MarkdownImage key={key} alt={block.alt} src={block.src} />;
        }

        if (block.type === "table") {
          const columnCount = Math.max(
            block.headers.length,
            block.aligns.length,
            ...block.rows.map((row) => row.length),
          );
          return (
            <ScrollView
              key={key}
              horizontal
              showsHorizontalScrollIndicator
              contentContainerStyle={styles.markdownTableScrollContent}
            >
              <View style={styles.markdownTable}>
                <View style={[styles.markdownTableRow, styles.markdownTableHeaderRow]}>
                  {Array.from({ length: columnCount }).map((_, columnIndex) => (
                    <View
                      key={`${key}-header-${columnIndex}`}
                      style={[
                        styles.markdownTableCell,
                        styles.markdownTableHeaderCell,
                        columnIndex === columnCount - 1 && styles.markdownTableCellLast,
                      ]}
                    >
                      {renderInlineMarkdown(
                        block.headers[columnIndex] || "",
                        [styles.markdownTableHeaderText, textAlignStyle(block.aligns[columnIndex] || "left")] as unknown as object,
                        `${key}-header-${columnIndex}`,
                      )}
                    </View>
                  ))}
                </View>
                {block.rows.map((row, rowIndex) => (
                  <View
                    key={`${key}-row-${rowIndex}`}
                    style={[
                      styles.markdownTableRow,
                      rowIndex === block.rows.length - 1 && styles.markdownTableRowLast,
                    ]}
                  >
                    {Array.from({ length: columnCount }).map((_, columnIndex) => (
                      <View
                        key={`${key}-${rowIndex}-${columnIndex}`}
                        style={[
                          styles.markdownTableCell,
                          columnIndex === columnCount - 1 && styles.markdownTableCellLast,
                        ]}
                      >
                        {renderInlineMarkdown(
                          row[columnIndex] || "",
                          [styles.markdownTableCellText, textAlignStyle(block.aligns[columnIndex] || "left")] as unknown as object,
                          `${key}-${rowIndex}-${columnIndex}`,
                        )}
                      </View>
                    ))}
                  </View>
                ))}
              </View>
            </ScrollView>
          );
        }

        if (block.type === "rule") {
          return <View key={key} style={styles.markdownRule} />;
        }

        return (
          <View key={key} style={styles.markdownCodeBlock}>
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
