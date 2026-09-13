# Recette MediNote

État actuel : application déployée, 120 notes annotées et résultats v1.1 publiés.
La [méthode et les limites](HUMAN_REVIEW_RESULTS.md) accompagnent les scores.
La CI de la release `b7261c3b9fab6a334a2a5f785b909b8a80b61e0f` a validé
141 tests Python, 7 tests frontend et 8 parcours navigateur. Son déploiement GitHub
6427164554 a réussi et le site a été vérifié en HTTPS.

Les entrées ci-dessous décrivent les étapes successives. Les mentions « en attente »
concernent la date de chaque entrée, pas l’état actuel de l’évaluation.

## État initial — 12 septembre 2026

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

## Campagne v1 réelle et publication des résultats d’exécution

Le gel utilise le commit `3138ec963c32c6c5acfac93ffddbf0490f5c08ca`, après correction
du schéma fournisseur qui n’exprimait pas la contrainte croisée de sujet déjà imposée
par Pydantic. Modèle, champs, renderer et corpus restent inchangés. Trois essais dev
ciblés ont confirmé la correction, y compris le cas précédemment rejeté.

- 132 tentatives réelles archivées : 12 démos, 80 test et 40 stress ; aucune reprise,
  aucune tentative supprimée, toutes techniquement valides. Coût estimé : 0,153097 $.
- Manifest, réponses brutes, notes et empreintes vérifiés depuis le checkout sans nouvel
  appel. L’historique des essais dev et son incident d’archivage restent explicites.
- 120 documents aveugles et formulaires vierges exportés. Mapping conservé dans l’état
  privé du serveur ; aucun événement humain ni annotation complétée inventé.
- Bundle public composé des douze sorties réelles `llm_recorded` ; rapport
  `awaiting_annotation`, métriques nulles et liens vers les artefacts d’exécution.
- 95 tests backend et 7 Vitest réussis. Les huit scénarios Playwright/axe passent : six
  lors du premier passage, puis les deux attentes de provenance corrigées et revérifiées.
  Build frontend, lint Python/TypeScript et intégrité des archives réussis.

Les critères logiciels et d’exécution de l’étape 09 sont remplis. Le critère des scores
finaux reste en attente de revue humaine complète. Les figures, bootstrap et métriques
sémantiques ne sont donc pas créés. La publication de la release de résultats réutilise
la CI et le déploiement par archive validée. Les anciennes captures montrent les illustrations.

## Filtrage réseau conservé et suivi GitHub

Le 12 septembre 2026 à 23:19 UTC, la release active
`05731da8e0a661e111826ca27bca0b2adc16b028` a été vérifiée depuis le serveur : archive exacte
de la CI `34722752889`, deux conteneurs conformes et healthy, santé et version HTTPS.
Le déploiement GitHub `6415505357` enregistre cette vérification avec l’opération
`verify_current`. Il ne représente pas un nouveau transfert ni un succès de l’ancien
workflow SSH. Le reçu est conservé sous `/opt/medinote/deployments/6415505357.json`.

La commande `scripts/deploy_from_server.py` prépare aussi les prochains déploiements par
HTTPS sortant, avec contrôle de CI et d’archive puis réutilisation des scripts de release.
Les tests ciblés de ce mode et des contrôles existants de release/déploiement passent :
40 tests. Le chemin d’enregistrement de la release active a été exécuté sur le serveur ;
le lancement d’une nouvelle release par cette commande est couvert par simulation.

Le filtrage réseau est conservé à la demande de l’opérateur. L’accès SSH entrant du runner
GitHub reste indisponible ; le déploiement depuis le serveur est documenté comme adaptation
du transport prévu à l’étape 11. Aucun changement des données, dépenses, images actives,
services voisins ou résultats scientifiques n’est nécessaire à cette synchronisation.

## Renforcement de l’évaluation — 13 septembre 2026

