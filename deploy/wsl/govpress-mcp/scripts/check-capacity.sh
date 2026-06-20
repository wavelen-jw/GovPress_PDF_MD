#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

MIN_C_FREE_GB="${MIN_C_FREE_GB:-80}"
MIN_D_FREE_GB="${MIN_D_FREE_GB:-500}"
MAX_RAW_GB="${MAX_RAW_GB:-40}"
MAX_DATA_GB="${MAX_DATA_GB:-120}"

gb_available() {
  local path="$1"
  df -BG "$path" | awk 'NR == 2 { gsub(/G/, "", $4); print $4 }'
}

gb_used() {
  local path="$1"
  if [[ -e "$path" ]]; then
    du -sBG "$path" | awk '{ gsub(/G/, "", $1); print $1 }'
  else
    echo 0
  fi
}

fail=0
c_free="$(gb_available /mnt/c)"
d_free="$(gb_available /mnt/d)"
raw_used="$(gb_used data/raw)"
data_used="$(gb_used data)"

if (( c_free < MIN_C_FREE_GB )); then
  echo "capacity_error c_free_gb=$c_free min_c_free_gb=$MIN_C_FREE_GB" >&2
  fail=1
fi

if (( d_free < MIN_D_FREE_GB )); then
  echo "capacity_error d_free_gb=$d_free min_d_free_gb=$MIN_D_FREE_GB" >&2
  fail=1
fi

if (( raw_used > MAX_RAW_GB )); then
  echo "capacity_error raw_used_gb=$raw_used max_raw_gb=$MAX_RAW_GB" >&2
  fail=1
fi

if (( data_used > MAX_DATA_GB )); then
  echo "capacity_error data_used_gb=$data_used max_data_gb=$MAX_DATA_GB" >&2
  fail=1
fi

if (( fail != 0 )); then
  exit 1
fi

echo "capacity_ok c_free_gb=$c_free d_free_gb=$d_free raw_used_gb=$raw_used data_used_gb=$data_used"
