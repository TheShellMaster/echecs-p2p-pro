import os
import sys
import time
import math
import wave
import chess
import pygame

# Set dummy drivers for headless testing
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from constants import resource_path, TIME_OPTIONS, SCREEN_WIDTH, SCREEN_HEIGHT
from audio import SoundManager, ensure_sound_assets
from network import NetworkManager
from ui import UI, Button, TextInput, PieceAnimation
from modals import PromotionModal, AISettingsModal, LocalSettingsModal, GameOverModal
from main import GameApp

def test_resource_path():
    print("Testing resource_path...")
    p = resource_path("assets")
    assert os.path.exists(p), f"Asset path not found: {p}"
    p_sound = resource_path(os.path.join("assets", "sounds", "move.wav"))
    assert os.path.exists(p_sound), f"Sound path not found: {p_sound}"
    print("  -> resource_path OK")

def test_audio_synthesis_and_manager():
    print("Testing audio synthesis and SoundManager...")
    ensure_sound_assets()
    for name in ["move.wav", "capture.wav", "check.wav", "gameover.wav"]:
        fp = resource_path(os.path.join("assets", "sounds", name))
        assert os.path.isfile(fp), f"Missing sound file: {fp}"
        with wave.open(fp, 'r') as wf:
            assert wf.getframerate() == 44100, f"Unexpected framerate for {name}"
            assert wf.getnchannels() == 1, f"Unexpected channels for {name}"
            assert wf.getnframes() > 0, f"Empty audio file: {name}"

    sm = SoundManager()
    assert sm.enabled, "SoundManager should be enabled"
    assert "move" in sm.sounds
    assert "capture" in sm.sounds
    assert "check" in sm.sounds
    assert "gameover" in sm.sounds
    
    # Test audio triggers
    b = chess.Board()
    sm.play_for_move(b, is_capture=False, is_game_over=False)
    sm.play_for_move(b, is_capture=True, is_game_over=False)
    # Check board with check
    b_check = chess.Board("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3")
    assert b_check.is_check()
    sm.play_for_move(b_check, is_capture=False, is_game_over=False)
    sm.play_for_move(b, is_capture=False, is_game_over=True)
    print("  -> Audio synthesis and SoundManager OK")

def test_piece_animation():
    print("Testing PieceAnimation...")
    anim = PieceAnimation(chess.E2, chess.E4, "wP", start_time=1000, duration_ms=180)
    assert anim.progress(1000) == 0.0
    p_mid = anim.progress(1090)
    assert 0.0 < p_mid < 1.0
    assert anim.progress(1180) == 1.0
    assert anim.is_finished(1180)
    assert not anim.is_finished(1100)
    print("  -> PieceAnimation OK")

