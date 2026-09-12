# Relecture humaine des références

Ce travail vérifie la fidélité des références aux dialogues fictifs. Il ne constitue pas
une validation médicale. Les références sont actuellement préparées par IA et non relues.

Préparer les documents lisibles, sans modifier le corpus ni geler une campagne :

```bash
uv run python scripts/prepare_reference_review.py --root . --output .state/reference-review-v1
```

Le dossier de sortie doit être neuf. Ouvrir `dev.html` (20 consultations), puis `test.html`
(40) et `stress.html` (20 variantes). Chaque document contient le dialogue intégral, tous
les champs des faits gold et les extraits sources avec leurs positions. `reference-hashes.json`
identifie les trois fichiers exacts. Ces documents locaux sont ignorés par Git.

Seuls les cas dev servent aux ajustements des prompts. La relecture des références test
et stress ne doit pas servir à ajuster le générateur. Toute amélioration conçue après
inspection des sorties test est déclarée post hoc, conformément au plan.

Pour chaque fait, vérifier le sujet, la valeur/unité, la polarité, la temporalité, la
certitude et le caractère attendu dans la note. Vérifier que l’extrait exact soutient
le fait et chercher les faits attendus manquants. Pour chaque paire stress, vérifier
la seule inversion cible et la stabilité des autres faits. Consigner toute correction
avec le `case_id`, le `fact_id`, la preuve et le motif ; ne pas modifier silencieusement v1.

Après relecture complète d’un fichier, le relecteur identifié crée ou confirme son propre
événement dans `data/review-events.jsonl` : `artifact_sha256` du fichier relu, `reviewer_id`,
`kind: human`, `reviewed_at` UTC, `outcome: accepted` ou `changes_requested`, et `remarks`.
La préparation de cet export ne crée aucun événement. Une relecture partielle ne permet
pas d’accepter le hash d’un fichier entier. Une modification des références invalide
l’acceptation de leur ancien hash ; après gel, appliquer la politique d’amendement du plan.

La relecture des références et l’annotation des sorties sont deux opérations différentes.
Après les générations réelles, utiliser l’export aveugle et
[le guide d’annotation](../eval/annotation-guide.v1.md) pour annoter les notes finales.
Aucun score sémantique final n’est publié à partir de ce seul dossier de références.
