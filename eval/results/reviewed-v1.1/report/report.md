# MediNote — rapport reproductible

Évaluation terminée : références vérifiées et notes annotées.

Mesures micro bout en bout ; résultats conditionnels et dénominateurs dans metrics.json.

| Mesure | A | B | B − A | IC95 |
|---|---|---|---|---|
| omission | 0.0417 | 0.0722 | 0.0306 | 0.0111 ; 0.0500 |
| coverage | 0.9583 | 0.9250 | -0.0333 | -0.0528 ; -0.0139 |
| expected_contradiction | 0.0000 | 0.0028 | 0.0028 | 0.0000 ; 0.0083 |
| unsupported | 0.0000 | 0.0000 | 0.0000 | 0.0000 ; 0.0000 |
| contradiction | 0.0000 | 0.0023 | 0.0023 | 0.0000 ; 0.0071 |
| negation_error | 0.0000 | 0.0030 | 0.0030 | 0.0000 ; 0.0091 |
| negative_coverage | 1.0000 | 1.0000 | 0.0000 | 0.0000 ; 0.0000 |
| resolvable_references | 1.0000 | 1.0000 | 0.0000 | 0.0000 ; 0.0000 |
| citation_precision | 0.9973 | 0.9954 | -0.0019 | -0.0095 ; 0.0060 |
| citation_coverage | 1.0000 | 0.9977 | -0.0023 | -0.0071 ; 0.0000 |
| technical_reliability | 1.0000 | 1.0000 | 0.0000 | 0.0000 ; 0.0000 |
| notes_with_additions | 0.0000 | 0.0000 | 0.0000 | 0.0000 ; 0.0000 |
| additions_per_consultation | 0.0000 | 0.0000 | 0.0000 | 0.0000 ; 0.0000 |

## Limites
- Corpus exclusivement synthétique, sans validation clinique.
- Annotation par l’auteur ; aucune indépendance revendiquée.
- Le style de B peut compromettre l’aveuglement.
- Comparaison des pipelines complets ; le mode de rédaction change aussi.
- Les coûts connus sont majorants sans déduction du cache ; les usages manquants restent inconnus.
- Alignement v1.1 amendé après observation : faits facultatifs sourcés admis hors références.
- Une seule personne a annoté les notes ; les contrôles logiciels ne vérifient pas la justesse de chaque décision.
- Faits de référence parfois composés et segmentation déclarée : une couverture partielle peut être surestimée.
- Les intervalles bootstrap mesurent la variabilité entre cas, pas l’incertitude de l’annotation.

## Observations d’erreur
- main-dermatologique-04 / c6e191292bc340fcaef8f92068866207 : ok. Voir les annotations de cette sortie.
- stress-04-negative / 7e1df684b1c24e0b8e3f1c1e8d0cc069 : ok. Voir les annotations de cette sortie.
