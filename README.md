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

**Sur ce corpus, A conserve davantage de faits attendus que B, pour un coût inférieur.** On a relu les 120 notes de test et de stress, puis vérifié les références sans les modifier. Les résultats ci-dessous reposent sur ces annotations et sur les [règles d’alignement v1.1](docs/ANNOTATION_AMENDMENT_V1_1.md). La relecture a été réalisée par l’auteur du projet, sans second avis indépendant ni validation clinique.

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

A reprend **345 des 360 faits attendus**, contre **333 pour B**. B compte 26 omissions et une contradiction, contre 15 omissions et aucune contradiction pour A. Aucun ajout non soutenu n’a été étiqueté dans cette relecture : cela ne prouve pas une absence générale d’hallucinations. Les intervalles donnent une idée de la variation entre les consultations, mais ne tiennent pas compte des erreurs possibles de relecture.

Le test de stress reste séparé : **0 paire sur 10 réussie pour chaque méthode** au
critère strict, qui exige le fait cible et tous les faits invariants dans les deux
variantes. L’incertitude sur l’origine de la plainte est omise dans les 40 notes :
ce score ne permet donc pas de départager les méthodes sur ce corpus.

On a ajouté un [diagnostic après coup](eval/results/stress-diagnostic-v1/) pour
séparer les dimensions, sans remplacer le résultat initial :

| Diagnostic du stress, selon les annotations | A | B |
|---|---:|---:|
| Paires réussies au critère strict initial | 0 / 10 | 0 / 10 |
| Paires où le fait cible est conservé dans les deux variantes | 10 / 10 | 9 / 10 |
| Notes conservant l’incertitude sur l’origine de la plainte | 0 / 20 | 0 / 20 |
| Notes conservant la préférence horaire | 2 / 20 | 20 / 20 |

Le fait cible est celui dont la polarité change. Sa conservation est jugée sur le
fait entier : il ne s’agit pas d’un taux pur de bonnes négations. Les 20 notes par
méthode viennent de dix paires, et ce diagnostic exploratoire ne constitue pas un
nouveau test indépendant. Tous les invariants sont détaillés dans le rapport.
[Méthodologie, dénominateurs et limites](docs/HUMAN_REVIEW_RESULTS.md).

Les 132 appels représentent **0,153097 $ estimés**, hors essais de développement, hébergement et temps de relecture. Les prix utilisés sont archivés dans le [fichier de tarification v1](eval/pricing.v1.json) ; ce ne sont pas une promesse de tarif futur. Lire les résultats enregistrés ne coûte aucun appel API.

[Rapport et intervalles v1.1](eval/results/reviewed-v1.1/report/report.md) · [Relevé d’exécution et coûts](eval/results/v1/report.md) · [Sorties brutes](eval/results/v1/) · [Résultats des comparateurs extractifs](eval/results/extractive-posthoc-1/report.md)

## Ce que les erreurs montrent

On a examiné [neuf erreurs et points à revoir](docs/ERROR_ANALYSIS.md) dans huit notes.
On retrouve notamment une négation portée deux fois dans B, une action de suivi oubliée,
un objectif précis perdu dans le résumé et une citation qui ne soutient qu’une partie
de la phrase. Un autre passage transforme « moins pendant les promenades » en une
absence de symptôme : l’annotation actuelle ne le compte pas comme contradiction,
ce qui en fait un cas utile pour une seconde relecture.

Cette analyse explique les scores sans les modifier. Les améliorations proposées
restent à tester sur de nouveaux cas, après avoir clarifié les désaccords d’annotation.

## Méthode

**A rédige directement.** Le modèle reçoit le dialogue et produit une note en sept rubriques, avec des références aux passages utilisés.

**B extrait puis met en forme.** Le même modèle relève les faits avec leur sujet, leur négation, leur temporalité et leur degré de certitude. Un programme Python les transforme ensuite en note selon des règles fixes, sans second appel à l’IA.

Je compare donc **deux pipelines complets**. Comme le mécanisme de rédaction change aussi, un éventuel écart ne pourra pas être attribué à la seule extraction.

Les deux comparateurs gratuits fournissent un repère plus simple : Lead-5 garde les cinq premiers tours de parole ; TF-IDF choisit cinq passages proches du vocabulaire global du dialogue. Ils recopient le texte et les locuteurs, sans utiliser les faits de référence pour sélectionner les extraits. Cet ajout est exploratoire, réalisé après v1. Sa qualité reste à annoter ; la longueur conservée ne mesure pas la couverture des faits.

La relecture distingue omissions, contradictions, ajouts sans source et citations insuffisantes. Le code, les données, les consignes et le modèle ont été gelés avant le test. L’amendement v1.1, ajouté après la relecture, autorise les faits facultatifs sourcés absents des références sans modifier les faits attendus. Les 10 000 tirages bootstrap appariés sont calculés sur les 40 consultations ; les paires de négation restent séparées.

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

**Le corpus reste artificiel.** Les dialogues et les références ont été préparés par
IA. Leur style régulier facilite certaines tâches et ne représente pas la diversité
des situations de travail. Ajouter davantage de dialogues générés ne suffirait pas.
Pour aller plus loin, il faudrait un nouveau jeu fictif rédigé séparément, des faits
de référence plus simples et une seconde relecture indépendante.

**Le résultat vaut pour une configuration précise.** On compare A et B avec un seul
modèle, un seul réglage et une génération par méthode et par cas. Le bootstrap mesure
les variations entre consultations, pas entre plusieurs générations du même modèle.
Une prochaine campagne pourrait répéter les appels et utiliser un second modèle,
avec un protocole et un budget définis avant de commencer.

**Une règle a changé après observation.** Cinq informations facultatives sourcées ont
mis en évidence un problème dans le validateur. L’amendement v1.1 le corrige sans
modifier les dialogues, les références ou les générations. Cette transparence permet
de suivre le changement, mais ne le rend pas prévu à l’avance. Il faudrait tester la
règle sur le développement puis la figer avant une nouvelle campagne.

**Le score de stress était trop agrégé.** Une seule omission commune suffit à produire
0/10 partout. Le diagnostic séparé rend ce résultat plus lisible, mais a lui aussi été
ajouté après coup. Pour un prochain test, on définirait avant les appels des mesures
distinctes pour le fait cible, les invariants et les omissions, en gardant le score
strict comme contrôle complémentaire. On vérifierait sur le développement que ces
mesures réagissent aux erreurs qu’on cherche à observer.

La relecture actuelle est celle de l’auteur du projet, et le style de B peut révéler
la méthode. Les cas ambigus de l’[analyse des erreurs](docs/ERROR_ANALYSIS.md) méritent
un second avis. Aucune validation clinique ni économie de temps au travail n’est
établie. Avec le budget actuel, la priorité reste d’améliorer les références et
l’annotation avant de multiplier les appels.

[Guide de relecture](docs/REFERENCE_REVIEW.md) · [Périmètre des expériences complémentaires](docs/RESEARCH_SCOPE.md)

La [release v1](https://github.com/KenziBoughadou/medinote/releases/tag/v1) rassemble
le code, les résultats et l’analyse. Elle utilise l’évaluation amendée v1.1 ;
le numéro de release ne change pas la version du protocole.

Le diagnostic du stress a été ajouté après cette release et reste séparé des résultats figés de v1.
