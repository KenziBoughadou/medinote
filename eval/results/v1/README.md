# Sorties brutes de la campagne v1

132 tentatives exécutées le 12 septembre 2026 sur le snapshot
`gpt-4.1-mini-2025-04-14`, dans l’API de production avec le budget partagé.
Les 12 démos, 80 sorties principales et 40 sorties stress sont conservées. Toutes sont
techniquement valides ; cela ne mesure pas leur fidélité sémantique.

- [Relevé d’exécution](report.md), [manifest de campagne](run-manifest.json),
  [manifest figé](../../frozen-manifest.v1.json).
- `runs.jsonl`, `raw-responses.jsonl` et `notes.jsonl` : index consolidés des 132 tentatives.
- `demo/`, `study/main-test/` et `study/stress/` : archives originales avec les fichiers
  individuels et leurs empreintes. Les index consolidés pointent vers ces mêmes fichiers.
- Code des générateurs figé au commit `3138ec963c32c6c5acfac93ffddbf0490f5c08ca`.
  Les commits de publication ultérieurs ne changent pas ces générateurs.

**L’évaluation est terminée.** On a annoté les 120 notes de test et de stress et
conservé les références après relecture. Les [résultats v1.1](../reviewed-v1.1/)
rassemblent les scores, les annotations et les intervalles de confiance. La
[méthodologie](../../../docs/HUMAN_REVIEW_RESULTS.md) explique comment on les calcule.

Ce dossier conserve les réponses du modèle au moment de la génération. Les statuts
inscrits dans ses manifests décrivent cet état initial, avant l’annotation. Les
résultats de l’évaluation sont archivés séparément pour garder cette chronologie.
Les douze notes de démonstration ne font pas partie des 120 notes évaluées.

La correspondance entre les identifiants des notes et les méthodes, masquée pendant
l’annotation, est maintenant [disponible](../reviewed-v1.1/blind-mapping.json).
Le corpus a été préparé par IA et reste entièrement fictif. L’évaluation a été faite
par l’auteur du projet, sans second avis indépendant ni validation clinique.

Vérifier les archives sans nouvel appel :

```bash
uv run python - <<'PY'
from pathlib import Path
from medinote.evaluation.runner import collect_runs
runs = collect_runs(Path('eval/results/v1'), Path('.'))
assert len(runs) == 132
print('132 tentatives et empreintes vérifiées')
PY
```

Les essais de mise au point sont distincts : [historique dev](../../../docs/DEV_TRIALS.md).
Leurs erreurs n’ont pas été supprimées ni transformées en succès de la campagne v1.