La demande de correction de l’analyse critique est traitée sans dépenses d’inférence.
La présentation porte désormais explicitement sur deux pipelines complets, et les consignes
de configuration de l’assistant sont retirées du plan. La provenance des données reste exacte.

Deux comparateurs extractifs ont produit 160 sorties sur les 80 consultations : lead-5 et
TF-IDF centroid-5. Aucun gold n’est lu par leur script. Leur manifest enregistre les hashes
d’entrée, de code et de sortie ; la campagne reste séparée de v1, ajoutée après sa publication,
avec métriques sémantiques absentes. Les proportions de mots conservés ne sont pas des scores
de couverture des faits.

Les 120 notes aveugles ont été préparées en douze lots HTML locaux de dix notes sous
`.state/relecture-v1`. Le formulaire permet segmentation, alignement, jugement des citations,
export et reprise. Le contrôle partiel réutilise les validateurs v1 ; les brouillons restent
non évalués. Les essais navigateur vérifient ajout, export, reprise, refus d’empreinte altérée,
absence de requête réseau et largeur mobile. Leurs exports sont des fixtures isolées sous
`.state/review-ui-test`, jamais des annotations expérimentales.

Les captures de l’atelier vierge et des comparateurs montrent leur fonctionnement réel.
La revue humaine, une comparaison de qualité avec ces baselines, un second modèle,
les répétitions et un entraînement restent non réalisés. Voir `docs/RESEARCH_SCOPE.md`
pour la correspondance entre chaque critique, la correction et la limite restante.

Validation locale : 127 tests Python réussis, Ruff et `git diff --check` conformes.
Les 28 fichiers référencés par le manifest gelé de v1 sont inchangés. Les empreintes
du script et des artefacts extractifs sont vérifiées. Aucun événement de revue humaine
n’a été ajouté et aucun appel fournisseur n’a été effectué pour ces corrections.

## Présentation publique et protocole

Le README français est réorganisé autour des résultats disponibles, de la méthode, de la
démo, de l’architecture et des limites. Le tableau principal sépare les coûts et latences
mesurés des indicateurs de fidélité en attente ; aucun chiffre illustratif de qualité
n’est utilisé. Les données proviennent des 40 paires du test principal.

Le document de préparation interne est retiré de la version publique courante à la demande
de l’auteur, avec conservation locale et sans réécriture de l’historique. Le protocole public
`docs/EXPERIMENT_PROTOCOL.md` présente les décisions pertinentes. Les liens de documentation,
le lien de méthodologie dans l’application et le Dockerfile sont adaptés à ce retrait.
Le script historique de préparation du corpus exige désormais le document éditorial exact
en argument au lieu de dépendre d’un fichier interne implicite ; la provenance v1 est intacte.

Les données, le code scientifique gelé et les observations archivées ne changent pas.
La revue humaine des références et des sorties reste la dépendance nécessaire pour publier
des résultats sémantiques finaux. Cette réorganisation documentaire ne la remplace pas.
# Pilote d’annotation exploratoire — 13 septembre 2026

À la demande de l’auteur, dix notes du lot aveugle existant sont examinées par l’assistant
IA, avec provenance explicite. Les décisions et sources sont archivées dans
`eval/results/annotation-pilot-1/` ; la méthode et les cas concrets sont décrits dans
`docs/ANNOTATION_PILOT.md`. Le README présente ce pilote comme partiel.

Résultat : 103 claims, cinq formulaires complets et cinq brouillons comportant neuf
décisions ouvertes. Une restitution partielle de faits composés et des propos sourcés
sans référence compatible empêchent de finaliser certaines annotations dans le schéma v1.
Ces difficultés sont conservées en `unresolved`, sans modifier le gold ou créer de faux
ajouts injustifiés. Les 110 autres notes restent à annoter ; les métriques globales et
la revue humaine restent en attente. Aucune nouvelle génération ou requête API payante.

