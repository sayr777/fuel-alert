#!/bin/bash
# Checks Telegram reachability and reconnects VPN only if needed.
# Runs every 5 minutes via cron.

LOG=/var/log/vpn-reconnect.log
exec >> "$LOG" 2>&1

telegram_reachable() {
    curl -sf --max-time 10 https://api.telegram.org > /dev/null
}

if telegram_reachable; then
    exit 0
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Telegram unreachable, reconnecting VPN..."

adguardvpn-cli disconnect || true
sleep 3
adguardvpn-cli connect -l "Vilnius"
sleep 5

if telegram_reachable; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Telegram reachable, restarting bot"
    docker compose -f /opt/fuel-alert/deploy/docker-compose.yml restart bot
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: Telegram still unreachable after reconnect"
fi
