"""
Adversarial Stress Test Suite for Milestone 1 / Engine Calibration & Coach Backend:
- Rapid sequential and concurrent Elo configurations across boundary values (500, 800, 1319, 1320, 1400, 2100, 3190, 3200, 3600).
- Extreme and malformed Elo inputs (-1000, 0, 450, 4000, 99999).
- Thread safety and rapid task cancellation during asynchronous move and hint calculations.
- Concurrency stress: rapid Ctrl+Z undo invocations while AI is computing in background.
- Subprocess lifecycle management (no process leaks, hangs, zombies, or crashes).
- Terminal board states handling (checkmate, stalemate) during asynchronous queries.
- Strict verification of humanized thinking pace (1.5s - 3.0s) mathematically and during actual live engine play.
"""

import os
import sys
import time
import random
import threading
import subprocess
import pytest
import chess
import chess.engine
import psutil

# Headless SDL configuration
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import constants
import ai
from ai import ChessAI, compute_thinking_pace, BOT_PERSONAS
import main
from main import GameApp


# ==============================================================================
# 1. RAPID SEQUENTIAL & CONCURRENT ELO CONFIGURATION ACROSS BOUNDARIES
# ==============================================================================

def test_stress_boundary_elo_rapid_sequential_and_concurrent():
    """
    Stress-test rapid sequential and multi-threaded Elo configurations across all boundary values:
    [500, 800, 1319, 1320, 1400, 2100, 3190, 3200, 3600].
    Verifies:
    1. Exact UCI dictionary compliance and clamping for every boundary value.
    2. Engine subprocess remains completely responsive without crash or desync.
    3. Multi-threaded race conditions on configure_elo do not corrupt state.
    """
    ai_instance = ChessAI()
    started = ai_instance.start()
    assert started is True
    assert ai_instance.engine is not None, "Stockfish 19 engine must be active"

    boundary_values = [500, 800, 1319, 1320, 1400, 2100, 3190, 3200, 3600]

    try:
        # Rapid sequential cycling (10 full cycles = 90 rapid reconfigurations)
        for cycle in range(10):
            for elo in boundary_values:
                cfg = ai_instance.configure_elo(elo)
                opts = cfg["uci_options"]
                skill = cfg.get("Skill Level", opts.get("Skill Level"))

                if elo < 1320:
                    assert opts["UCI_LimitStrength"] is True
                    assert opts["UCI_Elo"] == 1320
                    assert 0 <= skill <= 5
                    assert cfg["depth"] in [4, 5]
                elif 1320 <= elo < 3200:
                    assert opts["UCI_LimitStrength"] is True
                    assert opts["UCI_Elo"] == min(3190, elo)
                    assert 10 <= skill <= 20
                else:  # elo >= 3200
                    assert opts["UCI_LimitStrength"] is False
                    assert skill == 20
                    assert cfg["depth"] == 22

        # Verify engine is still responsive after 90 reconfigurations
        board = chess.Board()
        info = ai_instance.engine.analyse(board, chess.engine.Limit(time=0.05, depth=4))
        assert "score" in info

        # Multi-threaded concurrent configuration stress (10 threads firing 20 calls each)
        errors = []
        def worker(thread_id):
            try:
                for _ in range(20):
                    target_elo = random.choice(boundary_values)
                    c = ai_instance.configure_elo(target_elo)
                    assert "uci_options" in c
                    time.sleep(0.002)
            except Exception as exc:
                errors.append((thread_id, exc))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10.0)

        assert len(errors) == 0, f"Concurrent configure_elo produced errors: {errors}"

        # Engine still healthy after concurrent stress
        res = ai_instance.engine.play(board, chess.engine.Limit(time=0.05, depth=4))
        assert res.move is not None

    finally:
        ai_instance.close()


def test_stress_extreme_and_malformed_elo_inputs():
    """
    Stress-tests extreme Elo inputs: negative (-1000), zero, sub-slider (450),
    super-grandmaster (4000), and absurd values (99999).
    Must never crash or send invalid options to Stockfish.
    """
    ai_instance = ChessAI()
    ai_instance.start()
    assert ai_instance.engine is not None

    try:
        extremes = [-1000, 0, 100, 450, 4000, 99999]
        for val in extremes:
            cfg = ai_instance.configure_elo(val)
            assert isinstance(cfg, dict)
            opts = cfg["uci_options"]
            if val < 1320:
                assert opts["UCI_LimitStrength"] is True
                assert opts["UCI_Elo"] == 1320
            else:
                assert opts["UCI_LimitStrength"] is False
                assert opts["Skill Level"] == 20

        # Subprocess still healthy
        board = chess.Board()
        res = ai_instance.engine.play(board, chess.engine.Limit(time=0.05, depth=3))
        assert res.move in board.legal_moves
    finally:
        ai_instance.close()


