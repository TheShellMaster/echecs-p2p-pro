import pygame
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', BASE_DIR)
    return os.path.join(base_path, relative_path)

# Base Dimensions (Windowed default)
DEFAULT_WIDTH = 1040
DEFAULT_HEIGHT = 700
MIN_WIDTH = 800
MIN_HEIGHT = 600

SCREEN_WIDTH = DEFAULT_WIDTH
SCREEN_HEIGHT = DEFAULT_HEIGHT

EVAL_BAR_X = 14
EVAL_BAR_WIDTH = 18
EVAL_BAR_GAP = 12

BOARD_FRAME = 22
BOARD_X = EVAL_BAR_X + EVAL_BAR_WIDTH + EVAL_BAR_GAP + BOARD_FRAME  # 66
BOARD_Y = 66
SQUARE_SIZE = 70
BOARD_SIZE = SQUARE_SIZE * 8  # 560x560
FULL_BOARD_SIZE = BOARD_SIZE + (BOARD_FRAME * 2)  # 604x604

PANEL_X = 666
PANEL_WIDTH = SCREEN_WIDTH - PANEL_X - 16  # 358

# Board Themes (Bois Noble, Émeraude Tournoi, Néo Sombre, Marbre & Verre)
THEMES = {
    "bois": {
        "name": "Bois Noble",
        "light_sq": pygame.Color("#ebd3aa"),
        "dark_sq": pygame.Color("#a67b51"),
        "frame": pygame.Color("#4a3728"),
        "frame_inner": pygame.Color("#2e2117"),
        "border_accent": pygame.Color(80, 60, 45),
        "coord": pygame.Color("#e5a93c"),
    },
    "emeraude": {
        "name": "Émeraude Tournoi",
        "light_sq": pygame.Color("#eeeed2"),
        "dark_sq": pygame.Color("#769656"),
        "frame": pygame.Color("#2d3e2a"),
        "frame_inner": pygame.Color("#1c2819"),
        "border_accent": pygame.Color(69, 99, 56),
        "coord": pygame.Color("#bbf7d0"),
    },
    "neo": {
        "name": "Néo Sombre",
        "light_sq": pygame.Color("#475569"),
        "dark_sq": pygame.Color("#1e293b"),
        "frame": pygame.Color("#0f172a"),
        "frame_inner": pygame.Color("#020617"),
        "border_accent": pygame.Color(56, 189, 248),
        "coord": pygame.Color("#38bdf8"),
    },
    "marbre": {
        "name": "Marbre & Verre",
        "light_sq": pygame.Color("#e2e8f0"),
        "dark_sq": pygame.Color("#94a3b8"),
        "frame": pygame.Color("#334155"),
        "frame_inner": pygame.Color("#1e293b"),
        "border_accent": pygame.Color(148, 163, 184),
        "coord": pygame.Color("#f1f5f9"),
    }
}
THEME_KEYS = ["bois", "emeraude", "neo", "marbre"]
DEFAULT_THEME = "bois"

# Material 3 / Duolingo Light Theme UI Palette (Bright, clean, popular)
COLOR_BG_DARK = pygame.Color("#F8FAFC")       # Canvas background (clair et lumineux)
COLOR_BG_CARD = pygame.Color("#FFFFFF")       # Cartes blanches flottantes
COLOR_BG_HOVER = pygame.Color("#F1F5F9")      # Survol doux
COLOR_BORDER = pygame.Color("#E2E8F0")        # Liserés subtils
COLOR_BORDER_STRONG = pygame.Color("#CBD5E1") # Bordures plus nettes

# Accents vivants
COLOR_GOLD = pygame.Color("#F59E0B")          # Ambre / Or
COLOR_GOLD_HOVER = pygame.Color("#D97706")    # Ambre appuyé
COLOR_EMERALD = pygame.Color("#10B981")       # Vert Émeraude Duolingo
COLOR_EMERALD_DARK = pygame.Color("#059669")  # Émeraude 3D press-edge
COLOR_INDIGO = pygame.Color("#4F46E5")        # Indigo royal
COLOR_INDIGO_DARK = pygame.Color("#3730A3")   # Indigo 3D press-edge
COLOR_ROSE = pygame.Color("#F43F5E")          # Rose vif
COLOR_ROSE_DARK = pygame.Color("#BE123C")     # Rose 3D press-edge

# Typographie soignée (haute lisibilité)
COLOR_TEXT_MAIN = pygame.Color("#1E293B")     # Ardoise foncée intense
COLOR_TEXT_MUTED = pygame.Color("#64748B")    # Ardoise atténuée
COLOR_TEXT_WHITE = pygame.Color("#FFFFFF")

# Ombres douces (Drop shadows)
COLOR_SHADOW = (15, 23, 42, 22)
COLOR_SHADOW_DEEP = (15, 23, 42, 45)

# Backwards compatible palette
COLOR_WOOD_FRAME = THEMES["bois"]["frame"]
COLOR_WOOD_FRAME_INNER = THEMES["bois"]["frame_inner"]
COLOR_SQUARE_LIGHT = THEMES["bois"]["light_sq"]
COLOR_SQUARE_DARK = THEMES["bois"]["dark_sq"]

COLOR_HIGHLIGHT = pygame.Color(245, 158, 11, 100)
COLOR_CHECK = pygame.Color(239, 68, 68, 140)
COLOR_THREAT = pygame.Color(220, 38, 38, 85)
COLOR_THREAT_BORDER = pygame.Color(239, 68, 68, 200)
COLOR_MOVE_DOT = pygame.Color(16, 185, 129, 90)

# Tactical Annotations
COLOR_ARROW = (245, 158, 11, 220)
COLOR_ARROW_BORDER = (30, 41, 59, 230)
COLOR_CIRCLE_FILL = (245, 158, 11, 50)
COLOR_CIRCLE_RING = (245, 158, 11, 220)

# Clocks & Digital Displays (Modern crisp badge)
COLOR_LED_BG = pygame.Color("#0F172A")
COLOR_LED_BORDER = pygame.Color("#334155")
COLOR_LED_TEXT_ACTIVE = pygame.Color("#F59E0B")
COLOR_LED_TEXT_IDLE = pygame.Color("#94A3B8")
COLOR_LED_TEXT_WARN = pygame.Color("#EF4444")

# Networking
UDP_PORT = 50050
TCP_PORT = 50051
MAGIC_DISCOVERY = b"P2P_CHESS_DISCOVERY_V1"

# Clock Time Controls
TIME_OPTIONS = [
    ("Sans limite", 0),
    ("3 min Blitz", 180),
    ("5 min", 300),
    ("10 min Rapide", 600)
]
