#!/bin/sh
set -eu

config_path="${SERVICE_CONFIG_PATH:-/run/config/service.json}"
if [ ! -r "$config_path" ]; then
  printf '%s\n' "MySQL configuration file is not readable" >&2
  exit 1
fi

export MYSQL_ROOT_PASSWORD="$(jq -er '.database.rootPassword' "$config_path")"
export MYSQL_DATABASE="$(jq -er '.database.name' "$config_path")"
export MYSQL_USER="$(jq -er '.database.user' "$config_path")"
export MYSQL_PASSWORD="$(jq -er '.database.password' "$config_path")"

exec /usr/local/bin/docker-entrypoint.sh "$@"
