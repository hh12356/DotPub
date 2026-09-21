#!/bin/sh
set -e

cd /opt/dotpub

BACKUP_DIR=/root/backup
KEEP_DAYS=14

mkdir -p "$BACKUP_DIR"

docker compose --env-file ./backend/.env exec -T db \
  sh -c 'exec mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" --single-transaction --routines --triggers --default-character-set=utf8mb4 DotPub' \
  > "$BACKUP_DIR/dotpub.tmp"

mv "$BACKUP_DIR/dotpub.tmp" "$BACKUP_DIR/dotpub_$(date +%F).sql"
find "$BACKUP_DIR" -name 'dotpub_*.sql' -mtime +$KEEP_DAYS -delete

echo "$(date '+%F %T') 备份完成"
