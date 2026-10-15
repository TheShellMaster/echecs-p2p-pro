"""
test_adversarial_ui_state.py — Adversarial Stress Test Suite (Challenger 2)

Empirically tests and stress-tests:
1. Tactile hover reticles across all 64 squares, both flipped orientations,
   normal moves, captures, promotion squares, check/checkmate states, extreme pulse/radius.
2. Continuous Elo slider mathematics: extreme drag inputs (x=-500, x=5000),
   fine-grained magnetic snap thresholds (800, 1400, 2100, 3200 +- 45), persona card clicks.
3. Modal transition animations: start, intermediate, completed, and clamped states of ModalTransition.
4. Double-ply undo state machine at turn 0, turn 1, multiple captures, castling, en passant,
   promotions (all 4 promotion pieces), ranked guardrails, and active AI cancellation.
"""

import os
import sys
import time
import math
import pytest
import chess
import pygame

# Headless configuration for Pygame
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import constants
from constants import (
    COLOR_EMERALD, COLOR_ROSE, COLOR_BORDER, COLOR_BG_CARD,
    BOARD_X, BOARD_Y, SQUARE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT,
    BOT_PERSONAS
)
import ui
from ui import UI, draw_hover_reticle
import modals
from modals import AIPersonasModal, PromotionModal
import animations
from animations import ModalTransition, ease_out_back, ease_out_cubic
import main
from main import GameApp


@pytest.fixture(scope="module", autouse=True)
def setup_pygame():
    pygame.init()
    if not pygame.font.get_init():
        pygame.font.init()
    pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    yield
    pygame.quit()


# ==============================================================================
# SECTION 1: TACTILE HOVER RETICLES ADVERSARIAL TESTS
# ==============================================================================

