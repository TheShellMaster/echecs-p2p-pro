import os
import sys
import time
import chess
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from main import GameApp
from network import NetworkManager
from modals import PromotionModal, GameOverModal

def test_castling_and_secondary_animation():
    print("Testing Castling & Secondary Rook Animation...")
    app = GameApp()
    # Setup board for White Kingside castling
    # 1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. O-O
    app.reset_game(player_color=chess.WHITE, time_limit=0)
    for uci in ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5"]:
        app.execute_move(chess.Move.from_uci(uci))
        
    castle_move = chess.Move.from_uci("e1g1")
    assert castle_move in app.board.legal_moves, "Castling should be legal"
    app.execute_move(castle_move)
    
    # Check that animation has secondary rook slide
    assert app.ui.animation is not None
    assert app.ui.animation.from_sq == chess.E1
    assert app.ui.animation.to_sq == chess.G1
    assert app.ui.animation.secondary is not None
    rook_from, rook_to, rook_key = app.ui.animation.secondary
    assert rook_from == chess.H1
    assert rook_to == chess.F1
    assert rook_key == "wR"
    
    # Check SAN notation for castling
    assert app.move_history[-1]["white"] == "O-O"
    app.network.close()
    app.ai.close()
    print("  -> Castling animation and SAN notation OK")

def test_en_passant():
    print("Testing En Passant Move & Sound...")
    app = GameApp()
    # 1. e4 a6 2. e5 d5 3. exd6 (e.p.)
    app.reset_game(player_color=chess.WHITE, time_limit=0)
    for uci in ["e2e4", "a7a6", "e4e5", "d7d5"]:
        app.execute_move(chess.Move.from_uci(uci))
        
    ep_move = chess.Move.from_uci("e5d6")
    assert ep_move in app.board.legal_moves, "En passant should be legal"
    assert app.board.is_en_passant(ep_move)
    app.execute_move(ep_move)
    assert app.move_history[-1]["white"] == "exd6"
    assert app.board.piece_at(chess.D5) is None, "Captured pawn should be removed"
    app.network.close()
    app.ai.close()
    print("  -> En Passant OK")

def test_promotion_flow():
    print("Testing Pawn Promotion flow...")
    app = GameApp()
    # Board with White pawn on e7, can promote to e8
    app.board = chess.Board("8/4P3/8/8/8/8/8/4K2k w - - 0 1")
    app.reset_game(player_color=chess.WHITE, time_limit=0)
    app.board = chess.Board("8/4P3/8/8/8/8/8/4K2k w - - 0 1")
    
    # Try move e7 -> e8
    promoted = app.try_execute_player_move(chess.E7, chess.E8)
    assert promoted is True
    assert isinstance(app.active_modal, PromotionModal)
    assert app.pending_promotion == (chess.E7, chess.E8)
    
    # Simulate choosing Queen
    # Find queen button
    btn_q = app.active_modal.buttons[0]
    app.handle_modal_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': btn_q[0].center})], btn_q[0].center)
    assert app.active_modal is None
    assert app.board.piece_at(chess.E8).piece_type == chess.QUEEN
    assert app.move_history[-1]["white"] == "e8=Q"
    app.network.close()
    app.ai.close()
    print("  -> Promotion flow OK")

def test_checkmate_endgame():
    print("Testing Scholar's Mate (Checkmate)...")
    app = GameApp()
    app.reset_game(player_color=chess.WHITE, time_limit=0)
    for uci in ["e2e4", "e7e5", "d1h5", "b8c6", "f1c4", "g8f6", "h5f7"]:
        app.execute_move(chess.Move.from_uci(uci))
        
    assert app.board.is_checkmate()
    assert isinstance(app.active_modal, GameOverModal)
    assert "ÉCHEC ET MAT" in app.active_modal.message
    assert "Victoire des Blancs" in app.active_modal.message
    app.network.close()
    app.ai.close()
    print("  -> Checkmate endgame OK")

def test_empty_chat_and_server_names():
    print("Testing empty inputs for chat and server names...")
    app = GameApp()
    app.active_tab = "chat"
    app.chat_input.text = "   "
    app.send_chat_message()
    assert len(app.chat_messages) == 0, "Empty chat message should not be added"
    
    # Empty server name fallback
    app.network.set_server_name("")
    assert app.network.server_name == "Partie P2P"
    app.network.close()
    app.ai.close()
    print("  -> Empty inputs handling OK")

