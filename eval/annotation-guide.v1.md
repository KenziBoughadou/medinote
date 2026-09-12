# Guide d’annotation v1

Annoter les notes finales dans le bundle aveugle, avec les sources et les références.
L’apparence du rendu peut révéler B ; l’aveuglement n’est donc pas garanti. L’identité
de l’annotateur et la provenance IA/humaine doivent être déclarées exactement.
Les formulaires vierges ne sont pas des événements de revue.

Segmenter chaque assertion en faits sémantiques. Une phrase « toux sans fièvre »
contient deux faits. Une répétition identique compte comme un seul claim avec plusieurs
spans. Relire aussi les assertions sans citation. Aligner sujet/propriété/contexte,
puis comparer valeur, polarité, temps et certitude. Ne pas annoter à partir des seuls
faits intermédiaires de B. Les offsets sont des points de code Unicode.

| Label | Exemple français | Contre-exemple | Dénominateur |
|---|---|---|---|
| supported_expected | « Toux depuis trois jours » exactement sourcé et attendu | Durée absente de la source | P et E |
| supported_optional | Préférence horaire sourcée, non requise dans la note | Préférence inventée | P, pas E |
| contradiction | « Fièvre » alors que la source la nie | Fièvre non mentionnée | D/P et K/E si fait attendu |
| unsupported | « Prescription de 500 mg » absente des sources | Dose facultative explicitement rapportée | U/P |
| unresolved | Sujet impossible à déterminer après lecture | Sujet explicite dans le tour de parole | Bloque le rapport final |

E = C + K + O : faits attendus couverts, contredits, omis. Une négation inversée
compte comme contradiction, sans être ajoutée aux omissions et aux ajouts. Si la note
affirme simultanément le fait et son contraire, son statut gold est contradicted.
Un fait facultatif est not_required dans le gold, même lorsqu’un claim le couvre.
P compte les faits sémantiques uniques, U les ajouts non soutenus, D les contradictions.
Un dénominateur nul donne null, jamais un score parfait.

Chaque association claim–citation doit recevoir une décision de soutien sémantique et
une justification. Une citation peut soutenir un seul des faits d’une phrase. Une
référence résoluble n’est pas automatiquement probante. Donner les spans source exacts
pour les faits soutenus. Relire toutes les assertions et cocher segmentation_review_complete
uniquement après cette revue. Les décisions unresolved et les brouillons bloquent un rapport final.

Les erreurs de dose, polarité, sujet, temporalité et certitude sont des types de
contradiction. Pour les négations, le dénominateur contient les faits attendus repris
(couverts ou contredits) dont la polarité source est explicite.

Les échecs techniques n’ont pas de note à annoter. Ils restent dans les tentatives
prévues et valent tous les faits attendus omis en bout en bout. La précision des ajouts
et des citations est non applicable. Les résultats conditionnels aux notes valides
sont présentés séparément. Une annotation IA ne peut être renommée humaine : une vraie
relecture humaine produit sa propre annotation, avec sa provenance et ses décisions.
