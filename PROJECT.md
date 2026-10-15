# Project: Échecs P2P Pro — Modern AI Personas, Stockfish UCI Calibration, Coach Mode & Tactile Polish

## Architecture
- **Framework**: Python 3.12 + Pygame 2.6.1 + python-chess 1.11.2
- **Rendu**: Immediate-mode rendering à 60 FPS avec design tactile Material 3, animations d'accélération et easing curves.
- **Moteur d'échecs**: Stockfish 19 (`stockfish_bin`) interfacé via `chess.engine.SimpleEngine` (protocole UCI).
- **Communication réseau**: P2P (UDP broadcast pour découverte LAN, TCP pour jeu en direct).
- **Packaging**: PyInstaller 6.22.3, MinGW-w64 pour installeur Windows, `dpkg-deb` pour package Linux Debian.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Personas Data & Models | Définition des 4 bots (Lucas 800, Éléonore 1400, Alexandre 2100, Le Monstre 3200+) avec avatars, styles et citations | M1 | ORIGINAL_REQUEST §R1 |
| 2 | UCI Elo Calibration | Calibration authentique Stockfish 19 (`UCI_LimitStrength`, `UCI_Elo` avec clamping 1320-3190 et fallback `Skill Level`) | M1 | ORIGINAL_REQUEST §R2 |
| 3 | Immersive Thinking Time | Maintien du temps de réflexion organique (1.5s - 3.0s) et statut d'analyse personnalisé par persona | M1 | ORIGINAL_REQUEST §R2 |
| 4 | Coach Mode Backend | Calcul asynchrone des suggestions/indices (`best_move`), gestion de l'annulation `Ctrl+Z` (recul 2 demi-coups) | M1 | ORIGINAL_REQUEST §R2 |
| 5 | AI Personas Gallery Modal | Nouvelle modale `AIPersonasModal` avec 4 cartes personas interactives, sélection visuelle sans console | M2 | ORIGINAL_REQUEST §R1 |
| 6 | Continuous Elo Slider UI | Curseur tactile continu (500 à 3200 Elo) avec synchronisation bidirectionnelle avec les personas | M2 | ORIGINAL_REQUEST §R1 |
| 7 | Training vs Ranked Toggle | Bascule visuelle entre Mode Entraînement (avec hints et rollback) et Mode Classé | M2 | ORIGINAL_REQUEST §R2 |
| 8 | Coach Hints Board Display | Rendu visuel de la flèche lumineuse d'indice (best move) et bandeau conseil du Coach | M2 | ORIGINAL_REQUEST §R2 |
| 9 | Tactile Drag-and-Drop Reticles | Réticules magnétiques de visée `⌜ ⌝ ⌞ ⌟` et anneau pulsant sur les cases de destination légales survolées | M3 | ORIGINAL_REQUEST §R3 |
| 10 | Animated Selection Cards | Animation d'élévation dynamique et ombrage au survol des cartes personas | M3 | ORIGINAL_REQUEST §R3 |
| 11 | Fluid Modal Transitions | Transition d'apparition fluide (fondu alpha `ease_out_cubic` + pop-in élastique `ease_out_back`) | M3 | ORIGINAL_REQUEST §R3 |
| 12 | 100% E2E Automated Tests | Suite de tests complète (Tiers 1-4) validant personas, calibrage Elo, hints, rollback, et compatibilité | M4 | ORIGINAL_REQUEST §R4 |
| 13 | Executable Recompilation | Recompilation du binaire autonome `dist/EchecsP2P` via PyInstaller | M4 | ORIGINAL_REQUEST §R4 |
| 14 | Distribution Package Updates | Mise à jour des paquets dans `distribution/` (.deb, .tar.gz portable, installeurs) | M4 | ORIGINAL_REQUEST §R4 |
| 15 | GitHub Commit & Sync | Commit propre des sources et synchronisation sur le dépôt GitHub `TheShellMaster/echecs-p2p-pro` | M4 | ORIGINAL_REQUEST §R4 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M0 | E2E Testing Suite | Architecture de test opaque-box (Tiers 1-4) et publication de `TEST_READY.md` | none | DONE |
| M1 | Engine Calibration & Coach Backend | Data models Personas, calibration UCI Stockfish 19, Coach hint analysis et rollback Ctrl+Z | none | DONE |
| M2 | Personas Gallery & Elo Slider UI | Modale `AIPersonasModal`, slider continu 500-3200, intégration écran de jeu, hints UI | M1 | DONE |
| M3 | Tactile Ergonomics & Polish | Réticules magnétiques survol drag-and-drop, cartes animées, transitions de modales | M2 | DONE |
| M4 | Final Integration, Rebuild & GitHub | 100% test pass, tests adversariaux Tier 5, PyInstaller build, packages distribution/, push GitHub | M0, M3 | IN_PROGRESS |

