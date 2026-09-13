# Ce que les corrections permettent de défendre

MediNote étudie des systèmes qui utilisent un modèle déjà entraîné. Sa contribution porte
sur leur comparaison, les erreurs de contenu et la reproductibilité. Les bibliothèques
d’entraînement ne sont pas un critère de qualité en elles-mêmes. Aucun entraînement ni
expérience clinique n’est revendiqué.

## État après l’analyse critique du 13 septembre 2026

| Point soulevé | Changement réalisé | Limite restante |
|---|---|---|
| Positionnement trop proche d’un projet d’entraînement | Introduction française et anglaise centrée sur le NLP appliqué et l’évaluation de LLM. | Aucun modèle entraîné, aucune compétence d’optimisation de réseau revendiquée. |
| Résultats humains absents | Atelier local, douze lots de dix notes, export/reprise, vérification partielle avec les règles v1. | Aucune annotation humaine terminée par la préparation des outils. |
| Corpus artificiel et gold préparé par IA | Provenance conservée, références accessibles pendant la relecture, empreintes contrôlées. | Le corpus reste synthétique et petit. Ajouter des dialogues générés ne résoudrait pas ce biais. |
| A/B change plusieurs facteurs | Question principale corrigée pour porter sur les pipelines complets. | Aucun effet causal de l’extraction seule n’est mesuré. |
| Absence de baseline simple | Lead-5 et TF-IDF centroid-5 implémentés, testés et exécutés sur les 80 consultations. | La qualité des 160 extraits reste à annoter ; ils ne suivent pas les sept rubriques A/B. |
| Un seul modèle, aucune répétition | Ce périmètre est explicite ; aucun essai isolé n’est présenté comme mesure de variance. | Comparaison entre modèles et répétitions non exécutées, faute de budget défini. |
| Ingénierie plus visible que l’évaluation | README recentré sur question, observations, statut de revue et méthodes. | Les tests logiciels ne deviennent pas des résultats scientifiques. |
| Document de construction interne trop présent | Plan retiré de la version publique courante et conservé localement ; décisions utiles présentées dans `EXPERIMENT_PROTOCOL.md` et `ARCHITECTURE.md`. | Historique conservé ; provenance IA des données et absence de revue humaine toujours déclarées. |

## Deux comparateurs sans dépenses d’API

`scripts/extractive_baselines.py` lit exclusivement les dialogues typés. Les fonctions de
sélection ne reçoivent ni gold, ni tags expérimentaux, ni sorties A/B. Aucun modèle ou
paramètre n’est ajusté sur les résultats du test. Le choix de ces comparateurs intervient
après publication de v1 : leur campagne est donc explicitement exploratoire.

Lead-5 garde les cinq premiers tours. TF-IDF centroid-5 représente chaque tour par ses
comptes de mots, pondérés par `idf = 1 + log((1 + N) / (1 + df))`. Ici N est le nombre de
tours de la seule consultation courante ; df compte les tours contenant le mot. Les
vecteurs sont normalisés en norme L2, leur somme est normalisée pour former un centroïde,
puis les cinq tours les plus proches sont sélectionnés par produit scalaire. Les égalités
sont départagées par la position d’origine. L’ordre du dialogue est rétabli à la sortie.

Cette formule lissée suit la convention expliquée dans la
[documentation TF-IDF de scikit-learn](https://scikit-learn.org/stable/modules/feature_extraction.html#tfidf-term-weighting).
L’implémentation utilise la bibliothèque standard Python pour garder les dépendances de
v1 intactes. La tokenisation conserve les mots Unicode et les négations ; aucun stemming,
filtre de mots fréquents ou entraînement supervisé n’est ajouté. Les locuteurs et le texte
original sont recopiés. C’est une sélection lexicale, pas une compréhension clinique.

```bash
uv run python scripts/extractive_baselines.py --root . --output .state/baselines-reproduction
```

Le répertoire doit être neuf. Le manifest conserve les hashes du script, des deux fichiers
d’entrée et des sorties. `outputs.jsonl` contient les extraits ; `comparison.html` permet
leur lecture côte à côte avec le dialogue ; `report.md` sépare dev, test et stress.
La proportion de mots conservés mesure la compression, pas les omissions de faits.

## Ce qui demande encore une expérience

La priorité avec le budget actuel est la relecture de v1. Un premier lot permet d’estimer
le temps réel d’annotation ; ses résultats restent partiels et ne sont pas extrapolés à
la cohorte. Un autre relecteur sur les mêmes notes permettrait ensuite de rechercher les
désaccords, sans prétendre à une indépendance tant qu’elle n’a pas été réalisée.

Pour mieux contrôler le rôle de la rédaction, une expérience ultérieure pourrait réutiliser
exactement les faits déjà extraits par B et comparer leur rendu Python à une rédaction par
LLM. Cela contrôlerait l’entrée du rédacteur, mais ne prouverait toujours pas à soi seul
l’effet de l’extraction face au dialogue brut. Cette nouvelle condition doit avoir son
protocole et ses coûts propres ; elle n’est pas ajoutée rétroactivement à v1.

Un deuxième modèle demande un identifiant exact, un même ensemble de cas et des règles
de validation comparables. Un essai avec captures ne mesure ni la variance ni la robustesse.
Des répétitions devront rester regroupées par consultation pour ne pas compter plusieurs
tirages du même cas comme des cas indépendants. Aucun nouvel appel payant n’est lancé
dans cette correction, et aucun poids n’est téléchargé sur le VPS.

La représentativité demanderait des cas rédigés ou relus par des personnes compétentes,
une provenance et des droits clairs, puis un nouveau jeu réservé. Les consultations réelles
restent hors du périmètre actuel. Le fine-tuning attend des données corrigées, un objectif
mesurable, des ressources hors du VPS et un budget explicite. Un squelette d’entraînement
non exécuté ne serait pas une preuve supplémentaire.
