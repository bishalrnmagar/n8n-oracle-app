#!/bin/bash
# Setup script for finance-bot on Oracle Cloud VM
# Usage: scp -r docker/ ubuntu@<server-ip>:/tmp/finance-bot && ssh ubuntu@<server-ip> 'sudo bash /tmp/finance-bot/setup.sh'

set -e

APP_DIR="/opt/finance-bot"

echo "==> Copying files to $APP_DIR"
mkdir -p "$APP_DIR/db-init"
cp /tmp/finance-bot/docker-compose.yml "$APP_DIR/"
cp /tmp/finance-bot/Caddyfile "$APP_DIR/"
cp /tmp/finance-bot/db-init/init-finance-db.sql "$APP_DIR/db-init/"

# Copy .env if provided, otherwise check if one already exists
if [ -f /tmp/finance-bot/.env ]; then
    cp /tmp/finance-bot/.env "$APP_DIR/"
elif [ ! -f "$APP_DIR/.env" ]; then
    echo "==> WARNING: No .env file found. Copy .env.example and fill in your values:"
    echo "    cp $APP_DIR/.env.example $APP_DIR/.env"
    cp /tmp/finance-bot/.env.example "$APP_DIR/"
fi

echo "==> Stopping existing containers"
cd "$APP_DIR"
docker compose down 2>/dev/null || true

echo "==> Removing old postgres volume (fresh DB init)"
docker volume rm finance-bot_postgres_data 2>/dev/null || true

echo "==> Starting services"
docker compose up -d

echo "==> Waiting for postgres to be healthy..."
sleep 5
docker compose ps

echo "==> Done! Verify finance DB was created:"
echo "    docker compose exec postgres psql -U n8n -d finance -c '\dt'"
