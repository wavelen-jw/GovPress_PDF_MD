import React from "react";
import { Text, View } from "react-native";

import { styles } from "../styles";

type DiffRow =
  | { type: "added"; text: string; section: string }
  | { type: "removed"; text: string; section: string }
  | { type: "changed"; before: string; after: string; section: string };

type DiffToken = {
  text: string;
  changed: boolean;
};

function splitWords(value: string): string[] {
  return value.split(/(\s+)/).filter((token) => token.length > 0);
}

type DiffUnit = {
  section: string;
  text: string;
};

function isBlockBoundary(line: string): boolean {
  const trimmed = line.trim();
  if (!trimmed) {
    return true;
  }
  return (
    /^(#{1,6})\s+/.test(trimmed) ||
    /^>\s?/.test(trimmed) ||
    /^!\[([^\]]*)\]\(([^)]+)\)$/.test(trimmed) ||
    /^[-*]\s+\[( |x|X)\]\s+/.test(trimmed) ||
    /^[-*]\s+/.test(trimmed) ||
    /^\d+\.\s+/.test(trimmed) ||
    /^(-{3,}|\*{3,}|_{3,})$/.test(trimmed) ||
    /^```/.test(trimmed) ||
    trimmed.includes("|")
  );
}

function normalizeForDiff(markdown: string): DiffUnit[] {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const units: DiffUnit[] = [];
  let currentSection = "문서 본문";
  let paragraphBuffer: string[] = [];

  const flushParagraph = () => {
    if (!paragraphBuffer.length) {
      return;
    }
    units.push({
      section: currentSection,
      text: paragraphBuffer.join(" ").replace(/\s+/g, " ").trim(),
    });
    paragraphBuffer = [];
  };

  for (const rawLine of lines) {
    const trimmed = rawLine.trim();
    const sectionMatch = trimmed.match(/^#{1,6}\s+(.+)$/);
    if (sectionMatch) {
      flushParagraph();
      currentSection = sectionMatch[1].trim();
      units.push({ section: currentSection, text: trimmed });
      continue;
    }
    if (!trimmed) {
      flushParagraph();
      continue;
    }
    if (isBlockBoundary(trimmed)) {
      flushParagraph();
      units.push({ section: currentSection, text: trimmed });
      continue;
    }
    paragraphBuffer.push(trimmed);
  }

  flushParagraph();
  return units;
}

function buildInlineDiff(before: string, after: string): { beforeTokens: DiffToken[]; afterTokens: DiffToken[] } {
  const beforeWords = splitWords(before);
  const afterWords = splitWords(after);
  const count = Math.max(beforeWords.length, afterWords.length);
  const beforeTokens: DiffToken[] = [];
  const afterTokens: DiffToken[] = [];

  for (let index = 0; index < count; index += 1) {
    const prev = beforeWords[index];
    const next = afterWords[index];
    if (prev !== undefined) {
      beforeTokens.push({ text: prev, changed: prev !== next });
    }
    if (next !== undefined) {
      afterTokens.push({ text: next, changed: prev !== next });
    }
  }

  return { beforeTokens, afterTokens };
}

type DiffOp =
  | { type: "equal"; before: DiffUnit; after: DiffUnit }
  | { type: "added"; after: DiffUnit }
  | { type: "removed"; before: DiffUnit };

function buildLcsMatrix(before: DiffUnit[], after: DiffUnit[]): number[][] {
  const matrix = Array.from({ length: before.length + 1 }, () => Array(after.length + 1).fill(0));
  for (let i = before.length - 1; i >= 0; i -= 1) {
    for (let j = after.length - 1; j >= 0; j -= 1) {
      if (before[i].text === after[j].text) {
        matrix[i][j] = matrix[i + 1][j + 1] + 1;
      } else {
        matrix[i][j] = Math.max(matrix[i + 1][j], matrix[i][j + 1]);
      }
    }
  }
  return matrix;
}

function buildDiffOps(before: DiffUnit[], after: DiffUnit[]): DiffOp[] {
  const matrix = buildLcsMatrix(before, after);
  const ops: DiffOp[] = [];
  let i = 0;
  let j = 0;

  while (i < before.length && j < after.length) {
    if (before[i].text === after[j].text) {
      ops.push({ type: "equal", before: before[i], after: after[j] });
      i += 1;
      j += 1;
      continue;
    }
    if (matrix[i + 1][j] >= matrix[i][j + 1]) {
      ops.push({ type: "removed", before: before[i] });
      i += 1;
    } else {
      ops.push({ type: "added", after: after[j] });
      j += 1;
    }
  }

  while (i < before.length) {
    ops.push({ type: "removed", before: before[i] });
    i += 1;
  }
  while (j < after.length) {
    ops.push({ type: "added", after: after[j] });
    j += 1;
  }

  return ops;
}

function buildDiffRows(original: string, edited: string): DiffRow[] {
  const before = normalizeForDiff(original);
  const after = normalizeForDiff(edited);
  const ops = buildDiffOps(before, after);
  const rows: DiffRow[] = [];

  for (let index = 0; index < ops.length; index += 1) {
    const op = ops[index];
    if (op.type === "equal") {
      continue;
    }

    const nextOp = ops[index + 1];
    if (op.type === "removed" && nextOp?.type === "added" && op.before.section === nextOp.after.section) {
      rows.push({
        type: "changed",
        before: op.before.text,
        after: nextOp.after.text,
        section: op.before.section,
      });
      index += 1;
      continue;
    }

    if (op.type === "added") {
      rows.push({ type: "added", text: op.after.text, section: op.after.section });
      continue;
    }

    rows.push({ type: "removed", text: op.before.text, section: op.before.section });
  }

  return rows;
}

export function DiffPreview({
  original,
  edited,
  isDarkMode = false,
}: {
  original: string;
  edited: string;
  isDarkMode?: boolean;
}) {
  const rows = buildDiffRows(original, edited);
  const summary = rows.reduce(
    (acc, row) => {
      acc[row.type] += 1;
      acc.sections.add(row.section);
      return acc;
    },
    { added: 0, removed: 0, changed: 0, sections: new Set<string>() },
  );

  if (!rows.length) {
    return <Text style={[styles.previewEmpty, isDarkMode && styles.previewEmptyDark]}>변경된 내용이 없습니다.</Text>;
  }

  return (
    <View style={styles.diffPreview}>
      <View style={[styles.diffSummaryCard, isDarkMode && styles.diffSummaryCardDark]}>
        <View style={styles.diffSummaryRow}>
          <View style={[styles.diffSummaryPill, styles.diffCardAdded]}>
            <Text style={[styles.diffSummaryLabel, isDarkMode && styles.diffSummaryLabelDark]}>추가 {summary.added}</Text>
          </View>
          <View style={[styles.diffSummaryPill, styles.diffCardRemoved]}>
            <Text style={[styles.diffSummaryLabel, isDarkMode && styles.diffSummaryLabelDark]}>삭제 {summary.removed}</Text>
          </View>
          <View style={[styles.diffSummaryPill, styles.diffCardChanged]}>
            <Text style={[styles.diffSummaryLabel, isDarkMode && styles.diffSummaryLabelDark]}>변경 {summary.changed}</Text>
          </View>
        </View>
        <Text style={[styles.diffSummaryText, isDarkMode && styles.diffSummaryTextDark]}>
          영향 섹션: {[...summary.sections].slice(0, 4).join(", ")}
          {summary.sections.size > 4 ? ` 외 ${summary.sections.size - 4}` : ""}
        </Text>
      </View>
      {rows.map((row, index) => {
        const key = `diff-${index}`;

        if (row.type === "added") {
          return (
            <View key={key} style={[styles.diffCard, styles.diffCardAdded]}>
              <Text style={[styles.diffLabel, isDarkMode && styles.diffLabelDark]}>추가</Text>
              <Text style={[styles.diffText, isDarkMode && styles.diffTextDark]}>{row.text || " "}</Text>
            </View>
          );
        }

        if (row.type === "removed") {
          return (
            <View key={key} style={[styles.diffCard, styles.diffCardRemoved]}>
              <Text style={[styles.diffLabel, isDarkMode && styles.diffLabelDark]}>삭제</Text>
              <Text style={[styles.diffText, isDarkMode && styles.diffTextDark]}>{row.text || " "}</Text>
            </View>
          );
        }

        const { beforeTokens, afterTokens } = buildInlineDiff(row.before, row.after);

        return (
          <View key={key} style={[styles.diffCard, styles.diffCardChanged]}>
            <Text style={[styles.diffLabel, isDarkMode && styles.diffLabelDark]}>변경</Text>
            <Text style={[styles.diffBefore, isDarkMode && styles.diffBeforeDark]}>
              {beforeTokens.map((token, tokenIndex) => (
                <Text key={`before-${key}-${tokenIndex}`} style={token.changed ? styles.diffBeforeChanged : undefined}>
                  {token.text}
                </Text>
              ))}
            </Text>
            <Text style={[styles.diffArrow, isDarkMode && styles.diffArrowDark]}>{"->"}</Text>
            <Text style={[styles.diffAfter, isDarkMode && styles.diffAfterDark]}>
              {afterTokens.map((token, tokenIndex) => (
                <Text key={`after-${key}-${tokenIndex}`} style={token.changed ? styles.diffAfterChanged : undefined}>
                  {token.text}
                </Text>
              ))}
            </Text>
          </View>
        );
      })}
    </View>
  );
}
