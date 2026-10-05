# Protocole de l'étude externe ACI-Bench

## Question

Les écarts observés en v1 entre la rédaction directe (A) et l'extraction structurée (B)
se retrouvent-ils sur des consultations qui ne viennent pas de ce projet ?

La v1 reposait sur un corpus synthétique en français, très régulier, sur lequel les
deux méthodes approchaient du plafond. Cette étude applique les deux mêmes méthodes
à **ACI-Bench**, un corpus public de consultations en anglais écrites ou jouées par
des professionnels de santé, avec des notes de référence relues par des experts
([détails et licence](../../data/external/aci-bench/README.md)).

## Ce qui change par rapport à la v1, et pourquoi

| Élément | v1 | Étude externe | Raison |
|---|---|---|---|
| Langue | français | anglais | langue du corpus ; aucune traduction automatique, qui réintroduirait un texte généré |
| Consignes A et B | v1 | traduction fidèle, mêmes règles | comparer les mêmes méthodes |
| Plafond | 40 assertions ou faits | 80 | les notes d'ACI-Bench sont environ quatre fois plus longues |
| Référence | faits annotés avec leur passage source | note complète rédigée par des experts | format du corpus |
| Évaluation | relecture humaine de toutes les notes | deux juges automatiques indépendants, sans relecture humaine | volume de lecture trop important pour cette étude |

Le générateur reste `gpt-4.1-mini-2025-04-14`, à température 0, avec une seule génération
par méthode et par consultation, sans reprise. Le code de la v1 n'est pas modifié.

## Partitions

- **Développement** : les 20 consultations de la validation d'ACI-Bench. Elles servent
  à vérifier le fonctionnement des consignes et du juge. Toute modification est faite
  avant le gel.
- **Test** : les 40 consultations de test1 (MEDIQA-Chat 2023, tâche B). Elles ne sont
  générées qu'une fois, après le gel, et aucune consigne n'est modifiée ensuite.

## Évaluation automatique

Le juge est `gpt-4.1-2025-04-14`, un modèle plus grand que le générateur, pour limiter
le biais d'un modèle qui évalue ses propres sorties. Il ne connaît pas la méthode.
Il réalise trois tâches :

1. **Faits de référence** : découper la note de référence en faits atomiques, une fois
   par consultation. Les mêmes faits servent pour A et B.
2. **Couverture** : pour chaque fait de référence, dire si la note le reprend (`covered`),
   le contredit (`contradicted`) ou l'omet (`omitted`). Un fait repris sans un détail clé
   compte comme omis.
3. **Appui** : pour chaque assertion de la note, dire si le dialogue l'appuie
   (`supported`), la contredit (`contradicted`) ou ne la contient pas (`unsupported`),
   et si les segments cités suffisent.

Un appel au juge qui échoue techniquement (délai, JSON invalide, jugements manquants)
est relancé, trois tentatives au plus. Toutes les tentatives sont archivées.

## Critères

- **Critère principal** : l'écart B−A de couverture des faits de référence sur le test,
  avec un intervalle de confiance à 95 % par bootstrap apparié sur les consultations
  (10 000 tirages, graine 20261005).
- **Critères secondaires** : omissions, faits contredits, assertions sans appui,
  assertions contradictoires, citations suffisantes, ROUGE-1, ROUGE-2 et ROUGE-L par
  rapport à la note de référence, coût moyen et latence médiane.

Le ROUGE est calculé avec une tokenisation simple (minuscules, lettres et chiffres).
Il sert de repère avec la littérature sur ACI-Bench, sans être strictement comparable
aux implémentations officielles.

## Second juge

Un second juge, `gpt-5-mini-2025-08-07`, d'une autre génération de modèles, refait les
tâches de couverture et d'appui sur toutes les notes, avec les mêmes consignes et les
mêmes faits de référence que le juge principal. C'est un modèle à raisonnement : il
n'accepte pas de température, et son effort de raisonnement est fixé à `low`.
On mesure l'accord entre les deux juges élément par élément (accord brut, AC1 de Gwet
et kappa de Cohen), et le rapport présente les résultats selon chacun des deux juges.

**Aucune validation humaine n'est réalisée.** L'accord entre deux juges automatiques
mesure la sensibilité des résultats au choix du juge, pas l'exactitude des jugements :
deux modèles peuvent se tromper de la même façon. Les scores sont donc toujours
présentés comme indicatifs.

**Règle de décision fixée à l'avance** : si l'AC1 de Gwet entre les deux juges reste
sous 0,6 pour la couverture **ou** pour l'appui, les scores sont présentés comme
exploratoires, sans conclusion sur l'écart entre A et B.

La règle utilise l'AC1 plutôt que le kappa de Cohen parce que les assertions sans
appui devraient être rares. Quand une étiquette domine à ce point, le kappa devient
instable, voire indéfini, même si les deux juges sont presque toujours d'accord.
L'AC1 reste interprétable dans ce cas. Le kappa est tout de même publié.

## Coût et exécution

Les appels réels passent par la release de production et partagent son budget mensuel
de 10 $. Chaque appel réserve son coût maximal avant d'être envoyé. Estimation pour
les deux partitions : environ 0,50 $ de générations, 4 à 6 $ pour le juge principal
et 2 à 3 $ pour le second juge. Si le budget du mois ne suffit pas, la campagne
s'interrompt sans dépassement ; les jugements reprennent le mois suivant sans repayer
ceux déjà obtenus.

## Limites connues à l'avance

- Les consultations d'ACI-Bench sont écrites ou jouées, pas enregistrées chez de vrais
  patients, et elles sont en anglais.
- La note de référence est une rédaction possible parmi d'autres : une information
  absente de la référence n'est pas forcément une erreur de la note générée. C'est
  pourquoi l'appui dans le dialogue est mesuré séparément.
- Les deux juges automatiques peuvent se tromper, y compris de la même façon ; aucune
  relecture humaine ne vérifie leurs jugements.
