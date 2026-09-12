# Relevé d’exécution v1

Statut : **annotation des sorties et revue humaine des références en attente**.
Ce relevé décrit l’exécution réelle ; il ne remplace pas le rapport sémantique final.

| Cohorte | Tentatives prévues / archivées | Sorties techniquement valides | Coût estimé USD |
|---|---:|---:|---:|
| Six démos dev, A/B | 12 / 12 | 12 | 0,014175 |
| Quarante cas test, A/B | 80 / 80 | 80 | 0,094630 |
| Dix paires stress, deux variantes, A/B | 40 / 40 | 40 | 0,044292 |
| Total | 132 / 132 | 132 | 0,153097 |

Usage connu pour les 132 tentatives : 173 622 tokens d’entrée et 52 247 en sortie.
Aucun coût inconnu dans cette campagne. Estimation aux prix standards de 0,40 $ / million
en entrée et 1,60 $ en sortie, sans déduction du cache, arrondie vers le haut par tentative.
Les essais dev sont exclus de ce tableau et restent inclus dans le budget partagé.

Snapshot demandé et retourné : `gpt-4.1-mini-2025-04-14`. Température 0, maximum 4 000
tokens de sortie, `store=false`, Structured Outputs stricts. Un appel par méthode,
aucune reprise de campagne, aucun second appel de réparation. Le rendu B est déterministe.
L’ordre A/B alterné et les empreintes sont conservés dans chaque manifest.

Toutes les tentatives ont le statut `ok` : la sortie respecte le schéma et le rendu a
abouti. Ce statut ne prouve ni l’absence d’omission, d’ajout ou de contradiction, ni le
soutien sémantique des citations. Ces mesures restent absentes jusqu’à l’annotation.
Les durées individuelles et coûts de chaque tentative sont disponibles dans `runs.jsonl`.

Limites : dialogues synthétiques préparés par IA, diversité limitée, références non
relues humainement, notes non annotées, aucune revue clinique ni annotation indépendante.
Aucun gain de B sur A n’est revendiqué. Les exemples dev servent à la démonstration ;
ils ne remplacent pas les quarante cas test pour estimer les performances.

Le gel a été effectué après les essais dev et avant toute sortie test. Les modifications
préparatoires sont décrites dans `docs/DEV_TRIALS.md` à la racine du dépôt. Les archives
originales ne sont pas écrasées ; une correction ultérieure suit la politique de version
et d’amendement du protocole. Le rapport sémantique pourra être recalculé depuis ces
mêmes sorties après import des annotations complètes, sans nouvel appel au modèle.
