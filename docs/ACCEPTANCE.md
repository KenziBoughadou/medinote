# Recette MediNote — 12 septembre 2026

Application : implémentée, validations locale et CI réussies, images publiées et accessibles anonymement.
Publication : GitHub/GHCR, DNS, certificat et site HTTPS vérifiés ; supervision et accès SSH du runner à confirmer.
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
| 11 — CI/CD | Workflows, archives whitelistées, SHA/digests, préflight, flock, rollback et SQLite conservée | CI verte, GHCR anonyme, archive et HTTPS vérifiés ; transport initial depuis la session serveur |
| 09 — expériences | Douze sorties dev, 80 principales, 40 stress et annotations réelles | Non réalisé : clé propre au projet et campagne réelles en attente |
| 12 — portfolio | README FR/EN, cartes, commandes, captures et script vidéo ; états séparés | Dépôt public, démo locale, CI, documents, vidéo et HTTPS vérifiés |

## Dépendances externes ouvertes

- Le runner GitHub n’atteint pas le port SSH du VPS (timeout avant transfert).
  Les quatre secrets sont configurés et la clé dédiée fonctionne depuis le serveur.
  La première mise en ligne utilise la session serveur existante avec l’archive CI exacte.
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

## Mise en production — 12 septembre 2026

- L’opérateur a exécuté le bootstrap administrateur et créé l’enregistrement Cloudflare A
  `medinote`, proxifié, vers l’IP du VPS confirmée. Aucun contournement de privilèges.
- Release d’ouverture : `026183052a9548aa03529adea19c7c5970f13260`, issue de la
  [CI réussie](https://github.com/KenziBoughadou/medinote/actions/runs/34705714136).
- `/opt/medinote/current` activé après succès du contrôle HTTPS. Certificat Let's Encrypt
  pour `medinote.kbcompany.fr` vérifié ; `/`, `/healthz`, `/api/health/ready`, `/api/examples`
  et `/api/health/live` répondent 200, version attendue et six exemples présents.
- Les deux conteneurs sont healthy, sans port hôte, avec les UID, limites et réseaux prévus.
- Huit tests Playwright/axe réussis contre `https://medinote.kbcompany.fr` ; les relances
  y sont simulées par interception, sans appel fournisseur.
- Les sites existants `relay-ai.fr` et `api.relay-ai.fr/health` répondent toujours 200.
- Relances réelles désactivées ; rapport `awaiting_runs`, métriques nulles.
- Corrections d’exploitation : identifiant de sonde HTTP explicite, attente TLS bornée,
  contrôle de taille Docker par plafond avec digest strict, et nettoyage sans `previous`
  pour une première installation. Cette dernière erreur est survenue après activation
  du site et n’a pas interrompu le service ; le cas est couvert par un test de régression.

## Préparation des expériences — 12 septembre 2026

- Initialisation administrateur des clés préparée dans `scripts/configure-live-admin.py` :
  saisie masquée, HMAC aléatoire, permissions root:10001 / 0440, remplacement atomique,
  refus d’écraser une configuration renseignée. Aucun appel fournisseur dans ce script.
- 83 tests backend réussis, dont huit contrôles de cette initialisation ; Ruff et
  `git diff --check` réussis. Aucun changement frontend ne nécessite de nouveau build.
- Export local de relecture : 20 dialogues dev, 40 test et 20 variantes stress ;
  800 faits complets, empreintes vérifiées. Aucun événement humain ajouté.
- Snapshot `gpt-4.1-mini-2025-04-14` toujours documenté officiellement ; tarifs standards
  revérifiés : 0,40 $ / million de tokens d’entrée et 1,60 $ en sortie
  ([modèle](https://developers.openai.com/api/docs/models/gpt-4.1-mini),
  [tarifs](https://developers.openai.com/api/docs/pricing)). L’accès du compte reste à tester.
- Santé HTTPS vérifiée. Clé absente dans l’API active, relances désactivées : l’essai dev,
  le gel, les 132 tentatives et l’annotation restent en attente. Aucune métrique inventée.

Ces deux scripts auxiliaires préparent les opérations administratives et la relecture
déjà prévues ; ils ne changent ni les huit commandes de la CLI, ni l’architecture,
ni les données, les prompts ou les critères scientifiques du plan.

## Activation et essais dev — 12 septembre 2026

L’administrateur a configuré puis remplacé la clé API via la saisie masquée. L’API a été
recréée depuis la release active : configuration chargée, santé HTTPS vérifiée et relances
activées. Aucun secret n’est copié dans le checkout.

Sur les vingt cas dev, 40 essais A/B ont été archivés sous l’état privé de production :
39 sorties techniquement valides et un rejet du schéma (B attribuait le label d’un proche
au sujet patient). Un premier essai supplémentaire a rencontré une erreur du script
d’archivage après génération ; sa dépense et l’incident sont conservés, sa sortie n’est
pas présentée comme archivée. Total partagé à cette étape : 41 tentatives, 0,043863 $
estimés, toutes hors campagne figée. Ces nombres ne sont pas des scores sémantiques.

Le prompt B est précisé avant gel, exclusivement à partir de dev : sujet patient sans
label, proches explicitement identifiés, négation portée une seule fois, conservation
des précisions et certitudes. Modèle, schémas, rendu et corpus sont inchangés. Cette
modification suit l’étape 09.2 et exige une nouvelle image CI avant les nouveaux essais
et le gel. Aucun cas test n’a servi à cet ajustement.
