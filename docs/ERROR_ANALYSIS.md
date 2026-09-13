# Neuf erreurs et points à revoir dans les notes

On a choisi ces neuf observations après le calcul des résultats, pour comprendre ce
qui se cache derrière les pourcentages. Elles concernent huit notes distinctes et
couvrent les deux méthodes, le test principal et le stress. Cette sélection est
qualitative : elle n’est ni aléatoire ni une estimation de fréquence. Le dernier cas
signale une limite de l’annotation et n’ajoute pas d’erreur aux scores publiés.

Chaque exemple renvoie au dialogue, à la note enregistrée et à son annotation.
Les extraits sont recopiés depuis ces fichiers. Les pistes d’amélioration décrivent
ce qu’on pourrait tester dans une prochaine expérience ; elles n’ont pas été
appliquées aux générations de v1.

## 1. Une négation portée deux fois

Cas `main-dermatologique-04` · B, extraction structurée · `blind-0045`.

Dans le dialogue (`s008`) :

> J’utilise un shampooing parfumé sans traitement médical.

Dans la note (`medications_allergies.002`) :

> absence de traitement médical — nié ; patient ; actuel ; rapporté.

La sortie nie une « absence de traitement ». On a classé cette formulation comme une contradiction de polarité. Le format est valide et la citation mène au bon passage, mais leur combinaison ne conserve pas le sens. Dans une prochaine version, on pourrait contrôler le couple libellé–polarité avant le rendu. Cette piste reste à tester sur de nouveaux cas.

