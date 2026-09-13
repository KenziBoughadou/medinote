"""Source éditoriale IA du corpus v1. Aucun appel fournisseur ni événement humain.

À exécuter uniquement pour la préparation initiale ; refuser tout écrasement après gel.
Les lignes décrivent soixante situations distinctes, pas des paraphrases d'un parent.
"""

import argparse
from pathlib import Path

from medinote.corpus import DEMO_IDS, FAMILIES
from medinote.serialization import canonical_json, sha256_file, utc_now, write_json

# Titre | motif | début | contexte | signe nié | antécédent | médicament | observation | hypothèse exprimée | conduite annoncée
SCENARIOS = {
    "respiratoire": [
        "Toux sans fièvre|une toux sèche|trois jours|La toux revient surtout quand je parle longtemps au téléphone|fièvre|Une bronchite a été rapportée en hiver dernier|Je ne prends aucun médicament actuellement|La température mesurée est de 36,8 °C|Une irritation est évoquée comme possibilité, sans diagnostic arrêté|Je prévois de vous revoir vendredi pour refaire le point",
        "Essoufflement à la montée|un essoufflement dans les escaliers|deux semaines|Je peux marcher sur terrain plat mais je m’arrête au deuxième étage|douleur thoracique|Une entorse de cheville remonte à trois ans|Je prends du paracétamol occasionnellement, sans dose précisée|La fréquence respiratoire comptée est de 18 par minute|L’origine de cet essoufflement reste indéterminée à ce stade|Un nouvel examen est annoncé pour demain matin",
        "Voix enrouée après répétition|une voix enrouée|hier soir|Je dirige une chorale et ma voix fatigue en fin de répétition|gêne à avaler|Une intervention dentaire a eu lieu en mars|Je ne prends aucun traitement régulier|La voix est rauque pendant notre échange|Une sollicitation vocale est envisagée, sans certitude|Je propose un point téléphonique dans trois jours",
        "Sifflement au contact de poussière|un sifflement respiratoire|une semaine|Cela arrive quand je range les cartons du grenier et cesse ensuite|réveil nocturne|Un asthme a été mentionné pendant mon enfance|Un inhalateur ancien est cité, mais son nom est inconnu|La saturation mesurée est de 98 %|Un lien avec la poussière est une hypothèse à explorer|Une consultation de contrôle est annoncée pour lundi",
        "Douleur après une quinte|une douleur de la paroi thoracique|ce matin|La gêne est apparue pendant une quinte de toux très forte|crachat sanglant|Je rapporte une fracture du poignet il y a dix ans|Je n’ai pris aucun médicament pour cette gêne|La douleur est reproduite à la palpation latérale|Une origine pariétale est évoquée comme hypothèse|Un réexamen demain est annoncé si la gêne persiste",
        "Nez bouché au réveil|une obstruction nasale|un mois|Je la remarque surtout dans la chambre et moins pendant mes promenades|perte d’odorat|Une allergie aux graminées a été rapportée autrefois|Je cite un spray nasal sans pouvoir donner son nom|La température mesurée est de 36,6 °C|Une composante environnementale est seulement envisagée|Je propose de noter les circonstances avant notre prochain échange",
    ],
    "cardiovasculaire": [
        "Palpitations et histoire familiale|des palpitations brèves|cinq jours|Je les ressens après le café du matin, puis elles passent en quelques minutes|perte de connaissance|Mon père a eu un infarctus à cinquante ans|Je ne prends aucun traitement régulier|Le pouls mesuré est de 76 par minute|Le lien avec le café reste une hypothèse|Un électrocardiogramme est annoncé pour le prochain rendez-vous",
        "Chevilles gonflées le soir|un gonflement des chevilles|dix jours|Mes chaussures serrent après une journée debout au comptoir|douleur du mollet|Une hypertension a été rapportée il y a deux ans|Je prends de l’amlodipine, 5 mg le matin|Un œdème discret des deux chevilles est observé|Un effet du traitement est envisagé sans être confirmé|Une revue du traitement est prévue avec votre médecin habituel",
        "Mesures de tension discordantes|des mesures de tension variables|trois semaines|Je mesure ma tension avant de partir au travail et après le dîner|céphalée|Je rapporte une hypertension connue depuis quatre ans|Je prends du ramipril, 2,5 mg par jour|La pression mesurée au cabinet est de 132 sur 78 mmHg|La différence de contexte de mesure est une explication possible|Une série de mesures standardisées est annoncée avant le contrôle",
        "Malaise lors d’une attente|un malaise sans chute|samedi dernier|Je suis resté debout dans une salle chaude pendant une longue attente|douleur thoracique|Une appendicectomie est rapportée à l’adolescence|Je ne prends aucun médicament quotidien|Le pouls est régulier à 68 par minute|Un mécanisme vagal est évoqué comme possibilité|Je programme un nouvel échange après lecture du compte rendu disponible",
        "Jambes lourdes au voyage|une lourdeur des jambes|le retour de voyage lundi|La gêne touche les deux jambes après plusieurs heures assis dans le train|rougeur localisée|Des varices ont été signalées lors d’un ancien examen|Je ne prends aucun traitement pour les jambes|Les deux mollets ont le même périmètre à l’examen|Une gêne veineuse est une hypothèse exprimée|Un contrôle clinique est annoncé la semaine prochaine",
        "Battements rapides pendant la course|des battements rapides à l’effort|un mois|Je les remarque pendant les premières minutes de footing, avec retour au calme ensuite|syncope|Un souffle innocent a été évoqué dans mon enfance|Je prends un complément de magnésium, dose non précisée|Le pouls au repos est de 62 par minute|La nature des épisodes n’est pas déterminée pendant cette consultation|Un enregistrement du rythme est discuté pour une consultation ultérieure",
    ],
    "digestif": [
        "Brûlure après les repas|une brûlure épigastrique|quatre jours|Elle survient après le dîner et diminue quand je reste assis|vomissement|Une appendicectomie remonte à mes vingt ans|Je n’ai pris aucun médicament pour cet épisode|L’abdomen est souple à la palpation|Un reflux est évoqué comme hypothèse, sans conclusion certaine|Je prévois un contrôle dans une semaine",
        "Transit ralenti pendant un déplacement|un transit ralenti|cinq jours|Depuis le déplacement professionnel, mes horaires de repas ont changé|sang dans les selles|Une constipation passagère a déjà eu lieu pendant un voyage|Je prends du fer depuis un mois, dose non précisée|L’abdomen n’est pas distendu à l’examen|Le changement d’habitudes est une explication possible|Une réévaluation du transit est annoncée au retour",
        "Selles liquides après un buffet|des selles liquides|hier midi|J’ai eu quatre passages aux toilettes depuis un buffet partagé au travail|vomissement|Je ne rapporte aucun épisode comparable cette année|Je n’ai pris aucun médicament depuis le début|La température mesurée est de 37,1 °C|Une origine alimentaire est évoquée sans preuve confirmatoire|Je vous propose un point demain sur l’évolution",
        "Ballonnement en fin de journée|un ballonnement abdominal|six semaines|Mon pantalon serre surtout le soir et la sensation diminue pendant la nuit|amaigrissement|Une intolérance au lactose a été évoquée autrefois sans confirmation|Je ne prends aucun traitement régulier|L’abdomen est souple sans défense à l’examen|Une relation avec certains repas reste à préciser|Un relevé des repas et symptômes est annoncé avant le contrôle",
        "Nausées pendant les trajets|des nausées en voiture|deux mois|Elles apparaissent quand je lis sur la banquette arrière et cessent à l’arrêt|douleur abdominale|Je rapporte un mal des transports pendant mon enfance|Je n’ai pas utilisé de médicament pour les trajets récents|La température mesurée est de 36,9 °C|Un mal des transports est envisagé comme explication|Un suivi des circonstances est proposé avant un prochain échange",
        "Gêne à la déglutition des solides|une gêne à avaler les aliments solides|trois semaines|Le pain semble passer moins facilement, mais je bois normalement|régurgitation|Un reflux avait été évoqué il y a cinq ans|Je cite un ancien antiacide dont je ne connais plus le nom|La voix reste claire pendant l’entretien|La cause de cette gêne n’est pas déterminée aujourd’hui|Un avis spécialisé est annoncé et sera organisé par le cabinet",
    ],
    "urinaire": [
        "Brûlure en urinant|une brûlure à la miction|deux jours|La gêne apparaît à la fin du passage aux toilettes|douleur lombaire|Une infection urinaire a été rapportée l’année dernière|Je n’ai pris aucun antibiotique pour cet épisode|La température mesurée est de 36,7 °C|Une infection urinaire est évoquée mais reste à confirmer|Un prélèvement urinaire est annoncé pour cet après-midi",
        "Levers nocturnes pour uriner|des levers nocturnes pour uriner|deux mois|Je me lève deux fois et je bois une grande tisane avant de dormir|brûlure urinaire|Un calcul urinaire a été rapporté il y a dix ans|Je prends un traitement diurétique dont le nom sera apporté au contrôle|La pression mesurée est de 128 sur 76 mmHg|Le rôle des boissons du soir est une hypothèse|Une revue des horaires de prise est prévue au rendez-vous suivant",
        "Fuites pendant les sauts|des fuites urinaires pendant le sport|six mois|Elles surviennent pendant les sauts à la corde et pas pendant la marche|urgence mictionnelle|Un accouchement est rapporté il y a deux ans|Je ne prends aucun médicament quotidien|La température mesurée est de 36,5 °C|Une fuite à l’effort est envisagée sans bilan complet|Un bilan dédié est annoncé pour une prochaine consultation",
        "Urines plus foncées après une marche|des urines plus foncées|hier|J’ai marché longtemps et j’ai bu moins que d’habitude pendant la sortie|douleur en urinant|Je rapporte un ancien épisode de déshydratation estivale|Je n’ai pris aucun nouveau médicament cette semaine|Le pouls mesuré est de 72 par minute|Une urine concentrée est évoquée comme possibilité|Une vérification de l’évolution est annoncée pour demain",
        "Envies fréquentes au bureau|des envies fréquentes d’uriner|trois semaines|Je vais aux toilettes surtout pendant les réunions et moins à la maison|fuite urinaire|Je ne rapporte aucune opération urinaire|Je prends deux cafés le matin, sans médicament déclaré|La température mesurée est de 36,8 °C|Le contexte des réunions pourrait jouer un rôle, sans conclusion|Un calendrier mictionnel est proposé avant un contrôle",
        "Jet urinaire moins puissant|un jet urinaire moins puissant|quatre mois|Je prends plus de temps aux toilettes, surtout au premier passage du matin|sang visible dans les urines|Une intervention pour hernie inguinale remonte à huit ans|Je prends un antihistaminique dont le nom n’est pas connu|L’abdomen est souple à l’examen|Une cause obstructive est une hypothèse à explorer|Un bilan urinaire et un nouvel examen sont annoncés",
    ],
    "musculosquelettique": [
        "Poignet douloureux et correction|une douleur du poignet droit|trois jours|J’ai dit gauche en arrivant ; je corrige : la douleur concerne uniquement le poignet droit|chute|Une tendinite du coude gauche a été rapportée il y a deux ans|J’ai pris du paracétamol, 500 mg une fois hier|Une gêne à la flexion du poignet droit est observée|Une sollicitation mécanique est évoquée sans certitude|Un réexamen est prévu dans cinq jours",
        "Genou douloureux en descente|une douleur du genou gauche|deux semaines|La gêne apparaît surtout en descendant les escaliers après la randonnée|blocage du genou|Une entorse de ce genou remonte à six ans|Je n’ai pris aucun médicament pour cette douleur|La flexion du genou est possible à l’examen|Une origine mécanique est envisagée|Une réévaluation est annoncée après une semaine",
        "Épaule raide au réveil|une raideur de l’épaule droite|un mois|J’ai du mal à atteindre l’étagère haute mais je peux écrire sans gêne|fourmillement de la main|Une fracture de la clavicule droite est rapportée dans l’enfance|Je prends du paracétamol occasionnellement, dose inconnue|L’élévation active de l’épaule est limitée à l’examen|Une atteinte tendineuse est évoquée comme hypothèse|Une consultation de contrôle est annoncée après le bilan prévu",
        "Dos douloureux après un carton|une douleur lombaire|dimanche|La douleur est apparue lorsque j’ai soulevé un carton pendant le déménagement|faiblesse de jambe|Un lumbago a été rapporté il y a trois ans|Je n’ai pris aucun anti-inflammatoire pour cet épisode|La marche est possible pendant l’examen|Une lombalgie mécanique est envisagée sans diagnostic définitif|Je propose de réévaluer la gêne dans quelques jours",
        "Talon sensible au premier pas|une douleur du talon gauche|cinq semaines|Le premier pas du matin est le plus sensible, puis la gêne diminue|traumatisme récent|Je rapporte une ancienne entorse de cheville droite|Je ne prends aucun traitement régulier|Une sensibilité sous le talon gauche est constatée|Une origine aponévrotique est évoquée comme possibilité|Un nouvel examen est prévu après observation de l’évolution",
        "Doigts raides au froid|une raideur des doigts|cet hiver|La sensation arrive au contact du froid et disparaît en rentrant au chaud|gonflement articulaire|Un eczéma des mains a été rapporté auparavant|J’utilise une crème hydratante sans médicament oral|Les articulations ne sont pas gonflées à l’examen|La sensibilité au froid est une hypothèse descriptive, sans cause arrêtée|Je propose de documenter les épisodes avant le prochain rendez-vous",
    ],
    "neurologique": [
        "Céphalée et incertitude|un mal de tête par épisodes|une semaine|La douleur ressemble peut-être aux migraines de ma sœur, mais je n’en suis pas certain|trouble visuel|Je rapporte une commotion légère à l’adolescence|J’ai pris du paracétamol, 1 g hier soir|La marche est stable pendant l’examen|Une migraine est évoquée comme hypothèse et non comme diagnostic acquis|Un nouvel examen est annoncé si les épisodes se répètent",
        "Fourmillement après appui du coude|des fourmillements des deux derniers doigts|dix jours|Ils apparaissent quand mon coude gauche reste posé longtemps sur le bureau|perte de force|Une fracture du coude gauche remonte à quinze ans|Je ne prends aucun médicament pour cette gêne|La force de préhension est conservée à l’examen|Une irritation liée à l’appui est envisagée|Une réévaluation clinique est annoncée dans deux semaines",
        "Vertige en se retournant au lit|une sensation de rotation brève|quatre jours|Le lit semble tourner quand je me retourne vers la droite, puis tout se calme|perte auditive|Un épisode de vertige a été rapporté il y a cinq ans|Je n’ai pas pris de nouveau médicament récemment|La marche est stable à la sortie de la chaise|Un mécanisme positionnel est évoqué comme hypothèse|Un examen positionnel dédié est annoncé au prochain rendez-vous",
        "Oubli de noms dans la fatigue|des oublis de noms|trois mois|Je retrouve les noms plus tard et cela arrive surtout après une mauvaise nuit|désorientation|Une période d’insomnie a été rapportée l’an dernier|Je prends parfois de la mélatonine, dose non précisée|La personne est orientée dans le temps pendant l’entretien|Le manque de sommeil pourrait contribuer à la plainte|Un entretien plus détaillé est prévu après un relevé du sommeil",
        "Tremblement en tenant une tasse|un tremblement des mains|six mois|Je le vois quand je porte une tasse pleine et moins lorsque les mains reposent|chute d’objet|Ma mère présente un tremblement ancien non caractérisé|Je ne prends aucun traitement neurologique|Un tremblement fin apparaît bras tendus pendant l’examen|Un tremblement d’action est une description possible, sans cause établie|Une consultation dédiée est annoncée pour préciser son retentissement",
        "Sensation de brûlure du pied|une sensation de brûlure sous le pied droit|un mois|Elle apparaît le soir après une journée avec mes chaussures de sécurité|douleur lombaire|Une entorse de cheville droite a eu lieu l’an dernier|Je n’ai essayé aucun médicament pour cette sensation|La peau du pied est intacte à l’examen|Une irritation locale est envisagée sans preuve suffisante|Un nouvel examen de la sensibilité est annoncé",
    ],
    "dermatologique": [
        "Plaque après un bracelet|une plaque rouge au poignet|trois jours|Elle suit la zone du nouveau bracelet et gratte quand je transpire|suintement|Une réaction à des boucles d’oreilles a été rapportée autrefois|J’ai appliqué une crème hydratante, nom non précisé|Une plaque rouge limitée au poignet est observée|Une réaction de contact est envisagée|Un contrôle de l’évolution cutanée est annoncé dans une semaine",
        "Boutons après une lessive|de petits boutons sur les avant-bras|une semaine|Ils sont apparus après le changement de lessive, sans certitude de lien|fièvre|Un eczéma dans l’enfance est rapporté|Je ne prends aucun nouveau médicament|Des papules éparses sont observées sur les avant-bras|Une irritation est une hypothèse à confronter à l’évolution|Je propose de revoir la peau au prochain rendez-vous",
        "Ongle épaissi après une chaussure|un ongle de pied épaissi|quatre mois|L’ongle du gros orteil a changé après plusieurs sorties avec des chaussures serrées|douleur spontanée|Un choc sur cet orteil est rapporté l’année dernière|Je n’ai appliqué aucun traitement sur l’ongle|L’ongle du gros orteil droit est épaissi à l’examen|Une cause traumatique ou fongique est évoquée sans arbitrage|Un prélèvement est discuté avant tout traitement spécifique",
        "Démangeaison du cuir chevelu|une démangeaison du cuir chevelu|six semaines|Elle est plus marquée après certains shampooings et ne me réveille pas|chute de cheveux|Une peau sèche ancienne est rapportée|J’utilise un shampooing parfumé sans traitement médical|Des squames fines sont observées sur le cuir chevelu|Une irritation liée au produit est possible sans certitude|Une revue des produits utilisés est prévue au contrôle",
        "Tache observée sur l’avant-bras|une tache brune de l’avant-bras|deux mois|Je l’ai remarquée sur une photo, sans pouvoir dire si elle existait auparavant|saignement|Une exposition solaire importante pendant la jeunesse est rapportée|Je ne prends aucun traitement cutané|Une macule brune de 4 mm est mesurée|La nature de cette tache n’est pas déterminée pendant cet entretien|Un examen dermatologique est annoncé",
        "Fissure au bout des doigts|des fissures au bout des doigts|trois semaines|Elles apparaissent pendant les journées où je lave souvent du matériel|pus|Un eczéma des mains a été rapporté il y a deux hivers|J’utilise une crème barrière, nom non précisé|Deux fissures superficielles sont observées sur les doigts|Une irritation répétée est évoquée comme hypothèse|Un contrôle cutané est annoncé après une semaine",
    ],
    "suivi-chronique": [
        "Relevé glycémique incomplet|la revue de mon carnet glycémique|ce mois-ci|Il manque plusieurs mesures car le lecteur est tombé en panne la semaine dernière|malaise hypoglycémique|Un diabète de type 2 est rapporté depuis cinq ans|Je prends de la metformine, 500 mg matin et soir|Le poids mesuré est de 74 kg|L’équilibre récent ne peut pas être conclu avec ce carnet incomplet|Une nouvelle lecture du carnet est prévue au prochain contrôle",
        "Fatigue au suivi thyroïdien|une fatigue pendant mon suivi thyroïdien|six semaines|Je termine difficilement ma journée mais je continue mes activités habituelles|palpitation|Une hypothyroïdie est rapportée depuis trois ans|Je prends de la lévothyroxine, 50 microgrammes le matin|Le pouls mesuré est de 70 par minute|Le lien avec la thyroïde reste à vérifier|Un dosage biologique de contrôle est annoncé",
        "Observance irrégulière du traitement|des oublis de comprimés|un mois|Je saute parfois la prise du soir quand mes horaires de travail changent|douleur musculaire|Une hypercholestérolémie a été rapportée il y a deux ans|Je prends de l’atorvastatine, 10 mg le soir|La pression mesurée est de 124 sur 72 mmHg|Les oublis pourraient modifier l’interprétation du prochain bilan|Une revue de l’organisation des prises est annoncée",
        "Contrôle respiratoire stable rapporté|le suivi de mon asthme|ce trimestre|Je n’ai pas utilisé mon inhalateur de secours depuis le dernier rendez-vous|réveil nocturne|Un asthme est rapporté depuis l’adolescence|Je cite un inhalateur de fond dont le dosage sera vérifié sur la boîte|La saturation mesurée est de 99 %|La stabilité rapportée devra être confrontée au bilan prévu|Un contrôle fonctionnel respiratoire est annoncé",
        "Douleur ancienne et retentissement|le suivi d’une douleur chronique du dos|deux ans|La gêne varie et m’empêche parfois de rester assis pendant un film|trouble urinaire|Une chirurgie lombaire est rapportée il y a huit ans|Je prends du paracétamol à la demande, dose non précisée|La marche sans aide est observée|Le retentissement fonctionnel reste à préciser séparément de l’intensité|Un bilan fonctionnel est prévu au prochain rendez-vous",
        "Traitement antihypertenseur bien toléré|la revue de mon traitement de tension|trois mois|J’ai apporté les boîtes pour vérifier les noms et les horaires de prise|vertige au lever|Une hypertension est rapportée depuis six ans|Je prends du losartan, 50 mg le matin|La pression mesurée est de 126 sur 74 mmHg|La tolérance est rapportée comme satisfaisante sans conclusion sur le bilan complet|Un bilan de surveillance est annoncé pour le mois prochain",
    ],
    "sante-psychique": [
        "Sommeil fragmenté en période chargée|des réveils nocturnes|trois semaines|Je pense au travail lorsque je me réveille et je me rendors après une heure|idée suicidaire|Une période similaire a été rapportée pendant des examens|Je ne prends aucun somnifère|Le discours est cohérent pendant l’entretien|Une association avec la charge de travail est envisagée|Un entretien de suivi est proposé la semaine prochaine",
        "Appréhension avant une prise de parole|une forte appréhension avant les réunions|deux mois|Mes mains deviennent moites juste avant de présenter puis la tension diminue|consommation d’alcool pour gérer la situation|Une timidité ancienne est rapportée|Je ne prends aucun anxiolytique|La respiration est calme pendant l’entretien|Une anxiété liée à la situation est évoquée sans diagnostic définitif|Un temps d’échange dédié est annoncé",
        "Humeur basse après une séparation|une baisse de moral|six semaines|Je vois encore mes amis mais je trouve les soirées plus difficiles depuis la séparation|idée suicidaire|Un épisode de tristesse après un deuil est rapporté autrefois|Je ne prends aucun traitement psychotrope|Le contact est maintenu pendant l’entretien|Le contexte de séparation peut contribuer aux difficultés rapportées|Un suivi rapproché est annoncé pour la semaine suivante",
        "Épuisement après des horaires alternés|un épuisement en fin de semaine|deux mois|Mes horaires alternent entre matin et soir et mon sommeil est irrégulier|attaque de panique|Une insomnie passagère a été rapportée l’année dernière|Je prends parfois de la mélatonine, sans dose connue|Le discours reste organisé pendant l’entretien|Le rythme de travail est une hypothèse explicative à explorer|Une nouvelle consultation est prévue après un relevé des horaires",
        "Ruminations au coucher|des pensées répétitives au coucher|quatre semaines|Je repasse les tâches du lendemain et je vérifie plusieurs fois mon agenda|idée suicidaire|Je ne rapporte aucune prise en charge psychologique antérieure|Je ne prends aucun médicament pour le sommeil|La personne décrit clairement les circonstances pendant l’entretien|Un lien avec l’incertitude professionnelle est seulement envisagé|Un entretien de suivi est annoncé dans dix jours",
        "Retrait social après un déménagement|une difficulté à reprendre des activités sociales|trois mois|Depuis le déménagement je connais peu de monde mais je souhaite rejoindre une association|perte d’appétit|Une période d’isolement a été rapportée lors d’un ancien changement de ville|Je ne prends aucun psychotrope|Le contact est facile pendant l’entretien|La transition de vie est évoquée comme facteur possible|Un point sur les activités choisies est prévu au prochain rendez-vous",
    ],
    "prevention": [
        "Revue des boîtes de médicaments|la vérification de mes médicaments|aujourd’hui|J’ai apporté mes boîtes pour éviter de confondre les doses inscrites sur les emballages|prise d’aspirine|Une hypertension est rapportée depuis deux ans|Je prends du ramipril, 5 mg le matin, et non 10 mg comme dit au début|La pression mesurée est de 130 sur 80 mmHg|Une confusion de dose est constatée dans le récit, la boîte est à vérifier|Une conciliation avec l’ordonnance est annoncée",
        "Carnet vaccinal à compléter|la lecture de mon carnet vaccinal|aujourd’hui|Une page manque et je ne sais plus à quelle date le dernier rappel a eu lieu|réaction après une vaccination|Une vaccination antitétanique ancienne est rapportée sans date|Je ne prends aucun traitement immunosuppresseur déclaré|La température mesurée est de 36,6 °C|Le statut du rappel ne peut pas être établi avec les documents présents|Une recherche du justificatif est prévue avant de décider du calendrier",
        "Reprise progressive de la marche|la préparation d’une reprise d’activité|ce mois-ci|Je souhaite recommencer à marcher après plusieurs mois passés surtout au bureau|douleur thoracique à la marche|Une entorse de cheville a eu lieu l’hiver dernier|Je ne prends aucun traitement régulier|Le pouls mesuré est de 64 par minute|Le niveau d’activité actuel doit être précisé avant un objectif personnalisé|Un point sur les habitudes d’activité est annoncé",
        "Revue d’une allergie déclarée|la clarification d’une allergie ancienne|aujourd’hui|On m’a parlé d’une allergie pendant l’enfance mais je ne connais pas le produit concerné|réaction récente|Une éruption ancienne après un médicament inconnu est rapportée|Je ne prends aucun médicament quotidien|La peau visible ne présente pas d’éruption à l’examen|L’allergène n’est pas identifié et aucune attribution précise n’est possible|La recherche d’un ancien compte rendu est annoncée",
        "Discussion sur le tabac|un échange sur ma consommation de tabac|ce mois-ci|Je fume cinq cigarettes par jour et je souhaite parler de mes habitudes avant de décider|utilisation de cigarette électronique|Une tentative d’arrêt de deux mois est rapportée l’an dernier|Je n’utilise aucun substitut nicotinique actuellement|Le pouls mesuré est de 78 par minute|Les situations déclenchant la consommation restent à préciser|Un entretien de suivi est proposé pour discuter des objectifs choisis",
        "Préparation d’un voyage et traitements|la préparation de mes documents de santé pour un voyage|le départ prévu le mois prochain|Je veux vérifier la liste de mes traitements et les documents que je possède déjà|allergie médicamenteuse connue|Une chirurgie de cataracte est rapportée l’année dernière|Je prends de la metformine, 850 mg deux fois par jour|La pression mesurée est de 122 sur 70 mmHg|Les besoins liés au voyage ne sont pas déterminés pendant cet entretien|Une revue de l’ordonnance et des justificatifs est annoncée",
    ],
}


