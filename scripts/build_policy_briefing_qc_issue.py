from __future__ import annotations

import argparse
import json
from pathlib import Path


ISSUE_MARKER = "<!-- policy-briefing-qc-monitor -->"


def load_report(path: str | Path) -> dict[str, object]:
    payload = json.loads(Path(path).resolve().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Pipeline report must be a JSON object")
    return payload


def _build_title(report: dict[str, object]) -> str:
    return f"[QC] Policy briefing review required for {report.get('date')}"


def _collect_review_required_samples(report: dict[str, object]) -> list[dict[str, object]]:
    for entry in report.get("qc_commands", []):
        if not isinstance(entry, dict) or entry.get("command") != "triage":
            continue
        payload = entry.get("payload")
        if not isinstance(payload, dict):
            continue
        candidates = payload.get("entries")
        if not isinstance(candidates, list):
            continue
        return [
            item
            for item in candidates
            if isinstance(item, dict) and item.get("review_required") is True
        ]
    return []


def _collect_regression_failures(report: dict[str, object]) -> list[dict[str, object]]:
    for entry in report.get("qc_commands", []):
        if not isinstance(entry, dict) or entry.get("command") != "regression":
            continue
        payload = entry.get("payload")
        if not isinstance(payload, list):
            continue
        return [
            item
            for item in payload
            if isinstance(item, dict) and item.get("passed") is False
        ]
    return []


def _trim_text(value: object, *, limit: int = 280) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _collect_suggest_fix_proposals(report: dict[str, object]) -> list[dict[str, object]]:
    for entry in report.get("qc_commands", []):
        if not isinstance(entry, dict) or entry.get("command") != "suggest-fix":
            continue
        payload = entry.get("payload")
        if not isinstance(payload, dict):
            continue
        proposals = payload.get("proposals")
        if isinstance(proposals, list):
            return [item for item in proposals if isinstance(item, dict)]
    return []


def _collect_auto_patch_drafts(report: dict[str, object]) -> list[dict[str, object]]:
    for entry in report.get("qc_commands", []):
        if not isinstance(entry, dict) or entry.get("command") != "auto-patch-draft":
            continue
        payload = entry.get("payload")
        if not isinstance(payload, dict):
            continue
        drafts = payload.get("drafts")
        if isinstance(drafts, list):
            return [item for item in drafts if isinstance(item, dict)]
    return []


def _collect_fix_plans(report: dict[str, object]) -> list[dict[str, object]]:
    for entry in report.get("qc_commands", []):
        if not isinstance(entry, dict) or entry.get("command") != "fix-plan":
            continue
        payload = entry.get("payload")
        if not isinstance(payload, dict):
            continue
        plans = payload.get("plans")
        if isinstance(plans, list):
            return [item for item in plans if isinstance(item, dict)]
    return []


def _collect_apply_fix_hints(report: dict[str, object]) -> list[dict[str, object]]:
    for entry in report.get("qc_commands", []):
        if not isinstance(entry, dict) or entry.get("command") != "apply-fix-hint":
            continue
        payload = entry.get("payload")
        if not isinstance(payload, dict):
            continue
        hints = payload.get("hints")
        if isinstance(hints, list):
            return [item for item in hints if isinstance(item, dict)]
    return []


def build_issue_body(report: dict[str, object], *, summary_markdown: str | None = None) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    review_required = _collect_review_required_samples(report)
    regression_failures = _collect_regression_failures(report)
    suggest_fix_proposals = _collect_suggest_fix_proposals(report)
    auto_patch_drafts = _collect_auto_patch_drafts(report)
    fix_plans = _collect_fix_plans(report)
    apply_fix_hints = _collect_apply_fix_hints(report)

    lines = [
        ISSUE_MARKER,
        "",
        f"Policy briefing QC monitor detected follow-up work for `{report.get('date')}`.",
        "",
        "## Summary",
        "",
        f"- exported: `{summary.get('exported_count')}`",
        f"- scaffolded: `{summary.get('scaffolded_count')}`",
        f"- review_required: `{summary.get('review_required_count')}`",
        f"- proposals: `{summary.get('proposal_count')}`",
        f"- drafts: `{summary.get('draft_count')}`",
        "",
    ]

    if regression_failures:
        lines.extend(["## Regression Failures", ""])
        for item in regression_failures[:10]:
            sample_id = item.get("sample_id")
            finding_count = len(item.get("findings", [])) if isinstance(item.get("findings"), list) else 0
            lines.append(f"- `{sample_id}` findings=`{finding_count}`")
        lines.append("")

        lines.extend(["## Flagged Slice Preview", ""])
        for item in regression_failures[:5]:
            sample_id = item.get("sample_id")
            flagged_slices = item.get("flagged_slices", [])
            if not isinstance(flagged_slices, list) or not flagged_slices:
                continue
            lines.append(f"- sample: `{sample_id}`")
            for slice_payload in flagged_slices[:2]:
                if not isinstance(slice_payload, dict):
                    continue
                assertion_id = slice_payload.get("assertion_id")
                category = slice_payload.get("category")
                flag_reason = _trim_text(
                    slice_payload.get("flag_reason") or slice_payload.get("reason"),
                    limit=220,
                )
                source_summary = _trim_text(slice_payload.get("source_summary"), limit=220)
                markdown_slice = _trim_text(
                    slice_payload.get("markdown_slice") or slice_payload.get("markdown_preview"),
                    limit=320,
                )
                lines.append(f"  assertion: `{assertion_id}` category=`{category}`")
                if flag_reason:
                    lines.append(f"  why: {flag_reason}")
                if source_summary:
                    lines.append(f"  source: {source_summary}")
                if markdown_slice:
                    lines.append("  preview:")
                    lines.append("  ```text")
                    lines.append(markdown_slice)
                    lines.append("  ```")
            lines.append("")

        lines.extend(["## Secondary Signals", ""])
        for item in regression_failures[:5]:
            sample_id = item.get("sample_id")
            secondary_signals = item.get("secondary_signals", {})
            if not isinstance(secondary_signals, dict) or not secondary_signals:
                continue
            lines.append(f"- sample: `{sample_id}`")
            for key, value in list(secondary_signals.items())[:5]:
                lines.append(f"  {key}: `{_trim_text(value, limit=120)}`")
            lines.append("")

    if review_required:
        lines.extend(["## Review Required Samples", ""])
        for item in review_required[:10]:
            sample_id = item.get("sample_id")
            risk_score = item.get("risk_score")
            status = item.get("sample_status")
            lines.append(f"- `{sample_id}` risk=`{risk_score}` status=`{status}`")
        lines.append("")

    if suggest_fix_proposals:
        lines.extend(["## Immediate Fix Targets", ""])
        for proposal in suggest_fix_proposals[:5]:
            defect_class = proposal.get("defect_class")
            sample_ids = proposal.get("sample_ids", [])
            suggested_files = proposal.get("suggested_files", [])
            suggested_actions = proposal.get("suggested_actions", [])
            risk_notes = proposal.get("risk_notes", [])
            sample_summary = ", ".join(f"`{sample_id}`" for sample_id in sample_ids[:3]) or "-"
            file_summary = ", ".join(f"`{path}`" for path in suggested_files[:3]) or "-"
            lines.append(f"- defect: `{defect_class}`")
            lines.append(f"  samples: {sample_summary}")
            lines.append(f"  edit first: {file_summary}")
            if suggested_actions:
                lines.append(f"  first move: {suggested_actions[0]}")
            if len(suggested_actions) > 1:
                lines.append(f"  then: {suggested_actions[1]}")
            if risk_notes:
                lines.append(f"  guardrail: {risk_notes[0]}")
        lines.append("")

    if auto_patch_drafts:
        lines.extend(["## Patch Draft Summary", ""])
        for draft in auto_patch_drafts[:5]:
            defect_class = draft.get("defect_class")
            target_modules = draft.get("target_modules", [])
            draft_changes = draft.get("draft_changes", [])
            regression_targets = draft.get("regression_targets", [])
            post_patch_checks = draft.get("post_patch_checks", [])
            module_summary = ", ".join(f"`{path}`" for path in target_modules[:3]) or "-"
            regression_summary = ", ".join(f"`{path}`" for path in regression_targets[:3]) or "-"
            lines.append(f"- defect: `{defect_class}`")
            lines.append(f"  modules: {module_summary}")
            if draft_changes:
                lines.append(f"  patch: {draft_changes[0]}")
            if len(draft_changes) > 1:
                lines.append(f"  keep in mind: {draft_changes[1]}")
            lines.append(f"  regression: {regression_summary}")
            if post_patch_checks:
                lines.append(f"  validate: `{post_patch_checks[0]}`")
        lines.append("")

    if fix_plans:
        lines.extend(["## Investigation Commands", ""])
        for plan in fix_plans[:5]:
            defect_class = plan.get("defect_class")
            search_patterns = plan.get("search_patterns", [])
            inspect_commands = plan.get("inspect_commands", [])
            validation_commands = plan.get("validation_commands", [])
            implementation_notes = plan.get("implementation_notes", [])
            pattern_summary = ", ".join(f"`{pattern}`" for pattern in search_patterns[:4]) or "-"
            lines.append(f"- defect: `{defect_class}`")
            lines.append(f"  search: {pattern_summary}")
            if inspect_commands:
                lines.append(f"  inspect: `{inspect_commands[0]}`")
            if len(inspect_commands) > 1:
                lines.append(f"  inspect next: `{inspect_commands[1]}`")
            if validation_commands:
                lines.append(f"  validate after patch: `{validation_commands[0]}`")
            if implementation_notes:
                lines.append(f"  note: {implementation_notes[0]}")
        lines.append("")

    if apply_fix_hints:
        lines.extend(["## Copy-Paste Command Sequence", ""])
        for hint in apply_fix_hints[:5]:
            defect_class = hint.get("defect_class")
            command_sequence = hint.get("command_sequence", [])
            likely_edit_patterns = hint.get("likely_edit_patterns", [])
            assertion_update_hints = hint.get("assertion_update_hints", [])
            lines.append(f"- defect: `{defect_class}`")
            if likely_edit_patterns:
                lines.append(f"  patch pattern: {likely_edit_patterns[0]}")
            if assertion_update_hints:
                lines.append(f"  qc update: {assertion_update_hints[0]}")
            for command in command_sequence[:4]:
                lines.append(f"  cmd: `{command}`")
        lines.append("")

    if summary_markdown:
        lines.extend(
            [
                "## Attached Summary",
                "",
                "```md",
                summary_markdown.rstrip(),
                "```",
                "",
            ]
        )

    lines.extend(
        [
            "## Suggested Next Step",
            "",
            "Open `gov-md-converter`, patch the first target module from `Immediate Fix Targets`, then rerun the listed regression command before promoting any slices.",
            "",
        ]
    )
    return "\n".join(lines)


def build_issue_payload(report: dict[str, object], *, summary_markdown: str | None = None) -> dict[str, object]:
    return {
        "title": _build_title(report),
        "body": build_issue_body(report, summary_markdown=summary_markdown),
        "marker": ISSUE_MARKER,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a GitHub issue payload from a policy briefing QC pipeline report")
    parser.add_argument("report", help="Path to the aggregated pipeline JSON report")
    parser.add_argument("--summary-markdown", help="Optional path to an existing Markdown summary")
    parser.add_argument("--output", help="Optional path to write the payload JSON")
    parser.add_argument("--json", action="store_true", help="Print the payload as JSON")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = load_report(args.report)
    summary_text = None
    if args.summary_markdown:
        summary_text = Path(args.summary_markdown).resolve().read_text(encoding="utf-8")
    payload = build_issue_payload(report, summary_markdown=summary_text)
    if args.output:
        Path(args.output).resolve().write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.json or not args.output:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
