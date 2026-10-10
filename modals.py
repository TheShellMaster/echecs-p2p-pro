import pygame
import chess
from constants import *
from ui import Button

class PromotionModal:
    def __init__(self, color, ui_images, center_pos=None):
        self.color = color
        self.ui_images = ui_images
        cx = center_pos[0] if center_pos else SCREEN_WIDTH // 2
        cy = center_pos[1] if center_pos else SCREEN_HEIGHT // 2
        self.rect = pygame.Rect(cx - 160, cy - 60, 320, 120)
        self.options = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
        self.buttons = []
        
        c_prefix = 'w' if color == chess.WHITE else 'b'
        symbols = ['Q', 'R', 'B', 'N']
        for i, sym in enumerate(symbols):
            b_rect = pygame.Rect(self.rect.x + 20 + i * 72, self.rect.y + 40, 64, 64)
            img = ui_images.get(f"{c_prefix}{sym}")
            self.buttons.append((b_rect, self.options[i], img))

    def draw(self, screen, mouse_pos):
        w, h = screen.get_size()
        dim = pygame.Surface((w, h), pygame.SRCALPHA)
        dim.fill((15, 23, 42, 120))
        screen.blit(dim, (0, 0))
        
        # Ombre portée de la modale
        sh_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        pygame.draw.rect(sh_surf, (15, 23, 42, 40), (0, 0, self.rect.w, self.rect.h), border_radius=14)
        screen.blit(sh_surf, (self.rect.x, self.rect.y + 4))

        # Carte modale blanche
        pygame.draw.rect(screen, COLOR_BG_CARD, self.rect, border_radius=14)
        pygame.draw.rect(screen, COLOR_BORDER_STRONG, self.rect, width=2, border_radius=14)
        
        font = pygame.font.SysFont('Segoe UI', 16, bold=True)
        txt = font.render("Choisissez la promotion :", True, COLOR_TEXT_MAIN)
        screen.blit(txt, (self.rect.x + 20, self.rect.y + 12))
        
        for r, opt, img in self.buttons:
            is_hover = r.collidepoint(mouse_pos)
            bg = COLOR_BG_HOVER if is_hover else COLOR_BG_CARD
            pygame.draw.rect(screen, bg, r, border_radius=10)
            border_c = COLOR_EMERALD if is_hover else COLOR_BORDER
            pygame.draw.rect(screen, border_c, r, width=2, border_radius=10)
            if img:
                screen.blit(img, (r.x + (r.w - img.get_width())//2, r.y + (r.h - img.get_height())//2))

    def handle_click(self, mouse_pos):
        for r, opt, img in self.buttons:
            if r.collidepoint(mouse_pos):
                return opt
        return None

class AISettingsModal:
    def __init__(self, center_pos=None):
        cx = center_pos[0] if center_pos else SCREEN_WIDTH // 2
        cy = center_pos[1] if center_pos else SCREEN_HEIGHT // 2
        self.rect = pygame.Rect(cx - 250, cy - 245, 500, 490)
        self.selected_diff = 4  # Default Grand Maître
        self.selected_color = chess.WHITE
        self.selected_time = 0  # Default unlimited
        
        # Difficultés avec design 3D
        self.diff_buttons = [
            (Button((self.rect.x + 30, self.rect.y + 65, 210, 42), "1. Débutant (800)", font_size=15), 1),
            (Button((self.rect.x + 260, self.rect.y + 65, 210, 42), "2. Intermédiaire", font_size=15), 2),
            (Button((self.rect.x + 30, self.rect.y + 115, 210, 42), "3. Avancé (2200)", font_size=15), 3),
            (Button((self.rect.x + 260, self.rect.y + 115, 210, 42), "4. Grand Maître", font_size=15), 4),
        ]
        
        # Choix de la couleur
        self.color_buttons = [
            (Button((self.rect.x + 30, self.rect.y + 195, 135, 42), "Blancs", font_size=15), chess.WHITE),
            (Button((self.rect.x + 182, self.rect.y + 195, 135, 42), "Aléatoire", font_size=15), "RANDOM"),
            (Button((self.rect.x + 335, self.rect.y + 195, 135, 42), "Noirs", font_size=15), chess.BLACK),
        ]

        # Cadences de jeu
        self.time_buttons = [
            (Button((self.rect.x + 30, self.rect.y + 275, 210, 42), "Sans limite", font_size=15), 0),
            (Button((self.rect.x + 260, self.rect.y + 275, 210, 42), "3 min Blitz", font_size=15), 180),
            (Button((self.rect.x + 30, self.rect.y + 325, 210, 42), "5 min", font_size=15), 300),
            (Button((self.rect.x + 260, self.rect.y + 325, 210, 42), "10 min Rapide", font_size=15), 600),
        ]
        
        self.btn_cancel = Button((self.rect.x + 30, self.rect.y + 410, 210, 50), "Annuler", font_size=16)
        self.btn_start = Button((self.rect.x + 260, self.rect.y + 410, 210, 50), "Lancer le défi", 
                                bg_color=COLOR_EMERALD, text_color=pygame.Color("white"), font_size=18)

    def draw(self, screen, mouse_pos):
        w, h = screen.get_size()
        dim = pygame.Surface((w, h), pygame.SRCALPHA)
        dim.fill((15, 23, 42, 130))
        screen.blit(dim, (0, 0))
        
        # Ombre portée de la modale
        sh_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        pygame.draw.rect(sh_surf, (15, 23, 42, 40), (0, 0, self.rect.w, self.rect.h), border_radius=16)
        screen.blit(sh_surf, (self.rect.x, self.rect.y + 4))

        # Carte blanche
        pygame.draw.rect(screen, COLOR_BG_CARD, self.rect, border_radius=16)
        pygame.draw.rect(screen, COLOR_BORDER_STRONG, self.rect, width=2, border_radius=16)
        
        title_font = pygame.font.SysFont('Segoe UI', 22, bold=True)
        sec_font = pygame.font.SysFont('Segoe UI', 15, bold=True)
        
        title = title_font.render("Défier l'Ordinateur (Stockfish 19)", True, COLOR_TEXT_MAIN)
        screen.blit(title, (self.rect.x + (self.rect.w - title.get_width())//2, self.rect.y + 18))
        
        # 1. Difficulté
        screen.blit(sec_font.render("Niveau de difficulté :", True, COLOR_TEXT_MUTED), (self.rect.x + 30, self.rect.y + 45))
        for btn, diff in self.diff_buttons:
            btn.is_active = (self.selected_diff == diff)
            btn.draw(screen, mouse_pos)
            
        # 2. Couleur
        screen.blit(sec_font.render("Votre couleur :", True, COLOR_TEXT_MUTED), (self.rect.x + 30, self.rect.y + 172))
        for btn, col in self.color_buttons:
            btn.is_active = (self.selected_color == col)
            btn.draw(screen, mouse_pos)

        # 3. Cadence
        screen.blit(sec_font.render("Cadence de jeu (Horloge) :", True, COLOR_TEXT_MUTED), (self.rect.x + 30, self.rect.y + 252))
        for btn, t_val in self.time_buttons:
            btn.is_active = (self.selected_time == t_val)
            btn.draw(screen, mouse_pos)
            
        self.btn_cancel.draw(screen, mouse_pos)
        self.btn_start.draw(screen, mouse_pos)

    def handle_click(self, mouse_pos):
        for btn, diff in self.diff_buttons:
            if btn.rect.collidepoint(mouse_pos):
                self.selected_diff = diff
                return None
        for btn, col in self.color_buttons:
            if btn.rect.collidepoint(mouse_pos):
                self.selected_color = col
                return None
        for btn, t_val in self.time_buttons:
            if btn.rect.collidepoint(mouse_pos):
                self.selected_time = t_val
                return None
        if self.btn_cancel.rect.collidepoint(mouse_pos):
            return "CANCEL"
        if self.btn_start.rect.collidepoint(mouse_pos):
            return "START"
        return None

class LocalSettingsModal:
    def __init__(self, center_pos=None):
        cx = center_pos[0] if center_pos else SCREEN_WIDTH // 2
        cy = center_pos[1] if center_pos else SCREEN_HEIGHT // 2
        self.rect = pygame.Rect(cx - 250, cy - 180, 500, 360)
        self.selected_time = 0  # Default unlimited
        
        # Cadences de jeu
        self.time_buttons = [
            (Button((self.rect.x + 30, self.rect.y + 90, 210, 45), "Sans limite", font_size=16), 0),
            (Button((self.rect.x + 260, self.rect.y + 90, 210, 45), "3 min Blitz", font_size=16), 180),
            (Button((self.rect.x + 30, self.rect.y + 145, 210, 45), "5 min", font_size=16), 300),
            (Button((self.rect.x + 260, self.rect.y + 145, 210, 45), "10 min Rapide", font_size=16), 600),
        ]
        
        self.btn_cancel = Button((self.rect.x + 30, self.rect.y + 260, 210, 50), "Annuler", font_size=16)
        self.btn_start = Button((self.rect.x + 260, self.rect.y + 260, 210, 50), "Commencer la partie", 
                                bg_color=COLOR_EMERALD, text_color=pygame.Color("white"), font_size=18)

    def draw(self, screen, mouse_pos):
        w, h = screen.get_size()
        dim = pygame.Surface((w, h), pygame.SRCALPHA)
        dim.fill((15, 23, 42, 130))
        screen.blit(dim, (0, 0))
        
        # Ombre portée
        sh_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        pygame.draw.rect(sh_surf, (15, 23, 42, 40), (0, 0, self.rect.w, self.rect.h), border_radius=16)
        screen.blit(sh_surf, (self.rect.x, self.rect.y + 4))

        pygame.draw.rect(screen, COLOR_BG_CARD, self.rect, border_radius=16)
        pygame.draw.rect(screen, COLOR_BORDER_STRONG, self.rect, width=2, border_radius=16)
        
        title_font = pygame.font.SysFont('Segoe UI', 22, bold=True)
        sec_font = pygame.font.SysFont('Segoe UI', 15, bold=True)
        
        title = title_font.render("Partie Locale à Deux Joueurs", True, COLOR_TEXT_MAIN)
        screen.blit(title, (self.rect.x + (self.rect.w - title.get_width())//2, self.rect.y + 22))
        
        screen.blit(sec_font.render("Cadence de jeu (Horloge) :", True, COLOR_TEXT_MUTED), (self.rect.x + 30, self.rect.y + 65))
        for btn, t_val in self.time_buttons:
            btn.is_active = (self.selected_time == t_val)
            btn.draw(screen, mouse_pos)
            
        self.btn_cancel.draw(screen, mouse_pos)
        self.btn_start.draw(screen, mouse_pos)

    def handle_click(self, mouse_pos):
        for btn, t_val in self.time_buttons:
            if btn.rect.collidepoint(mouse_pos):
                self.selected_time = t_val
                return None
        if self.btn_cancel.rect.collidepoint(mouse_pos):
            return "CANCEL"
        if self.btn_start.rect.collidepoint(mouse_pos):
            return "START"
        return None

class GameOverModal:
    def __init__(self, message, sub_message="", center_pos=None):
        cx = center_pos[0] if center_pos else SCREEN_WIDTH // 2
        cy = center_pos[1] if center_pos else SCREEN_HEIGHT // 2
        self.rect = pygame.Rect(cx - 200, cy - 120, 400, 240)
        self.message = message
        self.sub_message = sub_message
        self.btn_replay = Button((self.rect.x + 30, self.rect.y + 160, 160, 48), "Rejouer", 
                                 bg_color=COLOR_EMERALD, text_color=pygame.Color("white"), font_size=18)
        self.btn_menu = Button((self.rect.x + 210, self.rect.y + 160, 160, 48), "Menu", font_size=17)

    def draw(self, screen, mouse_pos):
        w, h = screen.get_size()
        dim = pygame.Surface((w, h), pygame.SRCALPHA)
        dim.fill((15, 23, 42, 130))
        screen.blit(dim, (0, 0))
        
        # Ombre
        sh_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        pygame.draw.rect(sh_surf, (15, 23, 42, 45), (0, 0, self.rect.w, self.rect.h), border_radius=16)
        screen.blit(sh_surf, (self.rect.x, self.rect.y + 5))

        pygame.draw.rect(screen, COLOR_BG_CARD, self.rect, border_radius=16)
        pygame.draw.rect(screen, COLOR_GOLD, self.rect, width=2, border_radius=16)
        
        f1 = pygame.font.SysFont('Segoe UI', 24, bold=True)
        f2 = pygame.font.SysFont('Segoe UI', 15)
        
        t1 = f1.render(self.message, True, COLOR_TEXT_MAIN)
        t2 = f2.render(self.sub_message, True, COLOR_TEXT_MUTED)
        
        screen.blit(t1, (self.rect.x + (self.rect.w - t1.get_width())//2, self.rect.y + 36))
        screen.blit(t2, (self.rect.x + (self.rect.w - t2.get_width())//2, self.rect.y + 80))
        
        self.btn_replay.draw(screen, mouse_pos)
        self.btn_menu.draw(screen, mouse_pos)

    def handle_click(self, mouse_pos):
        if self.btn_replay.rect.collidepoint(mouse_pos):
            return "REPLAY"
        if self.btn_menu.rect.collidepoint(mouse_pos):
            return "MENU"
        return None
