# Journal des modifications

## [Non publié] — branche `codex/refonte-hors-ligne`

### Ajouté
- `godot/ui/board_3d.gd` : plateau 3D réaliste avec les pièces Aster (GLB Blender), matériaux réalistes, ombres et lueur. Coups en arc, captures au ralenti, lumière d'échec, bascule du roi au mat, glisser-déposer, survol, caméra cinématique et sons.
- Menu cinématique : la partie de l'Opéra (1858) rejouée au ralenti en fond, apparition des éléments en cascade, bullet time au survol, sortie figée avec zoom.
- Thème sombre et doré pour l'accueil et la partie. Transitions d'écran plus lentes.
- L'IA attend que la pièce du joueur ait atterri avant de jouer.
- Sons du client historique copiés dans `godot/assets/sounds/`.
- `godot/tools/capture_screens.gd` : captures d'écran automatiques.
- Documentation complète dans `docs/` (guide du joueur, architecture, développement, feuille de route) et ce journal.

### Corrigé
- Le client Godot **ne compilait pas**. Les inférences de type étaient invalides dans `core/chess_game.gd` (26 cas), `ui/game_screen.gd` et `net/lan_chess_transport.gd`. `verify_chess_game.gd` utilisait `back()` sur un `PackedStringArray`, et `_board.update()` n'existe pas dans Godot 4.
- L'adaptation à la taille de la fenêtre plantait : `HBoxContainer` ne peut pas devenir vertical, il a été remplacé par `BoxContainer`.

### Modifié
- `PRODUCT_REBOOT.md` : la direction « sobre et 2.5D » est remplacée par une vraie scène 3D, ultra réaliste, avec des menus en ralenti (décision du propriétaire du 21/10/2026).

## [2.1.0] — client Pygame
- Stockfish, animations au ralenti, design Material 3 (tag `v2.1.0-pygame-base`).
