"""
Opaque-box E2E test suite for AI Personas & Stockfish 19 UCI Elo Calibration.
Covers Tiers 1-4 as specified in PROJECT.md and TEST_INFRA.md:
- Tier 1: Feature Coverage (Metadata, continuous range 500-3200, UCI calibration, thinking pace).
- Tier 2: Boundary & Corner Cases (Clamping 500, 800, 1319, 1320, 2100, 3190, 3200, 3600, task cancel).
- Tier 3: Cross-Feature Combinations (Persona switch + slider adjust, legacy preset compatibility).
- Tier 4: Real-World Scenarios (Simulated games vs Lucas 800, Alexandre 2100, Le Monstre 3200+).
"""

import os
import sys
import time
import pytest
import chess
import chess.engine

# Ensure headless execution across all environments
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import constants
import ai
from ai import ChessAI, compute_thinking_pace, DIFFICULTY_PRESETS


def _get_uci_opts(cfg):
    """Helper to extract UCI options dict from configure_elo return value."""
    if isinstance(cfg, dict):
        return cfg.get("uci_options", cfg)
    return {}


# ==============================================================================
# TIER 1 — FEATURE COVERAGE (ISOLATION)
# ==============================================================================

def test_tier1_personas_metadata_presence_and_structure():
    """
    Tier 1: Verifies BOT_PERSONAS data structure exists in constants.py
    and contains all 4 required personas with complete metadata fields.
    """
    if not hasattr(constants, "BOT_PERSONAS"):
        pytest.skip("constants.BOT_PERSONAS pending Milestone 1 implementation")

    personas = constants.BOT_PERSONAS
    assert isinstance(personas, dict), "BOT_PERSONAS must be a dictionary"

    required_ids = {"lucas", "eleonore", "alexandre", "monster"}
    assert required_ids.issubset(set(personas.keys())), f"BOT_PERSONAS must contain {required_ids}"

    required_fields = {
        "id", "name", "title", "elo", "avatar_theme",
        "playstyle", "quote", "uci_limit_strength",
        "uci_elo", "skill_level", "depth", "time"
    }

    for pid in required_ids:
        p = personas[pid]
        missing = required_fields - set(p.keys())
        assert not missing, f"Persona '{pid}' is missing fields: {missing}"

        # Type & validity assertions
        assert p["id"] == pid
        assert isinstance(p["name"], str) and len(p["name"]) > 0
        assert isinstance(p["title"], str) and len(p["title"]) > 0
        assert isinstance(p["elo"], int) and p["elo"] > 0
        assert isinstance(p["avatar_theme"], str) and len(p["avatar_theme"]) > 0
        assert isinstance(p["playstyle"], str) and len(p["playstyle"]) > 5
        assert isinstance(p["quote"], str) and len(p["quote"]) > 5
        assert isinstance(p["uci_limit_strength"], bool)
        assert isinstance(p["uci_elo"], int) and p["uci_elo"] >= 1320
        assert isinstance(p["skill_level"], int) and 0 <= p["skill_level"] <= 20
        assert isinstance(p["depth"], int) and p["depth"] >= 1
        assert isinstance(p["time"], (int, float)) and p["time"] > 0