def create_case(family, index, row, case_id=None, stress=None):
    (
        title,
        reason,
        onset,
        context,
        negative,
        background,
        medication,
        observation,
        assessment,
        plan,
    ) = row.split("|")
    cid = case_id or f"main-{family}-{index:02}"
    # Questions ouvertes communes ; les faits distinctifs sont entièrement dans les réponses.
    dialogue = [
        (
            "clinician",
            "Bonjour. Cet entretien est fictif. Pouvez-vous expliquer avec vos mots la raison de votre venue, puis préciser depuis quand vous avez remarqué cette situation ?",
        ),
        (
            "patient",
            f"Je viens pour {reason}. Cela a commencé {onset}. Je souhaite décrire ce qui se passe sans donner moi-même un diagnostic.",
        ),
        (
            "clinician",
            "Dans quelles circonstances le remarquez-vous ? Je vais conserver les détails tels que vous les rapportez, y compris vos éventuelles hésitations ou corrections.",
        ),
        ("patient", context + "."),
        (
            "clinician",
            "Nous allons aussi noter ce qui est absent selon vous. Ensuite, indiquez les événements de santé antérieurs qui vous semblent utiles, en précisant la personne concernée.",
        ),
        ("patient", f"Je ne rapporte pas de {negative}. {background}."),
        (
            "clinician",
            "Pouvez-vous maintenant décrire les médicaments ou produits utilisés, même occasionnellement ? Si un nom ou une dose vous échappe, cette information restera non précisée.",
        ),
        ("patient", medication + "."),
        ("clinician", observation + ". " + assessment + "."),
        (
            "patient",
            "Je souhaite conserver une trace de ce qui a été dit aujourd’hui. Je préfère que les informations manquantes restent indiquées comme non mentionnées.",
        ),
        (
            "clinician",
            plan
            + ". Nous distinguons les possibilités évoquées des conclusions et les actions annoncées des actions déjà réalisées.",
        ),
        (
            "patient",
            "Je suis disponible pour un rendez-vous en fin de journée. Merci de noter cette préférence pratique séparément des informations cliniques.",
        ),
    ]
    segments = [
        dict(segment_id=f"s{i:03}", speaker=speaker, text=text)
        for i, (speaker, text) in enumerate(dialogue, 1)
    ]
    case = dict(
        schema_version="1.0",
        case_id=cid,
        group_id=f"parent-{cid}" if not stress else stress["pair_id"],
        family_id=family,
        suite="stress" if stress else "main",
        split="stress" if stress else ("dev" if index <= 2 else "test"),
        title=title,
        locale="fr-FR",
        segments=segments,
        provenance_id="agent-editorial-v1",
        focus_tags=["synthétique", negative],
        stress_pair=stress,
    )
    gold = []

    def add(
        key,
        section,
        label,
        value,
        sid,
        quote,
        polarity="affirmed",
        temporality="present",
        certainty="reported",
        subject=None,
        expected=True,
        unit=None,
    ):
        source = segments[sid - 1]["text"]
        start = source.index(quote)
        gold.append(
            dict(
                fact_id=f"{cid}.{key}",
                case_id=cid,
                fact_key=key,
                section=section,
                label=label,
                value=value,
                unit=unit,
                subject=subject or dict(kind="patient", label=None),
                polarity=polarity,
                temporality=temporality,
                certainty=certainty,
                expected_in_note=expected,
                evidence=[
                    dict(segment_id=f"s{sid:03}", start=start, end=start + len(quote), quote=quote)
                ],
            )
        )

    add("motif", "reason", reason, None, 2, f"Je viens pour {reason}.")
    add("debut", "history", "Début rapporté", onset, 2, f"Cela a commencé {onset}.")
    add("contexte", "history", "Circonstances rapportées", context, 4, context)
    add(
        "signe-cible",
        "history",
        negative,
        None,
        6,
        f"Je ne rapporte pas de {negative}.",
        polarity="negated",
    )
    subject = (
        dict(kind="relative", label="père" if background.startswith("Mon père") else "mère")
        if background.startswith(("Mon père", "Ma mère"))
        else None
    )
    add(
        "antecedent",
        "background",
        "Antécédent rapporté",
        background,
        6,
        background,
        temporality="past",
        subject=subject,
        polarity="negated" if background.startswith("Je ne rapporte") else "affirmed",
    )
    add(
        "traitement",
        "medications_allergies",
        "Traitement rapporté",
        medication,
        8,
        medication,
        polarity="negated"
        if medication.startswith(("Je ne ", "Je n’ai", "Je n’utilise"))
        else "affirmed",
    )
    add(
        "observation",
        "observations",
        "Observation exprimée",
        observation,
        9,
        observation,
        certainty="observed",
    )
    add(
        "evaluation",
        "assessment",
        "Évaluation exprimée",
        assessment,
        9,
        assessment,
        certainty="hypothetical",
    )
    add("conduite", "plan", "Conduite annoncée", plan, 11, plan, temporality="future")
    add(
        "disponibilite",
        "plan",
        "Préférence de rendez-vous",
        "fin de journée",
        12,
        "Je suis disponible pour un rendez-vous en fin de journée.",
        expected=False,
    )
    return case, gold


