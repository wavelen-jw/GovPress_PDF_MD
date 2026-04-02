#!/usr/bin/env bash
# GovPress bare-metal 설치 스크립트 (Docker 없음)
# 대상: Ubuntu 24.04 / 1 vCPU / 1 GB RAM
# 실행: sudo bash setup-bare.sh [배포_디렉터리]  (기본값: /home/ubuntu/GovPress_PDF_MD)
set -euo pipefail

DEPLOY_DIR="${1:-/home/ubuntu/GovPress_PDF_MD}"
COMPOSE_DIR="$DEPLOY_DIR/deploy/vps"
REPO_URL="https://github.com/wavelen-jw/GovPress_PDF_MD.git"
BRANCH="claude/optimize-low-performance-servers-7H90I"
VENV="$DEPLOY_DIR/.venv"
ENV_FILE="$COMPOSE_DIR/.env"
SERVICE_USER="${SUDO_USER:-ubuntu}"

info()  { echo "[INFO]  $*"; }
error() { echo "[ERROR] $*" >&2; exit 1; }

[[ $EUID -ne 0 ]] && error "sudo bash $0 으로 실행하세요"

# ── 1. 패키지 ────────────────────────────────────────────────────────────────
info "패키지 업데이트 및 설치..."
apt-get update -qq
apt-get install -y --no-install-recommends \
  python3 python3-pip python3-venv \
  default-jre-headless \
  curl git

# ── 2. Caddy 설치 ─────────────────────────────────────────────────────────────
if ! command -v caddy &>/dev/null; then
  info "Caddy 설치 중..."
  curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/gpg.key \
    | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  echo "deb [signed-by=/usr/share/keyrings/caddy-stable-archive-keyring.gpg] \
    https://dl.cloudsmith.io/public/caddy/stable/deb/debian any-version main" \
    > /etc/apt/sources.list.d/caddy-stable.list
  apt-get update -qq
  apt-get install -y caddy
else
  info "Caddy 이미 설치됨: $(caddy version)"
fi

# ── 3. cloudflared 설치 ───────────────────────────────────────────────────────
if ! command -v cloudflared &>/dev/null; then
  info "cloudflared 설치 중..."
  ARCH=$(dpkg --print-architecture)
  curl -fsSL "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${ARCH}.deb" \
    -o /tmp/cloudflared.deb
  dpkg -i /tmp/cloudflared.deb
  rm /tmp/cloudflared.deb
else
  info "cloudflared 이미 설치됨: $(cloudflared --version)"
fi

# ── 4. 저장소 클론 ────────────────────────────────────────────────────────────
if [[ -d "$DEPLOY_DIR/.git" ]]; then
  info "저장소 갱신..."
  sudo -u "$SERVICE_USER" git -C "$DEPLOY_DIR" fetch origin
  sudo -u "$SERVICE_USER" git -C "$DEPLOY_DIR" checkout "$BRANCH"
  sudo -u "$SERVICE_USER" git -C "$DEPLOY_DIR" pull origin "$BRANCH"
else
  info "저장소 클론..."
  sudo -u "$SERVICE_USER" git clone --branch "$BRANCH" "$REPO_URL" "$DEPLOY_DIR"
fi

# ── 5. Python 가상환경 & 패키지 설치 ─────────────────────────────────────────
info "Python 가상환경 설정..."
sudo -u "$SERVICE_USER" python3 -m venv "$VENV"
sudo -u "$SERVICE_USER" "$VENV/bin/pip" install --quiet --upgrade pip
sudo -u "$SERVICE_USER" "$VENV/bin/pip" install --quiet -r "$DEPLOY_DIR/requirements.txt"
sudo -u "$SERVICE_USER" "$VENV/bin/pip" install --quiet -U opendataloader-pdf
info "Python 패키지 설치 완료"