## Interface Contracts

### M1 Engine Calibration & Data Contracts
```python
# ai.py & constants.py

BOT_PERSONAS = {
    "lucas": {
        "id": "lucas",
        "name": "Lucas",
        "title": "Débutant",
        "elo": 800,
        "avatar_theme": "amber",
        "playstyle": "Attaque agressive & gaffes naïves",
        "quote": "J'adore avancer mes pions et attaquer sans attendre !",
        "uci_limit_strength": True,
        "uci_elo": 1320,  # Clamped to Stockfish 19 min (1320)
        "skill_level": 1,
        "depth": 4,
        "time": 0.3
    },
    "eleonore": {
        "id": "eleonore",
        "name": "Éléonore",
        "title": "Joueuse de Club",
        "elo": 1400,
        "avatar_theme": "emerald",
        "playstyle": "Jeu positionnel & développement solide",
        "quote": "Une structure de pions solide vaut mieux qu'une attaque précipitée.",
        "uci_limit_strength": True,
        "uci_elo": 1400,
        "skill_level": 10,
        "depth": 10,
        "time": 0.8
    },
    "alexandre": {
        "id": "alexandre",
        "name": "Alexandre",
        "title": "Maître National",
        "elo": 2100,
        "avatar_theme": "indigo",
        "playstyle": "Maîtrise tactique & calcul profond",
        "quote": "Chaque imprécision tactique scellera votre destin.",
        "uci_limit_strength": True,
        "uci_elo": 2100,
        "skill_level": 18,
        "depth": 16,
        "time": 1.2
    },
    "monster": {
        "id": "monster",
        "name": "Le Monstre Stockfish 19",
        "title": "Grand Maître Surhumain",
        "elo": 3200,
        "avatar_theme": "rose",
        "playstyle": "Calcul NNUE impitoyable & jeu parfait",
        "quote": "0.00 ou Mat forcé. Le calcul pur ne ment jamais.",
        "uci_limit_strength": False,
        "uci_elo": 3190,
        "skill_level": 20,
        "depth": 22,
        "time": 1.8
    }
}

class ChessAI:
    def configure_elo(self, elo: int, persona_id: str | None = None) -> dict: ...
    def get_hint_async(self, board: chess.Board, callback: callable) -> None: ...
    def cancel_ongoing_task(self) -> None: ...
```

### M1 ↔ M2 GameApp Integration
```python
# main.py
class GameApp:
    training_mode: bool  # True: suggestions and Ctrl+Z enabled; False: ranked
    coach_hint_move: chess.Move | None
    selected_persona: dict
    selected_elo: int
    def handle_undo_move(self) -> bool: ...  # Ctrl+Z rollback
    def request_coach_hint(self) -> None: ... # Triggers get_hint_async
```

### M2 ↔ M3 UI Components
```python
# modals.py
class AIPersonasModal:
    selected_persona: dict
    selected_elo: int
    training_mode: bool
    selected_color: chess.Color | str
    selected_time: int | None
    # Backward-compatible properties for test_app.py:
    selected_diff: int
```

## Code Layout
- `constants.py`: Couleurs Material 3, thèmes échiquier, dimensions, définitions personas.
- `ai.py`: Gestionnaire Stockfish, protocole UCI (`UCI_LimitStrength`, `UCI_Elo`), calibration Elo, analyse d'indices.
- `ui.py`: Rendu échiquier 3D, réticules magnétiques de survol `draw_hover_reticle`, boutons tactiles, flèches d'indice.
- `modals.py`: `AIPersonasModal` avec cartes animées, slider Elo continu, et sélecteur de mode.
- `animations.py`: Easing curves, transitions de modales (`ModalTransition`), interpolation de cartes.
- `main.py`: Contrôleur principal Pygame, raccourci `Ctrl+Z`, intégration barre latérale et boucles de drag-and-drop.
- `tests/`: Suites de tests unitaires et E2E (passent avec `python3.12 -m pytest -v`).
- `distribution/`: Exécutables et paquets déployables (.deb, .tar.gz, .exe).
