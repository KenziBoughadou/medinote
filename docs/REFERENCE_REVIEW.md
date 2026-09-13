# Relecture humaine des références

Ce travail vérifie la fidélité des références aux dialogues fictifs. Il ne constitue pas
une validation médicale. Les références préparées par IA ont été acceptées sans correction
par Kenzi le 13 septembre 2026. Les événements associés aux empreintes sont conservés
dans `data/review-events.jsonl`. Les [résultats de relecture](HUMAN_REVIEW_RESULTS.md)
décrivent les 120 annotations finales et l’amendement v1.1 utilisé pour leur import.

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

## Annoter les notes par petits lots

Les 120 documents aveugles déjà exportés sont disponibles localement sous
`.state/annotation-v1`. Leur mapping reste privé sur le serveur. Préparer des lots
avec le formulaire hors ligne :

```bash
uv run python scripts/annotation_review.py prepare --root . --blind .state/annotation-v1 --output .state/relecture-v1 --size 10
```

Le dossier de sortie doit être neuf. Ouvrir `index.html`, puis un lot. La copie de travail
actuelle contient douze lots de dix notes. Le document n’effectue aucun appel réseau et
ne contient ni nom de méthode ni mapping. Le style des notes peut toujours révéler B.

Lire le dialogue intégral et les références avant de juger la note. Pour chaque assertion,
ajouter autant d’informations que nécessaire. Les positions de début et de fin permettent
de séparer une phrase contenant plusieurs faits ; elles comptent les caractères Unicode,
comme Python. Une répétition se rattache à la même information par un passage supplémentaire.
Le texte, sa source, les faits associés, les décisions et les justifications restent inspectables.

Choisir les faits de référence liés à chaque information, les preuves du dialogue, la décision
et les éventuels types de contradiction. Juger chaque citation séparément. Examiner ensuite
tous les faits de référence pour identifier les omissions. Le formulaire ne présélectionne
aucune décision correcte. Les preuves choisies dans l’interface sont des tours de parole
complets ; préciser la portion pertinente dans la justification si nécessaire.

Renseigner son identifiant, exporter le lot et conserver le fichier JSONL avant de fermer.
Il n’y a pas de sauvegarde automatique. Recharger cet export dans le même lot pour reprendre.
Les brouillons ne sont pas des annotations finales, même si certains champs sont remplis.
Ne choisir « Relecture terminée par moi » qu’après avoir réellement terminé toute la note.
Les exports d’autres lots ou d’empreintes différentes sont refusés.

Vérifier un ou plusieurs lots sans attendre d’avoir terminé les 120 notes :

```bash
uv run python scripts/annotation_review.py check --root . --blind .state/annotation-v1 --annotations CHEMIN_DU_LOT_1.jsonl CHEMIN_DU_LOT_2.jsonl
```

La commande indique notes terminées, brouillons, manquants et erreurs avec le fichier et
la ligne. Les annotations finales passent les mêmes contrôles d’alignement que v1. Le code
de sortie 2 signale une erreur ; un résultat sans erreur peut rester incomplet. Vérifier
`all_complete` avant de passer à l’import final. Un contrôle réussi prouve une conformité
structurelle, pas l’identité du relecteur ni la justesse sémantique de ses décisions.

Lorsque tout est terminé, réunir les derniers exports de chaque lot dans un seul JSONL,
sans doublon, puis utiliser l’import et le rapport de la CLI existante sur le serveur.
Ne mélanger ni anciennes et nouvelles sauvegardes d’un même lot ni relecteurs distincts.
L’acceptation humaine des références reste une étape séparée. Aucun des outils ci-dessus
n’écrit dans `data/review-events.jsonl`, ne modifie v1 ou ne publie automatiquement des scores.
