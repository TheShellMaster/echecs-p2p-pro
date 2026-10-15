import chess
import chess.engine
import shutil
import threading
import os
import sys
import random
import time
from constants import resource_path, BASE_DIR, BOT_PERSONAS

DIFFICULTY_PRESETS = {
    1: {"name": "Débutant (800 Elo)", "skill": 1, "time": 0.3, "depth": 4, "persona_id": "lucas", "elo": 800},
    2: {"name": "Intermédiaire (1400 Elo)", "skill": 10, "time": 0.8, "depth": 10, "persona_id": "eleonore", "elo": 1400},
    3: {"name": "Avancé (2100 Elo)", "skill": 18, "time": 1.2, "depth": 16, "persona_id": "alexandre", "elo": 2100},
    4: {"name": "Grand Maître - Monstre (3200+ Elo)", "skill": 20, "time": 1.8, "depth": 22, "persona_id": "monster", "elo": 3200}
}

def compute_thinking_pace(board, difficulty=4):
    """
    Computes a humanized, immersive thinking duration strictly between 1.5s and 3.0s.
    Adjusts dynamically based on board complexity (remaining pieces, legal moves, check)
    and difficulty level with organic variance.
    """
    base_map = {1: 1.55, 2: 1.80, 3: 2.10, 4: 2.35}
    pace = base_map.get(difficulty, 2.25)

    # Complexity factor: pieces remaining
    pieces_count = len(board.piece_map())
    if 16 <= pieces_count <= 28:
        pace += 0.25  # Middlegame calculations
    elif pieces_count > 28:
        pace += 0.10  # Opening variations
    else:
        pace -= 0.10  # Technical endgame

    # Branching factor: legal moves count
    legal_count = board.legal_moves.count()
    if legal_count > 30:
        pace += 0.20
    elif legal_count > 20:
        pace += 0.10
    elif legal_count <= 6:
        pace -= 0.15

    # Check status
    if board.is_check():
        pace += 0.10

    # Natural organic variance (+/- 0.20s)
    variance = random.uniform(-0.15, 0.20)
    total = pace + variance

    # Strict clamping between 1.5s and 3.0s
    return max(1.5, min(3.0, round(total, 2)))