Validation : `ruff check backend scripts`, 130 tests Python réussis, recompilation exacte
des annotations et compteurs, empreintes des artefacts vérifiées, liens locaux valides,
manifest gelé v1 intact et aucun événement de revue humaine ajouté. Les trois nouveaux
tests vérifient le rejet des brouillons pour finalisation, des extraits ou citations
incohérents, ainsi que la reproduction sans écrasement des résultats. Aucun changement
d’architecture ou du runtime public ; ce pilote ne remplace pas l’étude finale prévue.


## Relecture confirmée et résultats v1.1 — 13 septembre 2026

On a terminé la relecture des 120 notes, classé les cinq informations
restées ouvertes comme facultatives et soutenues, et conservé sans correction
les références dev, test et stress. Trois événements associés aux hashes sont
ajoutés à `data/review-events.jsonl`. Les décisions finales, leur clôture et les
empreintes des archives reçues sont conservées dans `eval/results/reviewed-v1.1/`.

Le rapport utilise le validateur versionné v1.1, sans modification d’aucun fichier
du manifest gelé. Il conserve 40 paires test et dix paires stress, et réutilise les
formules et 10 000 tirages bootstrap de v1. Couverture : 345/360 pour A, 333/360 pour B ;
écart B−A de −3,33 points, IC95 [−5,28 ; −1,39]. Le stress strict donne 0/10 pour
chaque méthode, avec explication des invariants omis. Les limites de l’auteur comme
seul annotateur, des faits composés et des contrôles de segmentation sont déclarées.

Le rapport public et le README présentent les mesures effectivement calculées ;
aucun score test n’est transféré aux douze notes dev. Le mapping est publié après
clôture pour permettre la reproduction. Aucun nouvel appel fournisseur payant.

Validation locale : Ruff, 141 tests Python, 7 tests frontend et build réussis ;
reproduction octet pour octet des métriques, du rapport et des indices bootstrap ;
refus des annotations manquantes, dupliquées, non résolues et des mappings discordants ;
acceptation d’un rapport humain refusée si une référence manque. Les 28 fichiers
gelés et les liens Markdown sont vérifiés. Le déploiement reste fondé sur une release
issue d’une CI réussie, avec vérification publique et conservation de SQLite.

Écart méthodologique explicite : validateur v1.1 amendé après observation pour admettre
un fait facultatif soutenu sans gold. Les données, prompts, modèle, renderer, formules
et résultats historiques v1 restent inchangés. La relecture déclarée ne constitue
ni une validation clinique ni une annotation indépendante.

La release `a04111e4c5a04c68f8fb663c10c5653ca4afba11` a été déployée et vérifiée
en HTTPS le 13 septembre 2026 : CI 34779156975 et déploiement GitHub 6425814775
réussis, deux conteneurs sains, rapport `human_reviewed` et résultats contrôlés dans
le navigateur public. La comptabilité reste à 199 tentatives et 238 374 microdollars.
Le contrôle d’affichage a également conduit à préciser les écarts et leurs intervalles
en points de pourcentage dans l’interface, sans changer les valeurs calculées.

## Préparation de la release v1

Les cinq décisions ouvertes sont closes et les 120 annotations sont complètes.
Un nouveau calcul local reproduit à l’octet les métriques, les rapports et les
10 000 tirages bootstrap de l’évaluation v1.1, sans appel fournisseur.

L’analyse de neuf observations sur huit notes est publiée dans `docs/ERROR_ANALYSIS.md`.
Chaque exemple renvoie aux sources, à la note et à l’annotation. Le cas de « moins »
transformé en absence est présenté comme un désaccord à examiner, sans modifier les
comptages existants. Les README français et anglais présentent cette analyse.

Le tag de livraison `v1` désigne la version du projet. Les artefacts scientifiques
conservent leurs versions : campagne v1 et évaluation amendée v1.1. La release
est publiée après validation de son commit par la CI.
