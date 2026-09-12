#!/usr/bin/env bash
# Exécution explicite par l’administrateur. Aucun contournement par Docker.
set -Eeuo pipefail
set +x
umask 077
[[ $EUID -eq 0 ]] || { echo 'Ce bootstrap doit être exécuté par l’administrateur root.' >&2; exit 3; }
[[ -d /opt/secrets && ! -L /opt/secrets ]] || { echo 'Répertoire central des secrets absent ou invalide.' >&2; exit 2; }
[[ ! -e /opt/secrets/medinote.env ]] || { echo 'Le secret MediNote existe déjà ; aucun écrasement.' >&2; exit 2; }
[[ $(stat -c '%u' /opt/secrets) == 0 ]] || exit 2
if (( $(stat -c '%a' /opt/secrets) % 10 >= 2 )); then echo 'Vérifier les permissions du répertoire central sans les modifier globalement.' >&2; exit 2; fi
install -d -o kenzi -g kenzi -m 0750 /opt/medinote /opt/medinote/incoming /opt/medinote/releases
install -d -o 10001 -g 10001 -m 0750 /var/lib/medinote /var/lib/medinote/experiments
(set -o noclobber; printf 'MEDINOTE_LIVE_ENABLED=false\n' > /opt/secrets/medinote.env)
chown root:10001 /opt/secrets/medinote.env
chmod 0440 /opt/secrets/medinote.env
printf 'Bootstrap terminé en mode enregistré. L’administrateur peut renseigner les clés dans le fichier central, sans les afficher ni les copier dans le checkout.\n'
