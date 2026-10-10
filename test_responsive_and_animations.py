import os
import sys
import math
import pygame
import chess
from PIL import Image

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from constants import (
    MIN_WIDTH, MIN_HEIGHT, DEFAULT_WIDTH, DEFAULT_HEIGHT,
    BOARD_FRAME, EVAL_BAR_X, EVAL_BAR_WIDTH, EVAL_BAR_GAP
)
from main import GameApp
from animations import (
    ease_out_cubic, ease_out_back, ease_out_quad,
    PieceCinematicAnimation, RippleEffect, ConfettiParticleSystem
)
import logo_gen

def test_easing_functions():
    print("Testing Easing Functions...")
    # Easing values at boundaries
    assert ease_out_cubic(0.0) == 0.0
    assert ease_out_cubic(1.0) == 1.0
    assert ease_out_quad(0.0) == 0.0
    assert ease_out_quad(1.0) == 1.0
    
    # Monotonicity of ease_out_cubic
    prev = -1.0
    for step in range(11):
        t = step / 10.0
        val = ease_out_cubic(t)
        assert val >= prev, f"ease_out_cubic should be non-decreasing at {t}"
        prev = val

    # Test ease_out_back overshoot
    assert ease_out_back(0.0) == 0.0
    assert abs(ease_out_back(1.0) - 1.0) < 1e-5
    # Overshoot should exceed 1.0 during spring curve
    overshoot_found = any(ease_out_back(step / 100.0) > 1.0 for step in range(70, 99))
    assert overshoot_found, "ease_out_back should have an overshoot > 1.0 before settling"
    print("  -> Easing Functions OK")

def test_cinematic_piece_animation():
    print("Testing PieceCinematicAnimation (Slowmotion, Lift & Scale)...")
    anim = PieceCinematicAnimation(
        from_sq=chess.E2, to_sq=chess.E4, piece_key="wP",
        start_time=1000, duration_ms=280, is_capture=False
    )
    
    assert not anim.is_finished(1000)
    assert not anim.is_finished(1140)
    assert anim.is_finished(1280)
    assert anim.is_finished(1350)

    # Progress interpolation
    prog_start = anim.progress(1000)
    prog_mid = anim.progress(1140)
    prog_end = anim.progress(1280)
    assert abs(prog_start) < 0.01
    assert 0.60 < prog_mid < 0.98
    assert prog_end >= 0.99

    # Vertical Lift (arc parabolique)
    lift_start = anim.lift_height(1000)
    lift_mid = anim.lift_height(1140)
    lift_end = anim.lift_height(1280)
    assert abs(lift_start) < 0.01
    assert lift_mid < -10.0, f"Piece should be lifted by at least 10px mid-air: {lift_mid}"
    assert abs(lift_end) < 0.1

    # Dynamic scale factor (jusqu'à 1.15x)
    scale_start = anim.scale_factor(1000)
    scale_mid = anim.scale_factor(1140)
    scale_end = anim.scale_factor(1280)
    assert abs(scale_start - 1.0) < 0.01
    assert 1.10 <= scale_mid <= 1.16, f"Piece scale should reach ~1.15x: {scale_mid}"
    assert abs(scale_end - 1.0) < 0.01
    print("  -> Cinematic Piece Animation OK")

def test_ripple_and_confetti_effects():
    print("Testing RippleEffect & ConfettiParticleSystem...")
    pygame.init()
    surf = pygame.Surface((800, 600), pygame.SRCALPHA)
    
    # 1. RippleEffect
    ripple = RippleEffect(center_pos=(400, 300), color=(16, 185, 129), max_radius=60, duration_ms=400)
    t0 = ripple.start_time
    assert not ripple.is_finished(t0)
    ripple.draw(surf, t0 + 100)
    ripple.draw(surf, t0 + 250)
    assert ripple.is_finished(t0 + 400)
    assert ripple.is_finished(t0 + 500)

    # 2. ConfettiParticleSystem
    confetti = ConfettiParticleSystem()
    assert not confetti.is_active
    confetti.trigger(800, 600, count=80)
    assert confetti.is_active
    assert len(confetti.particles) == 80

    # Particle updates over time
    for _ in range(20):
        confetti.update(0.05)
    assert confetti.is_active
    confetti.draw(surf)

    # Force expiration or stop
    confetti.stop()
    assert not confetti.is_active
    assert len(confetti.particles) == 0
    print("  -> Ripple and Confetti OK")

