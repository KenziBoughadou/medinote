# Déploiement et exploitation

La production utilise `/opt/medinote/releases/<sha-complet>`, liens `current`/`previous`,
état `/var/lib/medinote` et secret `/opt/secrets/medinote.env`. Aucun fichier d’un autre
projet ou du Compose global n’est modifié.

## Prérequis externes

1. Administrateur : exécuter `sudo bash scripts/bootstrap-admin.sh` après lecture.
   Le script refuse l’écrasement d’un secret existant et prépare une première publication
   enregistrée, live désactivé. Il ne modifie ni ACL globales ni sudoers.
2. Administrateur : renseigner ultérieurement la clé OpenAI propre au projet et une clé
   HMAC d’au moins 32 octets aléatoires en hexadécimal dans le seul fichier central,
   propriétaire root, groupe 10001, mode 0440. Ne jamais afficher ou copier ces valeurs.
3. GitHub : dépôt public et packages `medinote-api`/`medinote-frontend` publics. Vérifier
   leur visibilité effective ; une publication GHCR réussie ne garantit pas cette visibilité.
4. Environnement GitHub `production` : `DEPLOY_HOST`, `DEPLOY_USER=kenzi`, `DEPLOY_SSH_KEY`,
   `DEPLOY_KNOWN_HOSTS`. L’empreinte SSH doit être vérifiée hors session. Aucun ssh-keyscan
   aveuglément approuvé ni StrictHostKeyChecking désactivé.
5. Cloudflare : créer `medinote.kbcompany.fr` vers l’IP confirmée par l’hébergeur, proxy
   activé, TLS Full (strict). Garder les domaines et protections existants.
6. Uptime Kuma existant : deux contrôles HTTP `/healthz` et `/api/health/ready`, intervalle
   60 secondes, trois échecs consécutifs, statut attendu 200, notifications opérateur existantes.

Le bootstrap et les raccordements externes ne sont pas réalisés par le code. Leur statut
vérifié se trouve dans [ACCEPTANCE.md](ACCEPTANCE.md).

## CI et release

La CI installe les dépendances verrouillées, teste Python/frontend/corpus/contrats,
construit sur GitHub les deux images linux/amd64 et vérifie leurs plafonds (600/128 Mio).
L’intégration CI teste nginx, CSP, changement d’IP API sans redémarrage nginx, candidate
unhealthy, retour aux deux conteneurs et persistance de la réservation SQLite.
Les scénarios navigateur simulent uniquement les réponses de relance via interception.

Après succès sur main, les images testées sont publiées sous le SHA complet, avec le label
OCI correspondant. L’archive contient uniquement les scripts/configurations autorisés,
les digests, tailles, SHA et hashes ; aucune clé, DB ou donnée privée. Bases figées dans
`deploy/base-images.lock.json`. Les actions GitHub sont épinglées par commit.

Lancer le workflow Deploy avec un SHA complet de main possédant une CI réussie. Il récupère
l’artefact exact, sans reconstruction ni git pull. Le serveur refuse les archives >20 Mio,
traversées, liens, périphériques, fichiers supplémentaires, digests/SHA incohérents et DB
incompatible. Sous flock, il exige les inodes et l’espace définis au plan, avant toute
mutation puis après le pull.

Commande serveur appliquée par le workflow :

```bash
bash /opt/medinote/releases/COMMIT_SHA_COMPLET/scripts/deploy.sh --release-dir /opt/medinote/releases/COMMIT_SHA_COMPLET
```

Remplacer le SHA par celui de l’artefact vérifié. Les deux images et leur configuration
sont appliquées ensemble, puis santé locale et HTTPS sont vérifiés avant activation des
liens. En cas d’échec, l’ancienne release est réappliquée et vérifiée. Sans ancienne release,
seuls les services MediNote sont arrêtés. La DB n’est jamais restaurée.

Rollback manuel :

```bash
bash /opt/medinote/current/scripts/rollback.sh
```

## Campagnes réelles

Ne pas exécuter de campagne payante depuis une DB temporaire du checkout. Le secret est
lu dans l’API via son bind readonly. Exemple complet utilisant la release active :

```bash
MEDINOTE_RELEASE=$(readlink -f /opt/medinote/current)
MEDINOTE_COMPOSE=(docker compose -p medinote --env-file "$MEDINOTE_RELEASE/release.env" -f "$MEDINOTE_RELEASE/deploy/compose.production.yml")
"${MEDINOTE_COMPOSE[@]}" exec -T api medinote eval freeze --root /app --output /var/lib/medinote/experiments/frozen-manifest.v1.json
"${MEDINOTE_COMPOSE[@]}" exec -T api medinote eval run --manifest /var/lib/medinote/experiments/frozen-manifest.v1.json --suite demo --output /var/lib/medinote/experiments/v1/demo
"${MEDINOTE_COMPOSE[@]}" exec -T api medinote eval run --manifest /var/lib/medinote/experiments/frozen-manifest.v1.json --suite main-test --output /var/lib/medinote/experiments/v1/study/main-test
"${MEDINOTE_COMPOSE[@]}" exec -T api medinote eval run --manifest /var/lib/medinote/experiments/frozen-manifest.v1.json --suite stress --output /var/lib/medinote/experiments/v1/study/stress
"${MEDINOTE_COMPOSE[@]}" exec -T api medinote eval export-blind --batch /var/lib/medinote/experiments/v1/study --output /var/lib/medinote/experiments/v1/blind
```

Les dossiers de campagne doivent être neufs. Faire compléter les formulaires par le
relecteur réel puis déposer son fichier d’annotations sous l’état privé, sans l’altérer :

```bash
"${MEDINOTE_COMPOSE[@]}" exec -T api medinote eval import-annotations --batch /var/lib/medinote/experiments/v1/study --annotations /var/lib/medinote/experiments/v1/annotations-complete.jsonl
"${MEDINOTE_COMPOSE[@]}" exec -T api medinote eval report --batch /var/lib/medinote/experiments/v1/study --annotations /var/lib/medinote/experiments/v1/annotations-complete.jsonl --output /var/lib/medinote/experiments/v1/report
"${MEDINOTE_COMPOSE[@]}" exec -T api medinote publish --demo-batch /var/lib/medinote/experiments/v1/demo --report /var/lib/medinote/experiments/v1/report --output /var/lib/medinote/experiments/v1/public-data
```

L’essai payé et la stabilisation des prompts dev doivent précéder ce gel ; toute
modification des prompts impose une nouvelle image. La CLI partage les quotas financiers
et le bail de l’API. Codes de sortie : 0 succès, 2 entrée invalide, 3 dépendance manquante,
4 campagne interrompue. Copier uniquement les artefacts synthétiques destinés à être
publiés vers le checkout, jamais le secret, la DB ou le mapping aveugle avant clôture.
Reconstruire ensuite une release de résultats avec la même CI.

## Démo et intégration locales

`make demo` ne démarre que Vite avec le bundle hors ligne. Pour utiliser deux images déjà
publiées, définir leurs références vérifiées dans `MEDINOTE_API_IMAGE` et
`MEDINOTE_FRONTEND_IMAGE`, puis :

```bash
docker compose -f deploy/compose.local.yml up -d --wait
```

Seul nginx est accessible sur `127.0.0.1:18080`. L’API n’a aucun port hôte.
Aucun build de production ni nettoyage Docker global ne doit être lancé sur le VPS partagé.