def test_rehost_after_game_over():
    print("Testing re-host after game over (Address already in use prevention)...")
    app = GameApp()
    app.network.host_game("Salon Rehost 1")
    app.reset_game(chess.WHITE, 0)
    app.state = "PLAY"
    app.trigger_game_over()
    # Click Menu on modal
    app.handle_modal_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': app.active_modal.btn_menu.rect.center})], app.active_modal.btn_menu.rect.center)
    assert app.state == "MENU"
    # Re-host now - should NOT throw OSError: Address already in use
    app.network.host_game("Salon Rehost 2")
    assert app.network.is_host is True
    app.network.close()
    app.ai.close()
    print("  -> Re-host after game over OK")

def test_p2p_timeout_sync():
    print("Testing P2P timeout synchronization...")
    host = NetworkManager()
    host.host_game("Host Timeout")
    client = NetworkManager()
    ok = client.connect_to("127.0.0.1")
    assert ok
    for _ in range(30):
        if host.connection:
            break
        time.sleep(0.05)
    assert host.connection is not None, "Host should have active connection"
    
    # Host sends timeout
    host.send_timeout("white")
    time.sleep(0.15)
    
    msgs = client.get_messages()
    timeout_msg = next((m for m in msgs if m.get("type") == "timeout"), None)
    assert timeout_msg is not None, f"Client did not receive timeout: {msgs}"
    assert timeout_msg["loser"] == "white"
    
    client.close()
    host.close()
    print("  -> P2P timeout synchronization OK")

def test_chat_utf8_long_messages_and_wrap():
    print("Testing UTF-8 encoding and chat message handling...")
    app = GameApp()
    app.active_tab = "chat"
    long_msg = "Bonjour tout le monde ! Prêt pour une belle partie d'échecs ? 🎯"
    app.chat_input.text = long_msg
    app.send_chat_message()
    assert len(app.chat_messages) == 1
    # Ensure message is NOT truncated to 24 chars
    assert app.chat_messages[0]["text"] == long_msg
    
    # Test drawing chat tab with word wrapping
    app.draw_side_panel((0, 0))
    app.network.close()
    app.ai.close()
    print("  -> UTF-8 encoding and chat wrapping OK")

def test_clock_runs_during_promotion():
    print("Testing that clock does not freeze during pawn promotion...")
    app = GameApp()
    app.reset_game(player_color=chess.WHITE, time_limit=300)
    app.board = chess.Board("8/4P3/8/8/8/8/8/4K2k w - - 0 1")
    # Initiate promotion move e7->e8
    app.try_execute_player_move(chess.E7, chess.E8)
    assert isinstance(app.active_modal, PromotionModal)
    
    # Simulate elapsed time
    app.last_clock_tick = time.time() - 3.0
    app.draw_play((0, 0), [])
    # Clock should have decreased even though PromotionModal is active!
    assert app.white_time < 300.0, f"White clock frozen during promotion: {app.white_time}"
    app.network.close()
    app.ai.close()
    print("  -> Clock running during promotion OK")

def test_captured_piece_in_animation():
    print("Testing captured piece retained in PieceAnimation...")
    app = GameApp()
    app.reset_game(player_color=chess.WHITE, time_limit=0)
    # Setup capture: 1. e4 d5 2. exd5
    app.execute_move(chess.Move.from_uci("e2e4"))
    app.execute_move(chess.Move.from_uci("d7d5"))
    cap_move = chess.Move.from_uci("e4d5")
    app.execute_move(cap_move)
    assert app.ui.animation is not None
    assert app.ui.animation.captured is not None
    cap_sq, cap_key = app.ui.animation.captured
    assert cap_sq == chess.D5
    assert cap_key == "bP"
    app.network.close()
    app.ai.close()
    print("  -> Captured piece in PieceAnimation OK")

def test_audio_no_clipping():
    print("Testing that audio synthesis does not clip (peak <= 0.86)...")
    import wave, struct
    for name in ["move.wav", "capture.wav", "check.wav", "gameover.wav"]:
        fp = os.path.join("assets", "sounds", name)
        with wave.open(fp, 'r') as wf:
            data = wf.readframes(wf.getnframes())
            samples = struct.unpack('<' + 'h' * (len(data) // 2), data)
            peak = max(abs(s) for s in samples) / 32767.0
            assert peak <= 0.86, f"{name} is clipping! Peak={peak}"
    print("  -> Audio synthesis no clipping OK")

if __name__ == "__main__":
    test_castling_and_secondary_animation()
    test_en_passant()
    test_promotion_flow()
    test_checkmate_endgame()
    test_empty_chat_and_server_names()
    test_rehost_after_game_over()
    test_p2p_timeout_sync()
    test_chat_utf8_long_messages_and_wrap()
    test_clock_runs_during_promotion()
    test_captured_piece_in_animation()
    test_audio_no_clipping()
    print("=== ALL EDGE CASE TESTS PASSED! ===")
