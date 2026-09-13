# Fiche du système

MediNote utilise le snapshot `gpt-4.1-mini-2025-04-14` via OpenAI Responses.
Il ne s’agit ni d’un modèle entraîné pour ce projet ni d’un modèle hébergé sur le VPS.
Les deux pipelines utilisent la même source, température 0, plafond 4 000 tokens,
Structured Outputs stricts, `store=false`, sans outils ni raisonnement demandé.

A rédige une note directement. B extrait des faits (sujet, polarité, temporalité,
certitude, valeur, unité, références), ensuite rendus par un gabarit Python fixe.
Les rubriques sont identiques et les listes absentes restent vides. Les champs nullable
sont explicitement présents. Aucun résultat invalide n’est réparé silencieusement.

Une requête estimée au-delà de 6 000 tokens ou de 24 000 octets est refusée.
Chaque tentative est limitée à 25 secondes ; deadline publique 55 secondes.
Une seule reprise publique est possible sur les statuts 429, 502, 503 ou 504, si le délai
`Retry-After` est absent ou inférieur ou égal à deux secondes, avec nouvelle réservation.
Les campagnes n’ont aucune reprise.

La fidélité sémantique, les erreurs de négation et les ajouts nécessitent l’annotation
des notes finales. Aucune précision clinique, confiance ou amélioration chiffrée n’est
actuellement revendiquée. Les erreurs sont visibles et les sources restent consultables.

Références officielles consultées le 11 septembre 2026 :
[modèle et tarifs](https://developers.openai.com/api/docs/models/gpt-4.1-mini),
[Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).
Les prix sont enregistrés dans `eval/pricing.v1.json` et doivent être revérifiés avant
le premier appel réel. Le snapshot et les tarifs standards ont été revérifiés le
12 septembre 2026 : 0,40 $ / million de tokens en entrée et 1,60 $ en sortie
([tarification officielle](https://developers.openai.com/api/docs/pricing)).
L’accès réel au snapshot a été confirmé sur les cas dev avec les deux pipelines,
dans l’API de production et avec la comptabilité partagée. Cette vérification technique
ne constitue pas une mesure de fidélité sémantique.
