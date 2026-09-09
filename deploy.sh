#!/bin/bash

# Ensure the script stops on errors
set -e

ENV_NAME=$1

case "$ENV_NAME" in
  prod)
    DB_PORT=7000
    BACKEND_PORT=7001
    BOTS_PORT=7002
    FRONTEND_PORT=7003
    ADMINER_PORT=7004
    BOT_SECRET="prod-secret-replace-me"
    ;;
  dallin)
    DB_PORT=8000
    BACKEND_PORT=8001
    BOTS_PORT=8002
    FRONTEND_PORT=8003
    ADMINER_PORT=8004
    BOT_SECRET="dallin-secret-replace-me"
    ;;
  lane)
    DB_PORT=9000
    BACKEND_PORT=9001
    BOTS_PORT=9002
    FRONTEND_PORT=9003
    ADMINER_PORT=9004
    BOT_SECRET="lane-secret-replace-me"
    ;;
  *)
    echo "Usage: ./deploy.sh {prod|dallin|lane}"
    exit 1
    ;;
esac

COMPOSE_PROJECT_NAME="village_${ENV_NAME}"

# Write the environment variables to .env so docker compose commands work seamlessly afterwards
cat << ENV_EOF > .env
DB_PORT=$DB_PORT
BACKEND_PORT=$BACKEND_PORT
BOTS_PORT=$BOTS_PORT
FRONTEND_PORT=$FRONTEND_PORT
ADMINER_PORT=$ADMINER_PORT
BOT_SECRET="$BOT_SECRET"
COMPOSE_PROJECT_NAME="$COMPOSE_PROJECT_NAME"
ENV_EOF

echo "Wrote environment variables to .env"
echo "Deploying environment: $ENV_NAME (Project: $COMPOSE_PROJECT_NAME)"
docker compose up -d --build
