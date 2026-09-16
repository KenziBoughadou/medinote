# Explorer la démonstration MediNote

La [démonstration en ligne](https://medinote.kbcompany.fr) présente six consultations
fictives et les douze notes enregistrées des méthodes A et B. Leur consultation
ne nécessite aucun nouvel appel au modèle.

## Comparer les notes

Choisir une consultation, puis comparer la note rédigée directement et celle
construite à partir des faits extraits. Ouvrir une citation pour retrouver le
passage correspondant dans le dialogue. La présence d’une citation ne garantit
pas qu’elle soutienne toute la phrase : il faut comparer les deux textes.

Le panneau de génération indique le modèle, le coût et la durée enregistrés.
Une note peut être exportée en Markdown pour être relue.

## Consulter les résultats

La page des résultats présente l’évaluation sur les quarante consultations de test.
Ces scores ne sont pas ceux des six consultations de démonstration, qui proviennent
du développement. Le [rapport d’évaluation](HUMAN_REVIEW_RESULTS.md) décrit les
mesures, les annotations et leurs limites.

Les dialogues et références sont synthétiques. La relecture a été réalisée par
l’auteur, sans second avis indépendant. Aucun usage clinique ni gain de temps
en situation de travail n’a été validé.

## Enregistrement local

`npm --prefix frontend run record:demo` s’utilise avec le frontend lancé sur le port 5173.
Le script écrit les captures à 1440 et 390 pixels et une vidéo de 1280 × 720 pixels,
d’une durée de 180 secondes. Le fournisseur est bloqué pendant l’enregistrement.
La vidéo archivée montre la première version illustrative de l’application.
