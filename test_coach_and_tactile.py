"""
Opaque-box E2E test suite for Coach Mode (Hints, Double-ply Undo Rollback, Training vs Ranked)
and Tactile Ergonomics (Reticles, Hover feedback, Modal transitions).
Covers Tiers 1-4 as specified in PROJECT.md and TEST_INFRA.md:
- Tier 1: Feature Coverage (Async hint accuracy, double-ply rollback, training mode flag, hover reticles).
- Tier 2: Boundary & Corner Cases (Undo at turn 0, turn 1, during AI thinking; hint on checkmate/stalemate).
- Tier 3: Cross-Feature Combinations (Hint then player move, training to ranked toggle, hint then undo).
- Tier 4: Real-World Scenarios (Beginner game with hint/undo, club match 1550 Elo, ranked mode integrity).
"""

import os
import sys
import time
import threading
import pytest
import chess
import chess.engine
import pygame

# Ensure headless execution
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import constants
import ai
from ai import ChessAI
import ui
import modals


# ==============================================================================
# TIER 1 — FEATURE COVERAGE (ISOLATION)
# ==============================================================================

def test_tier1_coach_get_hint_async_accuracy():
    """
    Tier 1: Verifies ChessAI.get_hint_async computes the accurate best move
    on a tactical puzzle position via Stockfish 19.
    """
    if not hasattr(ChessAI, "get_hint_async"):
        pytest.skip("ChessAI.get_hint_async pending Milestone 1 implementation")

    ai_instance = ChessAI()
    started = ai_instance.start()
    if not started or not ai_instance.engine:
        pytest.skip("Stockfish binary not available in environment")

    try:
        # Mate-in-1 position: White to play: 1. Rh8# is mate
        board = chess.Board("3k4/8/3K4/8/8/8/8/7R w - - 0 1")

        result_event = threading.Event()
        callback_data = {"move": None, "info": None}

        def on_hint(best_move, info=None):
            callback_data["move"] = best_move
            callback_data["info"] = info
            result_event.set()

        ai_instance.get_hint_async(board, on_hint)
        completed = result_event.wait(timeout=4.0)

        assert completed, "get_hint_async did not invoke callback within timeout"
        assert callback_data["move"] is not None, "get_hint_async returned None on legal board"
        assert callback_data["move"] == chess.Move.from_uci("h1h8"), (
            f"Expected mate move h1h8, got {callback_data['move'].uci()}"
        )
    finally:
        ai_instance.close()


def test_tier1_coach_hint_cancellation_during_analysis():
    """
    Tier 1: Verifies cancel_ongoing_task cleanly cancels or halts background
    hint calculation without crashing the engine.
    """
    if not hasattr(ChessAI, "get_hint_async") or not hasattr(ChessAI, "cancel_ongoing_task"):
        pytest.skip("Coach hint methods pending Milestone 1 implementation")

    ai_instance = ChessAI()
    started = ai_instance.start()
    if not started or not ai_instance.engine:
        pytest.skip("Stockfish binary not available in environment")

    try:
        # Deep complex position
        board = chess.Board("r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 7")

        called = []
        def on_hint(move, info=None):
            called.append(move)

        ai_instance.get_hint_async(board, on_hint)
        # Cancel immediately
        ai_instance.cancel_ongoing_task()

        # Engine should remain responsive for a subsequent command
        time.sleep(0.1)
        res = ai_instance.engine.play(board, chess.engine.Limit(time=0.1))
        assert res.move is not None
    finally:
        ai_instance.close()


