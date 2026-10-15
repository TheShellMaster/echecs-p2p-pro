# E2E Test Infra: Échecs P2P Pro — AI Personas, Engine Calibration & Coach Mode

## Test Philosophy
- Opaque-box, requirement-driven verification directly mapped to `ORIGINAL_REQUEST.md`.
- No reliance on mock objects for Stockfish: testing executes against real Stockfish 19 (`stockfish_bin`).
- Methodology: Category-Partition + Boundary Value Analysis + Pairwise Combinatorial + Real-World Workload Testing.

## Test Runner
- Command: `python3.12 -m pytest -v`
- Headless environment config: `SDL_VIDEODRIVER=dummy`, `SDL_AUDIODRIVER=dummy`
- Expected: 100% test pass rate with exit code 0.

## Feature Inventory Coverage
| # | Feature | Source | Tier 1 (Isolation) | Tier 2 (Boundary) | Tier 3 (Cross-Feature) | Tier 4 (Scenario) |
|---|---------|--------|:------------------:|:-----------------:|:----------------------:|:-----------------:|
| 1 | Personas Data Models | ORIGINAL_REQUEST §R1 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 2 | UCI Elo Calibration | ORIGINAL_REQUEST §R2 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 3 | Immersive Thinking Time | ORIGINAL_REQUEST §R2 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 4 | Coach Mode Backend (Undo/Hints) | ORIGINAL_REQUEST §R2 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 5 | AI Personas Gallery Modal | ORIGINAL_REQUEST §R1 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 6 | Continuous Elo Slider UI | ORIGINAL_REQUEST §R1 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 7 | Training vs Ranked Toggle | ORIGINAL_REQUEST §R2 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 8 | Coach Hints Board Display | ORIGINAL_REQUEST §R2 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 9 | Tactile Drag-and-Drop Reticles | ORIGINAL_REQUEST §R3 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 10 | Animated Selection Cards | ORIGINAL_REQUEST §R3 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 11 | Fluid Modal Transitions | ORIGINAL_REQUEST §R3 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 12 | 100% Automated Test Suite | ORIGINAL_REQUEST §R4 | ≥5 cases | ≥5 cases | ✓ | ✓ |
| 13 | Executable Recompilation | ORIGINAL_REQUEST §R4 | 1 case | 1 case | ✓ | ✓ |
| 14 | Distribution Packages | ORIGINAL_REQUEST §R4 | 1 case | 1 case | ✓ | ✓ |
| 15 | GitHub Commit & Sync | ORIGINAL_REQUEST §R4 | 1 case | 1 case | ✓ | ✓ |

## Test Case Tier Architecture
- **Tier 1 — Feature Coverage**: Verification of each persona (Lucas, Éléonore, Alexandre, Le Monstre), Elo slider values, hint generation, and undo mechanics.
- **Tier 2 — Boundary & Corner Cases**: Elo limits (500 min, 1319 edge, 1320 Stockfish min, 3190 Stockfish max, 3200+ GM), undo when board has 0 moves, 1 move, during AI turn; hint when game is over or in checkmate.
- **Tier 3 — Cross-Feature Combinations**: Switching persona then moving slider; requesting hint then doing Ctrl+Z; changing from training to ranked mode; drag-and-drop hover reticle over pinned piece square.
- **Tier 4 — Real-World Application Scenarios**:
  1. Full beginner game against Lucas with hint usage and two undos.
  2. Full club game against Éléonore with continuous slider adjusted to 1550 Elo.
  3. High-level blitz match against Alexandre (2100 Elo) in Ranked mode (no hints, no undo).
  4. Extreme challenge against Le Monstre (3200+ Elo) with analysis bar active and thinking pace 1.5-3.0s.
  5. Backwards-compatibility scenario verifying legacy modal interface calls (`selected_diff`, `selected_time`).
