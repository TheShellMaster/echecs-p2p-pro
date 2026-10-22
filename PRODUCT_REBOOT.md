# Refonte produit — exigences confirmées et décisions à valider

## Exigences de départ

- Une partie contre l'IA doit fonctionner sans réseau et sans compte.
- Deux appareils proches doivent pouvoir se trouver et jouer sans Internet.
- L'application vise Windows, macOS, Linux, Android et iOS.
- Jeu d'échecs **ultra réaliste** : vraie scène 3D, animations fluides, interface très interactive et menus en ralenti (slow motion). Décision du propriétaire du 21/10/2026, qui remplace l'orientation « sobre » précédente.
- L'échiquier reste lisible : le relief et les animations mettent les coups en valeur sans les masquer.
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

Le rendu retenu est une **vraie scène 3D** (`godot/ui/board_3d.gd`) : pièces Aster modélisées dans Blender (`assets/3d/aster_chess_set.glb`), matériaux PBR, ombres portées, caméra cinématique, glisser-déposer et survol. Les menus affichent la scène 3D en fond, avec une partie de démonstration rejouée au ralenti et un effet bullet time au survol. La lisibilité reste un critère : la caméra de jeu est fixe (légère respiration), les coups légaux et l'échec sont marqués sur le plateau. Material Maker pourra affiner les matériaux sans devenir une dépendance.

## Expérience de jeu

- Accueil centré sur « Reprendre », « Jouer contre l'IA » et « Jouer à proximité ».
- Partie plein écran : plateau prioritaire, commandes secondaires discrètes, pièces sélectionnées et coups légaux clairement marqués.
- Animations cinématiques : pièces en arc avec atterrissage amorti, captures renversées au ralenti avec poussée de caméra, échec pulsé en lumière rouge, roi mat qui bascule au ralenti. Une option « mouvement réduit » reste à ajouter.
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