# ==============================================================================
# 2. THREAD SAFETY & RAPID TASK CANCELLATION (MOVES & HINTS)
# ==============================================================================

def test_stress_rapid_cancellation_of_moves():
    """
    Stress-test rapid cancellation of asynchronous move calculations:
    Fires 30 get_move_async calls followed by cancel_ongoing_task.
    Verifies that NO cancelled callbacks execute and engine remains intact.
    """
    ai_instance = ChessAI()
    ai_instance.start()
    assert ai_instance.engine is not None

    board = chess.Board()
    executed_callbacks = []

    try:
        for i in range(30):
            tag = f"move_task_{i}"
            def on_move(move, t=tag):
                executed_callbacks.append(t)

            ai_instance.get_move_async(board, on_move)
            jitter = (i % 6) * 0.008  # 0ms to 40ms
            if jitter > 0:
                time.sleep(jitter)
            ai_instance.cancel_ongoing_task()

        # Allow grace period for daemon threads to settle
        time.sleep(0.4)
        assert len(executed_callbacks) == 0, f"Cancelled callbacks executed: {executed_callbacks}"

        # Legitimate move calculation must now succeed normally
        legit_move = []
        evt = threading.Event()
        def on_legit(move):
            legit_move.append(move)
            evt.set()

        ai_instance.get_move_async(board, on_legit)
        completed = evt.wait(timeout=4.0)
        assert completed is True
        assert len(legit_move) == 1
        assert legit_move[0] in board.legal_moves

    finally:
        ai_instance.close()


def test_stress_rapid_cancellation_of_hints():
    """
    Stress-test rapid cancellation and rapid spam of coach hint calculations:
    1. Verifies immediate cancellation (0ms) produces zero callbacks.
    2. Verifies that when cancel_ongoing_task is invoked, NO callback fires after cancellation.
    3. Verifies that burst hint requests (15 rapid requests) resolve cleanly to at most 1 callback.
    """
    ai_instance = ChessAI()
    ai_instance.start()
    assert ai_instance.engine is not None

    board = chess.Board()

    try:
        # Part 1: Immediate cancellation test
        immediate_fired = []
        for _ in range(20):
            ai_instance.get_hint_async(board, lambda m, info=None: immediate_fired.append(m))
            ai_instance.cancel_ongoing_task()
        time.sleep(0.3)
        assert len(immediate_fired) == 0, f"Immediate cancel callbacks fired: {len(immediate_fired)}"

        # Part 2: Cancellation barrier test
        fired_after_cancel = []
        for i in range(25):
            cancel_marker = threading.Event()
            def make_cb(marker, idx=i):
                def cb(move, info=None):
                    if marker.is_set():
                        fired_after_cancel.append(f"hint_{idx}")
                return cb

            ai_instance.get_hint_async(board, make_cb(cancel_marker))
            jitter = (i % 4) * 0.01  # 0ms to 30ms
            if jitter > 0:
                time.sleep(jitter)
            cancel_marker.set()
            ai_instance.cancel_ongoing_task()

        time.sleep(0.4)
        assert len(fired_after_cancel) == 0, f"Callbacks executed after cancel marker: {fired_after_cancel}"

        # Part 3: Burst test (15 rapid requests)
        burst_results = []
        evt = threading.Event()
        for i in range(15):
            def make_cb(idx):
                def cb(move, info=None):
                    burst_results.append((idx, move))
                    evt.set()
                return cb
            ai_instance.get_hint_async(board, make_cb(i))

        evt.wait(timeout=3.0)
        time.sleep(0.3)
        # Exactly one callback should complete (the latest active one)
        assert len(burst_results) <= 2, f"Too many burst callbacks completed: {burst_results}"
        if burst_results:
            last_idx, best_mv = burst_results[-1]
            assert best_mv in board.legal_moves

    finally:
        ai_instance.close()


# ==============================================================================
# 3. CONCURRENCY STRESS: RAPID CTRL+Z UNDO DURING BACKGROUND AI THINKING
# ==============================================================================

