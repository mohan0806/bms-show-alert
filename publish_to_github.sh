#!/usr/bin/env bash
# Create the GitHub repo and push this folder (run once, on your Mac, from this folder).
#   bash publish_to_github.sh            -> private repo (default)
#   bash publish_to_github.sh --public   -> public repo (needed to `git clone` on the phone without logging in)
set -euo pipefail
cd "$(dirname "$0")"

VIS="--private"
[ "${1:-}" = "--public" ] && VIS="--public"

if [ -f config.env ]; then
  git check-ignore -q config.env || { echo "config.env is not ignored! Aborting to protect your token."; exit 1; }
fi

[ -d .git ] || git init -b main
git add .
git status --short
git commit -m "BMS Show Alert: BookMyShow booking-open alerts via Telegram, call and phone alarm" || echo "(nothing new to commit)"

if git remote get-url origin >/dev/null 2>&1; then
  git push -u origin main
else
  gh repo create bms-show-alert $VIS --source=. --remote=origin --push \
    --description "Get alerted (Telegram, call, phone alarm) the moment a BookMyShow show opens for booking"
fi

USER_NAME="$(gh api user -q .login)"
echo
echo "Done: https://github.com/$USER_NAME/bms-show-alert"
echo "Tip: in README.md, replace <your-github-username> with $USER_NAME, then:"
echo "  git commit -am 'README: set clone URL' && git push"
