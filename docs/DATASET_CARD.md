# Fiche du corpus

Version 1.0. Langue : français de France. Données exclusivement synthétiques,
préparées par IA ; pas de dossier réel ni dataset traduit.
Provenance dans `data/provenance.v1.json`.

Le 13 septembre 2026, on a terminé la relecture des références et on les a
conservées sans correction. Les événements associés aux hashes figurent dans `data/review-events.jsonl`.
Cette revue ultérieure conserve l’origine IA et les textes initiaux ; aucune validation
clinique ou relecture indépendante n’est revendiquée.

60 parents principaux : six situations distinctes dans chacune des dix familles prévues,
deux dev et quatre test. Dix parents stress supplémentaires possèdent chacun une variante
positive et négative. Les parents stress sont disjoints des parents principaux. Les noms
de familles sont définis dans `backend/src/medinote/corpus.py` ; les six IDs de démonstration
sont conservés dans `data/demo_ids.v1.json`.

Chaque dialogue comporte douze tours, neuf faits attendus et un fait facultatif sourcé.
Les formulations d’entretien récurrentes sont explicites : ce corpus présente une diversité
limitée de styles et de longueur, même si ses situations sont distinctes. Il ne reproduit
ni les hésitations orales réelles ni la diversité clinique d’une population.

Spans `[start,end)` en points de code Unicode, citations exactes. Les paires stress changent
uniquement « ne » et « pas » dans le fait cible. Les contrôles automatiques vérifient effectifs,
parents, invariants, preuves, provenance et tailles des deux requêtes. Ils ne remplacent pas
une revue de fidélité du gold.

Le gold et les tags expérimentaux ne sont jamais fournis aux pipelines. Les exemples
illustratifs sont dérivés éditorialement des références ; ils ne servent pas à mesurer
un modèle. Une correction après gel impose un amendement et une version distincte.

Licence CC BY 4.0. Usage prévu : portfolio et étude comparative exploratoire.
Usage non validé : soin, diagnostic, prescription, décision clinique ou classement de modèles
sur des données représentatives.
