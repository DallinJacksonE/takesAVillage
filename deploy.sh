#!/bin/bash

# Ensure the script stops on errors
set -e

ENV_NAME=$1

case "$ENV_NAME" in
  prod)
    export DB_PORT=7000
    export BACKEND_PORT=7001
    export BOTS_PORT=7002
    export FRONTEND_PORT=7003
    export BOT_SECRET="prod-secret-replace-me"
    ;;
  dallin)
    export DB_PORT=8000
    export BACKEND_PORT=8001
    export BOTS_PORT=8002
    export FRONTEND_PORT=8003
    export BOT_SECRET="dallin-secret-replace-me"
    ;;
  lane)
    export DB_PORT=9000
    export BACKEND_PORT=9001
    export BOTS_PORT=9002
    export FRONTEND_PORT=9003
    export BOT_SECRET="lane-secret-replace-me"
    ;;
  *)
    echo "Usage: ./deploy.sh {prod|dallin|lane}"
    exit 1
    ;;
esac

# Docker Compose will natively use this environment variable as the project prefix
export COMPOSE_PROJECT_NAME="village_${ENV_NAME}"

echo "Deploying environment: $ENV_NAME (Project: $COMPOSE_PROJECT_NAME)"
docker compose up -d --build

