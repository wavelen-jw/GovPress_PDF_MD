#!/usr/bin/env bash
# GovPress VPS 최초 설치 스크립트
# 대상: Ubuntu 24.04 / 1 vCPU / 1 GB RAM
# 실행: bash setup.sh [배포_디렉터리]  (기본값: /home/ubuntu/GovPress_PDF_MD)
set -euo pipefail

DEPLOY_DIR="${1:-/home/ubuntu/GovPress_PDF_MD}"
COMPOSE_DIR="$DEPLOY_DIR/deploy/vps"
SERVICE_SRC="$COMPOSE_DIR/systemd/govpress-compose.service"
SERVICE_DST="/etc/systemd/system/govpress-compose.service"
REPO_URL="https://github.com/wavelen-jw/GovPress_PDF_MD.git"
TARGET_BRANCH="${GOVPRESS_DEPLOY_BRANCH:-}"

info()  { echo "[INFO]  $*"; }
error() { echo "[ERROR] $*" >&2; exit 1; }

remote_branch_exists() {
  local repo_dir="$1"
  local branch="$2"
  [[ -n "$branch" ]] || return 1
  git -C "$repo_dir" show-ref --verify --quiet "refs/remotes/origin/$branch"
}

sync_existing_repo() {
  local repo_dir="$1"
  local branch="$TARGET_BRANCH"
  local current_branch=""
  local default_branch=""

  info "저장소가 이미 존재합니다. 최신 상태로 갱신..."
  git -C "$repo_dir" fetch origin

  current_branch=$(git -C "$repo_dir" branch --show-current 2>/dev/null || true)
  default_branch=$(git -C "$repo_dir" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##' || true)

  if [[ -z "$branch" ]]; then
    if remote_branch_exists "$repo_dir" "$current_branch"; then
      branch="$current_branch"
    elif remote_branch_exists "$repo_dir" "$default_branch"; then
      branch="$default_branch"
    fi
  fi

  if [[ -n "$branch" ]] && remote_branch_exists "$repo_dir" "$branch"; then
    info "배포 브랜치 동기화: $branch"
    git -C "$repo_dir" checkout "$branch"
    git -C "$repo_dir" pull --ff-only origin "$branch"
    return
  fi

  info "원격 브랜치를 확인하지 못해 현재 체크아웃 유지: ${current_branch:-detached}"
  git -C "$repo_dir" pull --ff-only
}

# ── 루트 권한 확인 ──────────────────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
  error "root 또는 sudo 로 실행하세요: sudo bash $0"
fi

# ── 1. 패키지 업데이트 & 기본 도구 설치 ─────────────────────────────────────
info "패키지 업데이트..."
apt-get update -qq
apt-get install -y --no-install-recommends \
  ca-certificates curl git gnupg lsb-release

# ── 2. Docker CE 설치 ────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  info "Docker CE 설치 중..."
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update -qq
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  systemctl enable --now docker
  info "Docker 설치 완료"
else
  info "Docker 이미 설치됨: $(docker --version)"
fi

# ── 3. 저장소 클론 ────────────────────────────────────────────────────────────
if [[ -d "$DEPLOY_DIR/.git" ]]; then
  sync_existing_repo "$DEPLOY_DIR"
else
  info "저장소 클론 중: $REPO_URL → $DEPLOY_DIR"
  if [[ -n "$TARGET_BRANCH" ]]; then
    info "배포 브랜치 클론: $TARGET_BRANCH"
    git clone --branch "$TARGET_BRANCH" "$REPO_URL" "$DEPLOY_DIR"
  else
    git clone "$REPO_URL" "$DEPLOY_DIR"
  fi
fi

# ── 4. .env 파일 준비 ────────────────────────────────────────────────────────
ENV_FILE="$COMPOSE_DIR/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  info ".env 파일 생성 중 (기본값 사용)..."
  cp "$COMPOSE_DIR/.env.example" "$ENV_FILE"
  info "⚠  $ENV_FILE 를 열어 아래 값을 반드시 수정하세요:"
  info "    GOVPRESS_API_KEY, GOVPRESS_CORS_ALLOW_ORIGINS, CLOUDFLARE_TUNNEL_TOKEN"
else
  info ".env 파일이 이미 존재합니다: $ENV_FILE"
fi

# ── 5. data 디렉터리 생성 ─────────────────────────────────────────────────────
mkdir -p "$COMPOSE_DIR/data/storage" "$COMPOSE_DIR/data/caddy" "$COMPOSE_DIR/config/caddy"
info "스토리지 디렉터리 준비 완료"

# ── 6. systemd 서비스 등록 ────────────────────────────────────────────────────
info "systemd 서비스 등록 중..."
# WorkingDirectory를 실제 경로로 치환해서 복사
sed "s|__COMPOSE_DIR__|$COMPOSE_DIR|g" "$SERVICE_SRC" > "$SERVICE_DST"
systemctl daemon-reload
systemctl enable govpress-compose.service
info "govpress-compose.service 등록 완료"

# ── 7. 스택 시작 ─────────────────────────────────────────────────────────────
info "Docker Compose 스택 빌드 & 시작..."
docker compose -f "$COMPOSE_DIR/docker-compose.yml" up -d --build

# ── 8. 헬스 체크 ─────────────────────────────────────────────────────────────
info "헬스 체크 (최대 60초 대기)..."
for i in $(seq 1 12); do
  if curl -sf http://127.0.0.1:8080/health >/dev/null 2>&1; then
    info "✅ 서버 정상 응답"
    break
  fi
  if [[ $i -eq 12 ]]; then
    error "서버가 60초 내에 응답하지 않습니다. 로그를 확인하세요:\n  docker compose -f $COMPOSE_DIR/docker-compose.yml logs api"
  fi
  sleep 5
done

info "──────────────────────────────────────────────────"
info "설치 완료!"
info "  헬스 체크: curl http://127.0.0.1:8080/health"
info "  로그:      docker compose -f $COMPOSE_DIR/docker-compose.yml logs -f"
info "  .env 수정 후 재시작:"
info "             systemctl restart govpress-compose.service"
info "──────────────────────────────────────────────────"
