# Résultats après la relecture de Kenzi

Kenzi a remis les douze lots correspondant aux 120 notes de test et de stress, puis
un second envoi avec les corrections de 57 notes. Il a confirmé la relecture de
toutes les notes, la classification des cinq informations restées ouvertes comme
facultatives et soutenues, et l’acceptation sans correction des références dev, test
et stress. Ces confirmations ont été transcrites dans les artefacts du projet.

Il s’agit d’une annotation par l’auteur du projet. Aucune indépendance, qualification
clinique ou vérification externe de l’identité du relecteur n’est revendiquée.
La conformité des fichiers ne démontre pas la justesse de chaque jugement.

## Passage des exports aux résultats

Les exports initiaux étaient en brouillon et portaient un identifiant non renseigné.
La confirmation explicite de Kenzi a permis de renseigner son identifiant et de
marquer comme complètes les notes dont les contrôles d’alignement étaient réussis.
Les annotations nécessitant une correction sont restées en attente jusqu’au second
envoi. Les textes normalisés de plusieurs informations étaient identiques malgré
des contenus différents ; aucune fusion automatique de ces informations n’a été faite.

Les cinq dernières décisions ont été clôturées conformément à sa confirmation :
décrire la situation sans poser de diagnostic dans les notes 0059, 0068, 0075 et 0110,
et conserver une trace en signalant les informations manquantes dans la note 0098.
Le [journal de clôture](../eval/results/reviewed-v1.1/adjudication.json) conserve les
décisions avant et après confirmation. Les empreintes des archives reçues figurent
dans le [reçu de relecture](../eval/results/reviewed-v1.1/review-receipt.json).

Ces informations sont présentes dans le dialogue mais absentes des références
prédéfinies. Le [validateur v1.1](ANNOTATION_AMENDMENT_V1_1.md) permet de les classer
comme facultatives avec une preuve source, sans inventer un fait gold. Il conserve
les autres contrôles et n’ajoute rien au dénominateur des faits attendus.
Cet amendement intervient après observation et reste distinct du protocole initial.

Les textes, générations, références, guide initial et code gelé de v1 sont inchangés.
Les événements d’acceptation des références sont ajoutés séparément, associés aux
empreintes des trois fichiers concernés. Le mapping entre notes aveugles et méthodes
est publié après la clôture des annotations pour permettre la reproduction.

## Ce qui est calculé

Les 40 consultations test sont comparées par paires A/B. Chaque méthode possède
360 faits attendus. Les comptes sont additionnés avant division : ce sont des
proportions micro, pas une moyenne de pourcentages par note.

| Compteur du test principal | A | B |
|---|---:|---:|
| Faits attendus correctement couverts | 345 | 333 |
| Faits attendus omis | 15 | 26 |
| Faits attendus contredits | 0 | 1 |
| Informations de sortie annotées | 364 | 432 |
| Informations de sortie non soutenues | 0 | 0 |
| Informations de sortie contradictoires | 0 | 1 |
| Associations information–citation soutenues | 367 / 368 | 431 / 433 |

La couverture vaut 95,83 % pour A et 92,50 % pour B. La différence B−A est de
−3,33 points, avec un intervalle bootstrap de [−5,28 ; −1,39] points. Le calcul
réutilise les formules v1 : 10 000 rééchantillonnages des 40 consultations, mêmes
indices pour les deux méthodes, NumPy PCG64 et graine 20260911. Les indices sont
archivés dans `bootstrap-indices.json.gz`.

Ces intervalles reflètent les variations entre les cas du corpus. Ils n’estiment
ni l’incertitude des jugements du relecteur ni la généralisation à des consultations
réelles. Un intervalle [0 ; 0] pour les ajouts signifie simplement qu’aucun ajout
n’a été étiqueté dans ces données ; ce n’est pas une garantie de risque nul.

## Pourquoi le stress donne 0 sur 10

Le critère de réussite d’une paire exige que les deux variantes restituent le fait
dont la polarité change et tous les faits invariants, y compris les faits facultatifs
explicitement inclus dans ce critère. Ce test n’est donc pas un simple taux de bonnes
négations.

Dans les annotations reçues, les 40 notes de stress omettent que l’origine de la plainte
reste à préciser. Cette omission suffit à faire échouer toutes les paires. La préférence
horaire est également absente de 18 notes, et le signe cible n’est pas préservé dans une
note. Les [détails par variante](../eval/results/reviewed-v1.1/stress-details.json)
permettent de distinguer ces causes. Ce résultat strict n’est pas fusionné avec le test
principal et ne permet pas de conclure que toutes les négations sont erronées.

## Limites à garder visibles

Les références synthétiques contiennent parfois plusieurs informations dans un même
fait. Des annotations peuvent considérer ce fait comme couvert alors qu’un détail a
disparu. Le pilote a relevé ce problème, ainsi que des ambiguïtés de temporalité. Les
décisions confirmées par Kenzi sont conservées ; elles ne sont pas remplacées par celles
du pilote IA. Une seconde relecture et une référence plus atomique permettraient
d’étudier les désaccords dans une nouvelle version.

Plusieurs claims peuvent aussi utiliser le même passage complet pour des informations
différentes. Le contrôle actuel exige des extraits exacts et la couverture de toutes
les assertions, mais ne prouve pas une segmentation sémantique optimale. Les scores
dépendent donc de cette granularité déclarée.

L’auteur connaissait le projet et le pilote. Le style de B peut révéler sa méthode.
Le corpus est petit, artificiel et régulier, avec un seul modèle et une tentative
par méthode et par cas. Une meilleure couverture de A dans cette campagne ne prouve
pas une supériorité générale du résumé direct. Aucun gain de temps professionnel,
entraînement de modèle ou usage clinique validé n’est démontré.

## Reproduire le calcul

Depuis la racine du dépôt, dans l’environnement Python verrouillé :

```bash
uv run python scripts/report_reviewed_v1_1.py --output .state/reproduction-relecture-v1.1
```

Le répertoire doit être neuf. Le script vérifie les sorties gelées, le mapping,
l’ensemble des annotations et leur cohérence, puis calcule les métriques, intervalles
et figures sans nouvel appel API. Les [résultats archivés](../eval/results/reviewed-v1.1/report/)
contiennent les dénominateurs, coûts et empreintes. Les métriques et indices sont
reproductibles ; les métadonnées de création des SVG peuvent varier.

Les douze notes de démonstration proviennent du développement. Elles ne reçoivent
aucun score transféré depuis cette évaluation des 120 notes test/stress.
