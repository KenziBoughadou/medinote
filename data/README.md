# Corpus MediNote v1

80 consultations françaises entièrement fictives, préparées par IA : 60 parents principaux
(dix familles, 20 dev et 40 test) et dix parents stress indépendants en deux variantes.
Chaque dialogue contient 12 tours, neuf faits attendus et un fait facultatif sourcé.
Les six IDs publics sont fixés dans `demo_ids.v1.json` et appartiennent au développement.
Les champs des références ne sont jamais transmis au générateur.

Les paires stress ne changent que les marqueurs « ne » et « pas » dans la phrase cible.
Les autres faits restent identiques. Les offsets sont des points de code Unicode.

Textes, références et illustrations sont de provenance IA. Aucune revue humaine n'a
encore eu lieu. Les notes illustratives sont des exemples éditoriaux construits depuis
les références ; elles ne mesurent pas les performances d'un modèle. La préparation
initiale est conservée dans `scripts/prepare_corpus.py`. Ne pas la réexécuter pour
corriger silencieusement v1. Une modification après gel exige un amendement.

Le script de préparation historique exige un `--editorial-context` explicite pour toute
nouvelle préparation initiale. Il enregistre le hash de ce document et refuse d’écraser
un corpus existant ou gelé. Les données et la provenance v1 archivées ne sont pas régénérées.

Revue éditoriale et sémantique humaine en attente. Les annotations humaines doivent
porter sur les empreintes exactes et provenir d'un relecteur identifié.

Les illustrations historiques restent dans `illustrative-notes.v1.json`. Le bundle public
utilise désormais les douze générations dev réelles archivées sous `eval/results/v1/demo/`.
Leur origine est `llm_recorded` ; elles ne constituent pas une validation sémantique.