# ── 6. 스토리지 디렉터리 ─────────────────────────────────────────────────────
STORAGE_DIR="$DEPLOY_DIR/storage"
mkdir -p "$STORAGE_DIR"
chown "$SERVICE_USER:$SERVICE_USER" "$STORAGE_DIR"
info "스토리지 디렉터리: $STORAGE_DIR"

# ── 7. .env 파일 ─────────────────────────────────────────────────────────────
if [[ ! -f "$ENV_FILE" ]]; then
  sudo -u "$SERVICE_USER" cp "$COMPOSE_DIR/.env.example" "$ENV_FILE"
  info "⚠  $ENV_FILE 를 열어 아래 값을 반드시 수정하세요:"
  info "    GOVPRESS_API_KEY, GOVPRESS_CORS_ALLOW_ORIGINS, CLOUDFLARE_TUNNEL_TOKEN"
else
  info ".env 이미 존재: $ENV_FILE"
fi

# ── 8. Caddy 설정 ─────────────────────────────────────────────────────────────
info "Caddy 설정 적용..."
cp "$COMPOSE_DIR/Caddyfile" /etc/caddy/Caddyfile
# api가 localhost:8013에서 실행되므로 컨테이너명 대신 127.0.0.1 사용
sed -i 's|reverse_proxy api:8013|reverse_proxy 127.0.0.1:8013|g' /etc/caddy/Caddyfile
systemctl enable --now caddy

# ── 9. cloudflared 터널 등록 ─────────────────────────────────────────────────
# .env에서 CLOUDFLARE_TUNNEL_TOKEN 읽기
if grep -q "^CLOUDFLARE_TUNNEL_TOKEN=" "$ENV_FILE"; then
  CF_TOKEN=$(grep "^CLOUDFLARE_TUNNEL_TOKEN=" "$ENV_FILE" | cut -d= -f2-)
  if [[ -n "$CF_TOKEN" && "$CF_TOKEN" != "replace-with-your-token" ]]; then
    info "cloudflared 서비스 설치..."
    cloudflared service install "$CF_TOKEN"
    systemctl enable --now cloudflared
    info "cloudflared 서비스 활성화 완료"
  else
    info "⚠  CLOUDFLARE_TUNNEL_TOKEN 이 설정되지 않았습니다. 나중에 수동으로 실행하세요:"
    info "    cloudflared service install <TOKEN>"
  fi
fi

# ── 10. govpress-api systemd 서비스 등록 ─────────────────────────────────────
info "govpress-api.service 등록..."
sed \
  -e "s|__DEPLOY_DIR__|$DEPLOY_DIR|g" \
  -e "s|__VENV__|$VENV|g" \
  -e "s|__ENV_FILE__|$ENV_FILE|g" \
  -e "s|__SERVICE_USER__|$SERVICE_USER|g" \
  -e "s|__STORAGE_DIR__|$STORAGE_DIR|g" \
  "$COMPOSE_DIR/systemd/govpress-api.service" \
  > /etc/systemd/system/govpress-api.service
systemctl daemon-reload
systemctl enable govpress-api.service
systemctl start govpress-api.service

# ── 11. 헬스 체크 ────────────────────────────────────────────────────────────
info "헬스 체크 (최대 60초 대기)..."
for i in $(seq 1 12); do
  if curl -sf http://127.0.0.1:8013/health >/dev/null 2>&1; then
    info "✅ 서버 정상 응답"
    break
  fi
  [[ $i -eq 12 ]] && error "60초 내 응답 없음. 로그: journalctl -u govpress-api -n 50"
  sleep 5
done

info "──────────────────────────────────────────────────"
info "설치 완료! (Docker 없이 bare-metal 실행 중)"
info ""
info "  헬스 체크:  curl http://127.0.0.1:8013/health"
info "  로그:       journalctl -u govpress-api -f"
info "  재시작:     systemctl restart govpress-api"
info "  .env 위치:  $ENV_FILE"
info "──────────────────────────────────────────────────"
