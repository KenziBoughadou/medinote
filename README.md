# MediNote

[![CI](https://github.com/KenziBoughadou/medinote/actions/workflows/ci.yml/badge.svg)](https://github.com/KenziBoughadou/medinote/actions/workflows/ci.yml)

**Comparer la fidélité de deux pipelines de résumé avec un modèle de langage.** À partir d’une consultation fictive, je compare une note rédigée directement par l’IA et une note construite à partir de faits extraits. Je cherche à mesurer ce que chaque méthode conserve, oublie ou transforme, ainsi que son coût.

C’est un projet de **NLP appliqué et d’évaluation de LLM**. Le modèle est déjà entraîné. Les notes sont des brouillons à relire, sans validation clinique.

| L’expérience en quelques chiffres | |
|---|---|
| Données | 80 consultations fictives en français, 800 faits de référence |
| Test principal | 40 consultations réservées au test, après 20 cas de développement |
| Stress | 10 paires testant une inversion de négation |
| Méthodes | 2 pipelines LLM et 2 comparateurs sans modèle génératif |
| Sorties archivées | 132 générations LLM et, séparément, 160 extraits |
| Évaluation | 120 notes relues ; résultats v1.1 et bootstrap apparié |
| Application | React, TypeScript, Python, FastAPI et API OpenAI |

[Résultats](#résultats) · [Méthode](#méthode) · [Démo](#démo) · [Architecture](#architecture) · [Limites et suite](#limites-et-suite) · [English](README.en.md)

## Résultats

**Sur ce corpus, A conserve davantage de faits attendus que B, pour un coût inférieur.** Les 120 notes de test et de stress ont été relues par Kenzi, qui a aussi accepté les références sans correction. Les résultats ci-dessous sont calculés à partir de ses annotations, avec le [validateur amendé v1.1](docs/ANNOTATION_AMENDMENT_V1_1.md). Il s’agit d’une relecture par l’auteur, sans validation indépendante ou clinique.

Les mesures portent sur les **40 mêmes consultations test**, avec une génération par méthode et par cas. Les différences de qualité sont exprimées en points de pourcentage ; les coûts et délais sont comparés par un rapport.

| Mesure | Direct A | Structuré B | Écart B−A ou rapport B/A | IC 95 % de B−A |
|---|---:|---:|---:|---|
| Couverture fidèle des faits attendus | 95,83 % | 92,50 % | -3,33 points | [-5,28 ; -1,39] points |
| Omissions de faits attendus | 4,17 % | 7,22 % | 3,06 points | [1,11 ; 5,00] points |
| Contradictions dans la note | 0,00 % | 0,23 % | 0,23 points | [0,00 ; 0,71] points |
| Ajouts non soutenus | 0,00 % | 0,00 % | 0,00 points | [0,00 ; 0,00] points |
| Soutien sémantique des citations | 99,73 % | 99,54 % | -0,19 points | [-0,95 ; 0,60] points |
| Coût moyen par note | 0,00079 $ | 0,00158 $ | ×2,00 | Non calculé |
| Latence médiane | 2,29 s | 4,98 s | ×2,17 | Non calculé |

A reprend **345 des 360 faits attendus**, contre **333 pour B**. B compte 26 omissions et une contradiction, contre 15 omissions et aucune contradiction pour A. Aucun ajout non soutenu n’a été étiqueté dans cette relecture : cela ne prouve pas une absence générale d’hallucinations. Les intervalles bootstrap ne couvrent pas les erreurs possibles de l’annotateur.

Le test de stress reste séparé : **0 paire sur 10 réussie pour chaque méthode** au critère strict, qui exige les deux polarités et tous les faits invariants. L’incertitude sur l’origine de la plainte est omise dans les 40 notes de stress ; ce résultat ne signifie pas que toutes les négations sont erronées. [Méthodologie, dénominateurs et limites](docs/HUMAN_REVIEW_RESULTS.md).

Les 132 appels représentent **0,153097 $ estimés**, hors essais de développement, hébergement et temps de relecture. Les prix utilisés sont archivés dans le [fichier de tarification v1](eval/pricing.v1.json) ; ce ne sont pas une promesse de tarif futur. Lire les résultats enregistrés ne coûte aucun appel API.

[Rapport et intervalles v1.1](eval/results/reviewed-v1.1/report/report.md) · [Relevé d’exécution et coûts](eval/results/v1/report.md) · [Sorties brutes](eval/results/v1/) · [Résultats des comparateurs extractifs](eval/results/extractive-posthoc-1/report.md)

## Méthode

**A rédige directement.** Le modèle reçoit le dialogue et produit une note en sept rubriques, avec des références aux passages utilisés.

**B extrait puis met en forme.** Le même modèle relève les faits avec leur sujet, leur négation, leur temporalité et leur degré de certitude. Un programme Python les transforme ensuite en note selon des règles fixes, sans second appel à l’IA.

Je compare donc **deux pipelines complets**. Comme le mécanisme de rédaction change aussi, un éventuel écart ne pourra pas être attribué à la seule extraction.

Les deux comparateurs gratuits fournissent un repère plus simple : Lead-5 garde les cinq premiers tours de parole ; TF-IDF choisit cinq passages proches du vocabulaire global du dialogue. Ils recopient le texte et les locuteurs, sans utiliser les faits de référence pour sélectionner les extraits. Cet ajout est exploratoire, réalisé après v1. Sa qualité reste à annoter ; la longueur conservée ne mesure pas la couverture des faits.

La relecture distingue omissions, contradictions, ajouts sans source et citations insuffisantes. Le code, les données, les consignes et le modèle ont été gelés avant le test. L’amendement v1.1, ajouté après la relecture, autorise les faits facultatifs sourcés absents du gold sans modifier les faits attendus. Les 10 000 tirages bootstrap appariés sont calculés sur les 40 consultations ; les paires de négation restent séparées.

[Protocole expérimental](docs/EXPERIMENT_PROTOCOL.md) · [Règles d’évaluation](docs/EVALUATION.md) · [Guide d’annotation](eval/annotation-guide.v1.md)

## Démo

[Ouvrir MediNote](https://medinote.kbcompany.fr) pour comparer les notes sur six consultations fictives, retrouver les sources et exporter un brouillon. Les douze notes affichées sont des générations réellement enregistrées. Une relance est possible dans les quotas ; aucune consultation personnelle ne peut être saisie.

![Dialogue fictif et comparaison des deux notes avec leurs références.](docs/assets/readme-comparison.png)

*Une citation permet de retrouver un passage. Son existence ne garantit pas qu’il soutienne la phrase : il faut le lire.*

Dans un cadre professionnel, l’usage envisagé serait de préparer un compte rendu organisé, puis de le vérifier et le corriger. Des rubriques communes et un retour aux sources pourraient faciliter la transmission entre collègues. **Aucun gain de temps en situation de travail n’a été mesuré.** Il faudrait comparer le temps total de rédaction et de relecture, ainsi que les erreurs restantes.

## Architecture

React et TypeScript affichent les dialogues et les notes. Python, FastAPI et Pydantic préparent les requêtes, contrôlent les formats et construisent la note B. Les deux méthodes utilisent `gpt-4.1-mini-2025-04-14` via l’API OpenAI. SQLite conserve le budget et les quotas ; Docker et GitHub Actions servent à tester et publier les releases.

Le travail logiciel rend les résultats inspectables et reproductibles. Les tests de l’application ne remplacent pas l’évaluation de son contenu.

[Architecture détaillée](docs/ARCHITECTURE.md) · [Fiche du système](docs/MODEL_CARD.md) · [Fiche des données](docs/DATASET_CARD.md)

## Limites et suite

Les dialogues et les références ont été préparés par IA. Ils sont courts, réguliers et peu représentatifs de consultations réelles. L’étude utilise un seul modèle et une seule génération par méthode et par cas. Le style de B peut révéler sa méthode malgré l’annotation en aveugle. Aucune validation clinique, revue indépendante ou supériorité de B n’est revendiquée.

La priorité suivante est une seconde relecture, en particulier des faits composés et des couvertures partielles repérés pendant le [pilote exploratoire](docs/ANNOTATION_PILOT.md). Un formulaire accepté par le logiciel ne garantit pas que chaque décision soit juste. Les références et annotations actuelles restent consultables pour discuter ces désaccords sans effacer les résultats.

Ensuite, je pourrai comparer la fidélité des baselines, analyser les erreurs et concevoir une nouvelle expérience sur un jeu réservé. Un deuxième modèle, des répétitions ou un entraînement complémentaire demanderaient un budget et des données adaptés. Avec les moyens actuels, je privilégie la relecture avant de multiplier les appels.

[Commencer la relecture](docs/REFERENCE_REVIEW.md) · [Périmètre des expériences complémentaires](docs/RESEARCH_SCOPE.md)