[Dialogue](../data/cases.v1.jsonl#L40) · [Note complète](../eval/results/v1/study/main-test/notes/ab40c8fe670242bbb0a83b1c12a8b9f8.json) · [Annotation](../eval/results/reviewed-v1.1/annotations.jsonl#L45)

## 2. Le même problème sur le test de négation

Cas `stress-04-negative` · B, extraction structurée · `blind-0012`.

Dans le dialogue (`s006`) :

> Je ne rapporte pas une fièvre.

Dans la note (`history.003`) :

> absence de fièvre — nié ; patient ; actuel ; rapporté.

On retrouve la même double négation dans un cas réservé au stress. L’annotation compte une contradiction sur le signe cible. Elle appartient au test de stress et n’est donc pas ajoutée au compteur du test principal. Ce deuxième exemple montre que le problème ne se limite pas aux traitements.

[Dialogue](../data/stress.v1.jsonl#L8) · [Note complète](../eval/results/v1/study/stress/notes/b71813b531be422abd5eb92f6b9d0efc.json) · [Annotation](../eval/results/reviewed-v1.1/annotations.jsonl#L12)

## 3. Une action annoncée disparaît de la note

Cas `main-respiratoire-06` · B, extraction structurée · `blind-0018`.

Dans le dialogue (`s011`) :

> Je propose de noter les circonstances avant notre prochain échange.

La rubrique « Conduite annoncée » de B est vide. Le fait `main-respiratoire-06.conduite` est annoté comme omis. La note conserve pourtant le motif, plusieurs symptômes et la température : une structure bien remplie ne garantit pas que l’action prévue a été reprise. On pourrait étudier une vérification dédiée des actions et des délais, sans les inventer lorsqu’ils sont absents du dialogue.

[Dialogue](../data/cases.v1.jsonl#L6) · [Note complète](../eval/results/v1/study/main-test/notes/b0fe6c2a262e486fa9c89696e5759345.json) · [Annotation](../eval/results/reviewed-v1.1/annotations.jsonl#L18)

## 4. Le motif général reste, mais l’objectif précis se perd

Cas `main-prevention-06` · A, résumé direct · `blind-0024`.

Dans le dialogue (`s004`) :

> Je veux vérifier la liste de mes traitements et les documents que je possède déjà.

Dans la note (`reason.001`) :

> Le patient vient pour la préparation de ses documents de santé en vue d'un voyage prévu le mois prochain.

A garde la préparation d’un voyage, mais ne reprend pas le souhait précis de vérifier les éléments déjà disponibles. Le fait `main-prevention-06.contexte` est annoté comme omis. La revue de l’ordonnance apparaît ailleurs comme action annoncée ; elle ne remplace pas entièrement cette demande. Ce cas montre l’intérêt de vérifier les faits un par un plutôt que de juger seulement si le résumé semble cohérent.

[Dialogue](../data/cases.v1.jsonl#L60) · [Note complète](../eval/results/v1/study/main-test/notes/1f5589939e3a49a5946ae207ae6d2378.json) · [Annotation](../eval/results/reviewed-v1.1/annotations.jsonl#L24)

## 5. Une observation sans chiffre est oubliée

Cas `main-sante-psychique-05` · B, extraction structurée · `blind-0065`.

Dans le dialogue (`s009`) :

> La personne décrit clairement les circonstances pendant l’entretien.

B conserve l’hypothèse évoquée dans la seconde phrase du même passage, mais sa rubrique « Observations » reste vide. Le fait `main-sante-psychique-05.observation` est annoté comme omis. On pourrait vérifier, sur une nouvelle série, si l’extraction traite différemment les observations descriptives et les mesures chiffrées. Ce seul cas ne permet pas d’affirmer qu’il existe un biais général.

[Dialogue](../data/cases.v1.jsonl#L53) · [Note complète](../eval/results/v1/study/main-test/notes/530ae46f33a642529ed344a40c3cda16.json) · [Annotation](../eval/results/reviewed-v1.1/annotations.jsonl#L65)

## 6. L’incertitude n’est plus exprimée

Cas `main-digestif-04` · A, résumé direct · `blind-0015`.

Dans le dialogue (`s009`) :

> Une relation avec certains repas reste à préciser.

Dans la note (`observations.001`) :

> L’abdomen est souple sans défense à l’examen clinique.

A reprend l’examen abdominal et le relevé des repas prévu, mais pas le lien encore incertain avec les repas. Le fait `main-digestif-04.evaluation` est annoté comme omis. On perd ainsi la distinction entre une piste à explorer et une conclusion. Une prochaine évaluation pourrait examiner séparément la conservation des hypothèses et celle des observations.

[Dialogue](../data/cases.v1.jsonl#L16) · [Note complète](../eval/results/v1/study/main-test/notes/1ea0f4a81e1646ebbf5aba50e69bc2fd.json) · [Annotation](../eval/results/reviewed-v1.1/annotations.jsonl#L15)

## 7. Une phrase correcte peut avoir une citation insuffisante

Cas `main-sante-psychique-06` · A, résumé direct · `blind-0050`.

Dans le dialogue (`s004`) :

> Depuis le déménagement je connais peu de monde mais je souhaite rejoindre une association.

Dans la note (`observations.002`) :

> La transition de vie (déménagement) est évoquée comme facteur possible de la difficulté sociale.

La phrase générée cite à la fois `s004` et `s009`. Le premier passage donne le contexte du déménagement ; le second contient « La transition de vie est évoquée comme facteur possible. ». Dans l’annotation, `observations.002.c001` est jugée insuffisante pour soutenir toute la phrase, alors que `observations.002.c002` la soutient. L’information reste classée comme couverte, mais une association information–citation échoue. Le contexte de `s004` contribue tout de même à la phrase : une seconde relecture pourrait discuter si chaque citation doit soutenir toute l’information ou seulement sa partie. C’est une limite de granularité, pas un ajout inventé à compter en plus.

[Dialogue](../data/cases.v1.jsonl#L54) · [Note complète](../eval/results/v1/study/main-test/notes/0967aae1101742aead5a40debd65d18d.json) · [Annotation](../eval/results/reviewed-v1.1/annotations.jsonl#L50)

## 8. Une négation peut être bien traitée alors que la paire échoue

Cas `stress-01-positive` · A, résumé direct · `blind-0093`.

Dans le dialogue (`s009`) :

> L’origine de la plainte reste à préciser.

Dans la note (`history.002`) :

> Le patient rapporte également une fièvre.

A reprend correctement la fièvre dans cette variante positive. En revanche, l’incertitude sur l’origine de la plainte et la disponibilité en fin de journée ne sont pas reprises. Le critère strict exige aussi ces faits invariants pour les deux variantes : la paire échoue donc même si le signe cible est bien restitué ici. Les 40 notes de stress omettent le premier de ces invariants. On doit lire le score de 0/10 comme le résultat de cette règle complète, pas comme un taux de négations toutes incorrectes.

[Dialogue](../data/stress.v1.jsonl#L1) · [Note complète](../eval/results/v1/study/stress/notes/1659dbd5c1b341308a5785a947685850.json) · [Annotation](../eval/results/reviewed-v1.1/annotations.jsonl#L93)

## 9. Un cas à revoir : « moins » devient une absence

Cas `main-respiratoire-06` · B, extraction structurée · `blind-0018`.

Dans le dialogue (`s004`) :

> Je la remarque surtout dans la chambre et moins pendant mes promenades.

Dans la note (`history.002`) :

> obstruction nasale pendant les promenades — nié ; patient ; actuel ; rapporté.

Le dialogue indique une gêne moins marquée pendant les promenades ; B la présente comme niée. Cela suggère une perte du degré d’intensité, voire une contradiction. L’annotation finale rattache pourtant ce passage au fait de contexte et le classe comme soutenu. Ce point est donc une observation qualitative nouvelle, pas une contradiction supplémentaire déjà incluse dans les chiffres publiés. On conserve les scores de v1.1 et on réserve ce désaccord à une seconde annotation versionnée. Il illustre pourquoi les contrôles de format ne suffisent pas à garantir la qualité des jugements.

[Dialogue](../data/cases.v1.jsonl#L6) · [Note complète](../eval/results/v1/study/main-test/notes/b0fe6c2a262e486fa9c89696e5759345.json) · [Annotation](../eval/results/reviewed-v1.1/annotations.jsonl#L18)

## Ce qu’on en retient

Les erreurs observées portent autant sur ce qui disparaît que sur ce qui est mal
formulé. Le rendu structuré rend certains attributs faciles à inspecter, mais il peut
aussi rendre une extraction incohérente très explicite. Le résumé direct évite ces
gabarits, sans empêcher les omissions ou les citations insuffisantes.

La priorité serait de faire relire les cas ambigus par une seconde personne, puis
de définir des références où chaque fait correspond à une information simple. On
pourrait ensuite tester les changements de génération sur un nouveau jeu réservé.
Modifier les consignes à partir des erreurs ci-dessus, puis remesurer sur les mêmes
cas, ne fournirait pas une estimation indépendante du progrès.

[Méthode de calcul et limites](HUMAN_REVIEW_RESULTS.md) · [Rapport chiffré](../eval/results/reviewed-v1.1/report/report.md)