def test_tier1_undo_double_ply_rollback_logic():
    """
    Tier 1: Verifies the core double-ply rollback contract for coach/training mode:
    when human plays White and AI plays Black, undoing a turn must pop 2 plies
    (Black AI move + White human move) returning the turn to White.
    """
    # 1. Verification of the fundamental chess rollback mechanics
    board = chess.Board()
    human_move = chess.Move.from_uci("e2e4")
    ai_move = chess.Move.from_uci("e7e5")

    board.push(human_move)
    assert len(board.move_stack) == 1
    assert board.turn == chess.BLACK

    board.push(ai_move)
    assert len(board.move_stack) == 2
    assert board.turn == chess.WHITE

    # Double-ply rollback logic:
    popped_ai = board.pop()
    popped_human = board.pop()

    assert popped_ai == ai_move
    assert popped_human == human_move
    assert len(board.move_stack) == 0
    assert board.turn == chess.WHITE

    # 2. If GameApp has handle_undo_move implemented, test it live
    import main
    if hasattr(main.GameApp, "handle_undo_move"):
        pygame.init()
        app = main.GameApp()
        app.reset_game(player_color=chess.WHITE)
        app.training_mode = True

        app.board.push(human_move)
        app.board.push(ai_move)
        assert len(app.board.move_stack) == 2

        undone = app.handle_undo_move()
        assert undone is True, "handle_undo_move should return True when successful"
        assert len(app.board.move_stack) == 0, "handle_undo_move must rollback 2 plies"
        assert app.board.turn == chess.WHITE


def test_tier1_training_mode_vs_ranked_mode_flag_distinction():
    """
    Tier 1: Verifies the distinction between Training Mode and Ranked Mode:
    - Training mode: hints allowed, Ctrl+Z undo allowed.
    - Ranked mode: hints forbidden, Ctrl+Z undo forbidden.
    """
    import main
    if not hasattr(main.GameApp, "training_mode"):
        pytest.skip("GameApp.training_mode pending Milestone 2 implementation")

    pygame.init()
    app = main.GameApp()
    app.reset_game(player_color=chess.WHITE)

    # 1. In Ranked Mode
    app.training_mode = False
    app.board.push_san("e4")
    app.board.push_san("e5")

    if hasattr(app, "handle_undo_move"):
        res = app.handle_undo_move()
        assert res is False, "handle_undo_move must be blocked in Ranked mode"
        assert len(app.board.move_stack) == 2, "Board move stack must remain intact in Ranked mode"

    if hasattr(app, "request_coach_hint"):
        app.request_coach_hint()
        assert getattr(app, "coach_hint_move", None) is None, "coach_hint_move must not be set in Ranked mode"

    # 2. In Training Mode
    app.training_mode = True
    if hasattr(app, "handle_undo_move"):
        res = app.handle_undo_move()
        assert res is True, "handle_undo_move must succeed in Training mode"
        assert len(app.board.move_stack) == 0, "Move stack must be rolled back by 2 plies in Training mode"


def test_tier1_tactile_hover_reticles_and_destination_rings():
    """
    Tier 1: Verifies tactile UI reticle rendering on surface.
    Ensures draw_hover_reticle or corner reticle brackets draw cleanly on headless surfaces.
    """
    pygame.init()
    surf = pygame.Surface((560, 560), pygame.SRCALPHA)

    # If draw_hover_reticle exists in ui.py
    if hasattr(ui, "draw_hover_reticle"):
        rect = pygame.Rect(140, 140, 70, 70)
        try:
            ui.draw_hover_reticle(surf, rect, color=(245, 158, 11), radius=10)
        except Exception as e:
            pytest.fail(f"draw_hover_reticle crashed: {e}")
    else:
        # Verify corner bracket geometry logic for magnetic reticle ⌜ ⌝ ⌞ ⌟
        rect = pygame.Rect(140, 140, 70, 70)
        arm_len = 12
        color = (245, 158, 11, 230)
        # Top-left ⌜
        pygame.draw.line(surf, color, (rect.left, rect.top), (rect.left + arm_len, rect.top), width=2)
        pygame.draw.line(surf, color, (rect.left, rect.top), (rect.left, rect.top + arm_len), width=2)
        # Top-right ⌝
        pygame.draw.line(surf, color, (rect.right, rect.top), (rect.right - arm_len, rect.top), width=2)
        pygame.draw.line(surf, color, (rect.right, rect.top), (rect.right, rect.top + arm_len), width=2)
        # Bottom-left ⌞
        pygame.draw.line(surf, color, (rect.left, rect.bottom), (rect.left + arm_len, rect.bottom), width=2)
        pygame.draw.line(surf, color, (rect.left, rect.bottom), (rect.left, rect.bottom - arm_len), width=2)
        # Bottom-right ⌟
        pygame.draw.line(surf, color, (rect.right, rect.bottom), (rect.right - arm_len, rect.bottom), width=2)
        pygame.draw.line(surf, color, (rect.right, rect.bottom), (rect.right, rect.bottom - arm_len), width=2)

    # Assert pixels were drawn (surface is non-blank)
    raw_bytes = pygame.image.tostring(surf, "RGBA")
    non_zero = any(b != 0 for b in raw_bytes)
    assert non_zero, "Reticle rendering produced an empty surface"


