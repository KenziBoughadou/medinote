# Présenter MediNote en quelques minutes

La vidéo archivée montre la première version illustrative. Pour une présentation
actuelle, on peut suivre le parcours ci-dessous sur le site avec les notes enregistrées,
sans lancer de nouvel appel au modèle.

## Parcours de trois minutes

De 0 à 30 secondes, on choisit un cas de négation et on présente le dialogue fictif.

De 30 à 80 secondes, on compare les notes A et B, puis on ouvre une citation pour
retrouver le passage utilisé. On peut montrer le retour au bouton avec le clavier.

De 80 à 120 secondes, on affiche le modèle, le coût et la durée de génération,
puis on exporte une note en Markdown.

De 120 à 160 secondes, on ouvre les résultats : A couvre 345 faits attendus sur 360,
contre 333 pour B. On explique une omission et pourquoi le test strict de négation
échoue pour les deux méthodes malgré une bonne couverture sur le test principal.

De 160 à 180 secondes, on résume le rendu Python de B et on ouvre le dépôt GitHub.

## Pour un entretien plus long

On peut développer l’usage envisagé au travail : préparer un compte rendu organisé,
puis vérifier ses sources avant de le transmettre. Le gain de temps reste à mesurer.
On présente ensuite les deux méthodes, leur coût et les erreurs observées.

Les limites à expliquer sont le corpus fictif, la relecture par une seule personne,
le choix d’un seul modèle et l’absence de validation clinique. Une seconde annotation
permettrait de comparer les décisions avant de lancer une nouvelle expérience.

## Enregistrement local

`npm --prefix frontend run record:demo` s’utilise avec le frontend lancé sur le port 5173.
Le script écrit les captures à 1440 et 390 pixels et une vidéo de 1280 × 720 pixels,
d’une durée de 180 secondes. Le fournisseur est bloqué pendant l’enregistrement.
La vidéo reste sous 25 Mio, sans audio, avec réencodage VP9 si nécessaire.
