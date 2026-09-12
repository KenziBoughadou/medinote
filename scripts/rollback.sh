#!/usr/bin/env bash
set -Eeuo pipefail
BASE=/opt/medinote
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/deploy.sh"
acquire_deploy_lock
[[ -L "$BASE/previous" && -L "$BASE/current" ]] || { echo 'Aucune release précédente disponible.' >&2; exit 2; }
PREVIOUS=$(readlink -f "$BASE/previous")
[[ "$PREVIOUS" =~ ^/opt/medinote/releases/[0-9a-f]{40}$ ]] || exit 2
deploy_locked "$PREVIOUS"