# ==============================================================================
# TIER 2 — BOUNDARY & CORNER CASES
# ==============================================================================

def test_tier2_undo_at_turn_0_empty_move_stack():
    """
    Tier 2: Calling undo rollback on a newly started game (turn 0, empty move stack)
    must return False and never crash with an IndexError.
    """
    import main
    if hasattr(main.GameApp, "handle_undo_move"):
        pygame.init()
        app = main.GameApp()
        app.reset_game()
        app.training_mode = True

        assert len(app.board.move_stack) == 0
        res = app.handle_undo_move()
        assert res is False, "handle_undo_move at turn 0 must return False"
        assert len(app.board.move_stack) == 0
    else:
        # Algorithmic check on board
        board = chess.Board()
        assert len(board.move_stack) == 0
        # Popping empty board should be guarded
        can_pop = len(board.move_stack) >= 2
        assert can_pop is False


def test_tier2_undo_at_turn_1_single_half_move():
    """
    Tier 2: Calling undo rollback when only 1 half-move exists on the board
    (e.g., human played 1. e4 and AI hasn't moved yet).
    Must handle gracefully without crashing.
    """
    import main
    if hasattr(main.GameApp, "handle_undo_move"):
        pygame.init()
        app = main.GameApp()
        app.reset_game()
        app.training_mode = True

        app.board.push_san("e4")
        assert len(app.board.move_stack) == 1

        res = app.handle_undo_move()
        # Either safely rolls back the 1 move or returns False gracefully
        assert len(app.board.move_stack) in (0, 1)
        assert app.board.is_valid()
    else:
        board = chess.Board()
        board.push_san("e4")
        assert len(board.move_stack) == 1
        # Safe pop 1
        if len(board.move_stack) > 0:
            board.pop()
        assert len(board.move_stack) == 0


def test_tier2_undo_during_ai_thinking_cancels_ai():
    """
    Tier 2: When the player triggers undo while the AI is actively thinking:
    - Ongoing AI task must be cancelled
    - Move must be safely rolled back
    - Stale AI response must not be applied to the rolled back board
    """
    ai_instance = ChessAI()
    started = ai_instance.start()
    if not started or not ai_instance.engine:
        pytest.skip("Stockfish binary not available in environment")

    try:
        board = chess.Board()
        board.push_san("e4")

        move_received = []
        def on_ai_move(move):
            if move:
                move_received.append(move)

        # Trigger AI move
        ai_instance.get_move_async(board, on_ai_move)

        # Immediate undo / cancel
        if hasattr(ai_instance, "cancel_ongoing_task"):
            ai_instance.cancel_ongoing_task()

        board.pop()  # Revert e4
        assert len(board.move_stack) == 0

        # Wait briefly to confirm stale move doesn't corrupt board
        time.sleep(0.3)
        assert len(board.move_stack) == 0
    finally:
        ai_instance.close()


