# Ce que montre le premier lot d’annotations

J’ai ajouté un pilote sur dix notes pour confronter le guide d’évaluation aux sorties
réelles. L’annotation est réalisée par IA dans la session Codex, sans relecture humaine.
Le but est d’identifier des erreurs et les difficultés du protocole avant de calculer
un score global. Ce travail reste séparé de l’étude v1 et de ses formulaires de relecture.

## Ce qui a été examiné

Les dix premières notes du lot aveugle déjà préparé ont été lues avec leur dialogue
complet et leurs références. Cela représente huit consultations distinctes, sept notes
du test principal et trois notes de stress. Le choix suit l’ordre préexistant, sans
sélectionner les notes en fonction de leur qualité. Il intervient après la campagne v1
et ne constitue ni un nouveau test indépendant ni une comparaison appariée complète.

| Travail réalisé | Résultat |
|---|---:|
| Notes examinées | 10 sur les 120 notes prévues |
| Informations distinguées dans les notes | 103 |
| Formulaires IA complets | 5 |
| Formulaires laissés en brouillon | 5 |
| Décisions non résolues | 9 |
| Nouveaux appels API de génération ou d’annotation | 0 |

Ces nombres décrivent l’avancement de l’annotation. Ils ne donnent pas le taux de
fidélité d’une méthode. Un formulaire complet ne signifie pas que tous les faits sont
présents : une omission clairement identifiée peut recevoir une décision complète.
Le coût de la session de l’assistant n’est pas mesuré par la comptabilité API du projet.

## Comment les décisions ont été prises

Le dialogue est la source à respecter. Chaque phrase de la note est examinée, y compris
celles qui n’ont pas de citation. Le motif et sa durée sont séparés lorsqu’ils apparaissent
dans une même phrase. Deux formulations de la même action sont regroupées pour éviter
de compter deux fois une consultation de contrôle.

Chaque information est ensuite rapprochée des faits de référence. La décision porte
sur son sens : sujet, valeur, négation, temporalité et incertitude. Par exemple, une
date de début passée ne prouve pas que le symptôme a disparu. L’annotation ne consiste
donc pas à exiger que les mots ou les attributs du gold soient identiques à ceux de la note.

Les citations sont examinées séparément. Une référence existante peut soutenir une
partie de la phrase sans en justifier tous les détails. Les rattachements contextuels
simples, comme une mesure associée à l’unique lésion décrite, sont explicités dans les
justifications ; aucune connaissance médicale externe ne complète les sources.

Les positions exactes des extraits, les preuves et les décisions sont enregistrées en
JSONL. Un petit script transforme les décisions écrites en objets du schéma v1 et
contrôle leur cohérence. Il ne décide pas si une information est vraie. Les cinq
formulaires complets passent aussi les validateurs d’annotation existants.

## Des exemples concrets

| Note | Ce que dit la source | Ce que restitue la note | Décision |
|---|---|---|---|
| `blind-0004` | Un entretien de suivi est annoncé dans huit jours. | L’entretien est futur, mais le délai disparaît. | Couverture partielle ; décision ouverte pour le fait composé. |
| `blind-0010` | Atorvastatine, 10 mg le soir. | La molécule et la dose sont présentes ; « horaire de prise » n’a pas de valeur. | La prise le soir n’est pas restituée. Le fait traitement reste partiellement couvert. |
| `blind-0008` | Deux mois sont mentionnés, mais l’existence de la tache avant sa découverte sur photo est incertaine. | « Apparue depuis deux mois », puis conservation de l’incertitude dans une autre phrase. | Ambiguïté entre découverte et apparition ; pas de verdict automatique forcé. |
| `blind-0005` | L’origine de la plainte reste à préciser. | Cette information n’apparaît pas dans la note. | Omission du fait attendu `evaluation`. |
| `blind-0002` | Une consultation de contrôle est annoncée pour lundi. | Deux assertions décrivent ce même contrôle. | Une seule information avec deux occurrences ; pas deux actions distinctes. |

Les [décisions détaillées](../eval/results/annotation-pilot-1/decisions.json) contiennent
la justification de chaque information. Les [entrées du pilote](../eval/results/annotation-pilot-1/inputs/)
permettent de retrouver les formulations exactes, et les
[annotations compilées](../eval/results/annotation-pilot-1/compiled/annotations.jsonl)
leurs positions dans le texte.

## Pourquoi aucun pourcentage de fidélité n’est publié

La lecture fait apparaître trois difficultés à résoudre. Certains faits de référence
regroupent plusieurs informations, comme une action et sa date, alors que le schéma
prévoit surtout couvert, contredit ou omis. Une restitution partielle ne rentre pas
proprement dans ces trois états. De plus, certains propos sont présents dans le dialogue
sans avoir de référence dédiée : les traiter comme des ajouts inventés serait incorrect.
Enfin, une référence peut elle-même simplifier une ambiguïté du dialogue.

Ces situations restent marquées `unresolved`. Dans leurs brouillons, les statuts des
faits attendus sont provisoires et ne doivent pas être utilisés pour calculer un score.
Le rapport conserve donc `fidelity_metrics: null`. Calculer seulement sur les cinq notes
faciles à finaliser introduirait une sélection trompeuse. Les dix notes ne suffisent pas
non plus à produire le bootstrap apparié prévu sur quarante consultations.

Le fichier de référence gelé et le guide v1 sont conservés. Une règle pour la couverture
partielle ou une correction des références devra faire l’objet d’un amendement explicite,
puis être appliquée à toutes les notes concernées. Les 110 autres notes n’ont pas encore
été annotées dans ce pilote. La relecture humaine de l’ensemble reste à effectuer.

## Provenance et reproduction

L’environnement identifie l’assistant comme appartenant à la famille GPT-6, mais n’expose
pas son snapshot exact. Cette limite est inscrite dans les métadonnées plutôt que de
fournir un identifiant inventé. La session connaissait déjà le projet et le style des
deux méthodes ; aucune indépendance du juge ou garantie d’aveuglement n’est revendiquée.
Les références étant également préparées par IA, les erreurs de jugement peuvent être
corrélées. Ces annotations ne constituent aucune validation clinique.

Les [consignes archivées](../eval/results/annotation-pilot-1/instructions.md) ont une
empreinte, mais ne représentent pas tout le contexte de conversation. On peut reproduire
exactement la compilation des décisions existantes ; on ne peut pas promettre que leur
régénération par une autre session produirait les mêmes décisions.

Depuis la racine du dépôt, avec l’environnement Python du projet :

```bash
uv run python scripts/compile_annotation_pilot.py --output .state/annotation-pilot-reproduction
```

Le répertoire de sortie doit être neuf. `annotations.jsonl` et `summary.json` sont
reproductibles octet pour octet. Le manifest enregistre les empreintes des entrées,
des consignes, du guide, du compilateur et des sorties ; sa date dépend de l’exécution.
Le script ne contacte aucun fournisseur et ne crée aucun événement de revue humaine.
