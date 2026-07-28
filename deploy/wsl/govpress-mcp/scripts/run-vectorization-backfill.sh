#!/usr/bin/env bash
set -Eeuo pipefail

# Sequential and resumable by verified batch markers.

ROOT="${1:-data/fetch-log/metadata-migration/full-api-overwrite-vector-missing-v1}"
IDS_FILE="${2:-$ROOT/server-v-vectorization.ids}"
CONTAINER="${MCP_CONTAINER:-govpress-mcp-server-1}"
BATCH_SIZE="${VECTOR_DOCUMENT_BATCH:-250}"
PIPELINE_HOST="${PIPELINE_HOST:-scripts/derive-targeted-pipeline.py}"
PIPELINE_CONTAINER="/tmp/derive-targeted-pipeline.py"
LOCK_FILE="$ROOT/vectorization.lock"
MEMBERS_FILE="$ROOT/server-v-vectorization.members"
BATCH_PREFIX="$ROOT/vector-batch-"
SCOPE_FILE="$ROOT/vectorization-scope.sha256"

[[ "$BATCH_SIZE" =~ ^[1-9][0-9]*$ ]] || {
  echo "invalid VECTOR_DOCUMENT_BATCH: $BATCH_SIZE" >&2
  exit 2
}
[[ -f "$IDS_FILE" && -f "$PIPELINE_HOST" ]] || {
  echo "missing IDs or pipeline: $IDS_FILE $PIPELINE_HOST" >&2
  exit 1
}
docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null |
  grep -qx true || {
    echo "container not running: $CONTAINER" >&2
    exit 1
  }

mkdir -p "$ROOT"
exec 9>"$LOCK_FILE"
flock -n 9 || {
  echo "another vectorization backfill is running: $LOCK_FILE" >&2
  exit 1
}

scope="$(
  {
    sha256sum "$IDS_FILE"
    printf 'batch_size=%s\n' "$BATCH_SIZE"
  } | sha256sum | cut -d' ' -f1
)"
if [[ -f "$SCOPE_FILE" ]]; then
  [[ "$(cat "$SCOPE_FILE")" == "$scope" ]] || {
    echo "existing batches belong to a different ID scope" >&2
    exit 1
  }
else
  python3 - "$IDS_FILE" data/md "$MEMBERS_FILE" <<'PY'
import re
import sys
from pathlib import Path

ids_path, md_root, output = map(Path, sys.argv[1:])
ids = [
    line.strip()
    for line in ids_path.read_text(encoding="utf-8").splitlines()
    if line.strip()
]
wanted = set(ids)
found: dict[str, Path] = {}
duplicates: set[str] = set()
pattern = re.compile(r"^(\d+)(?:_|$)")
for path in md_root.glob("*/*/*.md"):
    match = pattern.match(path.stem)
    if not match or match.group(1) not in wanted:
        continue
    identifier = match.group(1)
    if identifier in found:
        duplicates.add(identifier)
    else:
        found[identifier] = path
missing = sorted(wanted - found.keys())
if missing or duplicates:
    raise SystemExit(
        f"Markdown mapping invalid: missing={len(missing)} "
        f"duplicates={len(duplicates)}"
    )
lines = []
for identifier in ids:
    path = found[identifier]
    year, month = path.parent.parent.name, path.parent.name
    lines.append(f"data/raw/{year}/{month}/{path.stem}.hwpx")
output.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"members={len(lines)} missing=0 duplicates=0")
PY
  rm -f -- "${BATCH_PREFIX}"*.members
  split -l "$BATCH_SIZE" -d -a 4 --additional-suffix=.members \
    "$MEMBERS_FILE" "$BATCH_PREFIX"
  printf '%s\n' "$scope" >"$SCOPE_FILE"
fi

mapfile -t batches < <(find "$ROOT" -maxdepth 1 -name 'vector-batch-*.members' | sort)
total="${#batches[@]}"
if [[ "${PREPARE_ONLY:-0}" == "1" ]]; then
  printf 'vectorization prepared batches=%s documents=%s\n' \
    "$total" "$(wc -l <"$IDS_FILE")"
  exit 0
fi

docker cp "$PIPELINE_HOST" "$CONTAINER:$PIPELINE_CONTAINER" >/dev/null
docker exec "$CONTAINER" python -m py_compile "$PIPELINE_CONTAINER"

completed=0
for batch in "${batches[@]}"; do
  name="$(basename "$batch" .members)"
  log="$ROOT/$name.log"
  done_file="$ROOT/$name.done"
  if [[ -f "$done_file" ]]; then
    completed=$((completed + 1))
    printf 'skip verified batch=%s progress=%s/%s\n' "$name" "$completed" "$total"
    continue
  fi

  printf 'start batch=%s progress=%s/%s documents=%s\n' \
    "$name" "$((completed + 1))" "$total" "$(wc -l <"$batch")"
  docker exec --workdir /app "$CONTAINER" \
    python "$PIPELINE_CONTAINER" \
    "/app/$batch" /app/data /app/data/govpress.db \
    http://qdrant:6333 http://tei:80 250 \
    --batch 512 \
    --inflight 4 \
    --prepare-workers 8 \
    --force \
    --qdrant-only \
    2>&1 | tee "$log"
  grep -q 'targeted_pipeline complete=' "$log" || {
    echo "batch verification marker missing: $name" >&2
    exit 1
  }
  {
    printf 'completed_at=%s\n' "$(date --iso-8601=seconds)"
    sha256sum "$batch" "$log"
  } >"$done_file.tmp"
  mv "$done_file.tmp" "$done_file"
  completed=$((completed + 1))
  printf 'complete batch=%s progress=%s/%s\n' "$name" "$completed" "$total"
done

printf 'vectorization backfill complete batches=%s documents=%s\n' \
  "$total" "$(wc -l <"$IDS_FILE")"
