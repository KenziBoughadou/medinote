# Résultats v1.1 après relecture

Les 120 annotations portent sur les 80 sorties du test principal
et les 40 sorties de stress de la campagne v1. Les références ont été acceptées sans
correction. Les fichiers gelés et les résultats historiques v1 sont conservés.

[Méthodologie et limites](../../../docs/HUMAN_REVIEW_RESULTS.md) ·
[Analyse de neuf erreurs et points à revoir](../../../docs/ERROR_ANALYSIS.md) ·
[Rapport chiffré](report/report.md) · [Métriques et dénominateurs](report/metrics.json) ·
[Annotations](annotations.jsonl) · [Clôture des cinq décisions](adjudication.json) ·
[Traçabilité de la relecture](review-receipt.json) · [Manifest](manifest.json)

Le mapping est rendu public après clôture pour permettre de rattacher les annotations
aux sorties archivées. La relecture est celle de l’auteur : elle n’est ni indépendante
ni une validation clinique. Les contrôles garantissent une cohérence de format et de
références, pas la justesse de toutes les décisions sémantiques.

La couverture test est de 345/360 pour A et 333/360 pour B. Le critère strict de stress
donne 0/10 pour les deux méthodes, principalement à cause d’un invariant omis dans
toutes les notes. Les cas et causes sont dans `stress-details.json`.

Reproduction sans nouvel appel API, depuis la racine :

```bash
uv run python scripts/report_reviewed_v1_1.py --output .state/reproduction-relecture-v1.1
```

La commande utilise le validateur amendé v1.1 ; la CLI historique `medinote eval report`
reste associée au validateur gelé v1. Les nouvelles figures sont des exports Matplotlib,
pas des captures retouchées. Les scores du test ne sont pas attribués aux notes dev.
