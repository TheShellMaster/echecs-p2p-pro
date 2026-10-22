# Feuille de route du client Godot

Légende : ✅ livré et vérifié · 🟡 partiel · ⬜ à faire.

## Expérience 3D et interactivité

| Fonction | État |
| --- | --- |
| Plateau 3D, pièces Aster, matériaux réalistes, ombres | ✅ |
| Coups en arc, atterrissage amorti, onde au sol | ✅ |
| Captures au ralenti avec zoom de caméra | ✅ |
| Lumière d'échec et bascule du roi au mat | ✅ |
| Glisser-déposer, survol, pièce sélectionnée qui flotte | ✅ |
| Menu cinématique : partie de démonstration au ralenti, bullet time, sortie figée | ✅ |
| Option « mouvement réduit » | ⬜ |
| Orientation des cavaliers, retournement du plateau quand on joue les Noirs | ⬜ |
| Effets de victoire (particules) | ⬜ |

## IA hors ligne et niveaux

| Fonction | État |
| --- | --- |
| IA minimax GDScript hors ligne (profondeur 2) | ✅ |
| Pilotage de Stockfish local depuis Godot (`OS.execute_with_pipe`) | 🟡 essai réel concluant, pas encore branché sur l'écran de partie |
| Niveaux 1 à 6 (Skill Level, temps de réflexion, IA de secours graduée) | ⬜ |
| Réflexion de l'IA dans un thread (animations sans à-coups) | ⬜ |
| Choix de la couleur | ⬜ |

## Apprentissage

| Fonction | État |
| --- | --- |
| Indice (meilleur coup affiché sur le plateau) | ⬜ |
| Coach : avis sur chaque coup (excellent, imprécision, gaffe) | ⬜ |
| Signalement des pièces en prise | ⬜ |
| Leçons et puzzles tactiques, avec progression enregistrée | ⬜ |

## Partie et confort

| Fonction | État |
| --- | --- |
| Règles complètes et vérificateur | ✅ |
| Sauvegarde et reprise locale (« Continuer ») | ⬜ |
| Choix de la pièce de promotion | ⬜ (dame automatique) |
| Nulles réclamables (50 coups, triple répétition) dans l'interface | ⬜ |
| Pendules | ⬜ |
| Export PGN | ⬜ |
| Réglages (son, coach, mouvement réduit) | ⬜ |

## Réseau et plateformes

| Fonction | État |
| --- | --- |
| Partie sur le réseau local (UDP et TCP) | 🟡 compile, pas encore testée sur deux appareils |
| Wi-Fi Direct (Android), proximité Apple | ⬜ |
| Exports Windows, macOS, Linux, Android, iOS | ⬜ (`export_presets.cfg` absent) |
