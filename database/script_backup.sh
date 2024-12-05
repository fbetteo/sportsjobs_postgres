#!/bin/bash
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/../home/sportsjobs_postgres/database_backups"
BACKUP_FILE="$BACKUP_DIR/sportsjobs_$TIMESTAMP.sql"

mkdir -p $BACKUP_DIR
export PGPASSFILE="/root/.pgpass"
pg_dump -U admin -h localhost -d sportsjobs > $BACKUP_FILE
echo "Backup created at $BACKUP_FILE"

# Optional: Keep only the last 7 backups
find $BACKUP_DIR -type f -mtime +7 -delete