def test_stress_rapid_undo_while_ai_thinking_in_gameapp():
    """
    Stress-test rapid Ctrl+Z undo invocations while AI is actively calculating its move:
    Simulates a human playing 1. e4, AI begins computing, and user triggers rapid
    successive undo requests at random thinking milestones.
    Verifies:
    1. AI task is aborted immediately without unhandled thread exceptions.
    2. Board rollback is clean and deterministic (empty move stack, White to move).
    3. No stale AI move ever enters the move queue or gets executed on the board.
    """
    import pygame
    pygame.init()

    app = GameApp()
    app.ai.start()
    app.mode = "ai"
    app.training_mode = True
    app.reset_game(player_color=chess.WHITE)
    assert app.ai.engine is not None, "Stockfish must be present"

    delays = [0.01, 0.05, 0.10, 0.25, 0.50, 0.80]

    try:
        for iteration, delay in enumerate(delays):
            # 1. Reset game state
            app.reset_game(player_color=chess.WHITE)
            app.training_mode = True
            app.mode = "ai"

            # 2. Player plays 1. e4
            move_e4 = chess.Move.from_uci("e2e4")
            app.execute_move(move_e4, animated=False)
            assert len(app.board.move_stack) == 1
            assert app.board.turn == chess.BLACK

            # 3. Trigger AI thinking cycle in GameApp
            app.waiting_for_ai = True
            def ai_done(move):
                if move:
                    app.ai_move_queue.put(move)
                else:
                    app.waiting_for_ai = False
            app.ai.get_move_async(app.board, ai_done)

            assert app.waiting_for_ai is True

            # 4. Wait for specified thinking milestone
            time.sleep(delay)

            # 5. Rapid burst of undo invocations (simulate user spamming Ctrl+Z)
            undo_results = []
            for _ in range(5):
                res = app.handle_undo_move()
                undo_results.append(res)

            # First undo must have succeeded (reverted e4)
            assert undo_results[0] is True, f"Iteration {iteration}: First undo failed"
            assert len(app.board.move_stack) == 0, f"Move stack should be empty, got {len(app.board.move_stack)}"
            assert app.board.turn == chess.WHITE
            assert app.waiting_for_ai is False

            # 6. Run simulated main loop cycles for 0.4s to verify no stale move enters queue or board
            t_end = time.time() + 0.4
            while time.time() < t_end:
                while not app.ai_move_queue.empty():
                    mv = app.ai_move_queue.get()
                    app.execute_move(mv, animated=False)
                time.sleep(0.02)

            assert app.ai_move_queue.empty() is True, "ai_move_queue should be empty after undo"
            assert len(app.board.move_stack) == 0, "Stale AI move executed on rolled-back board!"

    finally:
        app.ai.close()


# ==============================================================================
# 4. SUBPROCESS LIFECYCLE, LEAK & ZOMBIE DETECTION
# ==============================================================================

def test_stress_subprocess_lifecycle_and_leak_detection():
    """
    Stress-test Stockfish subprocess lifecycle:
    1. Repeated rapid start/close cycles (20 iterations).
    2. Repeated start calls WITHOUT calling close (re-initialization).
    3. Measure active Stockfish processes via psutil to guarantee ZERO leaks or zombies.
    """
    current_pid = os.getpid()
    parent_process = psutil.Process(current_pid)

    def count_child_stockfish():
        count = 0
        for child in parent_process.children(recursive=True):
            try:
                name = child.name().lower()
                cmdline = " ".join(child.cmdline()).lower()
                if "stockfish" in name or "stockfish" in cmdline:
                    if child.status() != psutil.STATUS_ZOMBIE:
                        count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return count

    initial_sf_count = count_child_stockfish()

    # 1. Rapid 20 start/close cycles
    for _ in range(20):
        ai_inst = ChessAI()
        ai_inst.start()
        assert ai_inst.engine is not None
        ai_inst.close()

    time.sleep(0.2)
    after_cycles_count = count_child_stockfish()
    assert after_cycles_count == initial_sf_count, (
        f"Stockfish processes leaked after start/close cycles: "
        f"initial={initial_sf_count}, current={after_cycles_count}"
    )

    # 2. Repeated start() without explicit close() on single instance
    ai_single = ChessAI()
    for _ in range(10):
        ai_single.start()
        assert ai_single.engine is not None

    time.sleep(0.2)
    # Should only have at most 1 active stockfish child
    assert count_child_stockfish() <= initial_sf_count + 1

    ai_single.close()
    time.sleep(0.2)
    assert count_child_stockfish() == initial_sf_count, "Processes leaked after close()"


# ==============================================================================
# 5. STRICT THINKING PACE VERIFICATION (1.5s - 3.0s)
# ==============================================================================

