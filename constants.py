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
        "light_sq": pygame.Color("#D8C7A4"),
        "dark_sq": pygame.Color("#78624A"),
        "frame": pygame.Color("#9A7550"),
        "frame_inner": pygame.Color("#D8C09D"),
        "border_accent": pygame.Color("#B8956B"),
        "coord": pygame.Color("#F4E7D1"),
    },
    "emeraude": {
        "name": "Émeraude Tournoi",
        "light_sq": pygame.Color("#F0EBD9"),
        "dark_sq": pygame.Color("#789572"),
        "frame": pygame.Color("#D8E1D4"),
        "frame_inner": pygame.Color("#EFE9DB"),
        "border_accent": pygame.Color("#9BAE96"),
        "coord": pygame.Color("#496247"),
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
DEFAULT_THEME = "emeraude"

# Atelier lumineux : papier, encre et vert profond.
COLOR_BG_DARK = pygame.Color("#F4F1E9")
COLOR_BG_CARD = pygame.Color("#FFFEFA")
COLOR_BG_HOVER = pygame.Color("#F0EBDD")
COLOR_BORDER = pygame.Color("#E4DED1")
COLOR_BORDER_STRONG = pygame.Color("#C9BDA9")

# Accents limités, repris dans les coups et les actions.
COLOR_GOLD = pygame.Color("#B47A3C")
COLOR_GOLD_HOVER = pygame.Color("#8E5D2E")
COLOR_EMERALD = pygame.Color("#3E765C")
COLOR_EMERALD_DARK = pygame.Color("#2C5C45")
COLOR_INDIGO = pygame.Color("#507F78")
COLOR_INDIGO_DARK = pygame.Color("#365F59")
COLOR_ROSE = pygame.Color("#BD6958")
COLOR_ROSE_DARK = pygame.Color("#8F4B40")
# High-contrast tactical colors stay vivid on the softened light board palette.
COLOR_MOVE_RETICLE = pygame.Color("#10B981")
COLOR_CAPTURE_RETICLE = pygame.Color("#F43F5E")

# Typographie encre, confortable sur les surfaces claires.
COLOR_TEXT_MAIN = pygame.Color("#25332C")
COLOR_TEXT_MUTED = pygame.Color("#69766F")
COLOR_TEXT_WHITE = pygame.Color("#FFFEFA")

# Ombres discrètes, sans bordure lourde autour de chaque composant.
COLOR_SHADOW = (48, 44, 35, 18)
COLOR_SHADOW_DEEP = (48, 44, 35, 32)

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
COLOR_LED_BG = pygame.Color("#101713")
COLOR_LED_BORDER = pygame.Color("#465648")
COLOR_LED_TEXT_ACTIVE = pygame.Color("#E2C27D")
COLOR_LED_TEXT_IDLE = pygame.Color("#B1BCB1")
COLOR_LED_TEXT_WARN = pygame.Color("#F17C70")

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

# AI Personas Data & Configurations (Stockfish 19 UCI Profiles)
BOT_PERSONAS = {
    "lucas": {
        "id": "lucas",
        "name": "Lucas",
        "title": "Débutant",
        "elo": 800,
        "avatar_theme": "amber",
        "playstyle": "Attaque agressive & gaffes naïves",
        "quote": "J'adore avancer mes pions et attaquer sans attendre !",
        "uci_limit_strength": True,
        "uci_elo": 1320,  # Clamped to Stockfish 19 min (1320)
        "skill_level": 1,
        "depth": 4,
        "time": 0.3
    },
    "eleonore": {
        "id": "eleonore",
        "name": "Éléonore",
        "title": "Joueuse de Club",
        "elo": 1400,
        "avatar_theme": "emerald",
        "playstyle": "Jeu positionnel & développement solide",
        "quote": "Une structure de pions solide vaut mieux qu'une attaque précipitée.",
        "uci_limit_strength": True,
        "uci_elo": 1400,
        "skill_level": 10,
        "depth": 10,
        "time": 0.8
    },
    "alexandre": {
        "id": "alexandre",
        "name": "Alexandre",
        "title": "Maître National",
        "elo": 2100,
        "avatar_theme": "indigo",
        "playstyle": "Maîtrise tactique & calcul profond",
        "quote": "Chaque imprécision tactique scellera votre destin.",
        "uci_limit_strength": True,
        "uci_elo": 2100,
        "skill_level": 18,
        "depth": 16,
        "time": 1.2
    },
    "monster": {
        "id": "monster",
        "name": "Le Monstre Stockfish 19",
        "title": "Grand Maître Surhumain",
        "elo": 3200,
        "avatar_theme": "rose",
        "playstyle": "Calcul NNUE impitoyable & jeu parfait",
        "quote": "0.00 ou Mat forcé. Le calcul pur ne ment jamais.",
        "uci_limit_strength": False,
        "uci_elo": 3190,
        "skill_level": 20,
        "depth": 22,
        "time": 1.8
    }
}
PERSONA_ORDER = ["lucas", "eleonore", "alexandre", "monster"]
DEFAULT_PERSONA = "eleonore"