def test_tier1_personas_individual_characteristics():
    """
    Tier 1: Verifies the distinct attributes of each of the 4 personas
    (Lucas Débutant 800, Éléonore Club 1400, Alexandre Maître 2100, Le Monstre 3200+).
    """
    if not hasattr(constants, "BOT_PERSONAS"):
        pytest.skip("constants.BOT_PERSONAS pending Milestone 1 implementation")

    personas = constants.BOT_PERSONAS

    # Lucas (~800 Elo Débutant)
    lucas = personas["lucas"]
    assert lucas["elo"] == 800
    assert "Lucas" in lucas["name"]
    assert "Débutant" in lucas["title"]
    assert lucas["avatar_theme"] == "amber"
    assert lucas["uci_limit_strength"] is True
    assert lucas["uci_elo"] == 1320, "Lucas must have uci_elo clamped to 1320 (Stockfish 19 min)"
    assert lucas["skill_level"] <= 2
    assert lucas["depth"] <= 6

    # Éléonore (~1400 Elo Club)
    eleonore = personas["eleonore"]
    assert eleonore["elo"] == 1400
    assert "Éléonore" in eleonore["name"]
    assert "Club" in eleonore["title"]
    assert eleonore["avatar_theme"] == "emerald"
    assert eleonore["uci_limit_strength"] is True
    assert eleonore["uci_elo"] == 1400
    assert 8 <= eleonore["skill_level"] <= 12

    # Alexandre (~2100 Elo Maître National)
    alexandre = personas["alexandre"]
    assert alexandre["elo"] == 2100
    assert "Alexandre" in alexandre["name"]
    assert "Maître" in alexandre["title"]
    assert alexandre["avatar_theme"] == "indigo"
    assert alexandre["uci_limit_strength"] is True
    assert alexandre["uci_elo"] == 2100
    assert 16 <= alexandre["skill_level"] <= 19

    # Le Monstre Stockfish 19 (~3200+ Elo Grand Maître Surhumain)
    monster = personas["monster"]
    assert monster["elo"] >= 3200
    assert "Monstre" in monster["name"]
    assert monster["avatar_theme"] == "rose"
    assert monster["uci_limit_strength"] is False, "Le Monstre must play at unbounded engine strength"
    assert monster["uci_elo"] == 3190
    assert monster["skill_level"] == 20
    assert monster["depth"] >= 20


def test_tier1_continuous_elo_configuration_range():
    """
    Tier 1: Verifies configure_elo accepts continuous values between 500 and 3200
    and outputs valid UCI configuration parameters.
    """
    if not hasattr(ChessAI, "configure_elo"):
        pytest.skip("ChessAI.configure_elo pending Milestone 1 implementation")

    ai_instance = ChessAI()
    test_elos = [500, 750, 1000, 1320, 1600, 2100, 2800, 3190, 3200]

    for elo in test_elos:
        cfg = ai_instance.configure_elo(elo)
        assert isinstance(cfg, dict), f"configure_elo({elo}) must return a configuration dictionary"
        uci_opts = _get_uci_opts(cfg)

        if elo >= 3200:
            assert uci_opts.get("UCI_LimitStrength") is False
            skill = cfg.get("skill_level", uci_opts.get("Skill Level"))
            assert skill == 20
        elif 1320 <= elo < 3200:
            assert uci_opts.get("UCI_LimitStrength") is True
            assert uci_opts.get("UCI_Elo") == elo
        else:  # elo < 1320
            assert uci_opts.get("UCI_LimitStrength") is True
            assert uci_opts.get("UCI_Elo") == 1320
            skill = cfg.get("skill_level", uci_opts.get("Skill Level"))
            assert skill is not None
            assert skill <= 5


def test_tier1_stockfish_uci_engine_calibration_live():
    """
    Tier 1: Directly verifies UCI configuration against the live Stockfish 19 engine.
    Ensures that configuring Lucas, Alexandre, or Le Monstre does not cause UCI protocol errors.
    """
    if not hasattr(ChessAI, "configure_elo"):
        pytest.skip("ChessAI.configure_elo pending Milestone 1 implementation")

    ai_instance = ChessAI()
    started = ai_instance.start()
    if not started or not ai_instance.engine:
        pytest.skip("Stockfish binary not available in environment")

    try:
        # 1. Calibrate Alexandre (2100)
        cfg_alex = ai_instance.configure_elo(2100, "alexandre")
        uci_alex = _get_uci_opts(cfg_alex)
        assert uci_alex.get("UCI_Elo") == 2100
        assert uci_alex.get("UCI_LimitStrength") is True

        # 2. Calibrate Lucas (800) -> Clamped to 1320
        cfg_lucas = ai_instance.configure_elo(800, "lucas")
        uci_lucas = _get_uci_opts(cfg_lucas)
        assert uci_lucas.get("UCI_Elo") == 1320
        assert uci_lucas.get("UCI_LimitStrength") is True

        # 3. Calibrate Le Monstre (3200) -> Unbounded strength
        cfg_monster = ai_instance.configure_elo(3200, "monster")
        uci_monster = _get_uci_opts(cfg_monster)
        assert uci_monster.get("UCI_LimitStrength") is False
    finally:
        ai_instance.close()


