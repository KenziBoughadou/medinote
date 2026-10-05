# ACI-Bench : copie figée pour l'étude externe

Ces deux fichiers sont des copies exactes du corpus public **ACI-Bench**, utilisées
pour vérifier les résultats de MediNote sur des consultations qui ne viennent pas
de ce projet.

| Fichier | Partition d'origine | Usage dans MediNote | SHA-256 |
|---|---|---|---|
| `valid.csv` | validation (20 consultations) | développement des consignes et du juge | `6629e89e3fb409d2b3eceab60dc7b32fe1d3fb8d4e07795039284965522aa4d0` |
| `clinicalnlp_taskB_test1.csv` | test1, MEDIQA-Chat 2023 tâche B (40 consultations) | test, lu après le gel | `5cc4008e68545f84913744a8e493a58bdf17ba7e1b7a0be46d6943d6bfca9471` |

Source : [github.com/wyim/aci-bench](https://github.com/wyim/aci-bench), dossier
`data/challenge_data`, commit `b909b2bb9cf1d19de08df15cddde7bd0179665e4`.
Aucune modification n'a été apportée aux fichiers.

## Origine des données, selon l'article de référence

- Les transcriptions des sous-ensembles **virtassist** et **virtscribe** ont été
  créées par une équipe d'au moins cinq experts (médecins, assistants médicaux,
  scribes, informaticiens cliniques), à partir de leur expérience et de l'étude
  de consultations réelles.
- Le sous-ensemble **aci** a été créé par un médecin et une personne non soignante
  qui jouent une consultation à partir d'une liste de symptômes.
- Les notes de référence ont été produites par un système automatique, puis
  vérifiées et réécrites par des experts du domaine. Les phrases sans appui dans
  le dialogue ont été repérées et retirées.

Ce ne sont donc pas des enregistrements de patients réels, mais des consultations
écrites ou jouées par des professionnels de santé, en anglais.

## Licence et citation

ACI-Bench est publié sous licence
[Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).

Yim, W., Fu, Y., Ben Abacha, A., Snider, N., Lin, T., Yetisgen, M. (2023).
*ACI-BENCH: a Novel Ambient Clinical Intelligence Dataset for Benchmarking
Automatic Visit Note Generation.* Nature Scientific Data.
