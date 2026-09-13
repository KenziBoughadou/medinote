# Comparateurs extractifs exploratoires

80 consultations, 160 extraits, aucun appel IA.

Chaque sortie recopie au plus 5 tours de parole (paramètre k dans le manifest), en conservant le locuteur et l’ordre original. Aucun fait gold ne sert à la sélection.

| Ensemble | Méthode | Sorties | Mots conservés / mots source |
|---|---|---:|---:|
| dev | lead | 20 | 45.9% |
| dev | tfidf_centroid | 20 | 47.6% |
| test | lead | 40 | 46.0% |
| test | tfidf_centroid | 40 | 47.5% |
| stress | lead | 20 | 50.2% |
| stress | tfidf_centroid | 20 | 48.0% |

Ce ratio mesure la longueur, pas la couverture des faits ni la qualité.

Ces méthodes peuvent retenir une question sans sa réponse, perdre une négation située dans un autre tour ou omettre une information rare. Copier le texte ne garantit pas une synthèse fidèle. Il n’y a ni note en sept rubriques ni score sémantique final.

Comparaison ajoutée après v1 : ne pas fusionner ses sorties avec les 132 appels figés. Une comparaison de fidélité avec A/B nécessite une annotation dédiée.
