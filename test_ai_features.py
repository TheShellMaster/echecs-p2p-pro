import os
import sys
import time
import chess
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from ai import ChessAI, compute_thinking_pace, DIFFICULTY_PRESETS
from main import GameApp
from constants import COLOR_THREAT, COLOR_THREAT_BORDER

def test_compute_thinking_pace_bounds():
    print("Testing compute_thinking_pace bounds and variation...")
    b_start = chess.Board()
    # Test all difficulties
    for diff in [1, 2, 3, 4]:
        for _ in range(20):
            pace = compute_thinking_pace(b_start, difficulty=diff)
            assert 1.5 <= pace <= 3.0, f"Pace out of bounds for diff {diff}: {pace}"

    # Test endgame board (only 3 pieces left)
    b_endgame = chess.Board("8/8/8/4k3/8/8/4K3/4Q3 w - - 0 1")
    for diff in [1, 2, 3, 4]:
        for _ in range(15):
            pace = compute_thinking_pace(b_endgame, difficulty=diff)
            assert 1.5 <= pace <= 3.0, f"Endgame pace out of bounds: {pace}"

    # Test board in check
    b_check = chess.Board("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3")
    assert b_check.is_check()
    for diff in [1, 2, 3, 4]:
        pace = compute_thinking_pace(b_check, difficulty=diff)
        assert 1.5 <= pace <= 3.0, f"In-check pace out of bounds: {pace}"

    print("  -> compute_thinking_pace strictly within [1.5s, 3.0s] OK")

def test_ai_async_delay():
    print("Testing ChessAI get_move_async duration >= 1.5s...")
    ai = ChessAI(difficulty=1)
    b = chess.Board()
    
    received_move = []
    t_start = time.time()
    
    def on_move(move):
        received_move.append((move, time.time() - t_start))

    ai.get_move_async(b, on_move)
    
    # Wait for completion
    timeout = 4.0
    while not received_move and (time.time() - t_start) < timeout:
        time.sleep(0.05)
        
    assert len(received_move) == 1, "AI should return a move"
    move, elapsed = received_move[0]
    assert move in b.legal_moves, f"Move {move} must be legal"
    assert elapsed >= 1.48, f"AI moved too quickly! Elapsed: {elapsed:.2f}s (expected >= 1.5s)"
    assert elapsed <= 3.2, f"AI took too long! Elapsed: {elapsed:.2f}s (expected <= 3.0s)"
    ai.close()
    print(f"  -> AI move returned in {elapsed:.2f}s (Humanized pacing OK)")

def test_ai_threat_detection():
    print("Testing AI Threat Detection...")
    app = GameApp()
    app.mode = "ai"
    app.reset_game(player_color=chess.BLACK, time_limit=0) # AI plays White
    
    # White plays 1. e4
    app.execute_move(chess.Move.from_uci("e2e4"))
    # Black plays 1... e5
    app.execute_move(chess.Move.from_uci("e7e5"))
    
    # AI (White) plays 2. Nf3 (threatens black pawn on e5)
    move_nf3 = chess.Move.from_uci("g1f3")
    app.execute_move(move_nf3)
    app.compute_ai_threats(move_nf3)
    
    # Verify e5 is in threatened squares
    assert chess.E5 in app.ai_threatened_squares, f"e5 pawn should be threatened by Nf3: {app.ai_threatened_squares}"
    
    # Player (Black) responds with 2... Nc6 (protects e5)
    app.execute_move(chess.Move.from_uci("b8c6"))
    # Threats should be cleared upon player's response
    assert len(app.ai_threatened_squares) == 0, "Threats should clear on player move"
    
    # AI plays 3. Bc4 (threatens f7 pawn)
    move_bc4 = chess.Move.from_uci("f1c4")
    app.execute_move(move_bc4)
    app.compute_ai_threats(move_bc4)
    assert chess.F7 in app.ai_threatened_squares, f"f7 pawn should be threatened by Bc4: {app.ai_threatened_squares}"
    
    app.network.close()
    app.ai.close()
    print("  -> AI threat detection OK")

def test_ai_fork_threat_detection():
    print("Testing AI Fork (Multiple piece threats)...")
    app = GameApp()
    app.mode = "ai"
    app.reset_game(player_color=chess.BLACK, time_limit=0)
    
    # Setup board where White Knight moves to c7, forking King on e8 and Rook on a8
    app.board = chess.Board("r3k3/8/8/8/8/5N2/8/4K3 w - - 0 1")
    # Move knight from f3 to d4 then to c7 or setup directly Nc7
    app.board = chess.Board("r3k3/2N5/8/8/8/8/8/4K3 b - - 0 1")
    # Previous move was knight to c7
    fork_move = chess.Move.from_uci("a6c7") # dummy from sq
    fork_move = chess.Move(chess.A6, chess.C7)
    app.compute_ai_threats(fork_move)
    
    # Both a8 (rook) and e8 (king) are attacked by Nc7
    assert chess.A8 in app.ai_threatened_squares, "Rook on a8 must be detected as threatened"
    assert chess.E8 in app.ai_threatened_squares, "King on e8 must be detected as threatened"
    
    app.network.close()
    app.ai.close()
    print("  -> AI multi-piece fork threat detection OK")

def test_ui_draw_highlights_with_threats():
    print("Testing UI drawing highlights with threats and animated indicator...")
    app = GameApp()
    app.mode = "ai"
    app.reset_game(player_color=chess.WHITE, time_limit=300)
    app.waiting_for_ai = True
    app.ai_threatened_squares = {chess.E4, chess.D5}
    
    # Draw screen
    app.draw_play((0, 0), [])
    # Verify no crash during draw_highlights and draw_side_panel with waiting_for_ai
    assert app.waiting_for_ai is True
    
    app.waiting_for_ai = False
    app.draw_play((0, 0), [])
    
    app.network.close()
    app.ai.close()
    print("  -> UI highlights and animated indicator render OK")

if __name__ == "__main__":
    print("=== RUNNING AI PACING & THREAT HIGHLIGHTING TESTS ===")
    test_compute_thinking_pace_bounds()
    test_ai_async_delay()
    test_ai_threat_detection()
    test_ai_fork_threat_detection()
    test_ui_draw_highlights_with_threats()
    print("=== ALL AI TESTS PASSED! ===")
