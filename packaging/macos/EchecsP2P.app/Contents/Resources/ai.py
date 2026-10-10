import chess
import chess.engine
import shutil
import threading
import os
import sys
import random
import time
from constants import resource_path, BASE_DIR

DIFFICULTY_PRESETS = {
    1: {"name": "Débutant (800 Elo)", "skill": 1, "time": 0.3, "depth": 4},
    2: {"name": "Intermédiaire (1500 Elo)", "skill": 7, "time": 0.6, "depth": 8},
    3: {"name": "Avancé (2200 Elo)", "skill": 14, "time": 1.0, "depth": 14},
    4: {"name": "Grand Maître - Monstre (3600+ Elo)", "skill": 20, "time": 1.8, "depth": 22}
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

    def set_difficulty(self, diff_level):
        self.difficulty = diff_level
        preset = DIFFICULTY_PRESETS.get(diff_level, DIFFICULTY_PRESETS[4])
        if self.engine:
            try:
                self.engine.configure({"Skill Level": preset["skill"]})
            except Exception:
                pass

    def start(self, diff_level=None):
        self.close()  # Cleanly quit any existing subprocess before launching new one
        if diff_level:
            self.difficulty = diff_level
        preset = DIFFICULTY_PRESETS.get(self.difficulty, DIFFICULTY_PRESETS[4])
        
        if self.engine_path:
            try:
                self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
                self.engine.configure({"Skill Level": preset["skill"]})
                self.engine_name = f"Stockfish 19 ({preset['name']})"
                self.is_monster = True
                return True
            except Exception as e:
                print(f"Stockfish execution failed: {e}")
                self.engine = None

        self.engine_name = f"Moteur Python ({preset['name']})"
        self.is_monster = False
        return True

    def ensure_engine(self):
        if self.engine is None and self.engine_path:
            with self.engine_lock:
                if self.engine is None and self.engine_path:
                    try:
                        self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
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

    def get_move_async(self, board, callback):
        board_copy = board.copy()
        preset = DIFFICULTY_PRESETS.get(self.difficulty, DIFFICULTY_PRESETS[4])
        thinking_delay = compute_thinking_pace(board_copy, self.difficulty)
        start_time = time.time()
        
        def _compute():
            move = None
            try:
                if self.engine:
                    engine_time = min(preset["time"], max(0.2, thinking_delay - 0.2))
                    if self.difficulty == 4:
                        limit = chess.engine.Limit(time=engine_time, depth=preset.get("depth", 22))
                    else:
                        limit = chess.engine.Limit(time=engine_time)
                    with self.engine_lock:
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
                    
            # Enforce humanized thinking pace so AI moves are NEVER instantaneous
            elapsed = time.time() - start_time
            sleep_needed = thinking_delay - elapsed
            if sleep_needed > 0:
                time.sleep(sleep_needed)
                
            callback(move)
                    
        threading.Thread(target=_compute, daemon=True).start()

    def close(self):
        with self.engine_lock:
            if self.engine:
                try:
                    self.engine.quit()
                except Exception:
                    pass
                self.engine = None
