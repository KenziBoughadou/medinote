# Essais de développement avant gel

Les essais utilisent uniquement les vingt consultations `dev`, via le service de génération
de la release de production et sa base d’usage partagée. Ils ne font pas partie des 132
tentatives de la campagne figée et ne permettent pas d’estimer les performances sur test.

## Première version des prompts

Release `57d4207422953639d94aec019a648f3eb010d2f5`, le 12 septembre 2026 :
40 essais A/B archivés, 39 sorties techniquement valides et un `schema_error`.
Le rejet concerne `main-neurologique-01`, méthode structurée : un proche était représenté
par `subject.kind=patient` avec un label familial, combinaison interdite par le contrat.

L’inspection de quelques sorties dev a aussi signalé des négations ambiguës dans le rendu
B (« absence … — nié »), la perte de précisions temporelles et des reformulations dans A.
Ce sont des observations de mise au point, sans annotation complète ni scores
sémantiques. La précision des citations reste à annoter même lorsqu’elles sont résolubles.

Un premier appel dev supplémentaire a rencontré une erreur d’archivage après génération
(objet Pydantic imbriqué non sérialisé par le script ponctuel). Sa réponse n’est pas
récupérable, sa dépense reste dans la comptabilité et l’incident est conservé sous
`/var/lib/medinote/experiments/pilot-dev-01/archival-error.json`. Cet appel est exclu de
toute analyse des sorties. Aucun appel n’a été effacé de la comptabilité.

## Ajustement autorisé avant gel

Le prompt B précise les contraintes déjà prévues : labels sans négation, sujet patient
sans label, proches identifiés, conservation des précisions et certitudes. Le prompt A,
le corpus, les références, le snapshot, les schémas et le renderer restent inchangés.
Le manifest des prompts est actualisé. Les nouveaux essais doivent utiliser la nouvelle
image issue de la CI ; aucune injection de prompt modifié dans une ancienne release.

Les essais initiaux restent sous l’état privé `experiments/pilot-dev-02-direct`,
`pilot-dev-02-structured` et `pilot-dev-remaining`, avec requêtes, réponses fournisseur,
sorties finales et métadonnées. Les budgets, secrets et identifiants de quota ne sont pas
publiés. La vérification des références et l’annotation des sorties sont nécessaires
pour publier les scores finaux.

## Contrainte de sujet envoyée au fournisseur

La release `8325cdc3b52f6a11a85a6f3668e5005c69f842f7` a produit 19 sorties valides sur
20 nouveaux essais B dev ; le même cas neurologique a été rejeté. La release
`e8eb90e13dc4ef97b17fc453ebc3943c6f08ef2f`, avec un exemple de comparaison supplémentaire,
a encore échoué sur ce cas, tandis que `main-prevention-02` a réussi. Ces observations
restent archivées dans `pilot-dev-structured-final` et `pilot-dev-comparison`.

Le diagnostic a identifié une lacune technique : la contrainte croisée du validateur
Pydantic `Subject` n’était pas représentée dans le JSON Schema envoyé au fournisseur.
Celui-ci autorisait donc une combinaison que le backend rejetait. Le constructeur de
requête exprime désormais exactement cette règle via un `anyOf` imbriqué : patient avec
label nul, ou proche/tiers avec label non vide. Aucun champ ni type métier ne change ;
le renderer et le validateur restent identiques. Sept tests couvrent la correspondance
des combinaisons entre contrat fournisseur et validation locale. Les unions imbriquées
sont [prises en charge par Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).

Cette correction précède le gel et ne repose sur aucune sortie test. Une nouvelle image
et un essai réel doivent confirmer sa prise en charge avant d’exécuter la campagne.

La correction a été confirmée dans la release `3138ec963c32c6c5acfac93ffddbf0490f5c08ca`
sur `main-neurologique-01`, `main-prevention-02` et `main-digestif-01` : trois sorties
structurées techniquement valides, archivées dans `pilot-dev-subject-schema`. Les prompts
ont alors été stabilisés et le manifest v1 figé avant toute génération test. Ces trois
succès ne constituent pas un score de fidélité ni une preuve de supériorité de B.

La campagne et l’annotation sont désormais terminées. Les [résultats v1.1](HUMAN_REVIEW_RESULTS.md)
sont calculés sur les notes du test, séparément des essais de développement décrits ici.