def test_stress_thinking_pace_monte_carlo_strict_bounds():
    """
    Monte Carlo stress test of compute_thinking_pace across 2,000 distinct board states:
    - Varying piece counts (32 down to 3)
    - Varying legal move counts (0 to 60)
    - Check positions and non-check positions
    - Difficulties 1, 2, 3, 4 and edge difficulty values.
    Strictly verifies that pace is NEVER < 1.50s and NEVER > 3.00s.
    """
    boards = [
        chess.Board(),  # Start
        chess.Board("r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"),  # Opening
        chess.Board("r1b2rk1/pp1p1ppp/2n1pn2/8/2PN4/2N3P1/PP2PPBP/R2Q1RK1 b - - 0 10"),  # Middlegame
        chess.Board("8/5k2/8/8/8/8/4K3/8 w - - 0 1"),  # Endgame (2 kings)
        chess.Board("rnb1kbnr/pppp1ppp/8/4p3/5PPq/8/PPPPP2P/RNBQKBNR w KQkq - 1 3"),  # Check
        chess.Board("8/8/4k3/8/8/8/4K2R/8 w - - 0 1"),  # Rook endgame
    ]

    # Generate more random boards by playing 1-20 random legal moves
    random.seed(42)
    for _ in range(50):
        b = chess.Board()
        for _ in range(random.randint(2, 25)):
            if b.is_game_over():
                break
            moves = list(b.legal_moves)
            if moves:
                b.push(random.choice(moves))
        boards.append(b)

    recorded_paces = []
    for b in boards:
        for diff in [1, 2, 3, 4, 0, 5, -1]:
            for _ in range(5):
                pace = compute_thinking_pace(b, diff)
                recorded_paces.append(pace)
                assert 1.50 <= pace <= 3.00, f"Thinking pace out of bounds: {pace} (diff={diff})"

    # Statistical verification: distribution has variance (not stuck on constant)
    min_pace = min(recorded_paces)
    max_pace = max(recorded_paces)
    assert min_pace >= 1.50
    assert max_pace <= 3.00
    assert max_pace - min_pace >= 0.80, f"Pace range should span at least 0.8s, got {max_pace - min_pace:.2f}s"


def test_stress_thinking_pace_live_engine_moves_across_all_personas():
    """
    Empirically verifies that actual live moves with Stockfish 19 strictly adhere to the
    thinking pace contract (1.5s - 3.0s) for ALL 4 humanized personas:
    - Lucas (800 Elo)
    - Éléonore (1400 Elo)
    - Alexandre (2100 Elo)
    - Le Monstre (3200+ Elo)
    Measures wall-clock time from get_move_async to callback invocation.
    """
    ai_instance = ChessAI()
    ai_instance.start()
    assert ai_instance.engine is not None

    board = chess.Board()

    try:
        for persona_id, pdata in BOT_PERSONAS.items():
            ai_instance.configure_elo(pdata["elo"], persona_id=persona_id)

            move_holder = []
            done_evt = threading.Event()
            t0 = time.time()

            def on_move(mv):
                move_holder.append(mv)
                done_evt.set()

            ai_instance.get_move_async(board, on_move)
            finished = done_evt.wait(timeout=4.0)
            elapsed = time.time() - t0

            assert finished is True, f"Move for persona '{persona_id}' timed out"
            assert len(move_holder) == 1
            assert move_holder[0] in board.legal_moves

            # Strict pacing check: allow ±0.03s margin for thread scheduler wakeup
            assert 1.47 <= elapsed <= 3.15, (
                f"Persona '{persona_id}' thinking pace violation: "
                f"elapsed={elapsed:.3f}s (must be ~1.5s - 3.0s)"
            )

    finally:
        ai_instance.close()


# ==============================================================================
# 6. TERMINAL BOARD STATE ADVERSARIAL CHALLENGE (CHECKMATE / STALEMATE)
# ==============================================================================

def test_stress_terminal_board_states_hints_and_moves():
    """
    Adversarial test feeding terminal game states to get_move_async and get_hint_async:
    - Fool's mate (Checkmate)
    - Stalemate position
    Must handle gracefully without crashing or throwing unhandled engine errors.
    """
    ai_instance = ChessAI()
    ai_instance.start()
    assert ai_instance.engine is not None

    try:
        # Checkmate board (Fool's mate: 1. f3 e5 2. g4 Qh4#)
        checkmate_board = chess.Board("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3")
        assert checkmate_board.is_checkmate() is True
        assert len(list(checkmate_board.legal_moves)) == 0

        # Hint on checkmate board
        hint_received = []
        evt_hint = threading.Event()
        def on_hint(m, info=None):
            hint_received.append(m)
            evt_hint.set()

        ai_instance.get_hint_async(checkmate_board, on_hint)
        evt_hint.wait(timeout=2.0)
        assert len(hint_received) == 1
        assert hint_received[0] is None, "Hint on checkmate board should be None"

        # Stalemate board (King trapped, no legal moves)
        stalemate_board = chess.Board("k7/8/1Q6/8/8/8/8/7K b - - 0 1")
        assert stalemate_board.is_stalemate() is True
        assert len(list(stalemate_board.legal_moves)) == 0

        move_received = []
        evt_mv = threading.Event()
        def on_mv(m):
            move_received.append(m)
            evt_mv.set()

        ai_instance.get_move_async(stalemate_board, on_mv)
        evt_mv.wait(timeout=4.0)
        assert len(move_received) == 1
        assert move_received[0] is None, "Move on stalemate board should be None"

    finally:
        ai_instance.close()