def get_stockfish_path():
    candidates = [
        resource_path("stockfish_bin"),
        resource_path("stockfish.exe"),
        resource_path("stockfish"),
        os.path.join(BASE_DIR, "stockfish_bin"),
        os.path.join(BASE_DIR, "stockfish.exe"),
        os.path.join(BASE_DIR, "stockfish"),
        "./stockfish_bin",
        "./stockfish.exe",
        "./stockfish",
        shutil.which("stockfish"),
        shutil.which("stockfish.exe"),
        "/usr/games/stockfish"
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            try:
                os.chmod(c, 0o755)
            except Exception:
                pass
            if os.access(c, os.X_OK) or c.endswith(".exe"):
                return c
    return None

class ChessAI:
    def __init__(self, difficulty=4):
        self.difficulty = difficulty
        self.engine_path = get_stockfish_path()
        self.engine = None
        self.engine_name = "Stockfish 19" if self.engine_path else "Moteur Intégré"
        self.is_monster = bool(self.engine_path)
        self.engine_lock = threading.Lock()
        self._current_cancel_event = None
        self._current_task_thread = None
        self.current_elo = 3200
        self.current_persona_id = "monster"
        self.current_config = None

        # Calibrate initial Elo configuration matching difficulty
        if self.difficulty in DIFFICULTY_PRESETS:
            preset = DIFFICULTY_PRESETS[self.difficulty]
            self.configure_elo(preset["elo"], persona_id=preset.get("persona_id"))
        else:
            self.configure_elo(3200, persona_id="monster")

    def configure_elo(self, elo: int, persona_id: str | None = None) -> dict:
        """
        Calibrate Stockfish 19 according to the official UCI protocol:
        - Stockfish 19 UCI_Elo requires min 1320 and max 3190.
        - For Elo >= 3200: configure {"UCI_LimitStrength": False, "Skill Level": 20}.
        - For 1320 <= Elo < 3200: configure {"UCI_LimitStrength": True, "UCI_Elo": elo}.
        - For Elo < 1320 (e.g. 500-1319): clamp UCI_Elo to 1320 with {"UCI_LimitStrength": True, "UCI_Elo": 1320},
          and scale "Skill Level" (0 to 5) with limited search depth (4-5) to genuinely reproduce
          human beginner play without crashing.
        """
        persona = None
        if persona_id and persona_id in BOT_PERSONAS:
            persona = BOT_PERSONAS[persona_id]
        elif persona_id is None:
            # Check if elo matches a registered persona
            for pid, pdata in BOT_PERSONAS.items():
                if pdata["elo"] == elo:
                    persona = pdata
                    persona_id = pid
                    break

        if persona is not None:
            elo = persona["elo"]
            name = persona["name"]
            depth = persona["depth"]
            search_time = persona["time"]
            skill_level = persona.get("skill_level", 20)
            if persona["uci_limit_strength"]:
                uci_config = {
                    "UCI_LimitStrength": True,
                    "UCI_Elo": persona["uci_elo"]
                }
                if persona["elo"] < 1320 or "skill_level" in persona:
                    uci_config["Skill Level"] = skill_level
            else:
                uci_config = {
                    "UCI_LimitStrength": False,
                    "Skill Level": 20
                }
            diff_map = {"lucas": 1, "eleonore": 2, "alexandre": 3, "monster": 4}
            diff_level = diff_map.get(persona_id, 4)
        else:
            # Continuous Elo calibration (e.g. 500 to 3200+)
            elo = int(elo)
            if elo >= 3200:
                uci_config = {"UCI_LimitStrength": False, "Skill Level": 20}
                skill_level = 20
                depth = 22
                search_time = 1.8
                diff_level = 4
                name = f"Niveau {elo} Elo"
            elif 1320 <= elo < 3200:
                clamped_uci_elo = min(3190, max(1320, elo))
                uci_config = {"UCI_LimitStrength": True, "UCI_Elo": clamped_uci_elo}
                if elo <= 2100:
                    fraction = (elo - 1320) / (2100 - 1320) if elo > 1320 else 0.0
                    skill_level = int(round(10 + fraction * (18 - 10)))
                else:
                    fraction = (elo - 2100) / (3190 - 2100) if elo < 3190 else 1.0
                    skill_level = int(round(18 + fraction * (20 - 18)))
                depth = int(round(10 + ((elo - 1320) / (3200 - 1320)) * (22 - 10)))
                search_time = round(0.8 + ((elo - 1320) / (3200 - 1320)) * (1.8 - 0.8), 2)
                diff_level = 2 if elo < 1800 else 3
                name = f"Niveau {elo} Elo"
            else:
                # Elo < 1320: clamp UCI_Elo to 1320, scale Skill Level (0 to 5), depth (4 to 5)
                fraction = max(0.0, min(1.0, (elo - 500) / (1320 - 500)))
                skill_level = max(0, min(5, int(round(fraction * 5))))
                uci_config = {
                    "UCI_LimitStrength": True,
                    "UCI_Elo": 1320,
                    "Skill Level": skill_level
                }
                depth = 4 if elo < 1000 else 5
                search_time = round(0.3 + fraction * (0.6 - 0.3), 2)
                diff_level = 1
                name = f"Niveau {elo} Elo"

        config_dict = {
            "elo": elo,
            "persona_id": persona_id,
            "name": name,
            "UCI_LimitStrength": uci_config.get("UCI_LimitStrength", False),
            "Skill Level": uci_config.get("Skill Level", skill_level),
            "depth": depth,
            "time": search_time,
            "skill_level": skill_level,
            "uci_options": uci_config,
        }
        if "UCI_Elo" in uci_config:
            config_dict["UCI_Elo"] = uci_config["UCI_Elo"]

        self.current_elo = elo
        self.current_persona_id = persona_id
        self.difficulty = diff_level
        self.current_config = config_dict

        if self.engine_path:
            self.engine_name = f"Stockfish 19 ({name})"
        else:
            self.engine_name = f"Moteur Python ({name})"

        if self.engine:
            try:
                with self.engine_lock:
                    self.engine.configure(uci_config)
            except Exception as e:
                print(f"Stockfish configure failed: {e}")

        return self.current_config

    def set_difficulty(self, diff_level):
        if isinstance(diff_level, str) and diff_level in BOT_PERSONAS:
            self.configure_elo(BOT_PERSONAS[diff_level]["elo"], persona_id=diff_level)
        elif isinstance(diff_level, int) and diff_level in [1, 2, 3, 4]:
            p_ids = ["lucas", "eleonore", "alexandre", "monster"]
            p_id = p_ids[diff_level - 1]
            self.configure_elo(BOT_PERSONAS[p_id]["elo"], persona_id=p_id)
        elif isinstance(diff_level, int) and diff_level >= 500:
            self.configure_elo(diff_level)
        else:
            self.difficulty = diff_level
            preset = DIFFICULTY_PRESETS.get(diff_level, DIFFICULTY_PRESETS[4])
            if self.engine:
                try:
                    with self.engine_lock:
                        self.engine.configure({"Skill Level": preset["skill"]})
                except Exception:
                    pass

    def start(self, diff_level=None):
        self.close()  # Cleanly quit any existing subprocess before launching new one
        if diff_level is not None:
            if isinstance(diff_level, str) and diff_level in BOT_PERSONAS:
                self.configure_elo(BOT_PERSONAS[diff_level]["elo"], persona_id=diff_level)
            elif isinstance(diff_level, int) and diff_level in [1, 2, 3, 4]:
                p_ids = ["lucas", "eleonore", "alexandre", "monster"]
                p_id = p_ids[diff_level - 1]
                self.configure_elo(BOT_PERSONAS[p_id]["elo"], persona_id=p_id)
            elif isinstance(diff_level, int) and diff_level >= 500:
                self.configure_elo(diff_level)
            else:
                self.set_difficulty(diff_level)
        elif self.current_config is None:
            self.configure_elo(3200, persona_id="monster")

        config = self.current_config or {}
        uci_opts = config.get("uci_options", {"Skill Level": 20})
        name = config.get("name", "Grand Maître - Monstre")

        if self.engine_path:
            try:
                self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
                self.engine.configure(uci_opts)
                self.engine_name = f"Stockfish 19 ({name})"
                self.is_monster = True
                return True
            except Exception as e:
                print(f"Stockfish execution failed: {e}")
                self.engine = None

        self.engine_name = f"Moteur Python ({name})"
        self.is_monster = False
        return True

    def ensure_engine(self):
        if self.engine is None and self.engine_path:
            with self.engine_lock:
                if self.engine is None and self.engine_path:
                    try:
                        self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
                        if self.current_config and "uci_options" in self.current_config:
                            self.engine.configure(self.current_config["uci_options"])
                        else:
                            preset = DIFFICULTY_PRESETS.get(self.difficulty, DIFFICULTY_PRESETS[4])
                            self.engine.configure({"Skill Level": preset["skill"]})
                        self.is_monster = True
                    except Exception as e:
                        print(f"Stockfish execution failed: {e}")
                        self.engine = None

    def _heuristic_eval(self, board):
        piece_vals = {
            chess.PAWN: 100,
            chess.KNIGHT: 310,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 0
        }
        score = 0
        for sq, piece in board.piece_map().items():
            val = piece_vals.get(piece.piece_type, 0)
            score += val if piece.color == chess.WHITE else -val
        return score

    def evaluate_board_sync(self, board):
        board_copy = board.copy()
        if board_copy.is_checkmate():
            if board_copy.turn == chess.WHITE:
                return -10000, "-M0"
            else:
                return 10000, "+M0"
        if board_copy.is_stalemate() or board_copy.is_insufficient_material():
            return 0, "0.0"

        score_cp = 0
        score_text = "0.0"
        engine_used = False

        if self.engine is None and self.engine_path:
            self.ensure_engine()

        if self.engine and self.engine_lock.acquire(timeout=0.15):
            try:
                info = self.engine.analyse(board_copy, chess.engine.Limit(time=0.06, depth=10))
                sc = info.get("score")
                if sc:
                    w_sc = sc.white()
                    if w_sc.is_mate():
                        m = w_sc.mate()
                        score_cp = 10000 if m > 0 else -10000
                        score_text = f"M{abs(m)}" if m > 0 else f"-M{abs(m)}"
                    else:
                        cp = w_sc.score()
                        score_cp = 0 if cp is None else cp
                        score_text = f"{score_cp/100:+.1f}" if score_cp != 0 else "0.0"
                    engine_used = True
            except Exception:
                pass
            finally:
                self.engine_lock.release()

        if not engine_used:
            score_cp = self._heuristic_eval(board_copy)
            score_text = f"{score_cp/100:+.1f}" if score_cp != 0 else "0.0"

        return score_cp, score_text

    def evaluate_board_async(self, board, callback):
        board_copy = board.copy()
        def _run():
            cp, txt = self.evaluate_board_sync(board_copy)
            callback(cp, txt)
        threading.Thread(target=_run, daemon=True).start()

    def cancel_ongoing_task(self):
        """Cleanly cancels background thinking / hint calculation."""
        if hasattr(self, "_current_cancel_event") and self._current_cancel_event is not None:
            self._current_cancel_event.set()

    def get_hint_async(self, board, callback):
        """
        Asynchronously analyzes the board using Stockfish 19 and calls callback(best_move, info).
        Cleanly cancellable via cancel_ongoing_task().
        """
        self.cancel_ongoing_task()
        cancel_evt = threading.Event()
        self._current_cancel_event = cancel_evt
        board_copy = board.copy()

        def _compute_hint():
            if cancel_evt.is_set():
                return
            best_move = None
            info = {}
            try:
                if self.engine is None and self.engine_path:
                    self.ensure_engine()
                if self.engine:
                    with self.engine_lock:
                        if not cancel_evt.is_set():
                            info = self.engine.analyse(
                                board_copy,
                                chess.engine.Limit(time=0.25, depth=12)
                            )
                            pv = info.get("pv", [None])
                            best_move = pv[0] if pv else None
                else:
                    legal = list(board_copy.legal_moves)
                    if legal:
                        best_move = legal[0]
                        info = {"pv": [best_move]}
            except Exception as e:
                print(f"Hint calculation error: {e}")
                legal = list(board_copy.legal_moves)
                if legal:
                    best_move = legal[0]
                    info = {"pv": [best_move]}

            if not cancel_evt.is_set():
                callback(best_move, info)

        t = threading.Thread(target=_compute_hint, daemon=True)
        self._current_task_thread = t
        t.start()

    def get_move_async(self, board, callback):
        self.cancel_ongoing_task()
        cancel_evt = threading.Event()
        self._current_cancel_event = cancel_evt
        board_copy = board.copy()
        preset = DIFFICULTY_PRESETS.get(self.difficulty, DIFFICULTY_PRESETS[4])
        thinking_delay = compute_thinking_pace(board_copy, self.difficulty)
        start_time = time.time()

        def _compute():
            if cancel_evt.is_set():
                return
            move = None
            try:
                if self.engine:
                    config = self.current_config or {}
                    search_time = config.get("time", preset["time"])
                    search_depth = config.get("depth", preset.get("depth"))
                    engine_time = min(search_time, max(0.2, thinking_delay - 0.2))
                    if search_depth is not None:
                        limit = chess.engine.Limit(time=engine_time, depth=search_depth)
                    else:
                        limit = chess.engine.Limit(time=engine_time)
                    with self.engine_lock:
                        if not cancel_evt.is_set():
                            res = self.engine.play(board_copy, limit)
                            move = res.move
                else:
                    # Fallback fast heuristic
                    legal = list(board_copy.legal_moves)
                    if legal:
                        captures = [m for m in legal if board_copy.is_capture(m)]
                        move = random.choice(captures) if captures and random.random() < 0.7 else random.choice(legal)
            except Exception as e:
                print(f"AI computing error: {e}")
                legal = list(board_copy.legal_moves)
                if legal:
                    move = random.choice(legal)

            if cancel_evt.is_set():
                return

            # Enforce humanized thinking pace so AI moves are NEVER instantaneous
            elapsed = time.time() - start_time
            sleep_needed = thinking_delay - elapsed
            if sleep_needed > 0:
                cancel_evt.wait(timeout=sleep_needed)

            if not cancel_evt.is_set():
                callback(move)

        t = threading.Thread(target=_compute, daemon=True)
        self._current_task_thread = t
        t.start()

    def close(self):
        self.cancel_ongoing_task()
        with self.engine_lock:
            if self.engine:
                try:
                    self.engine.quit()
                except Exception:
                    pass
                self.engine = None