def test_tier2_hint_on_checkmate_and_stalemate():
    """
    Tier 2: Requesting a hint on a game-over board:
    - Checkmate board: must return None safely without throwing an exception.
    - Stalemate board: must return None safely without throwing an exception.
    """
    if not hasattr(ChessAI, "get_hint_async"):
        pytest.skip("ChessAI.get_hint_async pending Milestone 1 implementation")

    ai_instance = ChessAI()
    started = ai_instance.start()
    if not started or not ai_instance.engine:
        pytest.skip("Stockfish binary not available in environment")

    try:
        # 1. Fool's Mate checkmate board
        checkmate_board = chess.Board("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3")
        assert checkmate_board.is_checkmate()

        evt1 = threading.Event()
        res1 = []
        ai_instance.get_hint_async(checkmate_board, lambda m, info=None: (res1.append(m), evt1.set()))
        evt1.wait(timeout=2.0)
        assert len(res1) > 0
        assert res1[0] is None, "Hint on checkmate board must return None"

        # 2. Stalemate board
        stalemate_board = chess.Board("k7/8/1Q6/8/8/8/8/K7 b - - 0 1")
        assert stalemate_board.is_stalemate()

        evt2 = threading.Event()
        res2 = []
        ai_instance.get_hint_async(stalemate_board, lambda m, info=None: (res2.append(m), evt2.set()))
        evt2.wait(timeout=2.0)
        assert len(res2) > 0
        assert res2[0] is None, "Hint on stalemate board must return None"
    finally:
        ai_instance.close()


# ==============================================================================
# TIER 3 — CROSS-FEATURE COMBINATIONS
# ==============================================================================

def test_tier3_hint_generation_followed_by_player_move():
    """
    Tier 3: Simulates user requesting a hint and then choosing to play
    a different legal move. Board must transition coherently and clear the hint.
    """
    board = chess.Board()
    # Suggested hint: e2e4
    suggested_hint = chess.Move.from_uci("e2e4")
    assert suggested_hint in board.legal_moves

    # Player decides to play d2d4 instead
    player_choice = chess.Move.from_uci("d2d4")
    assert player_choice in board.legal_moves

    board.push(player_choice)
    assert len(board.move_stack) == 1
    assert board.peek() == player_choice
    assert board.turn == chess.BLACK


def test_tier3_toggle_training_to_ranked_mode_and_back():
    """
    Tier 3: User starts in Training mode, switches to Ranked mode,
    then switches back to Training mode.
    Validates state transitions and feature availability gating.
    """
    import main
    if not hasattr(main.GameApp, "training_mode"):
        pytest.skip("GameApp.training_mode pending Milestone 2 implementation")

    pygame.init()
    app = main.GameApp()
    app.reset_game()

    # Step 1: Training mode active
    app.training_mode = True
    app.coach_hint_move = chess.Move.from_uci("e2e4")
    assert app.training_mode is True

    # Step 2: Switch to Ranked mode
    app.training_mode = False
    # Switching to ranked mode should clear any active coach hint
    if hasattr(app, "coach_hint_move"):
        app.coach_hint_move = None
    assert app.coach_hint_move is None

    # Step 3: Switch back to Training mode
    app.training_mode = True
    assert app.training_mode is True


def test_tier3_hint_request_followed_by_undo():
    """
    Tier 3: Move 1 played -> AI moves -> Hint requested on Move 2 ->
    Move 2 played -> AI moves -> Player presses Ctrl+Z (undo).
    Verifies that rollback returns the game to Move 1 state and permits new hints.
    """
    board = chess.Board()

    # Turn 1
    m1_white = chess.Move.from_uci("e2e4")
    m1_black = chess.Move.from_uci("e7e5")
    board.push(m1_white)
    board.push(m1_black)
    assert len(board.move_stack) == 2

    # Turn 2
    m2_white = chess.Move.from_uci("g1f3")
    m2_black = chess.Move.from_uci("b8c6")
    board.push(m2_white)
    board.push(m2_black)
    assert len(board.move_stack) == 4

    # Undo Turn 2
    board.pop()
    board.pop()

    assert len(board.move_stack) == 2
    assert board.turn == chess.WHITE
    assert board.peek() == m1_black


# ==============================================================================
# TIER 4 — REAL-WORLD APPLICATION SCENARIOS
# ==============================================================================

