#!/usr/bin/env bash
# Publish the editor to a personal hosting target.
#
# There is no build step: `index.html` is a self-contained single-page app,
# so it is simply copied to DEPLOY_DEST/index.html (which is why the published
# URL is a clean folder, e.g. https://typedev.github.io/ot-edit/).
#
# This script is generic; your target lives in `deploy.config` (git-ignored).
# Copy `deploy.config.example` to `deploy.config` and set DEPLOY_DEST to a
# directory inside a git repo you control (e.g. a GitHub Pages repo).
#
# Usage: ./deploy.sh
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="$SRC_DIR/deploy.config"
APP="$SRC_DIR/index.html"

if [ ! -f "$CONFIG" ]; then
  echo "ERROR: no deploy.config. Copy deploy.config.example to deploy.config and set DEPLOY_DEST." >&2
  exit 1
fi
# shellcheck source=/dev/null
source "$CONFIG"
: "${DEPLOY_DEST:?Set DEPLOY_DEST in deploy.config}"
[ -f "$APP" ] || { echo "ERROR: $APP not found" >&2; exit 1; }

REPO="$(git -C "$(dirname "$DEPLOY_DEST")" rev-parse --show-toplevel)"

if ! git -C "$SRC_DIR" ls-files --error-unmatch "$APP" >/dev/null 2>&1; then
  echo "WARNING: index.html is not tracked by git; the deploy commit will"
  echo "         reference a source revision that does not contain it."
elif ! git -C "$SRC_DIR" diff --quiet HEAD -- "$APP"; then
  echo "WARNING: index.html has uncommitted changes; the deploy commit will"
  echo "         reference a source revision that does not contain them."
fi

echo "==> Copying index.html to $DEPLOY_DEST/index.html"
mkdir -p "$DEPLOY_DEST"
cp "$APP" "$DEPLOY_DEST/index.html"

echo "==> Committing & pushing in $REPO"
git -C "$REPO" add "$DEPLOY_DEST"
if git -C "$REPO" diff --cached --quiet; then
  echo "No changes to publish."
  exit 0
fi
REV="$(git -C "$SRC_DIR" rev-parse --short HEAD)"
git -C "$REPO" commit -m "deploy ot-edit build from ${REV}"
git -C "$REPO" push

echo "==> Done."
