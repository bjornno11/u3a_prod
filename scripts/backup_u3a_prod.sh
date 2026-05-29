#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/srv/u3a_prod"
BACKUP_DIR="/srv/backups/u3a_prod"
DATE="$(date +%F_%H-%M)"
LOG_FILE="$BACKUP_DIR/backup_$DATE.log"

mkdir -p "$BACKUP_DIR"

{
  echo "Starting u3a_prod backup: $DATE"

  cd "$PROJECT_DIR"
  source "$PROJECT_DIR/venv/bin/activate"

  echo "Running Django check..."
  python manage.py check

  echo "Dumping database..."
  python manage.py dumpdata --natural-foreign --natural-primary \
    --exclude contenttypes \
    --exclude auth.permission \
    > "$BACKUP_DIR/u3a_prod_data_$DATE.json"

  echo "Backing up media..."
  tar -czf "$BACKUP_DIR/u3a_prod_media_$DATE.tar.gz" media/

  echo "Backing up server config..."
  tar -czf "$BACKUP_DIR/u3a_prod_config_$DATE.tar.gz" \
    /etc/nginx/sites-available/u3a.no \
    /etc/nginx/sites-available/skole.u3a.no \
    /etc/systemd/system/gunicorn_u3a_prod.service

  echo "Committing code changes to GitHub if needed..."
  git add -A

  if ! git diff --cached --quiet; then
    git commit -m "Automated u3a_prod backup $DATE"
    git push
  else
    echo "No code changes to commit."
  fi

  echo "Removing local backups older than 14 days..."
  find "$BACKUP_DIR" -type f -mtime +14 -delete

  echo "Backup completed successfully."
} >> "$LOG_FILE" 2>&1

