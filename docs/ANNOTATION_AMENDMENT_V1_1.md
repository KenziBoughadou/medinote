# Amendement d’alignement v1.1 — informations facultatives hors références

En contrôlant les annotations, on a repéré une contradiction entre le guide
et son validateur. Une information présente dans le dialogue, mais non requise dans
la note, doit pouvoir être classée comme facultative et soutenue. Le validateur v1
exige pourtant un identifiant de référence pour ce label, même lorsque la liste des
références ne contient pas cette information.

La correction v1.1 autorise uniquement `supported_optional` avec une liste `gold_ids`
vide. Des preuves exactes dans le dialogue restent obligatoires. Les citations restent
évaluées une par une ; les champs, empreintes, contradictions, faits attendus,
doublons et décisions ouvertes conservent les mêmes contrôles. Un fait attendu ne
peut pas être déclaré facultatif tout en gardant son alignement au gold attendu.

Cette règle est implémentée dans
[`annotation_alignment_v1_1.py`](../scripts/annotation_alignment_v1_1.py), copie versionnée
du validateur initial avec une seule condition modifiée. Le code v1, les dialogues,
les faits de référence et le manifest gelé sont conservés. Il s’agit d’un amendement
après observation des résultats, pas d’une règle présentée comme préenregistrée.

Un fait facultatif hors références compte dans les assertions de sortie et leurs
citations. Il n’ajoute aucun fait au dénominateur des faits attendus et ne transforme
pas une omission attendue en couverture. Les formules des métriques restent inchangées.
La correction ne règle pas à elle seule les limites de segmentation ou de couverture
partielle décrites dans le [pilote](ANNOTATION_PILOT.md).

Les cinq notes concernées dans le second envoi sont `blind-0059`, `blind-0068`,
`blind-0075`, `blind-0098` et `blind-0110`. On les avait laissées en `unresolved` car
l’information était sourcée sans référence compatible. Après relecture, on les a
classées comme facultatives et soutenues par le dialogue.
Le premier envoi et les corrections sont conservés séparément ; aucune substitution
silencieuse d’une annotation antérieure n’est effectuée.

Le 13 septembre 2026, on a terminé ces cinq décisions et conservé les références
sans correction. La clôture
est enregistrée dans `eval/results/reviewed-v1.1/adjudication.json`, avec les décisions
avant et après confirmation. Le [rapport de relecture](HUMAN_REVIEW_RESULTS.md) applique
la règle aux 120 notes, sans écraser les résultats v1.

Tout futur calcul utilisant cette règle doit identifier la version v1.1, enregistrer
son empreinte et celles des annotations, puis contrôler toute la cohorte. Il ne doit
ni écraser le rapport historique v1 ni présenter 115 notes valides comme 120 notes
finalisées. Les contrôles logiciels
vérifient la cohérence des fichiers ; ils ne remplacent pas la lecture des sources.
