# Architecture implémentée

Les choix expérimentaux sont décrits dans le [protocole](EXPERIMENT_PROTOCOL.md).
Ce document présente leur implémentation dans l’application et les outils d’évaluation.

```mermaid
flowchart LR
  Browser[Navigateur React] --> Cloudflare
  Cloudflare --> Traefik[Traefik existant]
  Traefik --> Nginx[nginx 8080]
  Nginx --> API[FastAPI 8000 privé]
  API --> Public[Bundle public immuable]
  API --> SQLite[SQLite budget, quotas, bail]
  SQLite --> OpenAI[Responses GPT-4.1 mini snapshot]
  OpenAI --> A[Note directe A]
  OpenAI --> B[Faits typés B]
  B --> Renderer[Rendu Python déterministe]
  CLI[CLI expérimentale] --> SQLite
```

Le frontend est une application à navigation par fragments, avec état local `useReducer`.
Les types proviennent de Pydantic via OpenAPI et `openapi-typescript`. Il n’existe ni
saisie clinique libre, compte, dossier patient, stockage navigateur de consultation,
route publique d’administration ou d’annotation.

La couche fournisseur capture usage, statut et sortie brute avant validation. Les pipelines
ne persistent rien. `GenerationService` réserve chaque tentative via `UsageStore`, applique
le bail global et régularise le coût, même si la sortie est invalide. La réponse live ne
reçoit aucune métrique d’une ancienne note. B applique les gabarits fixes de
`backend/src/medinote/rendering.py`, dont l’empreinte est conservée dans le manifest v1.

SQLite utilise WAL et BEGIN IMMEDIATE. Les appels réseau restent hors transaction.
Un crash ne rembourse pas la réservation ; le bail expire après 75 secondes. Les quotas
et le budget persistent lors d’un redémarrage ou rollback d’image. Les clés visiteur sont
HMAC-SHA256 avec rotation journalière, sans IP brute en base. Les anciennes clés sont purgées.

nginx remplace le header d’identité avec CF-Connecting-IP, sans faire confiance au header
homonyme du navigateur. L’API est uniquement sur le réseau privé et Uvicorn ignore les
proxy headers. L’absence d’IP Cloudflare en production interdit uniquement les appels payants.
Les sources ne sont jamais journalisées. Les headers CSP et de sécurité sont centralisés dans nginx.

Le bundle public contient douze générations dev réelles archivées. Les illustrations
historiques sont conservées séparément. Les 132 générations de v1 sont enregistrées,
mais leur annotation humaine reste à réaliser. Les contrôles techniques n’interprètent
jamais la fidélité clinique.