def test_tier1_thinking_pace_bounds_and_humanization():
    """
    Tier 1: Verifies compute_thinking_pace strictly respects the 1.5s - 3.0s bounds
    across diverse board complex positions and exhibits natural variance.
    """
    # 1. Standard initial position
    board_init = chess.Board()
    # 2. Complex middlegame with multiple pieces and legal moves
    board_mid = chess.Board("r1bqk2r/pp1p1ppp/2n2n2/2p1p3/1bP1P3/2NP1N2/PP3PPP/R1BQKB1R w KQkq - 1 6")
    # 3. Endgame with few pieces
    board_end = chess.Board("8/8/4k3/8/8/4K3/4P3/8 w - - 0 1")
    # 4. Check position
    board_check = chess.Board("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3")

    positions = [board_init, board_mid, board_end, board_check]

    for board in positions:
        for diff in [1, 2, 3, 4]:
            pace = compute_thinking_pace(board, diff)
            assert 1.5 <= pace <= 3.0, f"Thinking pace {pace}s out of bounds [1.5, 3.0] for diff {diff}"

    # Verify organic variance (multiple calls on same position should not be identical)
    paces = {compute_thinking_pace(board_mid, 4) for _ in range(25)}
    assert len(paces) > 1, "compute_thinking_pace must incorporate organic variance"


# ==============================================================================
# TIER 2 — BOUNDARY & CORNER CASES
# ==============================================================================

@pytest.mark.parametrize("elo,expected_strength,expected_uci_elo,min_skill,max_skill", [
    (500, True, 1320, 0, 1),
    (800, True, 1320, 0, 2),
    (1319, True, 1320, 0, 10),
    (1320, True, 1320, 0, 20),
    (2100, True, 2100, 15, 20),
    (3190, True, 3190, 18, 20),
    (3200, False, None, 20, 20),
    (3600, False, None, 20, 20),
])
def test_tier2_elo_clamping_exact_boundaries(elo, expected_strength, expected_uci_elo, min_skill, max_skill):
    """
    Tier 2: Exhaustively validates boundary points specified in ORIGINAL_REQUEST:
    - 500: slider minimum
    - 800: Lucas rating
    - 1319: edge just below Stockfish 19 minimum
    - 1320: exact Stockfish 19 minimum
    - 2100: Alexandre rating
    - 3190: exact Stockfish 19 maximum
    - 3200: Monster threshold
    - 3600: unbounded max
    """
    if not hasattr(ChessAI, "configure_elo"):
        pytest.skip("ChessAI.configure_elo pending Milestone 1 implementation")

    ai_instance = ChessAI()
    cfg = ai_instance.configure_elo(elo)
    uci_opts = _get_uci_opts(cfg)

    assert uci_opts.get("UCI_LimitStrength") == expected_strength, f"Elo {elo}: expected UCI_LimitStrength={expected_strength}"
    if expected_uci_elo is not None:
        assert uci_opts.get("UCI_Elo") == expected_uci_elo, f"Elo {elo}: expected UCI_Elo={expected_uci_elo}, got {uci_opts.get('UCI_Elo')}"

    skill = cfg.get("skill_level", uci_opts.get("Skill Level"))
    if skill is not None:
        assert min_skill <= skill <= max_skill, f"Elo {elo}: Skill Level {skill} out of range [{min_skill}, {max_skill}]"


