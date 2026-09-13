# MediNote : résumer une consultation sans en changer le sens

[![CI](https://github.com/KenziBoughadou/medinote/actions/workflows/ci.yml/badge.svg)](https://github.com/KenziBoughadou/medinote/actions/workflows/ci.yml)

**MediNote est un projet d’étude qui compare deux façons de transformer un dialogue médical en une note de synthèse avec une IA.** On peut lire le dialogue de départ, comparer les deux notes et retrouver les passages sur lesquels elles s’appuient.

Avec ce projet, je cherche à répondre à une question : **est-ce qu’une IA respecte mieux les informations d’une consultation lorsqu’on lui demande de les extraire avant de rédiger ?** J’ai construit une application pour observer les différences et un protocole pour pouvoir les mesurer.

Toutes les consultations sont fictives. MediNote n’a pas été validé pour le soin et n’est pas destiné à établir un diagnostic. Les notes restent des brouillons à relire.

[Voir le projet en ligne](https://medinote.kbcompany.fr) · [Consulter l’expérience](eval/results/v1/README.md) · [Présentation technique en anglais](README.en.md)

![Le dialogue fictif à gauche, le résumé direct au centre et la note issue des faits extraits à droite.](docs/assets/readme-comparison.png)

*L’application affiche ici de vraies générations enregistrées. La mention « Non évalué humainement » signifie que leur contenu attend encore une relecture.*

## Pourquoi travailler sur ce sujet ?

Une IA peut produire un texte clair et convaincant tout en changeant le sens de ce qu’on lui a donné. Dans une consultation, quelques mots peuvent faire toute la différence. Une absence de fièvre peut devenir une fièvre, un traitement pris par un proche peut être attribué au patient, ou une hypothèse peut être présentée comme une certitude.

Par exemple, si le dialogue contient « Je tousse depuis trois jours, mais je n’ai pas de fièvre », le résumé doit garder la toux, sa durée et l’absence de fièvre. Oublier la durée et affirmer une fièvre sont deux erreurs différentes. Pour comparer des méthodes, il faut pouvoir les distinguer.

C’est cette question de fidélité qui m’intéresse dans MediNote. Le but est de comprendre ce que chaque méthode conserve, oublie ou transforme. Je n’ai pas encore étudié le temps qu’un professionnel pourrait gagner en utilisant l’outil.

## Ce que cela pourrait apporter dans le monde du travail

L’usage que j’imagine est assez concret : une personne dispose déjà du texte d’un échange et doit en faire un compte rendu. MediNote pourrait lui proposer un premier brouillon organisé, qu’elle reprendrait avant de le valider. L’intérêt serait de consacrer moins de temps à remettre les informations en forme et davantage à vérifier ce qu’elles disent. C’est une possibilité à évaluer, pas un gain de temps démontré par le projet.

### Avoir une base pour rédiger

À partir d’un dialogue écrit, l’application rassemble les informations dans les mêmes sept rubriques. Une personne pourrait ainsi commencer sa relecture avec les symptômes, les traitements et les actions annoncées déjà regroupés. Elle devrait ensuite corriger les erreurs, compléter les oublis et décider de ce qui mérite d’être conservé. Si ces corrections demandent autant de travail qu’une rédaction manuelle, l’outil n’aura pas rempli cet objectif.

### Faciliter la lecture et la transmission

Un compte rendu sert aussi à quelqu’un qui n’a pas assisté à l’échange. Retrouver les informations au même endroit pourrait faciliter cette lecture et la transmission entre collègues. Par exemple, distinguer une hypothèse d’une action annoncée permettrait de mieux comprendre ce qui a été envisagé et ce qui a été décidé. Encore faut-il que la note respecte cette distinction : c’est justement l’un des points que je cherche à vérifier.

### Pouvoir contrôler ce que l’IA propose

Les citations donnent un point de départ pour la relecture. Si une phrase semble ambiguë, on peut revenir au passage du dialogue dont elle est issue. Cela pourrait faciliter la recherche d’une erreur ou la compréhension d’une reformulation. Il reste nécessaire de relire l’ensemble, car une information oubliée n’aura aucune citation sur laquelle cliquer.

Le projet porte sur des consultations fictives. Il ne permet pas aujourd’hui de traiter de vrais dossiers de patients. Un usage professionnel demanderait notamment une évaluation avec les personnes concernées et un cadre adapté à la confidentialité des données.

Je vois aussi une piste au-delà du médical : préparer des comptes rendus de réunion ou des synthèses d’entretiens à partir d’un texte, en gardant un lien avec les propos d’origine. Le principe pourrait être réutilisé, mais il faudrait adapter les rubriques, les consignes et les critères de vérification. Ces usages ne sont pas implémentés dans MediNote.

## Les deux méthodes comparées

Les deux méthodes utilisent exactement le même dialogue et la même version du modèle. Elles effectuent chacune un seul appel à l’IA.

### Méthode A : demander directement une note

La première méthode demande à l’IA de rédiger le résumé dans sept rubriques, en indiquant les passages du dialogue qui justifient ses phrases. Le texte obtenu est ensuite affiché dans l’application.

Cette approche laisse au modèle de la liberté pour reformuler. Elle peut donner une note plus naturelle à lire, mais cette liberté peut aussi conduire à perdre un détail ou à préciser une information qui ne l’était pas dans le dialogue.

### Méthode B : passer d’abord par une liste de faits

La seconde méthode demande à l’IA de relever les informations séparément. Pour chaque fait, elle doit préciser ce qui est décrit, la personne concernée, la présence ou l’absence du fait, le moment, le degré de certitude et la source.

Un programme Python transforme ensuite cette liste en note, avec des règles de rédaction fixes. Il n’y a pas de second appel à l’IA. L’idée est de rendre certaines informations plus faciles à contrôler, notamment les négations et les personnes concernées.

Cette méthode a aussi ses limites. Si l’IA extrait mal un fait ou l’oublie, le programme ne le corrigera pas. Il mettra en forme les informations reçues, même si elles sont incomplètes.

Les deux notes suivent les mêmes rubriques : motif de consultation, symptômes, antécédents, traitements et allergies, observations, hypothèses exprimées et actions annoncées.

**Je ne pars pas du principe que B est meilleure que A.** Les deux méthodes changent aussi la manière de rédiger. Un éventuel écart ne pourra donc pas être attribué uniquement à l’extraction des faits.

### Retrouver l’origine d’une phrase

Les références comme `s006` correspondent à des passages du dialogue. En cliquant dessus, on retrouve le texte utilisé pour justifier une phrase de la note.

Ce lien aide à vérifier le résultat, mais il ne suffit pas à prouver qu’une phrase est juste. Le programme peut vérifier qu’un passage existe. Il faut encore le lire pour savoir s’il soutient réellement ce que la note affirme.

<details>
<summary>Voir un exemple de vérification dans l’application</summary>

![Le passage s006 est sélectionné : « Je ne rapporte pas de vomissement ». Les deux notes peuvent être comparées à cette source.](docs/assets/readme-citation.png)

Le passage surligné parle à la fois de l’absence de vomissement et d’une appendicectomie. Une même source peut donc justifier plusieurs informations, qu’il faut examiner séparément.

</details>

## Où en est le projet ?

La première campagne a été exécutée le **12 septembre 2026**. Les réponses du modèle ont été enregistrées avec leurs sources, leur durée, leur consommation et leur coût estimé.

| Ensemble | Utilisation | Notes enregistrées |
|---|---|---:|
| Six consultations de démonstration | Montrer les deux méthodes dans l’application. Ces cas viennent du développement. | 12 |
| Quarante consultations de test | Comparer A et B sur des cas qui n’ont pas servi à ajuster les consignes. | 80 |
| Dix paires de stress | Observer ce qui change lorsqu’on inverse une négation, en gardant les autres faits identiques. Chaque paire contient deux variantes. | 40 |
| **Total** | Les essais de mise au point sont comptés séparément. | **132** |

Les 132 sorties respectent le format attendu et ont pu être transformées en notes. **Cela ne veut pas dire que les 132 notes sont fidèles au dialogue.** La relecture humaine des références et des notes reste à faire. Je ne peux donc pas encore annoncer de taux d’omission, de contradiction ou de précision.

L’application permet déjà de consulter les douze notes de démonstration, de suivre leurs citations et de les exporter. Leur lecture ne déclenche aucun nouvel appel à l’IA. Il est aussi possible de relancer une génération, dans la limite des quotas. Le site ne permet pas de saisir une consultation personnelle.

Les [réponses archivées](eval/results/v1/), le [relevé d’exécution](eval/results/v1/report.md) et les [essais de développement](docs/DEV_TRIALS.md) permettent de suivre ce qui a réellement été réalisé.

## Comment j’ai organisé l’expérience

### Garder des cas à part pour le test

Le corpus, qui désigne l’ensemble des dialogues utilisés, contient **80 consultations fictives en français**. Soixante couvrent dix familles de situations. Parmi elles, vingt servent à mettre au point les consignes données au modèle, aussi appelées *prompts*, et quarante sont réservées au test principal. Les vingt variantes restantes forment les dix paires de stress.

Cette séparation évite d’ajuster une méthode sur les exemples qui serviront ensuite à annoncer ses résultats. Les données, les consignes, le modèle et les règles de traitement ont été figés avant les générations de test. Des empreintes numériques permettent de vérifier que les fichiers n’ont pas changé depuis.

Les erreurs rencontrées pendant la mise au point sont conservées dans l’historique. Elles ne sont pas présentées comme des réussites de la campagne finale.

### Vérifier le contenu des notes

Les dialogues sont accompagnés de **800 faits de référence**, dont 720 sont considérés comme attendus dans les notes. Les dialogues et ces références ont été préparés par IA. Il faut donc aussi relire les références, car elles peuvent contenir des erreurs.

L’annotation consiste à examiner chaque information de la note et à expliquer pourquoi elle est correcte ou non. Une **omission** correspond à une information attendue qui manque. Une **contradiction** apparaît lorsque la note change une information, par exemple la personne concernée ou une négation. Un **ajout non soutenu** est une affirmation que le dialogue ne permet pas d’établir.

Les citations sont vérifiées séparément. Un passage peut exister sans justifier la phrase qui lui est attribuée. C’est ce que le protocole considère comme une **citation insuffisante**.

Les 120 notes de test et de stress sont préparées pour être relues sans afficher le nom de la méthode. Le style peut malgré tout permettre de reconnaître B. La première version prévoit une relecture par l’auteur du projet ; une seconde lecture indépendante serait une amélioration utile, mais elle n’a pas encore eu lieu.

### Ne pas se limiter à une moyenne

Chaque consultation test possède une note A et une note B. Les méthodes seront donc comparées sur les mêmes situations, en tenant compte du nombre d’informations à restituer. Les échecs techniques restent eux aussi comptés parmi les tentatives.

Après annotation, le protocole prévoit de rééchantillonner les quarante consultations 10 000 fois. Cette méthode, appelée *bootstrap*, sert à estimer l’incertitude autour des écarts observés. Les résultats sur les paires de négation seront présentés séparément. Je souhaite conserver plusieurs mesures plutôt que de tout ramener à un score unique qui pourrait cacher certains types d’erreurs.

Le [protocole détaillé](docs/EVALUATION.md) et le [guide d’annotation](eval/annotation-guide.v1.md) décrivent les règles retenues.

## Combien cela coûte ?

MediNote utilise **GPT-4.1 mini**, dans la version `gpt-4.1-mini-2025-04-14`. Le programme communique avec le modèle grâce à l’API d’OpenAI. Il n’utilise pas l’abonnement ChatGPT du visiteur et je n’ai pas entraîné de modèle spécialement pour ce projet.

Le prix dépend des *tokens*, qui sont des morceaux de texte lus ou générés. Pour cette campagne, l’estimation utilise **0,40 $ par million de tokens en entrée et 1,60 $ en sortie**, sans déduire les réductions liées au cache. Ces prix sont conservés dans le [fichier de tarification v1](eval/pricing.v1.json). Il faudra revérifier les [tarifs OpenAI](https://developers.openai.com/api/docs/pricing) avant une nouvelle campagne.

| Partie de l’expérience | Coût API estimé, hors taxes |
|---|---:|
| Douze notes de démonstration | 0,014175 $ |
| Quatre-vingts notes du test principal | 0,094630 $ |
| Quarante notes de stress | 0,044292 $ |
| **Total, hors essais de développement** | **0,153097 $** |

Sur les quarante cas du test principal, une note A coûte en moyenne environ **0,00079 $**, contre **0,00158 $** pour B. La durée médiane est de **2,29 secondes** pour A et **4,98 secondes** pour B. Autrement dit, la moitié des appels est plus rapide que cette durée et l’autre moitié plus lente.

Dans cette expérience, B demande donc davantage de temps et de tokens. La relecture devra permettre de savoir si cette différence s’accompagne d’une meilleure fidélité. Pour l’instant, je peux comparer les coûts et les délais, mais pas conclure sur la qualité du contenu.

Avec des dialogues et des tarifs comparables, **1 000 comparaisons A/B représenteraient environ 2,37 $ d’API**. C’est un calcul à partir de la campagne actuelle, pas un test réalisé à cette échelle. Des textes plus longs, un autre modèle ou des tentatives supplémentaires modifieraient le montant.

L’API n’est cependant qu’une partie du coût. Il faut aussi compter l’hébergement, la maintenance et le temps de relecture. Par exemple, **si** une note demandait 10 à 20 minutes d’annotation, les 120 notes représenteraient 20 à 40 heures de travail, sans compter la vérification des références. Il s’agit d’une hypothèse pour organiser la suite, pas d’une durée mesurée.

Pour garder la démonstration dans un budget raisonnable, le service dispose d’un plafond de **10 $ estimés par mois**, partagé entre les visiteurs et les expériences. Les relances publiques sont limitées à six tentatives par visiteur et trente au total par jour, avec une seule génération à la fois. Les notes enregistrées restent consultables lorsque les relances ne sont plus disponibles.

## Les limites que je garde en tête

La première limite concerne les données. Les dialogues sont courts, fictifs et construits avec des formulations assez régulières. Ils ne représentent pas toute la diversité d’une consultation, avec ses hésitations, ses interruptions ou ses ambiguïtés. Même de bons résultats sur ce corpus ne permettraient pas de conclure que l’outil est adapté à un usage clinique.

Les références ont également leurs limites. Comme elles ont été préparées par IA, elles peuvent contenir des erreurs ou des choix discutables sur les informations à retenir. La qualité de l’évaluation dépendra de leur relecture autant que de celle des notes générées.

L’expérience porte sur un seul modèle et une seule génération par méthode et par cas. Elle ne permet pas encore de savoir à quel point les résultats changeraient si l’on relançait plusieurs fois la même consultation. Elle ne permet pas non plus de généraliser à d’autres modèles.

Il faut aussi distinguer le format et le contenu. Pendant le développement, une sortie attribuait le label d’un proche au sujet « patient ». La contrainte a été corrigée dans le schéma envoyé au modèle. Cela empêche cette combinaison incohérente, mais ne suffit pas à vérifier que le bon sujet a été choisi dans chaque phrase. Le [détail de ce problème](docs/DEV_TRIALS.md) est conservé dans l’historique.

Enfin, MediNote travaille uniquement sur du texte. Il ne transcrit pas d’audio, ne se connecte pas à un dossier patient et n’a pas été évalué dans un parcours de soin. Je ne présente donc aucun bénéfice clinique ni gain de temps réel comme acquis.

## Ce que je voudrais améliorer ensuite

### Terminer la relecture humaine

La première étape est de relire les références puis d’annoter les 120 notes de test et de stress. C’est ce qui permettra de mesurer les erreurs au lieu de s’en tenir à quelques exemples. Les sorties sont déjà enregistrées : cette étape demande surtout du temps humain, sans nécessiter de nouveaux appels de génération.

### Rendre les dialogues plus variés

J’aimerais ensuite élargir les situations étudiées, avec davantage de corrections dans le dialogue, de proches mentionnés et d’informations incertaines. Une relecture avec un professionnel du domaine aiderait à mieux construire les cas et leurs références. Le travail à prévoir concerne surtout la préparation des données et leur annotation, puis le coût d’une nouvelle campagne.

### Améliorer les méthodes à partir des erreurs observées

Une fois les erreurs identifiées, il sera possible de modifier une consigne ou une règle de traitement, puis de vérifier l’effet de ce changement. Il faudra utiliser un nouveau jeu de test réservé. Les cas de v1, dont les sorties sont désormais accessibles, ne pourront plus servir de test indépendant pour une amélioration conçue à partir de leurs erreurs.

L’objectif serait de savoir précisément ce qu’une modification améliore, mais aussi ce qu’elle peut dégrader. Les anciennes versions et les éventuelles corrections des références devront rester documentées.

### Comparer la qualité, le coût et le temps de réponse

Comparer d’autres modèles et répéter certaines générations permettrait d’aller plus loin. Il serait aussi intéressant de mesurer le temps nécessaire à une personne pour vérifier chaque type de note. Une note produite plus rapidement n’est pas forcément plus rapide à relire.

Pour savoir si l’outil aide vraiment au travail, je voudrais comparer une rédaction manuelle et une rédaction avec assistance sur des tâches comparables. Je mesurerais le temps total jusqu’à la validation, relecture et corrections comprises, ainsi que les erreurs qui restent dans la note finale. Les retours des participants permettraient aussi de comprendre ce qui les aide ou les gêne. Le coût utile à comparer serait alors celui d’une note vérifiée, en comptant le temps humain, et pas seulement le prix de l’appel à l’IA. Cette étude d’usage reste à construire, séparément de la campagne actuelle.

Ces essais demanderaient un budget défini à l’avance, des appels supplémentaires et une relecture comparable entre les méthodes. Selon les modèles choisis, il faudrait aussi prendre en compte un éventuel coût d’hébergement.

### Envisager un entraînement complémentaire

Adapter un modèle au projet pourrait devenir pertinent si certaines erreurs reviennent malgré de meilleures consignes et de meilleurs contrôles. Cela demanderait des exemples corrigés pour l’apprentissage, séparés des données de test, puis une nouvelle évaluation.

Je n’ai pas encore de chiffrage fiable pour cette piste. Le coût dépendrait du modèle, des données disponibles, de l’entraînement et de son hébergement. Avant d’y consacrer du temps, je veux surtout disposer d’une mesure sérieuse des erreurs de la version actuelle.

Ces pistes décrivent la suite envisagée. Elles ne sont pas encore réalisées et ne changent pas les résultats enregistrés pour v1.

## Le travail réalisé autour du modèle

Le modèle de langage est un service externe. Le travail dans MediNote consiste à organiser son utilisation pour pouvoir observer, comparer et vérifier les résultats. Cela comprend les deux méthodes, la préparation des données, le protocole, les citations, l’archivage, l’interface et le suivi du budget.

L’interface utilise React et TypeScript pour afficher les dialogues et les notes. Le serveur repose sur Python, FastAPI et Pydantic pour préparer les requêtes, contrôler les formats et construire la note B. SQLite conserve la comptabilité des appels, y compris après un redémarrage. GitHub Actions et Docker servent à tester et à déployer des versions identifiables du projet.

La version publiée avec les résultats a passé **95 tests backend, 7 tests frontend et 8 scénarios navigateur**, dont les contrôles d’accessibilité. Ces tests vérifient le fonctionnement du logiciel. La fidélité des notes reste une question distincte, à laquelle la relecture humaine doit encore répondre.
