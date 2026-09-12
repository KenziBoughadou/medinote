# Recette MediNote — 12 septembre 2026

Application : implémentée, validations locale et CI réussies, images publiées et accessibles anonymement.
Publication : GitHub/GHCR vérifiés ; raccordement de production en attente.
Étude : en attente de générations réelles et de revue humaine.

Le SHA applicatif et la CI sont consignés dans le suivi de livraison ci-dessous. Aucun appel
payant, événement de revue humaine ou résultat scientifique n’a été produit par l’agent.

## Vérifications locales

- Python 3.12 ; installation `uv sync --frozen --group dev --group eval`.
- Node 22.23.2 installé dans le checkout ; Node système inchangé.
- `npm ci`, typecheck, ESLint, 7 tests Vitest et build Vite réussis ; audit npm : zéro vulnérabilité.
- Ruff et 70 tests Python réussis ; parcours intégral du gel jusqu’au rapport et à la publication sur
  132 observations simulées, conservées uniquement dans un répertoire temporaire de test.
- Corpus : 60 cas principaux (20 dev / 40 test), 20 variantes stress (10 paires), six exemples
  publics dev, 800 faits gold dont 720 attendus, sources exactes et provenance IA.
- 8 scénarios Playwright : six cas, citations, provenance, relance simulée, 429, exports,
  panne API/hors ligne et axe à 390, 1024 et 1440 px. Suite complète réussie.
- Configuration Compose production analysée sans démarrer de conteneur sur le VPS.
- Images construites exclusivement sur GitHub : API 276,09 Mio / plafond 600 Mio ;
  frontend 57,70 Mio / plafond 128 Mio. Les deux services sont healthy avec leurs UID,
  limites de ressources et système de fichiers en lecture seule.
- Intégration CI réussie : API recréée sur une autre IP sans redémarrage nginx,
  candidate unhealthy rejetée, deux conteneurs réappliqués, réservation SQLite conservée.
- Les huit scénarios navigateur passent aussi contre les images servies par nginx.

Les tests simulés constituent une preuve logicielle, pas une évaluation du modèle.

## Critères d’acceptation par étape

| Étape du plan | Vérification / preuve | État |
|---|---|---|
| 01 — environnements | uv.lock, package-lock.json, import, tests et typecheck ; live désactivé par défaut | Vérifié localement |
| 02 — contrats et sources | Références exactes, introuvables conservées, Unicode, nullables et champs supplémentaires ; export OpenAPI/TS reproductible | Vérifié localement |
| 03 — corpus | Effectifs, parents disjoints, dix paires, douze illustrations, provenance IA ; aucun événement humain fictif | Structure vérifiée ; revue humaine en attente |
| 04 — pipelines | Snapshot/source/rubriques communs ; une requête par pipeline, B déterministe ; refus et troncature avec usage capturé ; pas de réparation | Vérifié avec fournisseur simulé |
| 05 — budget | Réservation avant appel, deux connexions et deux processus, bail global, reprises, UTC, crash, quotas et persistance | Vérifié sur SQLite temporaire persistante |
| 06 — API/publication | Six IDs exclusivement, paramètres libres refusés, limite ASGI, bundle sans gold, live sans métriques, santé indépendante de la clé | Vérifié localement |
| 07 — interface | Clavier, source active, responsive, ancienne réponse ignorée, erreurs sans perte de note, exports, null et mode hors ligne | Vérifié Vitest/Playwright/axe |
| 08 — évaluation | Calcul à la main, alignement, dénominateurs, bootstrap apparié, intégrité, aveuglement et provenance ; parcours complet simulé | Vérifié localement |
| 10 — conteneurs | Configurations et digests figés ; non-root, ressources, réseau privé et secret readonly | Statique et intégration CI vérifiés ; images sous les plafonds |
| 11 — CI/CD | Workflows, archives whitelistées, SHA/digests, préflight, flock, rollback et SQLite conservée | CI verte, GHCR anonyme et archive vérifiés ; production bloquée par prérequis externes |
| 09 — expériences | Douze sorties dev, 80 principales, 40 stress et annotations réelles | Non réalisé : première publication et clé propres au projet manquantes |
| 12 — portfolio | README FR/EN, cartes, commandes, captures et script vidéo ; états séparés | Dépôt public, démo locale, CI, documents et vidéo vérifiés ; HTTPS de production en attente |

