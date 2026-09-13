# Protocole expérimental MediNote v1

Ce document rassemble les décisions nécessaires pour comprendre l’expérience.
Les paramètres exécutables sont conservés dans [protocol.v1.json](../eval/protocol.v1.json)
et les empreintes dans le [manifest gelé](../eval/frozen-manifest.v1.json).
Il ne remplace pas ces artefacts et ne modifie pas les observations archivées.

## Question et comparaison

Quel pipeline restitue le plus fidèlement les informations d’un dialogue fictif, et à quel
coût ? A demande directement une note ; B extrait des faits avant un rendu Python fixe.
Les deux suivent sept rubriques : motif, symptômes, antécédents, traitements et allergies,
observations, hypothèses exprimées et actions annoncées.

La comparaison porte sur les pipelines complets. Le mécanisme de rédaction diffère aussi :
elle ne permet pas d’attribuer un effet causal à la seule représentation intermédiaire.
La supériorité de B n’est ni supposée ni un critère de réussite du projet.

## Données et séparation

| Ensemble | Consultations | Usage |
|---|---:|---|
| Développement | 20 | Mise au point des consignes ; six cas servent à la démonstration |
| Test principal | 40 | Comparaison appariée A/B après gel |
| Stress | 20 variantes, soit 10 paires | Inversion de la polarité d’un fait, autres faits conservés |

Les 60 consultations principales couvrent dix familles, avec deux cas dev et quatre test
par famille. Les parents des paires stress sont distincts. Les 800 faits de référence,
dont 720 attendus dans les notes, sont liés à des extraits exacts du dialogue.
Les positions sont exprimées en points de code Unicode.

Textes et références sont préparés par IA. On a terminé leur relecture et on les a
conservés sans correction le 13 septembre 2026 ; les événements de revue sont
associés aux empreintes exactes, sans modification des références gelées.
Le générateur reçoit seulement le dialogue, jamais les références attendues ni les tags
expérimentaux. La [fiche du corpus](DATASET_CARD.md) précise ses limites et sa provenance.

## Paramètres figés et archivage

| Paramètre | Valeur v1 |
|---|---|
| Modèle A et B | `gpt-4.1-mini-2025-04-14` |
| Interface | OpenAI Responses, Structured Outputs stricts |
| Température | 0 |
| Plafond de sortie | 4 000 tokens |
| Stockage fournisseur demandé | `store=false` |
| Appels | Une tentative par cas et méthode, sans reprise ni réparation |
| Rendu B | Python déterministe, sans second modèle |
| Ordre | Cas triés ; alternance A→B puis B→A |

Le gel référence le code `3138ec963c32c6c5acfac93ffddbf0490f5c08ca`. Les fichiers de corpus,
références, prompts, schémas, rendu, évaluation, prix et dépendances sont contrôlés par
empreinte avant la campagne. Les mises au point restent documentées dans
[les essais dev](DEV_TRIALS.md), séparément des résultats de test.

La campagne du 12 septembre 2026 contient 12 générations de démonstration, 80 de test
et 40 de stress. Les manifests, réponses brutes, notes, usages, durées et coûts sont
[archivés](../eval/results/v1/). Une sortie qui respecte le JSON attendu est techniquement
valide ; cela ne préjuge pas de sa fidélité. Les refus, troncatures et autres erreurs
restent des observations, sans relance silencieuse.

## Relecture et mesures

Les 120 notes de test et de stress sont présentées dans un ordre mélangé, sans afficher
leur méthode. Le style de B peut néanmoins la révéler. La revue des références et
l’annotation des notes sont deux opérations distinctes, associées à leurs empreintes.
Le [guide d’annotation](../eval/annotation-guide.v1.md) définit les décisions exactes ;
[l’atelier de relecture](REFERENCE_REVIEW.md) facilite leur saisie progressive.

Chaque information est examinée séparément. Une phrase multifaits est segmentée ; une
répétition est regroupée. Les faits attendus reçoivent un statut couvert, contredit ou omis.
Une information sourcée facultative n’est pas un ajout injustifié. Une négation inversée
est une contradiction, sans double comptage comme omission. Les citations sont jugées
sur leur existence et, séparément, sur leur soutien sémantique à chaque information.

Les mesures principales sont la couverture fidèle, les omissions, les contradictions,
les ajouts non soutenus et la précision des citations. Les compteurs sont sommés avant
division : ce sont des agrégats micro. Les échecs techniques restent dans les mesures
bout en bout, avec faits attendus omis ; leur précision est non applicable. Les résultats
conditionnels aux notes valides exposent leurs propres effectifs. Un dénominateur nul
produit une valeur absente, jamais une note parfaite.

## Comparaison statistique

Le bootstrap rééchantillonne les 40 consultations test avec les mêmes indices pour A et B :
10 000 réplications, générateur NumPy PCG64, graine 20260911, ordre des cas trié. Les ratios
sont recalculés dans chaque tirage avant la différence B−A. L’intervalle percentile utilise
les bornes 2,5 et 97,5 %. Il reste absent si moins de 95 % des tirages définissent le ratio.
Les indices sont enregistrés pour permettre la reproduction.

Le stress est présenté séparément sur dix paires. Une paire réussit seulement si les deux
polarités cibles et les faits invariants sont correctement restitués. Aucun score global
ni p-value ne remplace la lecture des différentes catégories d’erreurs.

Les coûts API et latences sont descriptifs, issus des tentatives archivées. Ils ne mesurent
pas le temps de travail économisé. Les montants utilisent les tarifs figés, sans remise
de cache, et excluent hébergement et annotation. Voir le [relevé d’exécution](../eval/results/v1/report.md).

## Conditions de publication et extensions

On publie les scores finaux une fois les références vérifiées et toutes les notes
annotées. Les brouillons et les annotations automatiques restent identifiés séparément.
Les coûts peuvent être présentés plus tôt ; une mesure encore absente reste indiquée
comme non évaluée.

Une correction des références après gel impose un amendement et une version distincte.
Un changement de dialogue, modèle, prompt ou renderer demande une nouvelle campagne.
Une amélioration conçue après inspection du test est déclarée post hoc ; ce test ne redevient
pas indépendant. Les [comparateurs extractifs](RESEARCH_SCOPE.md) ajoutés ensuite restent
séparés de v1. Aucun entraînement, second fournisseur ou résultat clinique n’est inclus.

Un [pilote d’annotation exploratoire par IA](ANNOTATION_PILOT.md) examine les dix premières
notes du lot aveugle existant. Ses annotations et décisions ouvertes sont archivées
séparément. Il ne modifie ni les références gelées ni les conditions de publication
ci-dessus et ne produit pas de score global sur une cohorte partielle.

L’[amendement d’alignement v1.1](ANNOTATION_AMENDMENT_V1_1.md) prépare la prise en compte
des informations facultatives sourcées qui ne figurent pas dans les références.
Il conserve les fichiers gelés et ne clôture aucune décision ouverte à la place
du relecteur. Son enregistrement dans `eval/amendments.jsonl` distingue cette
préparation d’un recalcul et d’une publication de résultats.

Après résolution des cinq décisions restantes, cet amendement est appliqué
aux [120 annotations finales](HUMAN_REVIEW_RESULTS.md). Les résultats et indices bootstrap
sont archivés séparément dans `eval/results/reviewed-v1.1/`. Le gel et les résultats
historiques v1 restent conservés ; la revue par l’auteur n’est pas indépendante.