def test_game_app_flow_and_moves():
    print("Testing GameApp flow, animations, SAN notation, and clocks...")
    app = GameApp()
    
    # Test local game with 5 min timer
    app.reset_game(player_color=chess.WHITE, time_limit=300)
    assert app.time_limit == 300
    assert app.white_time == 300.0
    assert app.black_time == 300.0
    
    # Move 1: e4 (White)
    m1 = chess.Move.from_uci("e2e4")
    ok1 = app.execute_move(m1)
    assert ok1, "e2e4 should be legal"
    assert app.ui.animation is not None
    assert app.ui.animation.from_sq == chess.E2
    assert app.ui.animation.to_sq == chess.E4
    assert len(app.move_history) == 1
    assert app.move_history[0]["num"] == 1
    assert app.move_history[0]["white"] == "e4"
    assert app.move_history[0]["black"] == ""

    # Move 2: e5 (Black)
    m2 = chess.Move.from_uci("e7e5")
    ok2 = app.execute_move(m2)
    assert ok2, "e7e5 should be legal"
    assert len(app.move_history) == 1
    assert app.move_history[0]["black"] == "e5"

    # Move 3: Nf3 (White)
    m3 = chess.Move.from_uci("g1f3")
    ok3 = app.execute_move(m3)
    assert ok3, "Nf3 should be legal"
    assert len(app.move_history) == 2
    assert app.move_history[1]["white"] == "Nf3"
    assert app.move_history[1]["black"] == ""

    # Move 4: Nc6 (Black)
    m4 = chess.Move.from_uci("b8c6")
    ok4 = app.execute_move(m4)
    assert ok4, "Nc6 should be legal"
    assert app.move_history[1]["black"] == "Nc6"

    # Test clock decrement
    app.last_clock_tick = time.time() - 5.0  # simulate 5 seconds passed
    # White turn now (since move 4 was Black)
    app.draw_play((0, 0), [])
    assert app.white_time < 300.0, f"White clock did not decrement: {app.white_time}"

    # Test timeout trigger
    app.white_time = 0.001
    app.last_clock_tick = time.time() - 1.0
    app.draw_play((0, 0), [])
    assert isinstance(app.active_modal, GameOverModal), "Timeout should trigger GameOverModal"
    assert "TEMPS ÉCOULÉ" in app.active_modal.message
    
    # Test chat input and messaging
    app.active_tab = "chat"
    app.chat_input.text = "Hello opponent!"
    app.send_chat_message()
    assert len(app.chat_messages) >= 1
    assert app.chat_messages[0]["text"] == "Hello opponent!"
    assert app.chat_input.text == ""

    # Test switching tabs
    app.active_tab = "history"
    assert app.active_tab == "history"

    app.network.close()
    app.ai.close()
    print("  -> GameApp flow, animations, SAN notation, and clocks OK")

def test_p2p_network_chat_and_custom_name():
    print("Testing P2P network chat and custom server name...")
    host = NetworkManager()
    custom_name = "Salon de Thomas"
    host.host_game(server_name=custom_name)
    assert host.server_name == custom_name
    
    # Dynamic name change
    host.set_server_name("Salon VIP de Thomas")
    assert host.server_name == "Salon VIP de Thomas"
    
    time.sleep(0.1)
    client = NetworkManager()
    ok = client.connect_to("127.0.0.1")
    assert ok, "Client should connect to loopback"
    time.sleep(0.1)

    # Chat test
    client.send_chat("Thomas", "Prêt pour une partie ?")
    time.sleep(0.1)
    msgs = host.get_messages()
    chat_msg = next((m for m in msgs if m.get("type") == "chat"), None)
    assert chat_msg is not None, f"Host should receive chat: {msgs}"
    assert chat_msg["sender"] == "Thomas"
    assert chat_msg["text"] == "Prêt pour une partie ?"

    # Config sync test
    host.send_config(300)
    time.sleep(0.1)
    c_msgs = client.get_messages()
    config_msg = next((m for m in c_msgs if m.get("type") == "config"), None)
    assert config_msg is not None, f"Client should receive config: {c_msgs}"
    assert config_msg["time_limit"] == 300

    client.close()
    host.close()
    print("  -> P2P network chat and custom server name OK")

def test_modals():
    print("Testing Modals...")
    ai_modal = AISettingsModal()
    assert ai_modal.selected_time == 0
    assert ai_modal.selected_diff == 4
    # Test setting time
    for btn, t_val in ai_modal.time_buttons:
        if t_val == 180:
            ai_modal.handle_click(btn.rect.center)
            assert ai_modal.selected_time == 180
            break

    local_modal = LocalSettingsModal()
    assert local_modal.selected_time == 0
    for btn, t_val in local_modal.time_buttons:
        if t_val == 600:
            local_modal.handle_click(btn.rect.center)
            assert local_modal.selected_time == 600
            break

    go_modal = GameOverModal("Victoire", "Mat")
    assert go_modal.message == "Victoire"
    print("  -> Modals OK")

def run_all_tests():
    print("=== RUNNING FULL TEST SUITE ===")
    test_resource_path()
    test_audio_synthesis_and_manager()
    test_piece_animation()
    test_game_app_flow_and_moves()
    test_p2p_network_chat_and_custom_name()
    test_modals()
    print("=== ALL TESTS PASSED! ===")

if __name__ == "__main__":
    run_all_tests()
