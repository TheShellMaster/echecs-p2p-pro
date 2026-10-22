# Développement

## Prérequis

| Outil | Version | Usage |
| --- | --- | --- |
| Godot | 4.4.x (binaire officiel) | Client 3D |
| Python | 3.12 | Client historique et tests |
| Stockfish | binaire compatible avec l'hôte | IA du client historique ; à venir dans Godot |
| Blender | optionnel | Régénérer les pièces 3D |

Installer Godot sous Linux sans droits administrateur :

```sh
mkdir -p ~/.local/share/godot && cd ~/.local/share/godot
curl -LO https://github.com/godotengine/godot/releases/download/4.4.1-stable/Godot_v4.4.1-stable_linux.x86_64.zip
unzip Godot_v4.4.1-stable_linux.x86_64.zip
ln -sf "$PWD/Godot_v4.4.1-stable_linux.x86_64" ~/.local/bin/godot
```

## Client Godot

Toutes les commandes se lancent depuis la racine du dépôt.

```sh
godot --headless --path godot --import                                # premier import des assets (GLB, sons)
godot --path godot                                                    # jouer
godot --path godot -e                                                 # éditeur
godot --headless --path godot --script res://core/verify_chess_game.gd  # vérifier les règles
godot --headless --path godot --quit-after 300                        # repérer les erreurs de script
godot --path godot --script res://tools/capture_screens.gd            # captures → docs/images/captures/
```

### Règles de code GDScript

- Godot 4.4 refuse `:=` quand le type est inconnu, par exemple pour un `Dictionary` non typé ou pour `abs()`. Utilisez un type explicite (`var x: int = ...`), ou `=`.
- `PackedStringArray` n'a pas de méthode `back()`. Utilisez `[-1]`.
- `Control` n'a pas de méthode `update()` dans Godot 4. Utilisez `queue_redraw()`.
- Un conteneur qui doit changer d'orientation doit être un `BoxContainer`, pas un `HBoxContainer`.
- **Avant de livrer**, lancez `--quit-after` et le vérificateur de règles : aucune ligne `SCRIPT ERROR` ne doit apparaître.

### Fichiers générés par Godot

- `godot/.godot/` : cache, ignoré par Git.
- `*.uid` et `*.import` : **à commiter**. Godot s'en sert pour suivre les ressources.

## Client historique (Python)

```sh
python3.12 -m pip install -r requirements.txt pytest psutil
python3.12 main.py
python3.12 -m pytest -v
```

- Les tests sont à la racine, pas dans `tests/`. Certains utilisent un vrai Stockfish et ouvrent de vrais sockets locaux.
- `ai.get_stockfish_path()` cherche `stockfish_bin`, `stockfish.exe`, `stockfish`, puis le `PATH` et `/usr/games/stockfish`.
- Les binaires Stockfish ne sont pas versionnés.

## Paquets

- Linux : `python3.12 -m PyInstaller --clean -y EchecsP2P.spec` produit `dist/EchecsP2P`. Vérifiez le code de sortie : `build_linux.sh` peut annoncer un succès même quand la construction a échoué.
- `packaging/build_all_packages.py` **régénère** les sources d'installeurs. Ne modifiez pas les copies macOS : modifiez les sources Python à la racine.
- Exports Godot (desktop et mobile) : à configurer (`export_presets.cfg` absent), puis à valider sur chaque appareil cible.

## Contributions

1. Travaillez sur une branche dédiée. La refonte avance sur `codex/refonte-hors-ligne`.
2. Ne supprimez pas une fonction du client Pygame avant que son équivalent Godot soit validé.
3. Pas de service cloud pour les règles, l'IA ou la sauvegarde.
4. Mettez à jour `CHANGELOG.md` et la documentation concernée.
