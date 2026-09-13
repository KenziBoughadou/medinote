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
   Pour initialiser le fichier issu du bootstrap :
   `sudo python3 /home/kenzi/medinote/scripts/configure-live-admin.py`.
   La saisie est masquée, la clé HMAC est générée localement et le script refuse une
   configuration déjà renseignée. Il n’effectue aucun appel payant. Recréer ensuite
   le seul service API depuis la release active (`up -d --no-deps --force-recreate api`)
   pour prendre en compte le remplacement atomique du fichier bind-monté, puis vérifier
   la santé et les capacités. Les relances publiques deviennent alors disponibles.
   Pour remplacer une clé révoquée, réexécuter ce script avec `--rotate` : seule la clé
   API change, sans réinitialiser le HMAC, les quotas ou la DB. Ne transmettre aucune clé
   dans le chat ou en argument de commande ; la saisir uniquement à l’invite masquée.
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

La première mise en ligne HTTPS a été vérifiée le 12 septembre 2026. Le bootstrap et le DNS
ont été réalisés par l’opérateur. Les quatre secrets GitHub de l’environnement `production`
sont configurés, avec une clé SSH dédiée et une clé hôte vérifiée depuis le serveur.
La connexion au port 22 depuis le runner GitHub a expiré avant transfert ; le filtrage réseau
reste à vérifier par l’opérateur. Aucun changement de pare-feu global n’a été effectué.

Pour cette première mise en ligne, l’archive de la CI réussie a été téléchargée directement
depuis la session serveur autorisée, extraite par `unpack_release.py`, puis appliquée par
`deploy.sh`. Images, digests, configuration, verrou, contrôles et activation sont identiques
au workflow. Cette adaptation concerne uniquement le transport de l’archive.

## Déployer en conservant le filtrage SSH

Le filtrage actuel autorise SSH depuis l’adresse de l’opérateur. Le runner GitHub hébergé
ne dispose pas de cet accès. Le mode opérateur ci-dessous utilise uniquement des connexions
HTTPS sortantes depuis la session serveur autorisée. Il n’installe aucun runner sur le VPS,
ne modifie pas le pare-feu et ne nécessite pas de nouvelle clé.

Depuis le serveur, avec l’utilisateur `kenzi`, Python 3 et une session `gh` authentifiée
ayant accès aux artefacts et le droit d’écrire les déploiements du dépôt :

```bash
python3 /home/kenzi/medinote/scripts/deploy_from_server.py --sha COMMIT_SHA_COMPLET
```

Remplacer `COMMIT_SHA_COMPLET` par le SHA complet de la version souhaitée. La commande
vérifie son appartenance à `main`, sa CI réussie et son artefact non expiré. Elle récupère
l’archive exacte, valide son contenu et réutilise le déploiement et le rollback de la release,
sous le même verrou que les autres commandes de déploiement. Une release locale existante
doit correspondre octet pour octet à l’archive CI. Aucun build n’est exécuté sur le VPS.

Le suivi GitHub passe à `success` uniquement après vérification des deux conteneurs actifs,
de leurs images, de leur santé et du SHA servi en HTTPS. Un reçu sans secret est conservé
dans `/opt/medinote/deployments/<deployment_id>.json`. Un échec d’enregistrement GitHub après
validation de la production laisse le reçu `pending` ; il ne déclenche pas de rollback.
La commande refuse de contourner des protections ajoutées à l’environnement GitHub.

Pour vérifier et enregistrer une version déjà active sans relancer le déploiement :

```bash
python3 /home/kenzi/medinote/scripts/deploy_from_server.py --record-current
```

Ce mode crée une nouvelle entrée explicitement identifiée comme vérification de la release
active. Il ne transforme pas l’ancien workflow SSH échoué en réussite et ne supprime pas
l’historique. La CI continue à fonctionner sur GitHub, mais le lancement du déploiement
reste une action depuis le serveur. Le workflow SSH reste disponible pour un futur accès
réseau autorisé ; son bouton ne peut pas déployer avec le filtrage actuel.

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

Les sondes publiques envoient un `User-Agent` explicite `MediNote-Healthcheck/1.0` pour
éviter le rejet du client Python générique par Cloudflare. La vérification HTTPS est reprise
de façon bornée pendant l’émission initiale du certificat. Le digest garantit l’identité
de l’image ; la taille locale Docker est contrôlée contre le plafond, car sa comptabilisation
peut différer légèrement de celle du runner après téléchargement.

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
