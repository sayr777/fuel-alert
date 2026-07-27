#!/bin/bash
# Резервное копирование: PostgreSQL + фото (Yandex Object Storage)
# Запуск: crontab -e → 0 3 * * * /opt/fuel-alert/deploy/backup.sh
# Логи: /var/log/fuel-alert-backup.log

set -euo pipefail

ENV_FILE=/opt/fuel-alert/deploy/.env
LOG=/var/log/fuel-alert-backup.log
TMP_DIR=/tmp/fuel-alert-backup
KEEP_DAILY=30

log()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }
die()  { log "ERROR: $*"; exit 1; }
size() { du -sh "$1" | cut -f1; }

[[ -f "$ENV_FILE" ]] || die ".env not found at $ENV_FILE"
set -a; source "$ENV_FILE"; set +a

: "${S3_ENDPOINT_URL:?S3_ENDPOINT_URL not set}"
: "${S3_ACCESS_KEY:?S3_ACCESS_KEY not set}"
: "${S3_SECRET_KEY:?S3_SECRET_KEY not set}"
: "${S3_BUCKET:?S3_BUCKET not set}"
: "${BACKUP_BUCKET:?BACKUP_BUCKET not set}"
: "${DB_USER:?DB_USER not set}"
: "${DB_NAME:?DB_NAME not set}"

export AWS_ACCESS_KEY_ID="$S3_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="$S3_SECRET_KEY"
export AWS_DEFAULT_REGION=ru-central1

S3="aws s3 --endpoint-url $S3_ENDPOINT_URL"
S3UP="aws s3 --endpoint-url $S3_ENDPOINT_URL --no-progress"

mkdir -p "$TMP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE_TAG=$(date +%Y%m%d)

log "====== Backup started: $TIMESTAMP ======"

# ── 1. PostgreSQL dump ────────────────────────────────────────────────────────
log "DB: dumping $DB_NAME..."
DB_FILE="$TMP_DIR/db_${DATE_TAG}.sql.gz"
sudo docker exec deploy-db-1 pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$DB_FILE"
log "DB: dump ready ($(size "$DB_FILE"))"

log "DB: uploading to s3://$BACKUP_BUCKET/db/..."
$S3UP cp "$DB_FILE" "s3://${BACKUP_BUCKET}/db/$(basename "$DB_FILE")"
rm -f "$DB_FILE"
log "DB: uploaded."

# Ротация: оставить последние KEEP_DAILY дампов
log "DB: rotating (keep last $KEEP_DAILY)..."
$S3 ls "s3://${BACKUP_BUCKET}/db/" \
    | sort | head -n "-${KEEP_DAILY}" | awk '{print $4}' \
    | while read -r f; do
        [[ -n "$f" ]] || continue
        $S3 rm "s3://${BACKUP_BUCKET}/db/$f"
        log "DB: removed old backup: $f"
    done

# ── 2. Синхронизация фото ─────────────────────────────────────────────────────
log "Photos: syncing s3://$S3_BUCKET/ → s3://$BACKUP_BUCKET/photos/..."
$S3UP sync "s3://${S3_BUCKET}/" "s3://${BACKUP_BUCKET}/photos/"
log "Photos: sync done."

log "====== Backup complete ======"
