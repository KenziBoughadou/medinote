#!/usr/bin/env bash
set -Eeuo pipefail
umask 027
BASE=/opt/medinote
acquire_deploy_lock() { exec 9>"$BASE/deploy.lock"; flock -x 9; }
compose_release() { local release=$1; shift; docker compose -p medinote --env-file "$release/release.env" -f "$release/deploy/compose.production.yml" "$@"; }
pull_images() { compose_release "$1" pull; }
apply_release() { compose_release "$1" up -d --wait --wait-timeout 120; }
wait_ready() {
  local release=$1
  compose_release "$release" exec -T frontend wget -q -O /dev/null http://127.0.0.1:8080/healthz || return 1
  compose_release "$release" exec -T api python -c 'import json,urllib.request; r=urllib.request.urlopen("http://127.0.0.1:8000/api/health/ready",timeout=5); assert r.status==200; assert len(json.load(urllib.request.urlopen("http://127.0.0.1:8000/api/examples",timeout=5)))==6'
}
smoke_public() {
  local attempt
  for attempt in 1 2 3 4 5 6; do
    python3 "$1/scripts/smoke.py" --origin https://medinote.kbcompany.fr --sha "$(basename "$1")" && return 0
    [[ "$attempt" == 6 ]] || sleep 5
  done
  return 1
}
atomic_link() { local name=$1 target=$2; ln -s "$target" "$BASE/.$name.new.$$"; mv -Tf "$BASE/.$name.new.$$" "$BASE/$name"; }
activate_release() {
  local candidate=$1 old=$2
  if [[ -n "$old" && "$old" != "$candidate" ]]; then atomic_link previous "$old"; fi
  atomic_link current "$candidate"
}
rollback_release() {
  local old=$1 candidate=$2
  if [[ -n "$old" ]]; then
    apply_release "$old" && wait_ready "$old" && smoke_public "$old"
  else
    compose_release "$candidate" stop
    echo 'Premier déploiement échoué : services MediNote arrêtés, aucune release précédente.' >&2
    return 1
  fi
}
prune_medinote_releases() {
  local active previous directory
  active=$(readlink -f "$BASE/current")
  previous=$(readlink -f "$BASE/previous" 2>/dev/null || true)
  for directory in "$BASE"/releases/*; do
    [[ -d "$directory" && ! -L "$directory" && "$(basename "$directory")" =~ ^[0-9a-f]{40}$ ]] || continue
    [[ "$directory" != "$active" && "$directory" != "$previous" ]] || continue
    # Explicit allowlist from a valid obsolete MediNote manifest. Never prune another project.
    python3 - "$directory" "$active" "$previous" <<'PY'
import json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(sys.argv[1])/'scripts'))
from package_release import validate_release
obsolete=validate_release(Path(sys.argv[1]))
keep={item['ref'] for directory in sys.argv[2:] if directory for item in validate_release(Path(directory))['images'].values()}
for item in obsolete['images'].values():
    if item['ref'] not in keep:
        tag=item['ref'].split('@')[0]+':sha-'+obsolete['commit_sha']
        subprocess.run(['docker','image','rm',tag,item['ref']],check=False,stdout=subprocess.DEVNULL)
PY
    rm -r -- "$directory"
  done
}
main() {
  [[ $# == 2 && $1 == --release-dir ]] || { echo 'Usage: deploy.sh --release-dir ABSOLUTE_RELEASE_DIR' >&2; return 2; }
  acquire_deploy_lock
  deploy_locked "$2"
}
deploy_locked() {
  local candidate=$1 old=''
  [[ "$candidate" =~ ^/opt/medinote/releases/[0-9a-f]{40}$ && ! -L "$candidate" ]] || { echo 'Chemin de release refusé' >&2; return 2; }
  python3 "$candidate/scripts/deployment_preflight.py" --release-dir "$candidate"
  if [[ -L "$BASE/current" ]]; then old=$(readlink -f "$BASE/current"); fi
  pull_images "$candidate"
  python3 "$candidate/scripts/deployment_preflight.py" --release-dir "$candidate" --after-pull --inspect
  if ! apply_release "$candidate" || ! wait_ready "$candidate" || ! smoke_public "$candidate"; then
    rollback_release "$old" "$candidate" || { echo 'Échec du retour à un état healthy ; intervention opérateur requise.' >&2; return 1; }
    echo 'Candidate rejetée ; les deux images précédentes et leur configuration ont été restaurées.' >&2
    return 1
  fi
  activate_release "$candidate" "$old"
  prune_medinote_releases
  echo 'Release MediNote activée ; comptabilité SQLite conservée.'
}
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then main "$@"; fi