def main(editorial_context):
    root = Path(__file__).resolve().parents[1]
    if (root / "eval/frozen-manifest.v1.json").exists() or (root / "data/cases.v1.jsonl").exists():
        raise ValueError("Le corpus existant ne peut pas être écrasé par la préparation initiale")
    context_hash = sha256_file(editorial_context)
    cases = []
    facts = []
    stress_cases = []
    for family in FAMILIES:
        for index, row in enumerate(SCENARIOS[family], 1):
            case, gold = create_case(family, index, row)
            cases.append(case)
            facts.extend(gold)
    # Dix parents stress indépendants, décrits par des motifs distincts des parents principaux.
    stress_motifs = [
        "une gêne respiratoire après une peinture",
        "des battements perçus au repos le soir",
        "une pesanteur après le petit déjeuner",
        "une gêne urinaire après une longue réunion",
        "une douleur du coude après jardinage",
        "une sensation de tête légère au lever",
        "une rougeur derrière les oreilles",
        "la revue de mon carnet de poids",
        "une nervosité avant un changement de poste",
        "la revue de mes compléments alimentaires",
    ]
    for i, (family, motif) in enumerate(zip(FAMILIES, stress_motifs, strict=True), 1):
        row = "|".join(
            [
                f"Contraste de négation {i:02}",
                motif,
                "huit jours",
                f"Je note surtout cette situation lorsque je reprends mes activités habituelles après le déjeuner, dans le contexte de {motif}",
                "fièvre",
                "Une intervention dentaire ancienne est rapportée",
                "Je ne prends aucun traitement régulier",
                "La fréquence cardiaque mesurée est de 73 par minute",
                "L’origine de la plainte reste à préciser",
                "Un entretien de suivi est annoncé dans huit jours",
            ]
        )
        for variant in ["positive", "negative"]:
            meta = dict(
                pair_id=f"stress-parent-{i:02}",
                variant=variant,
                target_fact_key="signe-cible",
                invariant_fact_keys=[],
            )
            c, g = create_case(family, 1, row, f"stress-{i:02}-{variant}", meta)
            target = next(f for f in g if f["fact_key"] == "signe-cible")
            if variant == "positive":
                old = "Je ne rapporte pas de fièvre."
                # Forme grammaticale identique dans les deux variantes : « une fièvre ».
                c["segments"][5]["text"] = c["segments"][5]["text"].replace(
                    old, "Je rapporte une fièvre."
                )
                target["polarity"] = "affirmed"
                target["evidence"][0].update(
                    quote="Je rapporte une fièvre.", end=len("Je rapporte une fièvre.")
                )
            else:
                c["segments"][5]["text"] = c["segments"][5]["text"].replace(
                    "Je ne rapporte pas de fièvre.", "Je ne rapporte pas une fièvre."
                )
                target["evidence"][0].update(
                    quote="Je ne rapporte pas une fièvre.",
                    end=len("Je ne rapporte pas une fièvre."),
                )
            for f in g:
                if f["fact_key"] == "antecedent":
                    q = f["evidence"][0]["quote"]
                    start = c["segments"][5]["text"].index(q)
                    f["evidence"][0].update(start=start, end=start + len(q))
            meta["invariant_fact_keys"] = [
                f["fact_key"] for f in g if f["fact_key"] != "signe-cible"
            ]
            stress_cases.append(c)
            facts.extend(g)
    for filename, rows in [("cases", cases), ("stress", stress_cases), ("gold", facts)]:
        (root / f"data/{filename}.v1.jsonl").write_text(
            "".join(canonical_json(r) + "\n" for r in rows), encoding="utf-8"
        )
    write_json(
        root / "data/provenance.v1.json",
        [
            dict(
                provenance_id="agent-editorial-v1",
                kind="ai",
                author_id="Codex implementation agent",
                created_at=utc_now(),
                prompt_sha256=context_hash,
                review="none",
            )
        ],
    )
    write_json(root / "data/demo_ids.v1.json", DEMO_IDS)
    (root / "data/review-events.jsonl").touch()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--editorial-context", type=Path, required=True,
                        help="Document exact utilisé pour cette préparation initiale")
    main(parser.parse_args().editorial_context)
