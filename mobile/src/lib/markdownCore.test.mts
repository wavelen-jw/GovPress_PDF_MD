import assert from "node:assert/strict";
import test from "node:test";

import { parseMarkdown } from "./markdownCore.ts";

test("parses the shared report structures without a rendering framework", () => {
  const blocks = parseMarkdown(`# 보고서

## 추진계획

- 핵심 과제
  - 세부 과제

| 단계 | 목표\\|기준 |
| --- | --- |
| 1단계 | 시범<br>적용 |

> 검토 필요`);

  assert.deepEqual(
    blocks.map((block) => block.type),
    ["heading", "heading", "paragraph", "list_item", "table", "blockquote"],
  );
  assert.deepEqual(blocks.find((block) => block.type === "table"), {
    type: "table",
    headers: ["단계", "목표|기준"],
    aligns: ["left", "left"],
    rows: [["1단계", "시범\n적용"]],
  });
});

test("keeps executable HTML as inert parsed data", () => {
  const blocks = parseMarkdown("<script>alert(1)</script>");
  assert.deepEqual(blocks, [{ type: "paragraph", text: "<script>alert(1)</script>" }]);
});
