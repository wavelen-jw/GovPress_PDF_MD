#!/usr/bin/env bash
set -euo pipefail

BENCH_ROOT="${BENCH_ROOT:-/home/wavel/opendataloader-bench}"
VENV_PY="${BENCH_ROOT}/.venv/bin/python"
JAVA_BIN_DIR="${BENCH_ROOT}/.bin"

if [[ ! -x "${VENV_PY}" ]]; then
  echo "Missing benchmark venv python: ${VENV_PY}" >&2
  exit 1
fi

if [[ ! -x "${JAVA_BIN_DIR}/java" ]]; then
  echo "Missing benchmark java wrapper: ${JAVA_BIN_DIR}/java" >&2
  exit 1
fi

cd "${BENCH_ROOT}"
PATH="${JAVA_BIN_DIR}:$PATH" "${VENV_PY}" src/pdf_parser.py --engine readhim
PATH="${JAVA_BIN_DIR}:$PATH" "${VENV_PY}" src/evaluator.py --engine readhim

cd /home/wavel/GovPress_PDF_MD
python3 scripts/build_official_benchmark_page.py
