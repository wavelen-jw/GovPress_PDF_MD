import { STATUS_TONE } from "../constants";
import type { JobStatus } from "../types";

export function jobStatusPillStyle(status: JobStatus) {
  return {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 999,
    overflow: "hidden" as const,
    color: STATUS_TONE[status],
    backgroundColor: `${STATUS_TONE[status]}18`,
    fontWeight: "700" as const,
    fontSize: 12,
  };
}

export function detailBadgeStyle(status: JobStatus) {
  return {
    color: "#fffaf4",
    backgroundColor: STATUS_TONE[status],
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 8,
    fontWeight: "700" as const,
    alignSelf: "flex-start" as const,
  };
}
