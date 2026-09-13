# Consignes du pilote d’annotation

Examiner les dix premières notes du lot aveugle déjà préparé pour v1, dans leur ordre
existant. Ce périmètre est exploratoire et ne constitue pas un échantillon permettant
de comparer les méthodes. Les consignes ci-dessous sont précisées pendant cette
première lecture ; ce pilote n’est pas une nouvelle expérience préenregistrée.

Lire le dialogue entier, les références et le texte final de chaque note. Décomposer
les phrases qui contiennent plusieurs informations et regrouper les répétitions.
Pour chaque information, fournir ses positions exactes dans la note, son alignement
avec les références, les preuves textuelles et une justification de la décision.
Examiner chaque citation séparément. Ne pas déduire le soutien sémantique de la seule
existence d’un identifiant de source. Ne pas utiliser de connaissances médicales pour
compléter le dialogue ou pour attribuer un diagnostic.

Appliquer les labels du guide v1. Juger le sens du texte, pas l’égalité littérale de
ses mots ou des attributs du gold : une date de début passée ne signifie pas à elle
seule qu’un symptôme a cessé. Conserver les incertitudes et les détails absents.
Lorsqu’un fait composé n’est que partiellement repris et que le schéma binaire v1 ne
permet pas de le représenter fidèlement, employer `unresolved`, expliquer le détail
manquant et laisser la note en brouillon. Faire de même pour un fait soutenu par le
dialogue qui n’a pas de référence compatible, plutôt que l’appeler « hallucination »
ou inventer un alignement. Ne pas modifier les références gelées.

Les décisions sont produites par l’assistant IA de la session Codex. L’identifiant
exact du snapshot de cette session n’est pas disponible ; ne pas en inventer un.
Le champ `model_snapshot` contient cette indisponibilité explicitement, avec la
famille GPT-6 indiquée par l’environnement. L’empreinte de ce fichier identifie les
consignes archivées, pas l’ensemble du contexte conversationnel. La session a déjà
connaissance du projet ; aucune indépendance ni véritable aveuglement ne sont revendiqués.

Le script de compilation calcule seulement les offsets, empreintes et structures
JSON à partir des décisions écrites. Il ne juge pas les notes. Aucun appel fournisseur
supplémentaire, événement humain, score final ou nouvelle génération n’est autorisé.
Une note `complete` signifie que son formulaire IA est complet ; ce n’est ni une
validation humaine, ni une validation clinique, ni une finalisation de l’étude.