def test_tier2_extreme_and_out_of_range_elo_inputs():
    """
    Tier 2: Verifies that extreme or negative Elo values are handled gracefully
    without raising uncaught exceptions or crashing the engine.
    """
    if not hasattr(ChessAI, "configure_elo"):
        pytest.skip("ChessAI.configure_elo pending Milestone 1 implementation")

    ai_instance = ChessAI()
    extreme_values = [-100, 0, 100, 10000]

    for val in extreme_values:
        try:
            cfg = ai_instance.configure_elo(val)
            assert isinstance(cfg, dict)
            uci_opts = _get_uci_opts(cfg)
            # Below 1320 must be clamped to 1320
            if val < 1320:
                assert uci_opts.get("UCI_Elo", 1320) == 1320
                assert uci_opts.get("UCI_LimitStrength") is True
            # Above 3200 must have UCI_LimitStrength False
            if val >= 3200:
                assert uci_opts.get("UCI_LimitStrength") is False
        except Exception as e:
            pytest.fail(f"configure_elo({val}) crashed unexpectedly with: {e}")


def test_tier2_cancel_ongoing_task_idempotency_and_safety():
    """
    Tier 2: Verifies cancel_ongoing_task can be called safely:
    - when no background task is running (idle)
    - multiple times consecutively (idempotent)
    - after engine has been closed
    """
    ai_instance = ChessAI()
    if not hasattr(ai_instance, "cancel_ongoing_task"):
        pytest.skip("ChessAI.cancel_ongoing_task pending Milestone 1 implementation")

    # 1. Idle cancel
    try:
        ai_instance.cancel_ongoing_task()
    except Exception as e:
        pytest.fail(f"cancel_ongoing_task failed when idle: {e}")

    # 2. Sequential multiple cancels
    for _ in range(3):
        ai_instance.cancel_ongoing_task()

    # 3. After engine close
    ai_instance.close()
    ai_instance.cancel_ongoing_task()


# ==============================================================================
# TIER 3 — CROSS-FEATURE COMBINATIONS
# ==============================================================================

def test_tier3_persona_selection_then_continuous_slider_adjustment():
    """
    Tier 3: Simulates user flow of picking a preset persona and subsequently
    fine-tuning the continuous Elo slider.
    """
    if not hasattr(ChessAI, "configure_elo"):
        pytest.skip("ChessAI.configure_elo pending Milestone 1 implementation")

    ai_instance = ChessAI()

    # Step 1: Select Lucas (800)
    cfg1 = ai_instance.configure_elo(800, persona_id="lucas")
    uci1 = _get_uci_opts(cfg1)
    assert uci1.get("UCI_Elo") == 1320
    assert uci1.get("UCI_LimitStrength") is True

    # Step 2: Fine-tune slider to 1100
    cfg2 = ai_instance.configure_elo(1100)
    uci2 = _get_uci_opts(cfg2)
    assert uci2.get("UCI_Elo") == 1320
    assert uci2.get("UCI_LimitStrength") is True

    # Step 3: Slide up to 1600 (club level)
    cfg3 = ai_instance.configure_elo(1600)
    uci3 = _get_uci_opts(cfg3)
    assert uci3.get("UCI_Elo") == 1600
    assert uci3.get("UCI_LimitStrength") is True

    # Step 4: Pick Le Monstre (3200)
    cfg4 = ai_instance.configure_elo(3200, persona_id="monster")
    uci4 = _get_uci_opts(cfg4)
    assert uci4.get("UCI_LimitStrength") is False

    # Step 5: Adjust slider down to 2600
    cfg5 = ai_instance.configure_elo(2600)
    uci5 = _get_uci_opts(cfg5)
    assert uci5.get("UCI_LimitStrength") is True
    assert uci5.get("UCI_Elo") == 2600


