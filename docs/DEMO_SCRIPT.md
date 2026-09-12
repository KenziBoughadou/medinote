# Démonstration et entretien

La vidéo utilise uniquement les illustrations identifiées tant que les vraies générations
ne sont pas disponibles. Le fournisseur est inaccessible pendant la capture.

Vidéo trois minutes :

- 0–30 s : choisir le cas de négation, présenter la consultation fictive.
- 30–80 s : comparer A/B, cliquer les sources et revenir à la citation au clavier.
- 80–120 s : ouvrir la provenance, montrer la relance indisponible, exporter Markdown.
- 120–160 s : ouvrir le rapport en attente puis la méthodologie, sans scores fabriqués.
- 160–180 s : expliquer le rendu Python de B et montrer le lien GitHub.

Entretien cinq minutes : problème de traçabilité ; négation et source ; architecture
un appel A/un appel B et rendu fixe ; protocole avec segmentation des notes finales ;
coûts réservés et erreurs visibles ; limites synthétiques et revue humaine en attente.
La partie « résultats et cas d’échec réel » sera ajoutée uniquement après campagne réelle.
Actuellement, démontrer l’outil d’évaluation sur ses fixtures de tests et annoncer explicitement
qu’il ne s’agit pas d’un résultat du modèle.

Reproduction : `npm --prefix frontend run record:demo` avec le frontend lancé sur 5173.
Le script écrit les captures 1440 px/390 px et une vidéo 1280×720 de 180 secondes.
Si nécessaire, il normalise l’horloge de capture à 180 secondes en conservant le parcours
complet et réencode en VP9 600 kbit/s sans audio. La taille doit rester sous 25 Mio.
