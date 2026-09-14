# Coût et latence : intervalles de confiance

Complément descriptif calculé après la campagne v1, sans nouvel appel API.

| Mesure | A | B | B−A | IC 95 % de B−A | B/A | IC 95 % de B/A |
|---|---:|---:|---:|---|---:|---|
| Coût moyen par note | 0,000790 $ | 0,001576 $ | 0,000787 $ | [0,000749 ; 0,000826] $ | 1.996 | [1.946 ; 2.047] |
| Latence médiane | 2,291 s | 4,981 s | 2,690 s | [2,197 ; 2,860] s | 2.174 | [1.937 ; 2.293] |

On réutilise exactement les 10 000 tirages du bootstrap de fidélité : 40
consultations tirées avec remise, mêmes indices pour A et B, PCG64 et graine
20260911. À chaque tirage, on recalcule la moyenne des coûts et la médiane
des latences pour chaque méthode, puis B−A et B/A. La différence des médianes
n’est pas la médiane des différences. Les bornes sont les percentiles 2,5 et 97,5.

Les 80 appels test sont inclus ; aucun coût n’est manquant. Les coûts sont
les estimations archivées avec les tarifs v1, sans remise de cache. Les
intervalles sont conditionnels à ces tarifs et à cette campagne ; ils ne
prédisent pas une facture future. Les latences reflètent les appels enregistrés,
pas des répétitions à différents moments ni une garantie de service. Le coût
d’hébergement et le temps de relecture ne sont pas inclus.

Ce calcul décrit la variabilité entre consultations. Il ne mesure ni la
variation entre plusieurs générations d’un même cas, ni la généralisation
à un autre modèle ou corpus. Les intervalles de A et B sont aussi disponibles
dans [les résultats détaillés](results.json), avec les 40 paires et les empreintes.

Reproduction depuis la racine, vers un dossier neuf :

```bash
uv run python scripts/analyze_cost_latency_v1.py --output .state/cost-latency-v1
```
