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

function buildDiffRows(original: string, edited: string): DiffRow[] {
  const before = original.split("\n");
  const after = edited.split("\n");
  const rows: DiffRow[] = [];
  const count = Math.max(before.length, after.length);
  let currentSection = "문서 본문";

  for (let index = 0; index < count; index += 1) {
    const prev = before[index] ?? "";
    const next = after[index] ?? "";
    const sectionSource = next || prev;
    const sectionMatch = sectionSource.match(/^#{1,6}\s+(.+)$/);
    if (sectionMatch) {
      currentSection = sectionMatch[1].trim();
    }
    if (prev === next) {
      continue;
    }
    if (!prev && next) {
      rows.push({ type: "added", text: next, section: currentSection });
      continue;
    }
    if (prev && !next) {
      rows.push({ type: "removed", text: prev, section: currentSection });
      continue;
    }
    rows.push({ type: "changed", before: prev, after: next, section: currentSection });
  }

  return rows;
}

export function DiffPreview({
  original,
  edited,
}: {
  original: string;
  edited: string;
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
    return <Text style={styles.previewEmpty}>변경된 내용이 없습니다.</Text>;
  }

  return (
    <View style={styles.diffPreview}>
      <View style={styles.diffSummaryCard}>
        <View style={styles.diffSummaryRow}>
          <View style={[styles.diffSummaryPill, styles.diffCardAdded]}>
            <Text style={styles.diffSummaryLabel}>추가 {summary.added}</Text>
          </View>
          <View style={[styles.diffSummaryPill, styles.diffCardRemoved]}>
            <Text style={styles.diffSummaryLabel}>삭제 {summary.removed}</Text>
          </View>
          <View style={[styles.diffSummaryPill, styles.diffCardChanged]}>
            <Text style={styles.diffSummaryLabel}>변경 {summary.changed}</Text>
          </View>
        </View>
        <Text style={styles.diffSummaryText}>
          영향 섹션: {[...summary.sections].slice(0, 4).join(", ")}
          {summary.sections.size > 4 ? ` 외 ${summary.sections.size - 4}` : ""}
        </Text>
      </View>
      {rows.map((row, index) => {
        const key = `diff-${index}`;

        if (row.type === "added") {
          return (
            <View key={key} style={[styles.diffCard, styles.diffCardAdded]}>
              <Text style={styles.diffSection}>{row.section}</Text>
              <Text style={styles.diffLabel}>추가</Text>
              <Text style={styles.diffText}>{row.text || " "}</Text>
            </View>
          );
        }

        if (row.type === "removed") {
          return (
            <View key={key} style={[styles.diffCard, styles.diffCardRemoved]}>
              <Text style={styles.diffSection}>{row.section}</Text>
              <Text style={styles.diffLabel}>삭제</Text>
              <Text style={styles.diffText}>{row.text || " "}</Text>
            </View>
          );
        }

        const { beforeTokens, afterTokens } = buildInlineDiff(row.before, row.after);

        return (
          <View key={key} style={[styles.diffCard, styles.diffCardChanged]}>
            <Text style={styles.diffSection}>{row.section}</Text>
            <Text style={styles.diffLabel}>변경</Text>
            <Text style={styles.diffBefore}>
              {beforeTokens.map((token, tokenIndex) => (
                <Text key={`before-${key}-${tokenIndex}`} style={token.changed ? styles.diffBeforeChanged : undefined}>
                  {token.text}
                </Text>
              ))}
            </Text>
            <Text style={styles.diffArrow}>{"->"}</Text>
            <Text style={styles.diffAfter}>
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