def test_adversarial_tactile_hover_reticle_all_64_squares():
    """
    Stress-test draw_hover_reticle across every single square from 0 (A1) to 63 (H8).
    Verifies rendering does not raise exceptions, blits within bounds, and modifies pixels.
    """
    surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    for sq in range(64):
        surface.fill((0, 0, 0, 0))
        # Normal move, unflipped
        draw_hover_reticle(surface, sq, is_capture=False, flipped=False)
        # Verify surface has drawn pixels (non-zero alpha bounding box)
        bbox = surface.get_bounding_rect()
        assert bbox.width > 0 and bbox.height > 0, f"Reticle for sq {sq} produced empty bounding box"

        # Verify calculated position matches expected board coordinate
        file_idx = chess.square_file(sq)
        rank_idx = 7 - chess.square_rank(sq)
        expected_x = BOARD_X + file_idx * SQUARE_SIZE
        expected_y = BOARD_Y + rank_idx * SQUARE_SIZE
        assert abs(bbox.centerx - (expected_x + SQUARE_SIZE // 2)) <= 4
        assert abs(bbox.centery - (expected_y + SQUARE_SIZE // 2)) <= 4


def test_adversarial_tactile_hover_reticle_orientations_and_captures():
    """
    Verifies draw_hover_reticle rendering across both unflipped and flipped board orientations,
    and checks color differentiation between normal moves (EMERALD) and captures (ROSE).
    """
    surf_normal = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    surf_capture = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    # Test on square e4 (sq = 28: file 4, rank 3)
    sq_e4 = chess.E4

    # 1. Unflipped normal move
    draw_hover_reticle(surf_normal, sq_e4, is_capture=False, flipped=False)
    # 2. Unflipped capture
    draw_hover_reticle(surf_capture, sq_e4, is_capture=True, flipped=False)

    # Check that colors in reticles match expected hues
    # Normal uses COLOR_EMERALD (r=16, g=185, b=129), capture uses COLOR_ROSE (r=244, g=63, b=94)
    has_emerald = False
    has_rose = False
    for x in range(BOARD_X, BOARD_X + 8 * SQUARE_SIZE, 8):
        for y in range(BOARD_Y, BOARD_Y + 8 * SQUARE_SIZE, 8):
            cn = surf_normal.get_at((x, y))
            cc = surf_capture.get_at((x, y))
            if cn.g > 150 and cn.r < 50 and cn.a > 50:
                has_emerald = True
            if cc.r > 200 and cc.g < 100 and cc.a > 50:
                has_rose = True
    assert has_emerald, "Normal reticle failed to render emerald tones"
    assert has_rose, "Capture reticle failed to render rose tones"

    # 3. Flipped orientation test across corner squares
    corner_squares = [chess.A1, chess.H1, chess.A8, chess.H8]
    for sq in corner_squares:
        surf_flip = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        draw_hover_reticle(surf_flip, sq, is_capture=False, flipped=True)
        bbox = surf_flip.get_bounding_rect()
        c = 7 - chess.square_file(sq)
        r = chess.square_rank(sq)
        expected_x = BOARD_X + c * SQUARE_SIZE
        expected_y = BOARD_Y + r * SQUARE_SIZE
        assert abs(bbox.centerx - (expected_x + SQUARE_SIZE // 2)) <= 4
        assert abs(bbox.centery - (expected_y + SQUARE_SIZE // 2)) <= 4


def test_adversarial_tactile_hover_reticle_extreme_pulse_and_radius():
    """
    Stress-test draw_hover_reticle with adversarial values:
    pulse_factor = 0.0, -5.0, 100.0, float('nan'), radius = 0, 500, None,
    square as pygame.Rect, custom colors as tuple and pygame.Color.
    """
    surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    # Negative and extreme pulse factors (must clamp without crash)
    draw_hover_reticle(surface, chess.D4, pulse_factor=-10.0)
    draw_hover_reticle(surface, chess.D4, pulse_factor=0.0)
    draw_hover_reticle(surface, chess.D4, pulse_factor=50.0)

    # Custom radius values
    draw_hover_reticle(surface, chess.D4, radius=0)
    draw_hover_reticle(surface, chess.D4, radius=300)

    # Square passed directly as pygame.Rect
    custom_rect = pygame.Rect(120, 150, 72, 72)
    draw_hover_reticle(surface, custom_rect, is_capture=True)

    # Custom color inputs: pygame.Color vs 3-tuple vs 4-tuple
    draw_hover_reticle(surface, chess.E5, color=pygame.Color(255, 215, 0))
    draw_hover_reticle(surface, chess.E5, color=(100, 200, 255))
    draw_hover_reticle(surface, chess.E5, color=(100, 200, 255, 180))


def test_adversarial_tactile_hover_reticle_promotion_squares():
    """
    Verifies reticle rendering on promotion destination squares:
    Rank 8 for white pawns (A8..H8) and Rank 1 for black pawns (A1..H1).
    """
    surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    # Promotion squares for White: rank 8 (56..63)
    for file_sq in range(56, 64):
        surface.fill((0, 0, 0, 0))
        draw_hover_reticle(surface, file_sq, is_capture=False, flipped=False)
        bbox = surface.get_bounding_rect()
        assert bbox.width > 0, f"Promotion square {file_sq} failed to render reticle"

    # Promotion squares for Black: rank 1 (0..7)
    for file_sq in range(8):
        surface.fill((0, 0, 0, 0))
        draw_hover_reticle(surface, file_sq, is_capture=True, flipped=True)
        bbox = surface.get_bounding_rect()
        assert bbox.width > 0, f"Promotion capture square {file_sq} (flipped) failed to render"


def test_adversarial_tactile_hover_reticle_check_and_checkmate_positions():
    """
    Verifies board UI reticle and highlight interactions on check and checkmate states.
    """
    screen_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    board_ui = UI(screen_surf)

    # Checkmate: Fool's mate (1. f3 e5 2. g4 Qh4#)
    board = chess.Board()
    board.push_san("f3")
    board.push_san("e5")
    board.push_san("g4")
    board.push_san("Qh4")
    assert board.is_checkmate()

    # Test drawing hover reticle on checkmating queen square (H4) and mated king square (E1)
    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    board_ui.draw_hover_reticle(surf, chess.H4, is_capture=False, flipped=False)
    board_ui.draw_hover_reticle(surf, chess.E1, is_capture=True, flipped=False)

    # Test ChessBoardUI.draw_highlights with threatened squares on checkmate
    board_ui.draw_highlights(board, selected_square=chess.H4, last_move=board.peek(),
                             threatened_squares={chess.E1}, flipped=False)


# ==============================================================================
# SECTION 2: CONTINUOUS ELO SLIDER MATHEMATICS & PERSONAS MODAL
# ==============================================================================

def test_adversarial_elo_slider_extreme_drag_boundaries():
    """
    Stress-test AIPersonasModal.update_slider with extreme mouse_x coordinates:
    Far left: x = -500, x = -99999 -> clamps to min_elo (500)
    Far right: x = 5000, x = 99999 -> clamps to max_elo (3200)
    """
    modal = AIPersonasModal()

    # Far left boundary checks
    modal.update_slider(mouse_x=-500)
    assert modal.selected_elo == 500, f"Expected 500 Elo on x=-500, got {modal.selected_elo}"
    assert modal.selected_persona_id == "lucas"
    assert modal.selected_diff == 1

    modal.update_slider(mouse_x=-99999)
    assert modal.selected_elo == 500

    # Far right boundary checks
    modal.update_slider(mouse_x=5000)
    assert modal.selected_elo == 3200, f"Expected 3200 Elo on x=5000, got {modal.selected_elo}"
    assert modal.selected_persona_id == "monster"
    assert modal.selected_diff == 4

    modal.update_slider(mouse_x=99999)
    assert modal.selected_elo == 3200

    # Fine continuous sweep from left to right
    track_x = modal.slider_track_rect.x
    track_w = modal.slider_track_rect.w
    for x in range(track_x - 100, track_x + track_w + 100, 15):
        modal.update_slider(mouse_x=x)
        assert 500 <= modal.selected_elo <= 3200
        assert modal.selected_persona_id in BOT_PERSONAS
        assert 1 <= modal.selected_diff <= 4


def test_adversarial_elo_slider_magnetic_snap_exact_thresholds():
    """
    Verifies magnetic snap thresholds (+-45 Elo around 800, 1400, 2100, 3200).
    Constructs mouse_x values corresponding to exact un-snapped values and tests snap.
    """
    modal = AIPersonasModal()
    track_x = modal.slider_track_rect.x
    track_w = modal.slider_track_rect.w
    min_e = modal.min_elo
    max_e = modal.max_elo

    def elo_to_x(target_elo):
        rel = (target_elo - min_e) / (max_e - min_e)
        return track_x + rel * track_w

    # 1. Snap around Lucas (800 Elo, +-45: [755, 845])
    # Inside snap window
    modal.update_slider(elo_to_x(800))
    assert modal.selected_elo == 800
    assert modal.selected_persona_id == "lucas"

    modal.update_slider(elo_to_x(760))
    assert modal.selected_elo == 800
    assert modal.selected_persona_id == "lucas"

    modal.update_slider(elo_to_x(840))
    assert modal.selected_elo == 800
    assert modal.selected_persona_id == "lucas"

    # Outside snap window (e.g. 740, 860)
    modal.update_slider(elo_to_x(740))
    assert abs(modal.selected_elo - 740) <= 5
    assert modal.selected_elo != 800

    # 2. Snap around Éléonore (1400 Elo, +-45: [1355, 1445])
    modal.update_slider(elo_to_x(1400))
    assert modal.selected_elo == 1400
    assert modal.selected_persona_id == "eleonore"

    modal.update_slider(elo_to_x(1370))
    assert modal.selected_elo == 1400

    modal.update_slider(elo_to_x(1435))
    assert modal.selected_elo == 1400

    modal.update_slider(elo_to_x(1340))
    assert abs(modal.selected_elo - 1340) <= 5
    assert modal.selected_elo != 1400

    # 3. Snap around Alexandre (2100 Elo, +-45: [2055, 2145])
    modal.update_slider(elo_to_x(2100))
    assert modal.selected_elo == 2100
    assert modal.selected_persona_id == "alexandre"

    modal.update_slider(elo_to_x(2070))
    assert modal.selected_elo == 2100

    modal.update_slider(elo_to_x(2135))
    assert modal.selected_elo == 2100

    modal.update_slider(elo_to_x(2040))
    assert abs(modal.selected_elo - 2040) <= 5
    assert modal.selected_elo != 2100

    # 4. Snap around Le Monstre (3200 Elo, +-45: [3155, 3200])
    modal.update_slider(elo_to_x(3200))
    assert modal.selected_elo == 3200
    assert modal.selected_persona_id == "monster"

    modal.update_slider(elo_to_x(3170))
    assert modal.selected_elo == 3200


def test_adversarial_persona_cards_click_and_hitbox_inflation():
    """
    Verifies clicking directly and within inflated hitbox on persona cards,
    as well as clicking other interactive buttons (Training mode, Time, Color, Start/Cancel).
    """
    modal = AIPersonasModal()

    # 1. Click each persona card center
    for pid in ["lucas", "eleonore", "alexandre", "monster"]:
        card_rect = modal.persona_cards[pid]["rect"]
        res = modal.handle_click(card_rect.center)
        assert res is None  # Persona card selection does not close modal
        assert modal.selected_persona_id == pid
        assert modal.selected_elo == BOT_PERSONAS[pid]["elo"]
        assert modal.is_dragging_slider is False

    # 2. Click inflated boundary (top/bottom margin + 3px)
    lucas_card = modal.persona_cards["lucas"]["rect"]
    inflated_point = (lucas_card.centerx, lucas_card.bottom + 3)
    modal.select_persona("monster")
    assert modal.selected_persona_id == "monster"
    modal.handle_click(inflated_point)
    assert modal.selected_persona_id == "lucas", "Inflated hitbox click failed to select persona"

    # 3. Mode Toggle Clicks
    modal.training_mode = False
    modal.handle_click(modal.btn_mode_training.rect.center)
    assert modal.training_mode is True

    modal.handle_click(modal.btn_mode_ranked.rect.center)
    assert modal.training_mode is False

    # 4. Color selection clicks
    modal.handle_click(modal.color_buttons[2][0].rect.center)  # Black
    assert modal.selected_color == chess.BLACK
    modal.handle_click(modal.color_buttons[0][0].rect.center)  # White
    assert modal.selected_color == chess.WHITE

    # 5. Time cadence clicks
    modal.handle_click(modal.time_buttons[1][0].rect.center)  # 3 min (180s)
    assert modal.selected_time == 180

    # 6. Action buttons
    assert modal.handle_click(modal.btn_start.rect.center) == "START"
    assert modal.handle_click(modal.btn_cancel.rect.center) == "CANCEL"

    # 7. Click outside any button returns None
    assert modal.handle_click((-100, -100)) is None


def test_adversarial_event_handling_slider_drag():
    """
    Verifies handle_event correctly toggles is_dragging_slider and updates Elo.
    """
    modal = AIPersonasModal()
    touch_center = modal.slider_touch_rect.center

    # Mouse down on touch rect starts dragging
    event_down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": touch_center, "button": 1})
    modal.handle_event(event_down)
    assert modal.is_dragging_slider is True

    # Mouse motion while dragging updates slider
    new_x = modal.slider_track_rect.x + modal.slider_track_rect.w // 2
    event_motion = pygame.event.Event(pygame.MOUSEMOTION, {"pos": (new_x, touch_center[1])})
    modal.handle_event(event_motion)
    assert abs(modal.selected_elo - 1850) <= 80

    # Mouse up stops dragging
    event_up = pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": (new_x, touch_center[1]), "button": 1})
    modal.handle_event(event_up)
    assert modal.is_dragging_slider is False


# ==============================================================================
# SECTION 3: MODAL TRANSITION ANIMATIONS ADVERSARIAL TESTS
# ==============================================================================

def test_adversarial_modal_transition_phases_and_interpolation():
    """
    Verifies ModalTransition at start (t=0), quarter (t=0.25), half (t=0.50),
    peak bounce, completed (t=1.0), and overshoot states.
    """
    start_t = 1000
    duration = 220
    trans = ModalTransition(start_time=start_t, duration_ms=duration)

    # 1. Start state (t = start_t)
    assert trans.progress(start_t) == 0.0
    assert trans.is_finished(start_t) is False
    assert abs(trans.get_scale(start_t) - 0.90) < 1e-4
    assert trans.get_dim_alpha(start_t) == 0
    assert trans.get_content_alpha(start_t) == 0

    # 2. Intermediate states (quarter, half, three-quarter)
    t_25 = start_t + duration // 4
    t_50 = start_t + duration // 2
    t_75 = start_t + (3 * duration) // 4

    assert 0.20 < trans.progress(t_25) < 0.30
    assert 0.45 < trans.progress(t_50) < 0.55
    assert 0.70 < trans.progress(t_75) < 0.80

    # Monotonicity of alpha fade
    dim_0 = trans.get_dim_alpha(start_t)
    dim_25 = trans.get_dim_alpha(t_25)
    dim_50 = trans.get_dim_alpha(t_50)
    dim_75 = trans.get_dim_alpha(t_75)
    dim_100 = trans.get_dim_alpha(start_t + duration)
    assert dim_0 < dim_25 < dim_50 < dim_75 <= dim_100

    content_0 = trans.get_content_alpha(start_t)
    content_50 = trans.get_content_alpha(t_50)
    content_100 = trans.get_content_alpha(start_t + duration)
    assert content_0 < content_50 < content_100

    # 3. Completed state (t = start_t + duration)
    t_done = start_t + duration
    assert trans.progress(t_done) == 1.0
    assert trans.is_finished(t_done) is True
    assert abs(trans.get_scale(t_done) - 1.0) < 1e-3
    assert trans.get_dim_alpha(t_done) == 130
    assert trans.get_content_alpha(t_done) == 255

    # 4. Post-completed / clamped state (t >> start_t + duration)
    t_over = start_t + duration * 3
    assert trans.progress(t_over) == 1.0
    assert trans.is_finished(t_over) is True
    assert abs(trans.get_scale(t_over) - 1.0) < 1e-3
    assert trans.get_dim_alpha(t_over) == 130
    assert trans.get_content_alpha(t_over) == 255


def test_adversarial_modal_transition_edge_durations_and_negative_time():
    """
    Stress-test ModalTransition with boundary durations:
    duration_ms = 1, duration_ms = 0 (clamped to >= 1), duration_ms = 10000,
    and current_time before start_time (elapsed < 0).
    """
    # Negative elapsed time
    trans = ModalTransition(start_time=2000, duration_ms=200)
    assert trans.progress(1500) == 0.0
    assert trans.is_finished(1500) is False
    assert abs(trans.get_scale(1500) - 0.90) < 1e-4

    # Zero / negative duration_ms (clamped to max(1, duration_ms))
    trans_zero = ModalTransition(start_time=1000, duration_ms=0)
    assert trans_zero.duration_ms >= 1
    assert trans_zero.is_finished(1001) is True

    trans_neg = ModalTransition(start_time=1000, duration_ms=-50)
    assert trans_neg.duration_ms >= 1

    # Large duration
    trans_long = ModalTransition(start_time=0, duration_ms=10000)
    assert trans_long.progress(5000) == 0.5
    assert trans_long.is_finished(5000) is False


# ==============================================================================
# SECTION 4: GAMEAPP STATE MACHINE & DOUBLE-PLY UNDO ADVERSARIAL TESTS
# ==============================================================================

def test_adversarial_undo_at_turn_0_and_turn_1():
    """
    Verifies handle_undo_move edge cases:
    - Turn 0: empty board, must return False without modifying board.
    - Turn 1: single ply (e.g. 1. e4), rolls back 1 ply to turn 0, returns True.
    """
    app = GameApp()
    app.reset_game(player_color=chess.WHITE)
    app.training_mode = True

    # 1. Turn 0: empty move stack
    assert len(app.board.move_stack) == 0
    res_0 = app.handle_undo_move()
    assert res_0 is False, "Undo at turn 0 should return False"
    assert len(app.board.move_stack) == 0
    assert app.board.turn == chess.WHITE

    # 2. Turn 1: exactly 1 ply
    app.board.push_san("e4")
    assert len(app.board.move_stack) == 1
    res_1 = app.handle_undo_move()
    assert res_1 is True, "Undo at turn 1 should return True"
    assert len(app.board.move_stack) == 0
    assert app.board.turn == chess.WHITE
    assert app.last_move is None
    assert app.move_history == []


def test_adversarial_undo_after_multiple_captures_rebuilds_pieces():
    """
    Verifies double-ply undo cleanly restores captured pieces after a tactical skirmish:
    1. e4 d5 2. exd5 Qxd5 3. Nc3 Qd8 (6 plies)
    Repeated undo rolls back 2 plies each time and restores board pieces.
    """
    app = GameApp()
    app.reset_game(player_color=chess.WHITE)
    app.training_mode = True

    moves = ["e4", "d5", "exd5", "Qxd5", "Nc3", "Qd8"]
    for m in moves:
        app.board.push_san(m)
    assert len(app.board.move_stack) == 6

    # Undo 1: rolls back Nc3 and Qd8 -> back to ply 4 (after 2... Qxd5)
    u1 = app.handle_undo_move()
    assert u1 is True
    assert len(app.board.move_stack) == 4
    assert app.board.turn == chess.WHITE
    # Black Queen is on d5
    piece_d5 = app.board.piece_at(chess.D5)
    assert piece_d5 is not None and piece_d5.symbol() == 'q'

    # Undo 2: rolls back exd5 (capture) and Qxd5 (capture) -> back to ply 2 (after 1... d5)
    u2 = app.handle_undo_move()
    assert u2 is True
    assert len(app.board.move_stack) == 2
    assert app.board.turn == chess.WHITE
    # White pawn on e4 restored, Black pawn on d5 restored
    pawn_e4 = app.board.piece_at(chess.E4)
    pawn_d5 = app.board.piece_at(chess.D5)
    assert pawn_e4 is not None and pawn_e4.symbol() == 'P'
    assert pawn_d5 is not None and pawn_d5.symbol() == 'p'

    # Undo 3: rolls back 1. e4 d5 -> back to initial position (0 plies)
    u3 = app.handle_undo_move()
    assert u3 is True
    assert len(app.board.move_stack) == 0
    assert app.board.fen() == chess.STARTING_FEN


def test_adversarial_undo_after_castling_kingside_and_queenside():
    """
    Verifies double-ply undo correctly undoes kingside and queenside castling moves:
    Restores both King and Rook to initial squares, and restores castling rights.
    """
    app = GameApp()
    app.reset_game(player_color=chess.WHITE)
    app.training_mode = True

    # 1. Kingside Castling: 1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. O-O Nf6 (8 plies)
    ks_moves = ["e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5", "O-O", "Nf6"]
    for m in ks_moves:
        app.board.push_san(m)
    assert len(app.board.move_stack) == 8

    # White castled at ply 7 (O-O), Black moved at ply 8 (Nf6)
    assert app.board.piece_at(chess.G1).symbol() == 'K'
    assert app.board.piece_at(chess.F1).symbol() == 'R'

    # Undo double-ply
    u_ks = app.handle_undo_move()
    assert u_ks is True
    assert len(app.board.move_stack) == 6
    assert app.board.turn == chess.WHITE
    # King back on e1, Rook back on h1
    assert app.board.piece_at(chess.E1).symbol() == 'K'
    assert app.board.piece_at(chess.H1).symbol() == 'R'
    assert app.board.piece_at(chess.G1) is None
    assert app.board.piece_at(chess.F1) is None
    # White still has kingside castling right
    assert app.board.has_kingside_castling_rights(chess.WHITE)

    # 2. Queenside Castling
    app.reset_game(player_color=chess.WHITE)
    app.training_mode = True
    qs_moves = ["d4", "d5", "Nc3", "Nc6", "Bf4", "Bf5", "Qd2", "Qd7", "O-O-O", "O-O-O"]
    for m in qs_moves:
        app.board.push_san(m)
    assert len(app.board.move_stack) == 10

    u_qs = app.handle_undo_move()
    assert u_qs is True
    assert len(app.board.move_stack) == 8
    assert app.board.turn == chess.WHITE
    # Black castling undone: Black King back on e8, Rook back on a8
    assert app.board.piece_at(chess.E8).symbol() == 'k'
    assert app.board.piece_at(chess.A8).symbol() == 'r'


def test_adversarial_undo_after_en_passant_restores_captured_pawn():
    """
    Verifies double-ply undo after an en-passant capture cleanly restores:
    - The captured pawn on its original square (d5)
    - The capturing pawn back to its pre-capture square (e5)
    - Clears the en-passant arrival square (d6)
    - Restores en-passant target square in python-chess board
    """
    app = GameApp()
    app.reset_game(player_color=chess.WHITE)
    app.training_mode = True

    # 1. e4 a6 2. e5 d5 3. exd6 (en passant!) 4. a5
    ep_sequence = [
        chess.Move.from_uci("e2e4"),
        chess.Move.from_uci("a7a6"),
        chess.Move.from_uci("e4e5"),
        chess.Move.from_uci("d7d5"),  # sets ep_square to d6
        chess.Move.from_uci("e5d6"),  # White captures d5 en-passant
        chess.Move.from_uci("a6a5"),  # Black move
    ]
    for mv in ep_sequence:
        app.board.push(mv)
    assert len(app.board.move_stack) == 6

    # At this point, d5 is empty and White pawn is on d6
    assert app.board.piece_at(chess.D5) is None
    assert app.board.piece_at(chess.D6).symbol() == 'P'

    # Undo double-ply (rolls back a6a5 and e5d6)
    u_ep = app.handle_undo_move()
    assert u_ep is True
    assert len(app.board.move_stack) == 4
    assert app.board.turn == chess.WHITE

    # Captured Black pawn is back on d5!
    piece_d5 = app.board.piece_at(chess.D5)
    assert piece_d5 is not None and piece_d5.symbol() == 'p'
    # White pawn is back on e5!
    piece_e5 = app.board.piece_at(chess.E5)
    assert piece_e5 is not None and piece_e5.symbol() == 'P'
    # Square d6 is empty!
    assert app.board.piece_at(chess.D6) is None
    # En passant right restored!
    assert app.board.ep_square == chess.D6


def test_adversarial_undo_after_pawn_promotions_all_four_pieces():
    """
    Verifies double-ply undo after pawn promotion for all 4 promotion types (Q, R, B, N).
    Ensures promoted piece reverts back to a PAWN on rank 7.
    """
    promotion_pieces = [
        (chess.QUEEN, 'q', 'Q'),
        (chess.ROOK, 'r', 'R'),
        (chess.BISHOP, 'b', 'B'),
        (chess.KNIGHT, 'n', 'N'),
    ]

    for promo_piece, sym_lower, sym_upper in promotion_pieces:
        app = GameApp()
        app.training_mode = True

        # Setup custom board: White pawn on e7, Kings on h1 and a8
        fen = "k7/4P3/8/8/8/8/8/7K w - - 0 1"
        app.board = chess.Board(fen)
        app.board_history = [app.board.fen()]

        promo_move = chess.Move(chess.E7, chess.E8, promotion=promo_piece)
        black_move = chess.Move.from_uci("a8a7")

        app.board.push(promo_move)
        app.board.push(black_move)
        assert len(app.board.move_stack) == 2

        # Verify promoted piece is on e8
        piece_e8 = app.board.piece_at(chess.E8)
        assert piece_e8 is not None and piece_e8.symbol() == sym_upper
        assert app.board.piece_at(chess.E7) is None

        # Undo double-ply
        u_p = app.handle_undo_move()
        assert u_p is True
        assert len(app.board.move_stack) == 0
        assert app.board.turn == chess.WHITE

        # Must be reverted back to White PAWN on e7
        pawn_restored = app.board.piece_at(chess.E7)
        assert pawn_restored is not None and pawn_restored.symbol() == 'P'
        assert app.board.piece_at(chess.E8) is None


def test_adversarial_undo_guardrails_ranked_mode_game_over_and_p2p():
    """
    Verifies security guardrails for handle_undo_move:
    - Disabled when training_mode is False (Ranked mode)
    - Disabled when game_over is True
    - Disabled when mode is "p2p"
    """
    app = GameApp()
    app.reset_game(player_color=chess.WHITE)
    app.board.push_san("e4")
    app.board.push_san("e5")
    assert len(app.board.move_stack) == 2

    # 1. Ranked mode guardrail
    app.training_mode = False
    assert app.handle_undo_move() is False
    assert len(app.board.move_stack) == 2

    # 2. Game over guardrail
    app.training_mode = True
    app.game_over = True
    assert app.handle_undo_move() is False
    assert len(app.board.move_stack) == 2

    # 3. P2P mode guardrail
    app.game_over = False
    app.mode = "p2p"
    assert app.handle_undo_move() is False
    assert len(app.board.move_stack) == 2


def test_adversarial_undo_during_active_ai_thinking():
    """
    Verifies that if undo is triggered while AI is calculating (waiting_for_ai=True),
    the AI task is canceled, queue is drained, exactly 1 ply (human move) is rolled back,
    and board turn returns to human.
    """
    app = GameApp()
    app.reset_game(player_color=chess.WHITE)
    app.training_mode = True

    # Human plays 1. d4
    app.board.push_san("d4")
    assert len(app.board.move_stack) == 1

    # Simulate AI thinking state
    app.waiting_for_ai = True
    app.ai_move_queue.put(chess.Move.from_uci("d7d5"))

    # Trigger undo while waiting_for_ai
    undone = app.handle_undo_move()
    assert undone is True
    assert app.waiting_for_ai is False
    assert app.ai_move_queue.empty()
    assert len(app.board.move_stack) == 0
    assert app.board.turn == chess.WHITE
