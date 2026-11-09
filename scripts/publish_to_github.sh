#!/usr/bin/env bash
set -Eeuo pipefail
# Safe one-time handoff for the SuperApp Module 06 source archive.
# Run from any working directory on a machine with GitHub credentials/network.
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE_URL="https://github.com/alirzx/superApp_signature_stamp_detection.git"
TARGET_BRANCH=main
TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT
command -v git >/dev/null || { echo 'git is required' >&2; exit 1; }
command -v tar >/dev/null || { echo 'tar is required' >&2; exit 1; }

git clone --branch "$TARGET_BRANCH" --single-branch "$REMOTE_URL" "$TEMP_DIR/repo"
# Require a clean upstream snapshot and preserve the remote history.
cd "$TEMP_DIR/repo"
git fetch origin "$TARGET_BRANCH"
git merge --ff-only "origin/$TARGET_BRANCH"
# No CI file is generated or removed; teammate owns CI. Preserve existing remote CI if any.
cd "$SOURCE_DIR"
tar --exclude='.git' --exclude='.env' --exclude='.venv' \
    --exclude='node_modules' --exclude='dist' --exclude='__pycache__' \
    --exclude='.pytest_cache' -cf - . | tar -xf - -C "$TEMP_DIR/repo"
cd "$TEMP_DIR/repo"
git add -A
if git diff --cached --quiet; then
  echo 'Repository already matches generated source; no new commit.'
else
  git commit -m 'feat(module06): add standalone CPU stamp and signature detection service'
  git push origin "$TARGET_BRANCH"
fi
git status -sb
git log -1 --oneline
