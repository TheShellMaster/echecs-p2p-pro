import os
import sys
import time
import math
import chess
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from constants import (
    THEMES, THEME_KEYS, DEFAULT_THEME,
    SCREEN_WIDTH, SCREEN_HEIGHT,
    BOARD_X, BOARD_Y, BOARD_FRAME, SQUARE_SIZE, FULL_BOARD_SIZE,
    EVAL_BAR_X, EVAL_BAR_WIDTH
)
from main import GameApp
from ui import UI
from ai import ChessAI

def test_tactical_annotations():
    print("Testing Tactical Annotations (Right-Click Drag Arrows & Circles)...")
    app = GameApp()
    app.reset_game()

    # 1. Single right-click: create circle highlight
    # Simulate Right-Click Down on E4 (button 3)
    e4_x, e4_y = app.ui.square_to_screen_center(chess.E4, flipped=False)
    ev_down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 3, 'pos': (e4_x, e4_y)})
    app.handle_game_input([ev_down], (e4_x, e4_y))
    assert app.right_drag_start == chess.E4

    # Simulate Right-Click Up on same square E4 (button 3)
    ev_up = pygame.event.Event(pygame.MOUSEBUTTONUP, {'button': 3, 'pos': (e4_x, e4_y)})
    app.handle_game_input([ev_up], (e4_x, e4_y))
    assert chess.E4 in app.circles, f"Square E4 should have circle highlight: {app.circles}"

    # Right click again on E4 to toggle off
    app.handle_game_input([ev_down], (e4_x, e4_y))
    app.handle_game_input([ev_up], (e4_x, e4_y))
    assert chess.E4 not in app.circles, "Square E4 circle should toggle off"

    # 2. Right-click drag: create vector arrow from G1 to F3 (Knight move)
    g1_x, g1_y = app.ui.square_to_screen_center(chess.G1, flipped=False)
    f3_x, f3_y = app.ui.square_to_screen_center(chess.F3, flipped=False)
    ev_g1_down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 3, 'pos': (g1_x, g1_y)})
    ev_f3_up = pygame.event.Event(pygame.MOUSEBUTTONUP, {'button': 3, 'pos': (f3_x, f3_y)})
    
    app.handle_game_input([ev_g1_down], (g1_x, g1_y))
    assert app.right_drag_start == chess.G1
    app.handle_game_input([ev_f3_up], (f3_x, f3_y))
    assert (chess.G1, chess.F3) in app.arrows, f"Arrow (G1, F3) should be registered: {app.arrows}"

    # Add a second arrow from E2 to E4
    e2_x, e2_y = app.ui.square_to_screen_center(chess.E2, flipped=False)
    ev_e2_down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 3, 'pos': (e2_x, e2_y)})
    ev_e4_up = pygame.event.Event(pygame.MOUSEBUTTONUP, {'button': 3, 'pos': (e4_x, e4_y)})
    app.handle_game_input([ev_e2_down], (e2_x, e2_y))
    app.handle_game_input([ev_e4_up], (e4_x, e4_y))
    assert (chess.E2, chess.E4) in app.arrows
    assert len(app.arrows) == 2

    # Add circle highlight on D4
    d4_x, d4_y = app.ui.square_to_screen_center(chess.D4, flipped=False)
    app.handle_game_input([pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 3, 'pos': (d4_x, d4_y)})], (d4_x, d4_y))
    app.handle_game_input([pygame.event.Event(pygame.MOUSEBUTTONUP, {'button': 3, 'pos': (d4_x, d4_y)})], (d4_x, d4_y))
    assert chess.D4 in app.circles

    # Test rendering annotations overlay without crash
    app.ui.draw_annotations(app.circles, app.arrows, preview_arrow=(chess.D2, chess.D4), flipped=False)
    app.ui.draw_annotations(app.circles, app.arrows, preview_arrow=None, flipped=True)

    # 3. Left-click clears all arrows and circles
    ev_left = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': (e4_x, e4_y)})
    app.handle_game_input([ev_left], (e4_x, e4_y))
    assert len(app.arrows) == 0, f"Left-click should clear all arrows: {app.arrows}"
    assert len(app.circles) == 0, f"Left-click should clear all circles: {app.circles}"

    app.network.close()
    app.ai.close()
    print("  -> Tactical Annotations OK")

