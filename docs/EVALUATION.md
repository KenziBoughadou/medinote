# Protocole d’évaluation

La [présentation de l’expérience](EXPERIMENT_PROTOCOL.md) rassemble la question de recherche,
les cohortes, les paramètres et les conditions de publication. Les règles ci-dessous
décrivent l’exécution et le calcul des mesures.

Le protocole machine est `eval/protocol.v1.json`, le guide humain
`eval/annotation-guide.v1.md`. Les artefacts réels sont sous `eval/results/v1/` ;
la revue humaine et les métriques sémantiques restent en attente.
Les fixtures de tests sont artificielles et distinctes des observations scientifiques.

Le [dossier de relecture des références](REFERENCE_REVIEW.md) permet de préparer les
dialogues et preuves dans un format lisible, sans créer d’événement humain.

Avant tout appel réel : publication technique de la release, clé MediNote autorisée,
comptabilité persistante partagée, vérification du snapshot et du prix. Ajuster les prompts
sur dev uniquement. Geler corpus, gold, code, paramètres, prix, schémas, rendu et lockfiles.
Le gel refuse l’écrasement et les campagnes vérifient les hashes.

Prévoir 12 sorties dev publiques, 80 principales et 40 stress. Pour les case_id triés,
alterner A/B puis B/A. Une erreur conserve son observation, ses coûts connus et sa sortie
brute disponible. Une interruption liée au budget laisse un artefact `interrupted.json`
et impose une nouvelle campagne explicite ; aucune observation antérieure n’est remplacée.

Le runner produit `run-manifest.json`, `runs.jsonl`, `raw-responses.jsonl`, `notes.jsonl`
et les fichiers individuels. Regrouper les campagnes principales et stress sous un dossier
`study/`, et conserver `demo/` séparément. `export-blind --batch study` accepte ce regroupement,
masque méthode et coûts, et place le mapping dans `study/private/` mode 0700, fichier 0600.
Ne pas publier ce mapping avant clôture. La forme du rendu peut révéler B.

Les annotations finales doivent couvrir toutes les notes valides exportées, tous les faits
sémantiques et toutes les associations claim–citation. Les répétitions sont un claim à
plusieurs spans ; les phrases multifaits sont segmentées. Aucun `unresolved` n’est admissible.
Une contradiction prime sur une affirmation simultanée. Une référence facultative sourcée
n’est pas un ajout injustifié. Les imports créent un nouveau fichier, sans réétiqueter une
annotation IA en revue humaine.

E=C+K+O : couverture fidèle, contradiction, omission. P : assertions sémantiques uniques ;
U/P : ajouts ; D/P : contradictions. La négation inversée reste un sous-ensemble des
contradictions. Les métriques de citation séparent existence de l’ID et soutien sémantique.
Les échecs restent dans les ratios bout en bout, avec couverture nulle et faits attendus omis.
Les ratios de précision d’un échec sont non applicables. Les résultats conditionnels aux
notes valides exposent leurs propres dénominateurs. Aucun usage manquant n’est déclaré gratuit.

Sommer les compteurs avant division. Le bootstrap apparié conserve les indices de 10 000
tirages PCG64, seed 20260911, avec les mêmes consultations pour A/B. IC percentile 2,5/97,5 ;
intervalle null si moins de 95 % des tirages définissent le ratio. Le stress a son propre
dénominateur de dix paires et n’est pas fusionné au test principal. Pas de p-value ou de
score global de supériorité.

Le rapport peut être exploratoire `ai_annotated`. Le statut `human_reviewed` exige références
figées revues humainement, cohortes complètes et annotations finales humaines. Une revue
ultérieure référence les hashes figés et n’altère pas les données. Les figures sont des
exports Matplotlib SVG, jamais des valeurs inventées pour remplir une page vide.
