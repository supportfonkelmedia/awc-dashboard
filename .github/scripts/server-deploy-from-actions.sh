#!/usr/bin/env bash
# Run ON THE SERVER (cron or after you see a green "build" job in Actions).
# Server pulls from GitHub (outbound only) — no inbound SSH from GitHub needed.
#
# Prereqs on server:
#   - git, composer, php83 (or set PHP_BIN)
#   - GitHub CLI: https://cli.github.com/  (or install via dnf/yum)
#   - gh auth login --with-token < token file (PAT: repo + read:actions)
#
# Usage:
#   export GH_TOKEN=...   # fine-grained PAT or classic with repo + actions read
#   export DEPLOY_PATH=/home/awcdev/domains/awcdev.fonkelmedia.nl/public_html
#   export GIT_BRANCH=dev
#   ./server-deploy-from-actions.sh

set -eo pipefail

: "${DEPLOY_PATH:?Set DEPLOY_PATH}"
: "${GIT_BRANCH:?Set GIT_BRANCH (dev or main)}"
: "${GH_TOKEN:?Set GH_TOKEN for gh / GitHub API}"

REPO="${GITHUB_REPOSITORY:-supportfonkelmedia/awc-dashboard}"
ARTIFACT_NAME="vite-build-${GIT_BRANCH}"

cd "$DEPLOY_PATH"

echo "=== git pull (${GIT_BRANCH}) ==="
git fetch origin
git reset --hard "origin/${GIT_BRANCH}"

echo "=== download latest Vite artifact (${ARTIFACT_NAME}) ==="
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

export GH_TOKEN
RUN_ID="$(gh run list --repo "$REPO" --branch "$GIT_BRANCH" --workflow deploy.yml --limit 1 --json databaseId,conclusion -q '.[] | select(.conclusion=="success") | .databaseId' | head -1)"
if [ -z "$RUN_ID" ]; then
  echo "No successful deploy.yml run found for branch ${GIT_BRANCH}."
  exit 1
fi

gh run download "$RUN_ID" --repo "$REPO" -n "$ARTIFACT_NAME" -D "$TMP"
rm -rf public/build
mkdir -p public/build
cp -a "$TMP"/* public/build/

if [ -n "${PHP_BIN:-}" ]; then
  PHP="$PHP_BIN"
elif command -v php83 >/dev/null 2>&1; then
  PHP=php83
elif command -v php84 >/dev/null 2>&1; then
  PHP=php84
else
  PHP=php
fi

echo "=== composer & artisan ==="
COMPOSER="$(command -v composer)"
$PHP "$COMPOSER" install --no-dev --optimize-autoloader --no-interaction
$PHP artisan migrate --force --no-interaction
$PHP artisan storage:link --force 2>/dev/null || true
$PHP artisan config:cache
$PHP artisan route:cache
$PHP artisan view:cache

echo "=== done ==="
