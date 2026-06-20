#!/usr/bin/env bash
set -euo pipefail

input="${1:?input .hwp path required}"
output="${2:?output .hwpx path required}"

script_dir="$(cd "$(dirname "$0")" && pwd)"
script_win="$(wslpath -aw "$script_dir/hancom_hwp2hwpx_windows.py")"
input_win="$(wslpath -aw "$input")"
output_win="$(wslpath -aw "$output")"

cmd_bin="${CMD_EXE:-}"
if [[ -z "$cmd_bin" ]]; then
  if command -v cmd.exe >/dev/null 2>&1; then
    cmd_bin="$(command -v cmd.exe)"
  elif [[ -x /mnt/c/Windows/System32/cmd.exe ]]; then
    cmd_bin="/mnt/c/Windows/System32/cmd.exe"
  else
    echo "cmd.exe not found. Enable WSL interop or set CMD_EXE=/mnt/c/Windows/System32/cmd.exe." >&2
    exit 127
  fi
fi

win_python="${HANCOM_WINDOWS_PYTHON:-/mnt/c/anaconda3/python.exe}"
if [[ ! -x "$win_python" ]]; then
  echo "Windows Python not found: $win_python" >&2
  echo "Set HANCOM_WINDOWS_PYTHON to a Windows python.exe path." >&2
  exit 127
fi
win_python_win="$(wslpath -aw "$win_python" 2>/dev/null || printf "%s" "$win_python")"

if [[ -n "${HANCOM_SDK_DIR:-}" && -f "$HANCOM_SDK_DIR/License" ]]; then
  py_dir="$(dirname "$win_python")"
  if [[ ! -f "$py_dir/License" ]] || ! cmp -s "$HANCOM_SDK_DIR/License" "$py_dir/License"; then
    cp "$HANCOM_SDK_DIR/License" "$py_dir/License"
  fi
fi

args=(/d /c "$win_python_win" "$script_win" "$input_win" "$output_win")
if [[ -n "${HANCOM_SDK_DIR:-}" ]]; then
  args+=(--sdk-dir "$(wslpath -aw "$HANCOM_SDK_DIR" 2>/dev/null || printf '%s' "$HANCOM_SDK_DIR")")
fi

exec "$cmd_bin" "${args[@]}"
