# Campagne réelle v1 — annotation humaine en attente

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

Les références sont préparées par IA, non relues humainement. Aucun fichier d’annotation
complétée, métrique sémantique, bootstrap ou figure statistique n’est créé avant la revue.
La campagne est exploratoire et n’est pas une validation clinique.

Les 120 formulaires vierges et documents d’annotation sont dans l’état privé du serveur,
`/var/lib/medinote/experiments/v1/blind/`, avec une copie de travail locale ignorée par Git
dans `.state/annotation-v1/`. Le mapping méthode–note reste dans `study/private/` sur le
serveur jusqu’à la clôture de l’annotation. La forme du texte peut révéler la méthode B.
Le relecteur doit suivre [le guide](../../annotation-guide.v1.md), puis utiliser les
commandes d’import et de rapport décrites dans [l’exploitation](../../../docs/DEPLOYMENT.md).

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
