#!/bin/sh
# Push the torus project to GitHub -> Actions renders -> commit the mp4 back -> pull it.
# Usage: GH_TOKEN=<pat> sh ci.sh <owner/repo> [branch]
#   - creates the repo if it doesn't exist (needs classic PAT with 'repo' scope)
#   - pushes scripts + assets (including assets/narr.mp3 if you added it)
#   - waits for the workflow run to finish, then pulls the rendered mp4 back
set -e
REPO="$1"; BRANCH="${2:-main}"
[ -n "$REPO" ] || { echo "usage: GH_TOKEN=... sh ci.sh <owner/repo>"; exit 1; }
[ -n "$GH_TOKEN" ] || { echo "GH_TOKEN not set"; exit 1; }
cd "$(dirname "$0")"

# 1) create repo if missing (classic PAT with repo scope)
curl -fsS -H "Authorization: token $GH_TOKEN" "https://api.github.com/repos/$REPO" >/dev/null 2>&1 \
  || curl -fsS -X POST -H "Authorization: token $GH_TOKEN" \
       -d "{\"name\":\"${REPO#*/}\",\"private\":false}" \
       "https://api.github.com/user/repos" >/dev/null

# 2) push
git init -q -b "$BRANCH" 2>/dev/null || git init -q
git remote remove origin 2>/dev/null || true
git remote add origin "https://x-access-token:${GH_TOKEN}@github.com/$REPO.git"
git add -A
git -c user.name=ci -c user.email=ci@local commit -q -m "update" 2>/dev/null || true
git push -q -u origin "$BRANCH" --force || true

# 3) wait for the workflow run triggered by this push
RUN=$(curl -fsS -H "Authorization: token $GH_TOKEN" \
  "https://api.github.com/repos/$REPO/actions/runs?event=push&per_page=1" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['workflow_runs'][0]['id'])" 2>/dev/null || true)
[ -n "$RUN" ] || { echo "no run found"; exit 1; }
echo "run $RUN ..."
while :; do
  ST=$(curl -fsS -H "Authorization: token $GH_TOKEN" \
    "https://api.github.com/repos/$REPO/actions/runs/$RUN" \
    | python3 -c "import sys,json;print(json.load(sys.stdin)['status'])" 2>/dev/null || echo unknown)
  [ "$ST" = "completed" ] && break
  sleep 15
done
echo "run completed"

# 4) pull the committed mp4 back
git fetch -q origin "$BRANCH"
git checkout -q "$BRANCH" 2>/dev/null || git checkout -q -b "$BRANCH"
git pull -q origin "$BRANCH"
ls -la y_torus_from_plane*.mp4 2>/dev/null && echo "OK -> $(pwd)"
