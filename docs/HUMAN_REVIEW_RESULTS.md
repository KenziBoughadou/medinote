# Comment on a évalué les notes

On cherche à répondre à une question simple : est-ce que la note conserve ce qui a
été dit dans le dialogue, sans le déformer ni ajouter d’informations ? Pour le vérifier,
on a annoté les 80 notes du test principal et les 40 notes du test de négation.
On a aussi relu les références des trois ensembles : développement, test et stress.
Elles ont été conservées sans correction.

La relecture a été faite par l’auteur du projet. Il n’y a pas encore de second avis
indépendant, et ce travail ne constitue pas une validation clinique.

## Comment on passe du dialogue à une annotation

On lit le dialogue, puis on examine les informations de la note une par une. Pour
chacune, on cherche le passage qui la soutient et on vérifie notamment le sujet,
les négations et les précisions de temps. On distingue les informations correctes,
les contradictions et les ajouts sans source. On reprend ensuite les faits attendus
pour repérer ceux que la note a oubliés. Les citations sont vérifiées séparément :
un lien vers un passage existant ne suffit pas à prouver que la phrase est correcte.

Les notes ont été présentées sous des identifiants neutres, par lots de dix. Le style
de rédaction pouvait malgré tout permettre de reconnaître la méthode B.
Les [annotations](../eval/results/reviewed-v1.1/annotations.jsonl) conservent les extraits,
les décisions et leurs justifications. Les contrôles du logiciel vérifient leur
cohérence, mais ne décident pas si une information est juste.

## Pourquoi on a ajusté une règle

Cinq notes contenaient une information présente dans le dialogue, mais absente de la
liste des faits attendus. Dans les notes 0059, 0068, 0075 et 0110, il s’agissait du
souhait de décrire la situation sans poser soi-même un diagnostic. Dans la note 0098,
il s’agissait de conserver une trace en laissant les informations manquantes indiquées
comme non mentionnées.

On a classé ces informations comme facultatives et soutenues par leur source. Le
validateur initial exigeait pourtant un fait de référence associé. L’[ajustement
v1.1](ANNOTATION_AMENDMENT_V1_1.md) permet ce cas sans ajouter de fait attendu ni
modifier les formules. Cette règle a été corrigée après avoir vu les résultats ;
elle ne faisait donc pas partie des conditions initiales du calcul.

Le [journal des cinq décisions](../eval/results/reviewed-v1.1/adjudication.json)
permet de suivre cette correction. Les dialogues, les générations et les références
figés avant le test sont conservés. La correspondance entre les notes et les méthodes
est publiée avec les résultats pour permettre de refaire le calcul.

## Comment on calcule les scores

On compare les deux notes produites pour chacune des 40 consultations test. Chaque
méthode possède 360 faits attendus. Pour la couverture, on compte les faits correctement
repris, puis on divise par 360 : chaque fait attendu a le même poids. Pour les erreurs
dans la note, on divise par le nombre d’informations annotées dans les sorties.

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

Les 40 notes de stress omettent que l’origine de la plainte
reste à préciser. Cette omission suffit à faire échouer toutes les paires. La préférence
horaire est également absente de 18 notes, et le signe cible n’est pas préservé dans une
note. Les [détails par variante](../eval/results/reviewed-v1.1/stress-details.json)
permettent de distinguer ces causes. Ce résultat strict n’est pas fusionné avec le test
principal et ne permet pas de conclure que toutes les négations sont erronées.

## Ce qui peut influencer les résultats

Les références synthétiques contiennent parfois plusieurs informations dans un même
fait. Des annotations peuvent considérer ce fait comme couvert alors qu’un détail a
disparu. Le pilote a relevé ce problème, ainsi que des ambiguïtés de temporalité. On conserve
les décisions de la relecture finale, avec leurs différences par rapport au
pilote exploratoire réalisé par IA. Une seconde relecture et des références
découpées en faits plus simples permettraient d’étudier les désaccords dans une
nouvelle version.

Plusieurs informations annotées peuvent aussi utiliser le même passage complet pour des informations
différentes. Le contrôle actuel exige des extraits exacts et la couverture de toutes
les assertions, mais ne prouve pas une segmentation sémantique optimale. La façon de découper les phrases peut donc influencer les scores.

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
