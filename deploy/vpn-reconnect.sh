#!/bin/bash
# Reconnects AdGuard VPN and restarts the bot container.
# Runs every hour via cron to keep Telegram reachable from Yandex Cloud.

LOG=/var/log/vpn-reconnect.log
exec >> "$LOG" 2>&1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] reconnecting VPN..."

adguardvpn-cli disconnect || true
sleep 3
adguardvpn-cli connect -l "Vilnius"
sleep 5

if curl -sf --max-time 10 https://api.telegram.org > /dev/null; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Telegram reachable, restarting bot"
    docker compose -f /opt/fuel-alert/deploy/docker-compose.yml restart bot
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: Telegram still unreachable after reconnect"
fi