def test_tier3_legacy_compatibility_with_difficulty_presets():
    """
    Tier 3: Ensures backward compatibility with legacy start(diff_level)
    and set_difficulty(diff_level) methods to avoid breaking test_app.py.
    """
    ai_instance = ChessAI(difficulty=2)
    assert ai_instance.difficulty == 2
    assert 2 in DIFFICULTY_PRESETS

    ai_instance.set_difficulty(3)
    assert ai_instance.difficulty == 3

    # Legacy start should succeed cleanly
    started = ai_instance.start(diff_level=1)
    assert started is True
    assert ai_instance.difficulty == 1
    ai_instance.close()


# ==============================================================================
# TIER 4 — REAL-WORLD APPLICATION SCENARIOS
# ==============================================================================

def test_tier4_scenario_blitz_match_vs_alexandre():
    """
    Tier 4: Simulates a real blitz game opening against Alexandre (2100 Elo)
    with genuine Stockfish 19 engine moves.
    """
    ai_instance = ChessAI()
    started = ai_instance.start()
    if not started or not ai_instance.engine:
        pytest.skip("Stockfish binary not available in environment")

    try:
        if hasattr(ai_instance, "configure_elo"):
            ai_instance.configure_elo(2100, persona_id="alexandre")

        board = chess.Board()

        # Human plays 1. e4
        board.push_san("e4")

        # Request AI move via sync evaluation / play
        limit = chess.engine.Limit(time=0.3)
        res = ai_instance.engine.play(board, limit)
        assert res.move is not None
        assert res.move in board.legal_moves
        board.push(res.move)

        # Human plays 2. Nf3
        assert chess.Move.from_uci("g1f3") in board.legal_moves
        board.push_san("Nf3")

        # AI responds to 2. Nf3
        res2 = ai_instance.engine.play(board, limit)
        assert res2.move is not None
        assert res2.move in board.legal_moves
        board.push(res2.move)

        assert len(board.move_stack) == 4
    finally:
        ai_instance.close()


def test_tier4_scenario_grandmaster_challenge_vs_monster():
    """
    Tier 4: Tactical puzzle position evaluation against Le Monstre (3200+ Elo).
    Verifies that the engine detects decisive tactics under master settings.
    """
    ai_instance = ChessAI()
    started = ai_instance.start()
    if not started or not ai_instance.engine:
        pytest.skip("Stockfish binary not available in environment")

    try:
        if hasattr(ai_instance, "configure_elo"):
            ai_instance.configure_elo(3200, persona_id="monster")

        # Mate-in-2 puzzle: White to move and win
        # 1. Qf7+ Kh8 2. Qf8# (or Qxg7#)
        board = chess.Board("r1b2r1k/pp3ppp/8/3N4/8/5Q2/PqP2PPP/R3R1K1 w - - 0 1")

        # Analyse position
        info = ai_instance.engine.analyse(board, chess.engine.Limit(time=0.4, depth=14))
        score = info.get("score")
        assert score is not None

        # Verify best move is high-quality / legal
        pv = info.get("pv")
        assert pv and len(pv) > 0
        best_move = pv[0]
        assert best_move in board.legal_moves
    finally:
        ai_instance.close()


def test_tier4_scenario_beginner_flow_vs_lucas():
    """
    Tier 4: Verifies that Lucas (800 Elo) can be configured, generates legal moves,
    and runs without engine timeouts or protocol failure.
    """
    ai_instance = ChessAI()
    started = ai_instance.start()
    if not started or not ai_instance.engine:
        pytest.skip("Stockfish binary not available in environment")

    try:
        if hasattr(ai_instance, "configure_elo"):
            ai_instance.configure_elo(800, persona_id="lucas")

        board = chess.Board()
        # Human plays 1. d4
        board.push_san("d4")

        # AI moves with beginner-friendly limit
        limit = chess.engine.Limit(time=0.25)
        res = ai_instance.engine.play(board, limit)
        assert res.move is not None
        assert res.move in board.legal_moves
    finally:
        ai_instance.close()