def test_board_themes():
    print("Testing Visual Board Themes (4 Themes)...")
    app = GameApp()

    expected_themes = ["bois", "emeraude", "neo", "marbre"]
    for th in expected_themes:
        assert th in THEMES, f"Missing theme in constants.py: {th}"
        data = THEMES[th]
        for key in ["name", "light_sq", "dark_sq", "frame", "frame_inner", "border_accent", "coord"]:
            assert key in data, f"Theme {th} missing key: {key}"

    # Test cycling through all 4 themes in UI
    ui = app.ui
    assert ui.theme_key == "bois"
    assert ui.theme["name"] == "Bois Noble"

    th2 = ui.cycle_theme()
    assert th2 == "emeraude"
    assert ui.theme["name"] == "Émeraude Tournoi"

    th3 = ui.cycle_theme()
    assert th3 == "neo"
    assert ui.theme["name"] == "Néo Sombre"

    th4 = ui.cycle_theme()
    assert th4 == "marbre"
    assert ui.theme["name"] == "Marbre & Verre"

    th5 = ui.cycle_theme()
    assert th5 == "bois"

    # Test app.cycle_theme method and button label
    app.cycle_theme()
    assert app.current_theme == "emeraude"
    assert "Émera" in app.btn_theme.text

    # Verify 3D board renders with all 4 themes without crashing
    for th in expected_themes:
        ui.set_theme(th)
        ui.draw_3d_board(flipped=False)
        ui.draw_3d_board(flipped=True)

    app.network.close()
    app.ai.close()
    print("  -> Board Themes OK")

def test_eval_bar_and_stockfish():
    print("Testing Real-Time Eval Bar & Stockfish Evaluation...")
    app = GameApp()
    app.reset_game()

    # 1. Starting board evaluation (Stockfish engine should be initialized via ensure_engine)
    score_cp, score_text = app.ai.evaluate_board_sync(app.board)
    assert isinstance(score_cp, (int, float))
    assert isinstance(score_text, str)
    assert app.ai.engine is not None, "Stockfish engine should be initialized"
    assert app.ai.is_monster is True, "Stockfish engine is_monster should be True"
    assert abs(score_cp) < 250, f"Starting position score should be near balanced: {score_cp}"

    # 2. Checkmate position evaluation (Scholar's mate)
    b_mate = chess.Board("r1bqkb1r/pppp1ppp/2n5/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 0 1")
    b_mate.push(chess.Move.from_uci("h5f7"))
    assert b_mate.is_checkmate()
    mate_cp, mate_text = app.ai.evaluate_board_sync(b_mate)
    assert mate_cp == 10000 or mate_cp == -10000 or "M" in mate_text

    # 3. Asynchronous evaluation callback
    res = []
    def on_done(cp, txt):
        res.append((cp, txt))

    app.ai.evaluate_board_async(app.board, on_done)
    timeout = 2.0
    t0 = time.time()
    while not res and (time.time() - t0) < timeout:
        time.sleep(0.05)
    assert len(res) == 1, "Async evaluation should invoke callback"

    # 4. Draw Eval Bar rendering
    app.ui.draw_eval_bar(EVAL_BAR_X, 44, EVAL_BAR_WIDTH, 604, 0.50, "0.0", flipped=False)
    app.ui.draw_eval_bar(EVAL_BAR_X, 44, EVAL_BAR_WIDTH, 604, 0.85, "+2.4", flipped=False)
    app.ui.draw_eval_bar(EVAL_BAR_X, 44, EVAL_BAR_WIDTH, 604, 0.15, "-3.1", flipped=True)
    app.ui.draw_eval_bar(EVAL_BAR_X, 44, EVAL_BAR_WIDTH, 604, 1.0, "M2", flipped=False)

    app.network.close()
    app.ai.close()
    print("  -> Eval Bar & Stockfish Evaluation OK")

