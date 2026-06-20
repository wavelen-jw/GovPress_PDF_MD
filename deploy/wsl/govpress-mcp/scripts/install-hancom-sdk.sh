#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

SDK_ARCHIVE="${1:-${SDK_ARCHIVE:-}}"
INSTALL_ROOT="${HANCOM_INSTALL_ROOT:-/mnt/c/Hancom/HWP_SDK}"
WINDOWS_PYTHON="${HANCOM_WINDOWS_PYTHON:-/mnt/c/anaconda3/python.exe}"

find_archive() {
  find /mnt/c/Users/user/Downloads /mnt/c/Users/user/Desktop /mnt/d /home/wavel \
    -maxdepth 4 -type f \
    \( -iname "*hwp*sdk*.zip" -o -iname "*hancom*hwp*.zip" -o -iname "*hancom*sdk*.zip" -o -iname "*hwpsdk*.zip" \) \
    2>/dev/null | sort -r | head -1
}

if [[ -z "$SDK_ARCHIVE" ]]; then
  SDK_ARCHIVE="$(find_archive || true)"
fi

if [[ -z "$SDK_ARCHIVE" || ! -f "$SDK_ARCHIVE" ]]; then
  cat >&2 <<'EOF'
Hancom HWP SDK archive was not found.

Put the downloaded SDK zip under one of these locations and rerun:
- /mnt/c/Users/user/Downloads
- /mnt/c/Users/user/Desktop
- /mnt/d
- /home/wavel

Or pass the path explicitly:
  scripts/install-hancom-sdk.sh /mnt/c/Users/user/Downloads/<Hancom-HWP-SDK>.zip
EOF
  exit 1
fi

if [[ ! -x "$WINDOWS_PYTHON" ]]; then
  echo "Windows Python not found: $WINDOWS_PYTHON" >&2
  echo "Set HANCOM_WINDOWS_PYTHON to python.exe, for example /mnt/c/anaconda3/python.exe" >&2
  exit 1
fi

mkdir -p "$INSTALL_ROOT"

case "${SDK_ARCHIVE,,}" in
  *.zip)
    rm -rf "$INSTALL_ROOT/.extracting"
    mkdir -p "$INSTALL_ROOT/.extracting"
    python3 - <<PY
import zipfile
from pathlib import Path
archive = Path("$SDK_ARCHIVE")
target = Path("$INSTALL_ROOT/.extracting")
with zipfile.ZipFile(archive) as zf:
    zf.extractall(target)
PY
    shopt -s dotglob nullglob
    extracted=("$INSTALL_ROOT/.extracting"/*)
    if [[ ${#extracted[@]} -eq 1 && -d "${extracted[0]}" ]]; then
      rm -rf "$INSTALL_ROOT/current"
      mv "${extracted[0]}" "$INSTALL_ROOT/current"
      rmdir "$INSTALL_ROOT/.extracting"
    else
      rm -rf "$INSTALL_ROOT/current"
      mv "$INSTALL_ROOT/.extracting" "$INSTALL_ROOT/current"
    fi
    ;;
  *)
    echo "Unsupported SDK archive type: $SDK_ARCHIVE" >&2
    exit 1
    ;;
esac

sdk_dir="$(find "$INSTALL_ROOT/current" -type f -iname hwpsdk.py -printf '%h\n' 2>/dev/null | head -1)"
dll_path="$(find "$INSTALL_ROOT/current" -type f -iname SHDKFunctionExport.dll -printf '%p\n' 2>/dev/null | head -1)"

if [[ -z "$sdk_dir" || -z "$dll_path" ]]; then
  echo "SDK extracted, but hwpsdk.py or SHDKFunctionExport.dll was not found under $INSTALL_ROOT/current" >&2
  find "$INSTALL_ROOT/current" -maxdepth 4 -type f | head -80 >&2
  exit 1
fi

cat > hancom.env <<EOF
HANCOM_SDK_DIR=$sdk_dir
HANCOM_WINDOWS_PYTHON=$WINDOWS_PYTHON
HANCOM_HWP2HWPX_CMD=scripts/hancom-hwp2hwpx-windows.sh
CMD_EXE=/mnt/c/Windows/System32/cmd.exe
EOF

"$WINDOWS_PYTHON" - <<PY
import os, sys
sdk_dir = r"$(wslpath -aw "$sdk_dir")"
sys.path.insert(0, sdk_dir)
os.environ["PATH"] = sdk_dir + os.pathsep + os.environ.get("PATH", "")
import hwpsdk
print("hwpsdk_import=ok")
print("sdk_dir=" + sdk_dir)
PY

echo "Installed Hancom HWP SDK to $INSTALL_ROOT/current"
echo "Wrote $(pwd)/hancom.env"
