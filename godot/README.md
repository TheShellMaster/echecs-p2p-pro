# Client Échecs 3D (Godot 4.4)

Nouveau client du jeu : vraie scène 3D, pièces sculptées, animations cinématiques et menus en ralenti. Tout fonctionne hors ligne. Le client Python/Pygame à la racine reste la référence fonctionnelle jusqu'à la parité des fonctions.

```sh
godot --path godot                                                      # jouer (depuis la racine)
godot --headless --path godot --script res://core/verify_chess_game.gd  # vérifier les règles
```

- `app.gd` : routeur des écrans. Le démarrage réel passe par `app.tscn`, pas par `main.tscn`.
- `core/` : règles d'échecs indépendantes de l'interface ([API](core/README.md)).
- `ui/` : `board_3d.gd` (plateau 3D), `home_screen.gd` (menu), `game_screen.gd` (partie), `nearby_screen.gd` (réseau local).
- `net/` : transport pour le réseau local.
- `tools/` : captures d'écran automatiques.

Documentation : [guide du joueur](../docs/GUIDE_JOUEUR.md), [architecture](../docs/ARCHITECTURE.md), [développement](../docs/DEVELOPPEMENT.md), [feuille de route](../docs/FEUILLE_DE_ROUTE.md).

## Principes

- Jouer contre l'IA sans compte et sans Internet.
- Jouer à deux sur le même appareil, ou trouver une partie à proximité.
- Un rendu 3D réaliste et vivant, qui garde le plateau lisible.
- Aucun service cloud pour les règles, l'IA ou la sauvegarde.
- Portage progressif : on ne retire pas une fonction historique tant que son équivalent n'existe pas ici.
