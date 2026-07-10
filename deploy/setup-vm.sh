#!/usr/bin/env bash
# Yandex Cloud Ubuntu 22.04/24.04 VM — first-run setup
# Run as root: bash setup-vm.sh
set -euo pipefail

APP_DIR=/opt/fuel-alert
REPO_URL="https://github.com/sayr777/fuel-alert.git"   # <-- замените на свой репо

# ── Docker ────────────────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  echo "==> Installing Docker..."
  apt-get update -q
  apt-get install -y ca-certificates curl gnupg
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update -q
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  systemctl enable --now docker
fi

# ── Project ───────────────────────────────────────────────────────────────────
if [ ! -d "$APP_DIR/.git" ]; then
  echo "==> Cloning repo..."
  git clone "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR/deploy"

if [ ! -f .env ]; then
  cp .env.example .env
  echo ""
  echo "============================================================"
  echo "  ЗАПОЛНИТЕ $APP_DIR/deploy/.env перед запуском!"
  echo "  nano $APP_DIR/deploy/.env"
  echo "============================================================"
  exit 0
fi

# ── Firewall (ufw) ────────────────────────────────────────────────────────────
if command -v ufw &>/dev/null; then
  ufw allow 22/tcp
  ufw allow 80/tcp
  ufw allow 443/tcp
  ufw --force enable
fi

# ── Start ─────────────────────────────────────────────────────────────────────
echo "==> Building and starting services..."
docker compose pull --ignore-buildable
docker compose up -d --build --profile bot

echo ""
echo "==> Done! Services:"
docker compose ps
