#!/usr/bin/env bash
# Runs on the server via: ssh ... 'bash -s' < deploy-remote.sh
# Env: DEPLOY_PATH, GIT_BRANCH, PHP_BIN (optional)
set -eo pipefail

: "${DEPLOY_PATH:?DEPLOY_PATH is required}"
: "${GIT_BRANCH:?GIT_BRANCH is required}"

cd "$DEPLOY_PATH"

git fetch origin
git reset --hard "origin/${GIT_BRANCH}"

if [ -n "${PHP_BIN:-}" ]; then
  PHP="$PHP_BIN"
elif command -v php83 >/dev/null 2>&1; then
  PHP=php83
elif command -v php84 >/dev/null 2>&1; then
  PHP=php84
else
  PHP=php
fi

COMPOSER="$(command -v composer)"
$PHP "$COMPOSER" install --no-dev --optimize-autoloader --no-interaction

$PHP artisan migrate --force --no-interaction
$PHP artisan storage:link --force 2>/dev/null || true
$PHP artisan config:cache
$PHP artisan route:cache
$PHP artisan view:cache