def test_responsive_layout_recalculation():
    print("Testing Responsive Windowing Layout at Multiple Resolutions...")
    app = GameApp()

    resolutions = [
        (800, 600),     # Minimum supported
        (1040, 700),    # Default
        (1280, 720),    # HD 720p
        (1366, 768),    # Laptop standard
        (1920, 1080),   # Full HD 1080p
    ]

    for w, h in resolutions:
        app.recalculate_layout(w, h)
        ui = app.ui
        
        # 1. Chessboard bounds & Square size
        assert ui.square_size >= 44, f"Square size too small at {w}x{h}: {ui.square_size}"
        assert ui.square_size <= 95, f"Square size too large at {w}x{h}: {ui.square_size}"
        assert ui.board_size == ui.square_size * 8
        assert ui.full_board_size == ui.board_size + 2 * BOARD_FRAME

        # 2. No horizontal clipping or overlap
        # Check that Chessboard + Frame does not overlap with Side Panel
        board_right_edge = ui.board_x + ui.board_size + BOARD_FRAME
        assert board_right_edge <= ui.panel_x, (
            f"Board overlaps side panel at {w}x{h}: board right={board_right_edge}, panel_x={ui.panel_x}"
        )

        # Check that Side Panel fits inside window width
        panel_right_edge = ui.panel_x + ui.panel_width
        assert panel_right_edge <= w, (
            f"Side panel overflows window width at {w}x{h}: panel right={panel_right_edge}, window_w={w}"
        )

        # 3. Fits vertically inside window
        board_bottom_edge = ui.board_y + ui.board_size + BOARD_FRAME
        assert board_bottom_edge <= h, (
            f"Board overflows window height at {w}x{h}: board bottom={board_bottom_edge}, window_h={h}"
        )

        # 4. Buttons are within bounds
        assert app.btn_theme.rect.right <= ui.panel_x + ui.panel_width
        assert app.btn_eval_toggle.rect.right <= ui.panel_x + ui.panel_width
        assert app.tab_btn_history.rect.right <= ui.panel_x + ui.panel_width
        assert app.tab_btn_chat.rect.right <= ui.panel_x + ui.panel_width
        assert app.btn_back.rect.bottom <= ui.board_y - BOARD_FRAME + ui.full_board_size + 10

        # 5. Piece sprites scaled appropriately
        wP_img = ui.images.get('wP')
        assert wP_img is not None
        assert abs(wP_img.get_width() - int(ui.square_size * 0.88)) <= 1

        # 6. Render full board & play state without exceptions
        app.screen = pygame.Surface((w, h))
        app.ui.screen = app.screen
        app.ui.draw_3d_board(flipped=False)
        app.ui.draw_3d_board(flipped=True)
        app._draw_player_cards(app.board)
        app.draw_side_panel((0, 0))

    app.network.close()
    app.ai.close()
    print("  -> Responsive Layout Recalculation OK")

def test_hexagonal_logo_generation():
    print("Testing 3D Hexagonal Chessboard Logo & Icon Validation...")
    logo_gen.generate_all_icons("assets")

    # Verify assets/logo.png
    logo_file = "assets/logo.png"
    assert os.path.exists(logo_file)
    with Image.open(logo_file) as im:
        assert im.size == (512, 512), f"Logo should be 512x512, got {im.size}"
        assert im.mode == "RGBA"

    # Verify assets/icon.png
    icon_png = "assets/icon.png"
    assert os.path.exists(icon_png)
    with Image.open(icon_png) as im:
        assert im.size == (256, 256)
        assert im.mode == "RGBA"

    # Verify assets/icon.ico multi-resolution
    icon_ico = "assets/icon.ico"
    assert os.path.exists(icon_ico)
    with Image.open(icon_ico) as im:
        assert im.format == "ICO"
    print("  -> Hexagonal Logo & Icons OK")
