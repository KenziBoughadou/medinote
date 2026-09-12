# Recette MediNote — 12 septembre 2026

Application : implémentée, validation locale effectuée ; validation des images par CI en cours.
Publication : raccordement de production en attente.
Étude : en attente de générations réelles et de revue humaine.

Le SHA applicatif et la CI sont consignés dans le suivi de livraison ci-dessous. Aucun appel
payant, événement de revue humaine ou résultat scientifique n’a été produit par l’agent.

## Vérifications locales

- Python 3.12 ; installation `uv sync --frozen --group dev --group eval`.
- Node 22.23.2 installé dans le checkout ; Node système inchangé.
- `npm ci`, typecheck, ESLint, 7 tests Vitest et build Vite réussis ; audit npm : zéro vulnérabilité.
- Ruff et 70 tests Python réussis ; parcours intégral du gel jusqu’au rapport sur
  120 observations simulées, conservées uniquement dans un répertoire temporaire de test.
- Corpus : 60 cas principaux (20 dev / 40 test), 20 variantes stress (10 paires), six exemples
  publics dev, 800 faits gold dont 720 attendus, sources exactes et provenance IA.
- 8 scénarios Playwright : six cas, citations, provenance, relance simulée, 429, exports,
  panne API/hors ligne et axe à 390, 1024 et 1440 px. Suite complète réussie.
- Configuration Compose production analysée sans démarrer de conteneur sur le VPS.
- Images non construites sur le VPS. Build, plafonds de taille et intégration conteneur
  sont réservés au runner GitHub, conformément au plan.

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
| 10 — conteneurs | Configurations et digests figés ; non-root, ressources, réseau privé et secret readonly | Statique vérifié ; intégration CI à consigner |
| 11 — CI/CD | Workflows, archives whitelistées, SHA/digests, préflight, flock, rollback et SQLite conservée | Scripts testés ; production bloquée par prérequis externes |
| 09 — expériences | Douze sorties dev, 80 principales, 40 stress et annotations réelles | Non réalisé : première publication et clé propres au projet manquantes |
| 12 — portfolio | README FR/EN, cartes, commandes, captures et script vidéo ; états séparés | Documents et vidéo vérifiés ; CI à consigner |

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

Les notes illustratives ont été sérialisées avec le renderer déterministe après sa création
pour éviter une seconde implémentation du même gabarit. Les travaux documentaires de 12
ont été préparés sans attendre les opérations externes de 09/11 ; leurs états incomplets
sont explicites. Les fichiers scientifiques nécessitant de vraies générations ou une revue
n’ont pas été créés pour remplir artificiellement la liste du plan.

## Suivi de livraison

- Vidéo vérifiée par ffprobe : 180 secondes, 18810606 octets (17.94 Mio), sans audio ; fournisseur bloqué pendant la capture. Illustrations explicitement étiquetées.
- Dépôt public créé : <https://github.com/KenziBoughadou/medinote>.
- Validation des images et publication GHCR : résultats à consigner après le premier push.

La liste exhaustive des fichiers créés est dans [FILES_CHANGED.md](FILES_CHANGED.md).