def test_replay_navigation():
    print("Testing Interactive Replay & History Navigation...")
    app = GameApp()
    app.reset_game()

    # Execute moves: 1. e4 e5 2. Nf3 Nc6
    moves = ["e2e4", "e7e5", "g1f3", "b8c6"]
    for m in moves:
        app.execute_move(chess.Move.from_uci(m))

    assert len(app.board.move_stack) == 4
    assert app.replay_index == 4
    assert not app.is_replaying()

    # 1. Step backward with replay prev button or step_replay(-1)
    app.step_replay(-1)
    assert app.replay_index == 3
    assert app.is_replaying()
    
    # Display board should represent board state after 3 moves (1. e4 e5 2. Nf3)
    b3 = app.get_display_board()
    assert len(b3.move_stack) == 3
    assert b3.piece_at(chess.C6) is None, "Knight on c6 should not be present at move 3"
    assert b3.piece_at(chess.F3) is not None, "Knight on f3 should be present at move 3"

    # Live board should remain intact!
    assert len(app.board.move_stack) == 4
    assert app.board.piece_at(chess.C6) is not None

    # 2. Step backward to move 0 (starting board)
    app.replay_index = 0
    assert app.is_replaying()
    b0 = app.get_display_board()
    assert len(b0.move_stack) == 0
    assert b0.fen() == chess.STARTING_FEN

    # 3. Step forward with step_replay(1)
    app.step_replay(1)
    assert app.replay_index == 1
    b1 = app.get_display_board()
    assert len(b1.move_stack) == 1
    assert b1.piece_at(chess.E4) is not None

    # 4. Keyboard navigation (Left / Right / Home / End)
    # Simulate Left Arrow key
    ev_left = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_LEFT, 'unicode': ''})
    app.handle_game_input([ev_left], (0, 0))
    assert app.replay_index == 0

    # Simulate Right Arrow key
    ev_right = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RIGHT, 'unicode': ''})
    app.handle_game_input([ev_right], (0, 0))
    assert app.replay_index == 1

    # Simulate End key -> return to live game
    ev_end = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_END, 'unicode': ''})
    app.handle_game_input([ev_end], (0, 0))
    assert app.replay_index == 4
    assert not app.is_replaying()

    # 5. Clicking "Revenir au direct" button
    app.replay_index = 2
    assert app.is_replaying()
    # Click live button
    app.handle_game_input([pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': app.btn_replay_live.rect.center})], app.btn_replay_live.rect.center)
    assert app.replay_index == 4
    assert not app.is_replaying()

    app.network.close()
    app.ai.close()
    print("  -> Replay Navigation OK")

def test_player_cards_and_material():
    print("Testing Player Cards & Captured Material Tally...")
    app = GameApp()
    app.reset_game()

    # Initial material
    w_caps, b_caps, w_diff, b_diff = app.compute_material_stats(app.board)
    assert all(cnt == 0 for cnt in w_caps.values())
    assert all(cnt == 0 for cnt in b_caps.values())
    assert w_diff == 0 and b_diff == 0

    # White captures a pawn: 1. e4 d5 2. exd5
    app.execute_move(chess.Move.from_uci("e2e4"))
    app.execute_move(chess.Move.from_uci("d7d5"))
    app.execute_move(chess.Move.from_uci("e4d5"))

    w_caps, b_caps, w_diff, b_diff = app.compute_material_stats(app.board)
    assert w_caps['P'] == 1, f"White should have captured 1 pawn: {w_caps}"
    assert b_caps['P'] == 0
    assert w_diff == 1, f"White should have +1 material advantage: {w_diff}"
    assert b_diff == 0

    # Black captures White Queen: setup board without white queen to verify queen difference
    b_test = chess.Board()
    b_test.remove_piece_at(chess.D1) # Remove White Queen
    w_caps, b_caps, w_diff, b_diff = app.compute_material_stats(b_test)
    assert b_caps['Q'] == 1, f"Black should have captured Queen: {b_caps}"
    assert b_diff == 9, f"Black should have +9 material advantage: {b_diff}"
    assert w_diff == 0

    # Test clock string formatter
    app.time_limit = 300
    assert app.format_clock(300) == "05:00"
    assert app.format_clock(125) == "02:05"
    assert app.format_clock(9) == "00:09"
    app.time_limit = 0
    assert app.format_clock(0) == "∞"

    # Test quick audio mute toggle (M key) and flip board toggle (F key)
    assert not app.sounds.muted
    ev_m = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_m, 'unicode': 'm'})
    app.handle_game_input([ev_m], (0, 0))
    assert app.sounds.muted, "M key should mute sound"
    app.handle_game_input([ev_m], (0, 0))
    assert not app.sounds.muted, "M key should unmute sound"

    assert not app.flipped
    ev_f = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_f, 'unicode': 'f'})
    app.handle_game_input([ev_f], (0, 0))
    assert app.flipped, "F key should flip board"
    app.handle_game_input([ev_f], (0, 0))
    assert not app.flipped, "F key should unflip board"

    # Test draw_player_card execution
    card_rect = pygame.Rect(44, 10, 604, 30)
    app.ui.draw_player_card(card_rect, "Stockfish 19", "3600 GM", "bot", is_active_turn=True,
                            clock_str="03:45", clock_warn=False, captured_pieces=b_caps,
                            material_diff=b_diff, is_top=True)
    app.ui.draw_player_card(card_rect, "Vous", "1850", "human", is_active_turn=False,
                            clock_str="04:12", clock_warn=False, captured_pieces=w_caps,
                            material_diff=w_diff, is_top=False)

    # Verify _draw_player_cards logic for both White and Black player perspectives
    # Perspective 1: Player is White
    app.mode = "ai"
    app.player_color = chess.WHITE
    app.flipped = False
    captured_calls = []
    orig_draw_card = app.ui.draw_player_card
    def mock_draw_card(*args, **kwargs):
        captured_calls.append((args, kwargs))
    app.ui.draw_player_card = mock_draw_card

    app._draw_player_cards(app.board)
    assert len(captured_calls) == 2
    top_call, bot_call = captured_calls[0], captured_calls[1]
    # Top card must be Opponent (Stockfish/bot)
    assert "Stockfish" in top_call[0][1]
    assert top_call[1]["avatar_type"] == "bot"
    assert top_call[1]["is_top"] is True
    # Bottom card must be Player (Vous/human)
    assert "Vous" in bot_call[0][1]
    assert bot_call[1]["avatar_type"] == "human"
    assert bot_call[1]["is_top"] is False

    # Perspective 2: Player is Black (Flipped board)
    captured_calls.clear()
    app.player_color = chess.BLACK
    app.flipped = True
    app._draw_player_cards(app.board)
    assert len(captured_calls) == 2
    top_call, bot_call = captured_calls[0], captured_calls[1]
    # When playing Black (flipped=True):
    # Top card (White pieces) MUST be Opponent (Stockfish/bot)!
    assert "Stockfish" in top_call[0][1], f"Top card should be Stockfish when playing Black: {top_call[0][1]}"
    assert top_call[1]["avatar_type"] == "bot"
    assert top_call[1]["is_top"] is True
    # Bottom card (Black pieces) MUST be Player (Vous/human)!
    assert "Vous" in bot_call[0][1], f"Bottom card should be Vous when playing Black: {bot_call[0][1]}"
    assert bot_call[1]["avatar_type"] == "human"
    assert bot_call[1]["is_top"] is False

    app.ui.draw_player_card = orig_draw_card

    # Verify Replay button labels match exact requirements
    assert app.btn_replay_first.text == "< <", f"First button label should be '< <': {app.btn_replay_first.text}"
    assert app.btn_replay_last.text == "> >", f"Last button label should be '> >': {app.btn_replay_last.text}"

    app.network.close()
    app.ai.close()
    print("  -> Player Cards & Material Tally OK")

def run_all_enhancement_tests():
    print("=== RUNNING UI ENHANCEMENTS TEST SUITE ===")
    test_tactical_annotations()
    test_board_themes()
    test_eval_bar_and_stockfish()
    test_replay_navigation()
    test_player_cards_and_material()
    print("=== ALL UI ENHANCEMENT TESTS PASSED! ===")

if __name__ == "__main__":
    run_all_enhancement_tests()
