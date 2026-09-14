# Ce que mesure le test de stress

Ce diagnostic est ajouté après observation des résultats de v1. Il décompose les
annotations existantes sans changer le score strict, les notes ou les références.
Aucun nouvel appel au modèle. Ces mesures sont descriptives et ne sont pas un
nouveau benchmark indépendant.

| Mesure | A direct | B structuré |
|---|---:|---:|
| Paires réussies au critère strict initial | 0 / 10 | 0 / 10 |
| Paires avec le fait cible conservé dans les deux variantes | 10 / 10 | 9 / 10 |
| Notes avec le fait cible conservé | 20 / 20 | 19 / 20 |

Le fait cible est celui dont la polarité change entre les deux variantes.
« Conservé » signifie que l’annotation le classe comme couvert ; ce critère porte
sur le fait entier, pas uniquement sur le mot de négation. Une omission échoue
aussi. Les 20 notes par méthode correspondent à dix paires, pas à vingt cas
indépendants. On ne calcule pas de nouvel intervalle ni de classement global.

## Conservation des faits invariants

Chaque ligne porte sur les 20 variantes par méthode. La disponibilité reste
facultative dans le test principal, mais fait partie du critère strict de stress.
Une assertion facultative doit être sourcée et reliée à sa référence pour compter.

| Fait invariant | A direct | B structuré |
|---|---:|---:|
| antecedent | 20 / 20 | 20 / 20 |
| conduite | 20 / 20 | 20 / 20 |
| contexte | 20 / 20 | 20 / 20 |
| debut | 20 / 20 | 20 / 20 |
| disponibilite | 2 / 20 | 20 / 20 |
| evaluation | 0 / 20 | 0 / 20 |
| motif | 20 / 20 | 20 / 20 |
| observation | 20 / 20 | 20 / 20 |
| traitement | 20 / 20 | 20 / 20 |

## Comment lire ces résultats

L’omission systématique de l’évaluation exprimée suffit à faire échouer toutes
les paires au score strict. Ce score a donc peu de pouvoir pour départager les
méthodes sur ces données. Le détail permet de distinguer cette omission du
traitement du fait cible, sans sélectionner seulement les faits réussis.

Le découpage est post hoc, le corpus est synthétique et une seule personne a
annoté les notes. Les résultats restent dépendants de ces décisions. Pour une
nouvelle campagne, il faudrait définir les dimensions à mesurer avant les appels,
tester leur sensibilité sur le développement puis les figer pour un nouveau jeu.

[Détail des 40 notes](diagnostic.json) · [Empreintes](manifest.json) ·
[Méthodologie](../../../docs/HUMAN_REVIEW_RESULTS.md)

Pour refaire le diagnostic depuis la racine, dans un nouveau dossier :

```bash
uv run python scripts/analyze_stress_v1.py --output .state/stress-diagnostic-v1
```
