# Refonte produit — exigences confirmées et décisions à valider

## Exigences de départ

- Une partie contre l'IA doit fonctionner sans réseau et sans compte.
- Deux appareils proches doivent pouvoir se trouver et jouer sans Internet.
- L'application vise Windows, macOS, Linux, Android et iOS.
- L'échiquier reste immédiatement lisible et agréable à jouer. Le relief et les animations servent les coups, ils ne les masquent pas.
- Les changements de produit ne doivent pas effacer l'application ni les modifications déjà présentes dans ce dépôt.

## Ce que le dépôt prouve aujourd'hui

- La base est un client Pygame/Python. `main.py` concentre une grande partie de l'interface et du jeu.
- `network.py` annonce les parties par broadcast UDP et échange des messages par socket TCP. C'est du LAN, pas une architecture Internet. La découverte par broadcast doit être adaptée aux restrictions mobiles.
- `ai.py` s'appuie sur Stockfish local. Il n'y a donc pas besoin d'un service IA distant pour respecter le fonctionnement hors ligne.
- `packaging/android/buildozer.spec` décrit un paquet Android Pygame, mais le dépôt ne contient pas de projet iOS ni de chaîne de compilation iOS. Les versions installées ailleurs restent à inventorier avant d'affirmer que tous les appareils sont couverts.
- L'historique Git disponible ne contient que le commit `290bc6d`. Les modifications non commitées restent présentes dans l'arbre de travail.

## Architecture produit — décision retenue

### Jeu hors ligne

Le cœur d'échecs, la sauvegarde des parties et l'IA restent sur l'appareil. Une partie IA ne contacte aucun serveur. Stockfish peut rester le moteur, mais son intégration doit être propre à chaque cible : processus local sur desktop, bibliothèque/native bridge sur Android et iOS. Il faut vérifier la faisabilité de compilation et les obligations GPL avant de choisir le packaging final.

### Parties entre appareils proches

Le premier objectif réseau est « même réseau Wi-Fi, sans Internet » : annonce de salon sur le réseau local, découverte automatique, puis connexion directe entre appareils. Un code court peut rester un recours manuel si la découverte échoue, mais ce n'est ni un code de parrainage ni une étape obligatoire.

Pour jouer sans routeur ni point d'accès, il faut des adaptateurs natifs : Wi-Fi Direct / découverte de services sur Android, APIs Apple de proximité sur iPhone/iPad, et une stratégie desktop. Ces APIs ne sont pas identiques. La compatibilité Android ↔ iOS sans infrastructure doit être prouvée sur les appareils cibles avant d'être promise. Le comportement hors ligne ne signifie pas que chaque radio fonctionne sans permission : les systèmes demandent des autorisations de découverte locale.

Le protocole de partie sera indépendant de l'interface et du transport. Chaque message porte un identifiant de partie, un numéro de séquence et un coup UCI; les clients valident les coups légaux localement. L'hôte arbitre l'ordre des coups et partage un état de reprise. Aucune identité ni connexion cloud n'est requise.

### Moteur et rendu

Le nouveau client sera construit dans Godot 4 avec GDScript. Ce choix remplace Pygame comme direction produit, car le projet doit être un jeu tactile animé avec des exports desktop et mobiles cohérents. Pygame reste la référence fonctionnelle pendant le portage; ses sources et l'historique ne sont pas supprimés. Les exports Windows/macOS/Linux/Android/iOS restent des jalons à vérifier séparément, pas une promesse acquise par le choix du moteur.

Le rendu retenu est une scène 2.5D lisible : perspective légère, pièces sculptées, lumière douce, prise en main au doigt et transitions brèves. Le plateau reste fixe pendant les coups. On construit d'abord un client 2D/2.5D performant; Blender, outil libre de modélisation et d'animation, servira aux pièces si cela améliore le résultat. Material Maker est libre et pourra créer les matériaux PBR, sans devenir une dépendance de l'application. Le 3D complet n'est pas le but : il risque de réduire la lecture tactique et la précision sur petit écran.

## Expérience de jeu

- Accueil centré sur « Reprendre », « Jouer contre l'IA » et « Jouer à proximité ».
- Partie plein écran : plateau prioritaire, commandes secondaires discrètes, pièces sélectionnées et coups légaux clairement marqués.
- Animations rapides et sobres pour déplacement, capture, échec et fin de partie; option mouvement réduit et retour instantané.
- Analyse, chat, variantes et réglages apparaissent à la demande.
- IA réglable par niveau et rythme, avec indices facultatifs, entièrement hors ligne.

## Historique et migration

Le commit existant `290bc6d` est conservé. La branche locale `codex/refonte-hors-ligne` et le tag `v2.1.0-pygame-base` marquent la base avant la migration. Rien n'est supprimé. La copie d'archive existante reste distincte du dépôt. Les fichiers modifiés et non suivis doivent être examinés et sauvegardés avant toute migration qui les remplace.

La migration se fait par étapes réversibles, avec Pygame conservé jusqu'à validation :

1. Inventorier les cibles de build réellement produites et les appareils disponibles.
2. Construire dans Godot un vrai vertical slice : accueil interactif, partie contre une IA locale, coups légaux complets, sauvegarde/reprise locale, animations et interface tactile.
3. Migrer sans perte les fonctions phares : Stockfish local, profils/niveaux, apprentissage/indices, horloges, replay et export PGN, annotations, thèmes, chat et partie LAN.
4. Brancher d'abord la découverte sur le même Wi-Fi; ajouter des adaptateurs natifs Wi‑Fi Direct/Apple pour les parties sans routeur après validation Android ↔ iOS sur matériel réel.
5. Construire et vérifier chaque plateforme avant de remplacer une version distribuée. Tout résultat de build doit être réellement installé/lancé sur la cible.

## Références techniques consultées

- Android Wi-Fi Direct peut découvrir et connecter des appareils proches sans réseau ni hotspot; l'API demande toutefois des permissions système et des sockets standards.
- Apple fournit des APIs de découverte locale/proximité et impose la déclaration des services Bonjour ainsi que l'autorisation réseau local. Certaines options P2P Apple ne sont interopérables qu'entre appareils Apple.
- Blender est libre pour la création d'assets 3D. Les licences de chaque asset importé restent à vérifier.