## Dépendances externes ouvertes

- `/opt/medinote`, `/var/lib/medinote` et le secret central MediNote ne sont pas préparés.
  Le bootstrap doit réellement être exécuté par l’administrateur ; aucun contournement de
  privilèges via Docker n’a été utilisé.
- DNS `medinote.kbcompany.fr` non résolu au contrôle. HTTPS public non vérifié.
- Secrets SSH et empreinte known_hosts de l’environnement GitHub `production` non renseignés
  par cette implémentation. Destination DNS à confirmer depuis l’hébergeur.
- Clé OpenAI propre à MediNote et activation live absentes. Accès réel au snapshot non testé.
- Contrôles Uptime Kuma à créer par l’opérateur, sans nouveau destinataire de notification.
- Corpus/gold et notes finales à relire par une personne identifiée ; aucune revue humaine
  ne peut être déclarée par l’agent à sa place.

## Écarts et adaptations

Aucune décision d’architecture du plan n’est remplacée. La résolution initiale de Vitest 3
présentait une vulnérabilité corrigée dans Vitest 4.1.11 ; le lockfile a été régénéré avec
npm 11 après un bug de résolution npm 10, puis `npm ci` a été vérifié avec npm 10. Le plan
ne verrouille pas le major de Vitest. React 19, TypeScript 5, Vite 7, Tailwind 4, Node 22,
Python 3.12, les contrats et le modèle restent ceux du plan.

Les chemins temporaires nginx sont tous sous `/tmp` pour respecter l’exécution non-root
en lecture seule. Le test de remplacement d’IP emploie un sous-réseau explicite dans le
seul Compose CI, exigé par Docker pour réserver cette IP. Ces corrections conservent
les choix du plan. La vidéo conserve le parcours complet, avec normalisation de son
horloge de capture à 180 secondes.

Les notes illustratives ont été sérialisées avec le renderer déterministe après sa création
pour éviter une seconde implémentation du même gabarit. Les travaux documentaires de 12
ont été préparés sans attendre les opérations externes de 09/11 ; leurs états incomplets
sont explicites. Les fichiers scientifiques nécessitant de vraies générations ou une revue
n’ont pas été créés pour remplir artificiellement la liste du plan.

## Suivi de livraison

- Vidéo vérifiée par ffprobe : 180 secondes, 18810606 octets (17.94 Mio), sans audio ; fournisseur bloqué pendant la capture. Illustrations explicitement étiquetées.
- Dépôt public créé : <https://github.com/KenziBoughadou/medinote>.
- Commit applicatif validé : `fa507635bcbc5eff42bd24b074ef2712a24e68b9`.
- [CI réussie, vérification et publication](https://github.com/KenziBoughadou/medinote/actions/runs/34689739369) : 70 tests Python, 7 Vitest, 8 Playwright/axe ; lint, typecheck, build, corpus, contrats et intégration réussis.
- Archive `release-fa507635bcbc5eff42bd24b074ef2712a24e68b9.tar.gz` téléchargée puis validée par `unpack_release.py` ; manifest, hashes de configuration, SHA complet et schéma SQLite 1 concordants. Disponible dans les artefacts de cette CI pendant 30 jours.
- Accès anonyme aux deux manifests GHCR vérifié, HTTP 200 et digests concordants ; aucune image construite ni déployée sur le VPS.

| Image de cette release | Taille non compressée | Référence immuable |
|---|---:|---|
| API | 289 496 711 octets | `ghcr.io/kenziboughadou/medinote-api@sha256:3aefd6436aaf2bf4dd740c8d07fb364df821107096047551ed6dc1c103d566df` |
| Frontend | 60 499 364 octets | `ghcr.io/kenziboughadou/medinote-frontend@sha256:1e00624b8b67f1500a1a62e21ae9a5f0b59581ef1ba75d3e3748d51678b748c5` |

Les commits documentaires ultérieurs peuvent avoir leur propre release CI ; les références
ci-dessus désignent exactement la release vérifiée dans ce relevé.

La liste exhaustive des fichiers créés est dans [FILES_CHANGED.md](FILES_CHANGED.md).
