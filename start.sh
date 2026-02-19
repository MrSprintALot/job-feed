#!/bin/bash
set -e

echo "=== JobFeed Starting ==="

# Use Railway volume if available, otherwise local
if [ -n "$RAILWAY_VOLUME_MOUNT_PATH" ]; then
    echo "Using Railway volume at $RAILWAY_VOLUME_MOUNT_PATH"
    mkdir -p "$RAILWAY_VOLUME_MOUNT_PATH"
    # Symlink db file to the volume for persistence
    ln -sf "$RAILWAY_VOLUME_MOUNT_PATH/jobs.db" /app/db/jobs.db
else
    echo "No volume detected, using local storage"
fi

# Init database
echo "Initializing database..."
python -c "from db.database import init_db; init_db()"

# Run initial scrape in background (don't block server start)
echo "Starting background scrape..."
python -m scrapers.runner --terms "data analyst" "bi engineer" "business intelligence" "analytics engineer" "power bi" &

# Start server
echo "Starting server on port ${PORT:-5000}..."
exec gunicorn app:app \
    --bind "0.0.0.0:${PORT:-5000}" \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