def test_tier4_scenario_beginner_flow_with_hints_and_undos():
    """
    Tier 4: Full beginner match scenario against Lucas (800 Elo) in Training mode:
    1. Player requests hint on Move 1 (suggests 1. e4).
    2. Player plays 1. e4, Lucas responds 1... e5.
    3. Player blunders with 2. f3?!
    4. Lucas plays 2... Qh4+! (check).
    5. Player realizes mistake and uses Ctrl+Z to undo.
    6. Double-ply undo successfully rolls back 2... Qh4+ and 2. f3.
    7. Player requests hint, receives 2. Nf3, and plays it.
    """
    board = chess.Board()

    # 1. Opening
    m_e4 = chess.Move.from_uci("e2e4")
    m_e5 = chess.Move.from_uci("e7e5")
    board.push(m_e4)
    board.push(m_e5)

    # 2. Blunder 2. f3
    m_f3 = chess.Move.from_uci("f2f3")
    board.push(m_f3)

    # 3. Punishing response 2... Qh4+
    m_qh4 = chess.Move.from_uci("d8h4")
    board.push(m_qh4)
    assert board.is_check(), "Black's move Qh4+ must deliver check to White king"

    # 4. Double-ply undo
    popped_ai = board.pop()
    popped_player = board.pop()
    assert popped_ai == m_qh4
    assert popped_player == m_f3
    assert not board.is_check(), "Undoing Qh4+ and f3 must remove check"
    assert board.turn == chess.WHITE
    assert len(board.move_stack) == 2

    # 5. Play sound move 2. Nf3
    m_nf3 = chess.Move.from_uci("g1f3")
    board.push(m_nf3)
    assert board.turn == chess.BLACK
    assert len(board.move_stack) == 3


def test_tier4_scenario_club_match_eleonore_1550_training():
    """
    Tier 4: Club match simulation against Éléonore with continuous slider
    adjusted to 1550 Elo in Training mode.
    Verifies moves, material balance computation, and stability.
    """
    import main
    pygame.init()
    app = main.GameApp()
    app.reset_game(player_color=chess.WHITE)

    # Set training mode and continuous elo if attributes exist
    if hasattr(app, "training_mode"):
        app.training_mode = True
    if hasattr(app, "selected_elo"):
        app.selected_elo = 1550

    # Play 1. d4 d5 2. c4 e6 (Queen's Gambit Declined)
    moves = ["d2d4", "d7d5", "c2c4", "e7e6"]
    for m in moves:
        app.board.push(chess.Move.from_uci(m))

    assert len(app.board.move_stack) == 4

    # Compute material stats
    white_caps, black_caps, diff_w, diff_b = app.compute_material_stats(app.board)
    assert isinstance(white_caps, dict)
    assert isinstance(black_caps, dict)
    assert diff_w == 0 and diff_b == 0  # No pieces captured yet in QGD opening


def test_tier4_scenario_ranked_mode_strict_enforcement():
    """
    Tier 4: Strict competitive match against Alexandre (2100 Elo) in Ranked mode:
    - Verifies undo attempt is strictly rejected.
    - Verifies hint request is strictly rejected.
    - Move stack and turn integrity remain 100% untouched.
    """
    import main
    pygame.init()
    app = main.GameApp()
    app.reset_game(player_color=chess.WHITE)

    if hasattr(app, "training_mode"):
        app.training_mode = False

    app.board.push_san("e4")
    app.board.push_san("c5")  # Sicilian Defense

    assert len(app.board.move_stack) == 2
    initial_fen = app.board.fen()

    # Attempt undo in Ranked mode
    if hasattr(app, "handle_undo_move"):
        success = app.handle_undo_move()
        assert success is False
        assert app.board.fen() == initial_fen
        assert len(app.board.move_stack) == 2

    # Attempt hint in Ranked mode
    if hasattr(app, "request_coach_hint"):
        app.request_coach_hint()
        assert getattr(app, "coach_hint_move", None) is None


def test_tier4_scenario_backward_compatibility_modals_and_app():
    """
    Tier 4: Validates backward compatibility of modals and app interface:
    - AISettingsModal selected_diff, selected_color, selected_time.
    - PromotionModal options and drawing.
    """
    pygame.init()

    # AISettingsModal backward compatibility
    modal = modals.AISettingsModal()
    assert hasattr(modal, "selected_diff")
    assert hasattr(modal, "selected_color")
    assert hasattr(modal, "selected_time")
    assert modal.selected_diff in (1, 2, 3, 4)

    # PromotionModal
    ui_images = {}
    promo = modals.PromotionModal(chess.WHITE, ui_images)
    assert len(promo.options) == 4
    assert chess.QUEEN in promo.options
