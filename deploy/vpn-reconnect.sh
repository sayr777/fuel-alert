#!/bin/bash
# Checks Telegram reachability and reconnects VPN only if needed.
# Runs every 5 minutes via cron (as user sayr777, NOT root).

LOG=/var/log/vpn-reconnect.log
CREDS=/opt/fuel-alert/deploy/.vpn-credentials
exec >> "$LOG" 2>&1

telegram_reachable() {
    curl -sf --max-time 10 https://api.telegram.org > /dev/null
}

if telegram_reachable; then
    exit 0
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Telegram unreachable, reconnecting VPN..."

# If daemon is not running — start it and re-login
if ! adguardvpn-cli status 2>/dev/null | grep -qE "Connected|Disconnected"; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] VPN daemon not running, starting daemon..."
    adguardvpn-cli start || true
    sleep 8
fi

# Re-login if session expired
if adguardvpn-cli status 2>&1 | grep -qi "log in\|not logged"; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Session expired, logging in..."
    if [ -f "$CREDS" ]; then
        source "$CREDS"
        adguardvpn-cli login --username "$VPN_USER" --password "$VPN_PASS" || true
        sleep 3
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: credentials file not found: $CREDS"
    fi
fi

adguardvpn-cli disconnect 2>/dev/null || true
sleep 3

# Try locations in order of reliability
for LOCATION in "Amsterdam" "Vilnius" "Frankfurt"; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Trying location: $LOCATION"
    adguardvpn-cli connect -l "$LOCATION" || true
    sleep 6
    if telegram_reachable; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Telegram reachable via $LOCATION, restarting bot"
        sudo docker compose -f /opt/fuel-alert/deploy/docker-compose.yml restart bot
        exit 0
    fi
    adguardvpn-cli disconnect 2>/dev/null || true
    sleep 2
done

echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: Telegram still unreachable after trying all locations"
