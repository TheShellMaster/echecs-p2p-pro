# Repository guidance

## Two clients, incremental migration

- `PRODUCT_REBOOT.md` defines the Godot migration and offline requirements. Preserve the root Python/Pygame client as the functional reference until feature parity and target-device validation. Rules, AI, and saves must work without accounts or cloud services; proximity play means LAN, not proven cross-platform Wi-Fi Direct.
- Godot uses `godot/project.godot` (4.4, GL Compatibility). The real startup path is `app.tscn` → `app.gd` → `ui/` screens, **not** `main.tscn`. The router owns the LAN transport; `core/chess_game.gd` owns rules independently of UI, networking, clocks, and AI.
- Godot square indices run **a8 = 0 → h1 = 63**, unlike python-chess (**a1 = 0**). Pieces are FEN letters, uppercase for White. See `godot/core/README.md` for move/state contracts, including claimable versus automatic draws.
- Legacy startup is `main.py` / `GameApp`; it coordinates python-chess, Pygame UI, `ai.py` (local UCI engine), and `network.py` (UDP discovery/TCP play). Python tests do not exercise the Godot client.

## Run and verify

Commands below run from the repository root:

```sh
# Python 3.12 environment: runtime plus test dependencies
python3.12 -m pip install -r requirements.txt pytest psutil
python3.12 main.py

# Full legacy suite; tests live at the root, not in tests/
python3.12 -m pytest -v
# Focused suites or a single test
python3.12 -m pytest -v test_personas_and_calibration.py test_coach_and_tactile.py
python3.12 -m pytest -v test_personas_and_calibration.py::test_tier1_stockfish_uci_engine_calibration_live

# Godot client and independent rules verifier (requires Godot installed)
godot --path godot
godot --headless --path godot --script res://core/verify_chess_game.gd
```

- `requirements.txt` omits `pytest` and `psutil`; the adversarial suite imports both. Test modules set `SDL_VIDEODRIVER=dummy` and `SDL_AUDIODRIVER=dummy` themselves.
- Engine tests use real Stockfish. Some skip if unavailable, but the subprocess lifecycle test asserts a live engine. Supply a host-compatible executable: `ai.get_stockfish_path()` searches bundled/root `stockfish_bin`, `stockfish.exe`, `stockfish`, then PATH and `/usr/games/stockfish`. Engine binaries are gitignored; their presence locally does not imply a fresh clone includes them.
- Legacy network tests open real localhost sockets. The suite also includes timed AI waits and subprocess stress tests. Historical totals in `TEST_READY.md` are not current verification results.

## GUI and packaging constraints

- Follow `.gemini/rules/gui_desktop_invariants.md`: all user interaction stays in the GUI, critical assets must be local and validated/generated before runtime, and missing external engines require a working fallback. For Python resources use `constants.resource_path()` (`__file__` / PyInstaller `_MEIPASS`), not the working directory. Packaged releases need usable launch shortcuts and an actual launch check.
- Linux executable build: install PyInstaller separately, then run `python3.12 -m PyInstaller --clean -y EchecsP2P.spec`. The spec bundles `assets/` and requires root `stockfish_bin`; output is `dist/EchecsP2P`. `build_linux.sh` wraps this but can print success after a failed build, so check the direct command's exit status.
- `packaging/build_all_packages.py` is a generation script, not a cross-platform validation suite: it overwrites Windows installer sources, Android configuration, and macOS bundle copies. Edit root Python sources rather than `packaging/macos/.../Resources/` copies. Its Windows step packages an existing root `EchecsP2P.exe`; macOS still requires Python; Android only generates scaffolding, not an APK.
