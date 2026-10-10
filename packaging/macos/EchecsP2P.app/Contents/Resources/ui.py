import pygame
import chess
import math
import os
import sys
from constants import *
from animations import (
    PieceCinematicAnimation,
    RippleEffect,
    ease_out_cubic,
    ease_out_back
)

class Button:
    """
    Bouton tactile 3D style Duolingo / Material 3 :
    Possède un biseau inférieur physique épais qui s'enfonce de 3px au clic de la souris.
    """
    def __init__(self, rect, text, bg_color=None, hover_color=None, 
                 text_color=None, font_size=18, border_color=None, edge_color=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        
        # Thème par défaut clair Material 3
        self.bg_color = bg_color if bg_color is not None else COLOR_BG_CARD
        self.hover_color = hover_color if hover_color is not None else COLOR_BG_HOVER
        self.text_color = text_color if text_color is not None else COLOR_TEXT_MAIN
        self.border_color = border_color if border_color is not None else COLOR_BORDER
        
        # Couleur du rebord 3D inférieur
        if edge_color is not None:
            self.edge_color = edge_color
        elif self.bg_color == COLOR_BG_CARD or self.bg_color == pygame.Color("#FFFFFF"):
            self.edge_color = pygame.Color("#CBD5E1")
        elif self.bg_color == COLOR_EMERALD:
            self.edge_color = COLOR_EMERALD_DARK
        elif self.bg_color == COLOR_INDIGO:
            self.edge_color = COLOR_INDIGO_DARK
        elif self.bg_color == COLOR_GOLD:
            self.edge_color = COLOR_GOLD_HOVER
        else:
            # Assombrissement automatique pour l'arête inférieure
            r = max(0, self.bg_color.r - 35)
            g = max(0, self.bg_color.g - 35)
            b = max(0, self.bg_color.b - 35)
            self.edge_color = pygame.Color(r, g, b)

        self.font_size = font_size
        self.font = pygame.font.SysFont('Segoe UI', font_size, bold=True)
        self.is_active = False
        self.is_pressed = False
        self.extrude_depth = 4   # Hauteur normale du relief 3D
        self.press_offset = 3    # Enfoncement physique en pixels lors du clic

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_pressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_pressed = False

    def draw(self, surface, mouse_pos):
        is_hovered = self.rect.collidepoint(mouse_pos)
        is_mouse_down = pygame.mouse.get_pressed()[0]
        
        # Déterminer si le bouton est physiquement enfoncé
        pressed = (is_hovered and is_mouse_down) or self.is_pressed or self.is_active
        offset_y = self.press_offset if pressed else 0
        current_edge = max(1, self.extrude_depth - offset_y)

        # 1. Ombre portée douce au sol
        shadow_rect = pygame.Rect(self.rect.x + 1, self.rect.y + self.extrude_depth + 1, 
                                  self.rect.width, self.rect.height)
        shadow_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (15, 23, 42, 25 if not pressed else 12), 
                         (0, 0, self.rect.width, self.rect.height), border_radius=10)
        surface.blit(shadow_surf, (shadow_rect.x, shadow_rect.y))

        # 2. Rebord inférieur 3D (Extrusion physique)
        base_rect = pygame.Rect(self.rect.x, self.rect.y + offset_y + current_edge, 
                                self.rect.width, self.rect.height - current_edge)
        edge_col = COLOR_GOLD_HOVER if self.is_active else self.edge_color
        pygame.draw.rect(surface, edge_col, base_rect, border_radius=10)

        # 3. Face supérieure du bouton
        face_rect = pygame.Rect(self.rect.x, self.rect.y + offset_y, 
                                self.rect.width, self.rect.height - self.extrude_depth)
        
        face_color = self.hover_color if (is_hovered and not pressed) else self.bg_color
        if self.is_active and self.bg_color == COLOR_BG_CARD:
            face_color = pygame.Color("#FEF3C7") # Ambre très clair pour boutons actifs
        
        pygame.draw.rect(surface, face_color, face_rect, border_radius=10)

        # Liseré de contour
        b_col = COLOR_GOLD if self.is_active else (COLOR_BORDER_STRONG if is_hovered else self.border_color)
        pygame.draw.rect(surface, b_col, face_rect, width=2, border_radius=10)

        # 4. Rendu du Texte centré (décalé avec l'enfoncement)
        txt_col = COLOR_GOLD_HOVER if (self.is_active and self.bg_color == COLOR_BG_CARD) else self.text_color
        text_surf = self.font.render(self.text, True, txt_col)
        text_rect = text_surf.get_rect(center=face_rect.center)
        surface.blit(text_surf, text_rect)

class TextInput:
    """Champ de saisie stylisé Material 3 avec fond clair et focus indigo/or."""
    def __init__(self, rect, initial_text="", placeholder="Tapez ici...", max_chars=50, font_size=15):
        self.rect = pygame.Rect(rect)
        self.text = initial_text
        self.placeholder = placeholder
        self.max_chars = max_chars
        self.font = pygame.font.SysFont('Segoe UI', font_size)
        self.is_active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.is_active = self.rect.collidepoint(event.pos)
            return None
        elif event.type == pygame.KEYDOWN and self.is_active:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return "SUBMIT"
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                return "CHANGE"
            elif event.key == pygame.K_ESCAPE:
                self.is_active = False
                return None
            elif len(self.text) < self.max_chars and event.unicode and event.unicode.isprintable():
                self.text += event.unicode
                return "CHANGE"
        return None

    def draw(self, surface, mouse_pos):
        is_hovered = self.rect.collidepoint(mouse_pos)
        
        # Ombre douce
        sh_rect = pygame.Rect(self.rect.x, self.rect.y + 1, self.rect.width, self.rect.height)
        sh_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(sh_surf, (15, 23, 42, 15), (0, 0, self.rect.width, self.rect.height), border_radius=8)
        surface.blit(sh_surf, (sh_rect.x, sh_rect.y))

        # Fond blanc
        pygame.draw.rect(surface, pygame.Color("#FFFFFF"), self.rect, border_radius=8)
        
        # Bordure : Indigo quand actif, liseré doux sinon
        if self.is_active:
            border_col = COLOR_INDIGO
            border_w = 2
        elif is_hovered:
            border_col = COLOR_BORDER_STRONG
            border_w = 1
        else:
            border_col = COLOR_BORDER
            border_w = 1
        pygame.draw.rect(surface, border_col, self.rect, width=border_w, border_radius=8)
        
        # Zone de texte avec découpage interne
        inner_rect = pygame.Rect(self.rect.x + 10, self.rect.y + 2, self.rect.width - 20, self.rect.height - 4)
        prev_clip = surface.get_clip()
        surface.set_clip(inner_rect)
        
        display_text = self.text
        avail_w = self.rect.width - 24
        if not display_text and not self.is_active:
            txt_surf = self.font.render(self.placeholder, True, COLOR_TEXT_MUTED)
            text_x = self.rect.x + 12
        else:
            txt_surf = self.font.render(display_text, True, COLOR_TEXT_MAIN)
            if txt_surf.get_width() > avail_w:
                text_x = self.rect.x + 12 - (txt_surf.get_width() - avail_w)
            else:
                text_x = self.rect.x + 12
            
        text_y = self.rect.y + (self.rect.height - txt_surf.get_height()) // 2
        surface.blit(txt_surf, (text_x, text_y))
        
        # Curseur clignotant
        if self.is_active:
            cursor_visible = (pygame.time.get_ticks() // 450) % 2 == 0
            if cursor_visible:
                cx = text_x + txt_surf.get_width() + 2
                cy1 = text_y + 2
                cy2 = text_y + txt_surf.get_height() - 2
                pygame.draw.line(surface, COLOR_INDIGO, (cx, cy1), (cx, cy2), 2)
                
        surface.set_clip(prev_clip)

class PieceAnimation(PieceCinematicAnimation):
    """Alias rétro-compatible vers PieceCinematicAnimation."""
    pass

class UI:
    def __init__(self, screen):
        self.screen = screen
        self.images = {}
        self.mini_images = {}
        self.raw_images = {}
        self.shadow_surface = None
        self.lifted_shadow_surface = None
        self.theme_key = DEFAULT_THEME
        self.theme = THEMES[self.theme_key]
        
        # Dimensions dynamiques (Responsive)
        self.board_x = BOARD_X
        self.board_y = BOARD_Y
        self.square_size = SQUARE_SIZE
        self.board_size = BOARD_SIZE
        self.full_board_size = FULL_BOARD_SIZE
        self.panel_x = PANEL_X
        self.panel_width = PANEL_WIDTH

        self.create_piece_shadow()
        self.load_assets()
        
        self.coord_font = pygame.font.SysFont('Segoe UI', 14, bold=True)
        self.eval_font = pygame.font.SysFont('Segoe UI', 11, bold=True)
        self.card_font_name = pygame.font.SysFont('Segoe UI', 13, bold=True)
        self.card_font_badge = pygame.font.SysFont('Segoe UI', 10, bold=True)
        self.card_font_diff = pygame.font.SysFont('Segoe UI', 12, bold=True)
        self.card_font_led = pygame.font.SysFont('Courier New', 14, bold=True)
        
        self.animation = None
        self.ripples = []

    def set_theme(self, theme_key):
        if theme_key in THEMES:
            self.theme_key = theme_key
            self.theme = THEMES[theme_key]

    def cycle_theme(self):
        idx = THEME_KEYS.index(self.theme_key) if self.theme_key in THEME_KEYS else 0
        new_key = THEME_KEYS[(idx + 1) % len(THEME_KEYS)]
        self.set_theme(new_key)
        return new_key

    def create_piece_shadow(self):
        # 1. Ombre normale posée au sol
        w = max(10, self.square_size - 15)
        h = max(5, self.square_size // 3)
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (15, 23, 42, 65), (0, 0, w, h))
        self.shadow_surface = s

        # 2. Ombre élargie et estompée lorsque la pièce est soulevée (zoom 1.15x)
        lw = int(w * 1.25)
        lh = int(h * 1.35)
        ls = pygame.Surface((lw, lh), pygame.SRCALPHA)
        pygame.draw.ellipse(ls, (15, 23, 42, 40), (0, 0, lw, lh))
        self.lifted_shadow_surface = ls

    def load_assets(self):
        pieces = ['wK', 'wQ', 'wR', 'wB', 'wN', 'wP', 'bK', 'bQ', 'bR', 'bB', 'bN', 'bP']
        for p in pieces:
            path = resource_path(os.path.join("assets", f"{p}.png"))
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                self.raw_images[p] = img
                self._scale_piece(p, img)
            else:
                print(f"Warning: Asset missing {path}")

    def _scale_piece(self, piece_key, raw_img):
        p_size = int(self.square_size * 0.88)
        scaled = pygame.transform.smoothscale(raw_img, (p_size, p_size))
        self.images[piece_key] = scaled
        self.mini_images[piece_key] = pygame.transform.smoothscale(raw_img, (18, 18))

    def recalculate_layout(self, window_width, window_height):
        """
        Recalcule dynamiquement la disposition de l'échiquier et des composants
        pour s'adapter sans débordement à n'importe quelle taille de fenêtre.
        """
        w = max(MIN_WIDTH, window_width)
        h = max(MIN_HEIGHT, window_height)

        # Calcul de la taille maximale des cases en fonction de la résolution
        # Marge latérale réservée pour barre d'éval (45px) + frame (44px) + panneau latéral (340px)
        avail_w_for_board = w - 45 - (BOARD_FRAME * 2) - 340 - 40
        avail_h_for_board = h - (BOARD_FRAME * 2) - 90  # 90px pour cartes joueurs haut/bas

        new_sq_size = int(min(avail_w_for_board, avail_h_for_board) // 8)
        self.square_size = max(44, min(95, new_sq_size))
        self.board_size = self.square_size * 8
        self.full_board_size = self.board_size + (BOARD_FRAME * 2)

        self.board_x = EVAL_BAR_X + EVAL_BAR_WIDTH + EVAL_BAR_GAP + BOARD_FRAME
        self.board_y = max(45, (h - self.board_size) // 2)

        self.panel_x = self.board_x + self.board_size + BOARD_FRAME + 24
        self.panel_width = max(280, w - self.panel_x - 16)

        # Mettre à jour l'ombre et redimensionner les sprites
        self.create_piece_shadow()
        for p, raw in self.raw_images.items():
            self._scale_piece(p, raw)

    def start_animation(self, from_sq, to_sq, piece_key, secondary=None, captured=None, 
                        duration_ms=280, is_capture=False, is_check=False):
        """Démarre le glissement cinématique slow-motion (280ms)."""
        self.animation = PieceCinematicAnimation(
            from_sq, to_sq, piece_key, pygame.time.get_ticks(), 
            duration_ms=duration_ms, secondary=secondary, captured=captured,
            is_capture=is_capture, is_check=is_check
        )
        if is_capture:
            self.trigger_square_ripple(to_sq, color=(245, 158, 11))
        elif is_check:
            self.trigger_square_ripple(to_sq, color=(239, 68, 68))

    def trigger_square_ripple(self, square, color=(16, 185, 129), flipped=False):
        """Déclenche une onde de choc sur une case spécifique."""
        cx, cy = self.square_to_screen_center(square, flipped)
        max_rad = int(self.square_size * 0.85)
        self.ripples.append(RippleEffect((cx, cy), color=color, max_radius=max_rad, duration_ms=480))

    def draw_3d_board(self, flipped=False):
        t = self.theme
        bx = self.board_x
        by = self.board_y
        bs = self.board_size
        fbs = self.full_board_size
        sq_s = self.square_size

        # 1. Ombre portée douce du plateau (3D depth)
        shadow_rect = pygame.Rect(bx - BOARD_FRAME + 5, by - BOARD_FRAME + 7, fbs, fbs)
        shadow_surf = pygame.Surface((fbs, fbs), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (15, 23, 42, 35), (0, 0, fbs, fbs), border_radius=14)
        self.screen.blit(shadow_surf, (shadow_rect.x, shadow_rect.y))

        # 2. Cadre extérieur biseauté
        outer_frame = pygame.Rect(bx - BOARD_FRAME, by - BOARD_FRAME, fbs, fbs)
        pygame.draw.rect(self.screen, t["frame"], outer_frame, border_radius=12)
        pygame.draw.rect(self.screen, t["border_accent"], outer_frame, width=2, border_radius=12)

        # 3. Biseau intérieur
        inner_frame = pygame.Rect(bx - 3, by - 3, bs + 6, bs + 6)
        pygame.draw.rect(self.screen, t["frame_inner"], inner_frame, border_radius=4)

        # 4. Coordonnées (A-H et 1-8)
        files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        ranks = ['1', '2', '3', '4', '5', '6', '7', '8']
        if flipped:
            files.reverse()
        else:
            ranks.reverse()

        coord_col = t.get("coord", COLOR_GOLD)
        for i, f in enumerate(files):
            x = bx + i * sq_s + (sq_s // 2)
            # Bas
            txt = self.coord_font.render(f.upper(), True, coord_col)
            self.screen.blit(txt, (x - txt.get_width()//2, by + bs + 3))
            # Haut
            self.screen.blit(txt, (x - txt.get_width()//2, by - BOARD_FRAME + 3))

        for i, r in enumerate(ranks):
            y = by + i * sq_s + (sq_s // 2)
            # Gauche
            txt = self.coord_font.render(r, True, coord_col)
            self.screen.blit(txt, (bx - BOARD_FRAME + 6, y - txt.get_height()//2))
            # Droite
            self.screen.blit(txt, (bx + bs + 6, y - txt.get_height()//2))

        # 5. Rendu des 64 cases
        for r in range(8):
            for c in range(8):
                is_light = (r + c) % 2 == 0
                color = t["light_sq"] if is_light else t["dark_sq"]
                sq_rect = pygame.Rect(bx + c * sq_s, by + r * sq_s, sq_s, sq_s)
                pygame.draw.rect(self.screen, color, sq_rect)

        # 6. Rendu des ondes de choc actives
        now = pygame.time.get_ticks()
        self.ripples = [rip for rip in self.ripples if not rip.is_finished(now)]
        for rip in self.ripples:
            rip.draw(self.screen, now)

    def square_to_screen(self, square, flipped=False):
        c = chess.square_file(square)
        r = chess.square_rank(square)
        if not flipped:
            r = 7 - r
        else:
            c = 7 - c
        return self.board_x + c * self.square_size, self.board_y + r * self.square_size

    def square_to_screen_center(self, square, flipped=False):
        sx, sy = self.square_to_screen(square, flipped)
        return sx + self.square_size // 2, sy + self.square_size // 2

    def screen_to_square(self, x, y, flipped=False):
        bx = self.board_x
        by = self.board_y
        bs = self.board_size
        sq_s = self.square_size
        if not (bx <= x < bx + bs and by <= y < by + bs):
            return None
        c = (x - bx) // sq_s
        r = (y - by) // sq_s
        if not flipped:
            r = 7 - r
        else:
            c = 7 - c
        return chess.square(c, r)

    def draw_annotations(self, circles, arrows, preview_arrow=None, flipped=False, draw_circles=True, draw_arrows=True):
        if not circles and not arrows and not preview_arrow:
            return
            
        annot_surf = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        sq_s = self.square_size
        
        # 1. Cercles tactiques sous les pièces
        if draw_circles and circles:
            for sq in circles:
                cx, cy = self.square_to_screen_center(sq, flipped)
                rad = (sq_s // 2) - 4
                pygame.draw.circle(annot_surf, COLOR_CIRCLE_FILL, (cx, cy), rad)
                pygame.draw.circle(annot_surf, COLOR_CIRCLE_RING, (cx, cy), rad, width=4)
                pygame.draw.circle(annot_surf, (15, 23, 42, 120), (cx, cy), rad + 2, width=1)
                pygame.draw.circle(annot_surf, (15, 23, 42, 120), (cx, cy), rad - 3, width=1)

        # 2. Flèches vectorielles précises au-dessus des pièces
        if draw_arrows and (arrows or preview_arrow):
            arrow_list = list(arrows)
            if preview_arrow and preview_arrow[0] != preview_arrow[1]:
                arrow_list.append(preview_arrow)

            for from_sq, to_sq in arrow_list:
                x1, y1 = self.square_to_screen_center(from_sq, flipped)
                x2, y2 = self.square_to_screen_center(to_sq, flipped)
                dx = x2 - x1
                dy = y2 - y1
                dist = math.hypot(dx, dy)
                if dist < 8:
                    continue
                    
                angle = math.atan2(dy, dx)
                ux = math.cos(angle)
                uy = math.sin(angle)
                nx = -uy
                ny = ux
                
                head_len = min(22.0, dist * 0.45)
                head_half_w = 14.0
                
                tip = (x2 - ux * 6.0, y2 - uy * 6.0)
                base_cx = tip[0] - ux * head_len
                base_cy = tip[1] - uy * head_len
                
                h_left = (base_cx + nx * head_half_w, base_cy + ny * head_half_w)
                h_right = (base_cx - nx * head_half_w, base_cy - ny * head_half_w)
                
                shaft_half_w = 6.0
                start_cx = x1 + ux * 8.0
                start_cy = y1 + uy * 8.0
                
                s_left_start = (start_cx + nx * shaft_half_w, start_cy + ny * shaft_half_w)
                s_right_start = (start_cx - nx * shaft_half_w, start_cy - ny * shaft_half_w)
                s_left_end = (base_cx + nx * shaft_half_w, base_cy + ny * shaft_half_w)
                s_right_end = (base_cx - nx * shaft_half_w, base_cy - ny * shaft_half_w)
                
                poly = [s_left_start, s_left_end, h_left, tip, h_right, s_right_end, s_right_start]
                pygame.draw.polygon(annot_surf, COLOR_ARROW, poly)
                pygame.draw.polygon(annot_surf, COLOR_ARROW_BORDER, poly, width=2)
            
        self.screen.blit(annot_surf, (0, 0))

    def draw_eval_bar(self, x, y, width, height, eval_ratio, eval_text, flipped=False):
        container = pygame.Rect(x, y, width, height)
        
        # Ombre
        sh_rect = pygame.Rect(x + 2, y + 2, width, height)
        sh_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(sh_surf, (15, 23, 42, 35), (0, 0, width, height), border_radius=6)
        self.screen.blit(sh_surf, (sh_rect.x, sh_rect.y))

        pygame.draw.rect(self.screen, pygame.Color("#FFFFFF"), container, border_radius=6)
        
        ratio = max(0.02, min(0.98, eval_ratio))
        
        if not flipped:
            white_h = int(height * ratio)
            black_h = height - white_h
            
            if black_h > 0:
                b_rect = pygame.Rect(x, y, width, black_h)
                pygame.draw.rect(self.screen, pygame.Color("#1E293B"), b_rect, 
                                 border_top_left_radius=6, border_top_right_radius=6)
            if white_h > 0:
                w_rect = pygame.Rect(x, y + black_h, width, white_h)
                pygame.draw.rect(self.screen, pygame.Color("#F8FAFC"), w_rect, 
                                 border_bottom_left_radius=6, border_bottom_right_radius=6)
            split_y = y + black_h
        else:
            white_h = int(height * ratio)
            black_h = height - white_h
            
            if white_h > 0:
                w_rect = pygame.Rect(x, y, width, white_h)
                pygame.draw.rect(self.screen, pygame.Color("#F8FAFC"), w_rect, 
                                 border_top_left_radius=6, border_top_right_radius=6)
            if black_h > 0:
                b_rect = pygame.Rect(x, y + white_h, width, black_h)
                pygame.draw.rect(self.screen, pygame.Color("#1E293B"), b_rect, 
                                 border_bottom_left_radius=6, border_bottom_right_radius=6)
            split_y = y + white_h

        pygame.draw.line(self.screen, COLOR_GOLD, (x, split_y), (x + width - 1, split_y), 2)
        pygame.draw.rect(self.screen, COLOR_BORDER, container, width=2, border_radius=6)
        
        # Pastille de score au-dessus de la barre
        if eval_text:
            pill_w = max(38, self.eval_font.size(eval_text)[0] + 10)
            pill_h = 20
            pill_x = x + (width - pill_w) // 2
            pill_y = y - 24
            
            pill_rect = pygame.Rect(pill_x, pill_y, pill_w, pill_h)
            pygame.draw.rect(self.screen, pygame.Color("#FFFFFF"), pill_rect, border_radius=5)
            pygame.draw.rect(self.screen, COLOR_BORDER_STRONG, pill_rect, width=1, border_radius=5)
            
            txt_col = pygame.Color("#0F172A")
            if "M" in eval_text:
                txt_col = COLOR_GOLD_HOVER
            txt_surf = self.eval_font.render(eval_text, True, txt_col)
            self.screen.blit(txt_surf, (pill_rect.centerx - txt_surf.get_width()//2, 
                                        pill_rect.centery - txt_surf.get_height()//2))

    def draw_player_card(self, rect, name, rating_str, avatar_type, is_active_turn, 
                         clock_str, clock_warn=False, captured_pieces=None, material_diff=0, is_top=False,
                         captures_color='b'):
        card_rect = pygame.Rect(rect)
        
        # Ombre portée de carte
        sh_surf = pygame.Surface((card_rect.width, card_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(sh_surf, (15, 23, 42, 18), (0, 0, card_rect.width, card_rect.height), border_radius=8)
        self.screen.blit(sh_surf, (card_rect.x, card_rect.y + 2))

        # Carte blanche Material 3
        bg_col = pygame.Color("#FFFFFF") if not is_active_turn else pygame.Color("#F0FDF4")
        pygame.draw.rect(self.screen, bg_col, card_rect, border_radius=8)
        
        border_col = COLOR_EMERALD if is_active_turn else COLOR_BORDER
        border_w = 2 if is_active_turn else 1
        pygame.draw.rect(self.screen, border_col, card_rect, width=border_w, border_radius=8)
        
        # 1. Cercle Avatar
        av_x = card_rect.x + 10
        av_y = card_rect.centery
        av_rad = 12
        av_bg = pygame.Color("#E0E7FF") if avatar_type != "bot" else pygame.Color("#FEF3C7")
        pygame.draw.circle(self.screen, av_bg, (av_x + av_rad, av_y), av_rad)
        pygame.draw.circle(self.screen, COLOR_EMERALD if is_active_turn else COLOR_BORDER_STRONG, (av_x + av_rad, av_y), av_rad, width=1)
        
        f_av = pygame.font.SysFont('Segoe UI', 11, bold=True)
        av_sym = "IA" if avatar_type == "bot" else ("P2" if is_top else "P1")
        av_txt_col = COLOR_GOLD_HOVER if avatar_type == "bot" else COLOR_INDIGO
        av_txt = f_av.render(av_sym, True, av_txt_col)
        self.screen.blit(av_txt, (av_x + av_rad - av_txt.get_width()//2, av_y - av_txt.get_height()//2))
        
        # 2. Nom du joueur et badge Elo
        text_x = av_x + av_rad * 2 + 8
        name_surf = self.card_font_name.render(name, True, COLOR_TEXT_MAIN)
        self.screen.blit(name_surf, (text_x, card_rect.centery - name_surf.get_height()//2))
        text_x += name_surf.get_width() + 8
        
        if rating_str:
            badge_surf = self.card_font_badge.render(rating_str, True, COLOR_GOLD_HOVER)
            badge_rect = pygame.Rect(text_x, card_rect.centery - 9, badge_surf.get_width() + 8, 18)
            pygame.draw.rect(self.screen, pygame.Color("#FEF3C7"), badge_rect, border_radius=4)
            pygame.draw.rect(self.screen, pygame.Color("#FDE68A"), badge_rect, width=1, border_radius=4)
            self.screen.blit(badge_surf, (badge_rect.x + 4, badge_rect.y + 2))
            text_x += badge_rect.w + 12
            
        # 4. Horloge numérique
        clock_w = 84
        clock_rect = pygame.Rect(card_rect.right - clock_w - 8, card_rect.centery - 13, clock_w, 26)
        max_cap_x = clock_rect.left - 24

        # 3. Affichage du matériel capturé
        if captured_pieces:
            cap_x = text_x
            order = ['P', 'N', 'B', 'R', 'Q']
            for sym in order:
                cnt = captured_pieces.get(sym, 0)
                if cnt > 0 and cap_x < max_cap_x:
                    piece_key = f"{captures_color}{sym}"
                    img = self.mini_images.get(piece_key)
                    if img:
                        num_draw = min(3, cnt)
                        for _ in range(num_draw):
                            if cap_x + 9 > max_cap_x:
                                break
                            self.screen.blit(img, (cap_x, card_rect.centery - 9))
                            cap_x += 9
                        if cnt > 3 and cap_x + 16 <= max_cap_x:
                            f_cnt = pygame.font.SysFont('Segoe UI', 10, bold=True)
                            c_s = f_cnt.render(f"x{cnt}", True, COLOR_TEXT_MUTED)
                            self.screen.blit(c_s, (cap_x + 1, card_rect.centery - 6))
                            cap_x += c_s.get_width() + 4
                        cap_x += 4

            if material_diff > 0 and cap_x < max_cap_x:
                diff_surf = self.card_font_diff.render(f"+{material_diff}", True, COLOR_EMERALD)
                self.screen.blit(diff_surf, (cap_x + 2, card_rect.centery - diff_surf.get_height()//2))

        # Cadre horloge
        pygame.draw.rect(self.screen, COLOR_LED_BG, clock_rect, border_radius=5)
        c_border = COLOR_EMERALD if is_active_turn else COLOR_LED_BORDER
        pygame.draw.rect(self.screen, c_border, clock_rect, width=1, border_radius=5)
        
        c_col = COLOR_LED_TEXT_WARN if clock_warn else (COLOR_LED_TEXT_ACTIVE if is_active_turn else COLOR_LED_TEXT_IDLE)
        clk_surf = self.card_font_led.render(clock_str, True, c_col)
        self.screen.blit(clk_surf, (clock_rect.centerx - clk_surf.get_width()//2, 
                                    clock_rect.centery - clk_surf.get_height()//2))
        
        # 5. Point lumineux pulsation tour actif
        if is_active_turn:
            dot_rad = 4
            now_ticks = pygame.time.get_ticks()
            pulse = (math.sin(now_ticks / 200.0) + 1.0) / 2.0
            dot_alpha = int(180 + pulse * 75)
            dot_surf = pygame.Surface((12, 12), pygame.SRCALPHA)
            pygame.draw.circle(dot_surf, (16, 185, 129, dot_alpha), (6, 6), dot_rad)
            self.screen.blit(dot_surf, (clock_rect.left - 16, card_rect.centery - 6))

    def draw_highlights(self, board, selected_square, last_move, threatened_squares=None, flipped=False):
        if isinstance(threatened_squares, bool):
            flipped = threatened_squares
            threatened_squares = None

        sq_s = self.square_size

        # 0. Menace IA
        if threatened_squares:
            now = pygame.time.get_ticks()
            pulse = (math.sin(now / 220.0) + 1.0) / 2.0
            glow_alpha = int(75 + pulse * 45)
            border_alpha = int(170 + pulse * 60)
            
            for th_sq in threatened_squares:
                sx, sy = self.square_to_screen(th_sq, flipped)
                glow_surf = pygame.Surface((sq_s, sq_s), pygame.SRCALPHA)
                glow_surf.fill((220, 38, 38, glow_alpha))
                rad = sq_s // 2
                pygame.draw.circle(glow_surf, (255, 60, 60, int(glow_alpha * 0.7)), (rad, rad), rad - 6)
                self.screen.blit(glow_surf, (sx, sy))
                
                border_surf = pygame.Surface((sq_s, sq_s), pygame.SRCALPHA)
                pygame.draw.rect(border_surf, (239, 68, 68, border_alpha), 
                                 (0, 0, sq_s, sq_s), width=3, border_radius=4)
                
                c_len = 8
                col = (255, 90, 90, border_alpha)
                pygame.draw.line(border_surf, col, (2, 2), (2 + c_len, 2), 2)
                pygame.draw.line(border_surf, col, (2, 2), (2, 2 + c_len), 2)
                pygame.draw.line(border_surf, col, (sq_s - 3, 2), (sq_s - 3 - c_len, 2), 2)
                pygame.draw.line(border_surf, col, (sq_s - 3, 2), (sq_s - 3 - c_len, 2), 2)
                pygame.draw.line(border_surf, col, (2, sq_s - 3), (2 + c_len, sq_s - 3), 2)
                pygame.draw.line(border_surf, col, (2, sq_s - 3), (2, sq_s - 3 - c_len), 2)
                pygame.draw.line(border_surf, col, (sq_s - 3, sq_s - 3), (sq_s - 3 - c_len, sq_s - 3), 2)
                pygame.draw.line(border_surf, col, (sq_s - 3, sq_s - 3), (sq_s - 3, sq_s - 3 - c_len), 2)
                self.screen.blit(border_surf, (sx, sy))

        # 1. Dernier coup joué (Lueur ambrée)
        if last_move:
            for sq in [last_move.from_square, last_move.to_square]:
                sx, sy = self.square_to_screen(sq, flipped)
                s = pygame.Surface((sq_s, sq_s), pygame.SRCALPHA)
                s.fill(COLOR_HIGHLIGHT)
                self.screen.blit(s, (sx, sy))

        # 2. Alerte Échec au Roi
        if board.is_check():
            king_sq = board.king(board.turn)
            if king_sq is not None:
                sx, sy = self.square_to_screen(king_sq, flipped)
                s = pygame.Surface((sq_s, sq_s), pygame.SRCALPHA)
                s.fill(COLOR_CHECK)
                self.screen.blit(s, (sx, sy))

        # 3. Case sélectionnée (Lueur indigo / cyan)
        if selected_square is not None:
            sx, sy = self.square_to_screen(selected_square, flipped)
            s = pygame.Surface((sq_s, sq_s), pygame.SRCALPHA)
            s.fill(pygame.Color(79, 70, 229, 110))
            self.screen.blit(s, (sx, sy))
            pygame.draw.rect(self.screen, COLOR_INDIGO, 
                             (sx, sy, sq_s, sq_s), width=3)

            # Points indicateurs de déplacements possibles
            for move in board.legal_moves:
                if move.from_square == selected_square:
                    tx, ty = self.square_to_screen(move.to_square, flipped)
                    is_capture = board.is_capture(move)
                    
                    dot_surf = pygame.Surface((sq_s, sq_s), pygame.SRCALPHA)
                    if is_capture:
                        pygame.draw.circle(dot_surf, (239, 68, 68, 180), (sq_s//2, sq_s//2), 
                                           sq_s//2 - 6, width=4)
                    else:
                        pygame.draw.circle(dot_surf, COLOR_MOVE_DOT, (sq_s//2, sq_s//2), 
                                           sq_s//7)
                    self.screen.blit(dot_surf, (tx, ty))

    def draw_pieces(self, board, selected_square=None, dragged_pos=None, flipped=False):
        now = pygame.time.get_ticks()
        if self.animation and self.animation.is_finished(now):
            self.animation = None

        anim_suppressed_squares = set()
        if self.animation:
            anim_suppressed_squares.add(self.animation.to_sq)
            if self.animation.secondary:
                anim_suppressed_squares.add(self.animation.secondary[1])

        sq_s = self.square_size

        # Rendu des pièces statiques
        for square in chess.SQUARES:
            if square == selected_square and dragged_pos is not None:
                continue
            if self.animation and square in anim_suppressed_squares:
                continue

            piece = board.piece_at(square)
            if piece:
                color = 'w' if piece.color == chess.WHITE else 'b'
                key = f"{color}{piece.symbol().upper()}"
                if key in self.images:
                    sx, sy = self.square_to_screen(square, flipped)
                    
                    # Si la pièce est sélectionnée mais non encore glissée (soulèvement 1.15x)
                    if square == selected_square and dragged_pos is None:
                        # Ombre soulevée
                        sh_x = sx + (sq_s - self.lifted_shadow_surface.get_width()) // 2
                        sh_y = sy + sq_s - self.lifted_shadow_surface.get_height() + 2
                        self.screen.blit(self.lifted_shadow_surface, (sh_x, sh_y))
                        
                        img = self.images[key]
                        # Zoom 1.15x
                        scaled_w = int(img.get_width() * 1.15)
                        scaled_h = int(img.get_height() * 1.15)
                        lifted_img = pygame.transform.smoothscale(img, (scaled_w, scaled_h))
                        px = sx + (sq_s - scaled_w) // 2
                        py = sy + (sq_s - scaled_h) // 2 - 8  # Soulèvement de 8px
                        self.screen.blit(lifted_img, (px, py))
                    else:
                        # Ombre 3D normale
                        sh_x = sx + (sq_s - self.shadow_surface.get_width()) // 2
                        sh_y = sy + sq_s - self.shadow_surface.get_height() - 4
                        self.screen.blit(self.shadow_surface, (sh_x, sh_y))
                        
                        img = self.images[key]
                        px = sx + (sq_s - img.get_width()) // 2
                        py = sy + (sq_s - img.get_height()) // 2 - 2
                        self.screen.blit(img, (px, py))

        # Rendu de la pièce prise sous l'animation
        if self.animation and self.animation.captured:
            c_sq, c_key = self.animation.captured
            c_img = self.images.get(c_key)
            if c_img:
                csx, csy = self.square_to_screen(c_sq, flipped)
                c_sh_x = csx + (sq_s - self.shadow_surface.get_width()) // 2
                c_sh_y = csy + sq_s - self.shadow_surface.get_height() - 4
                self.screen.blit(self.shadow_surface, (c_sh_x, c_sh_y))
                
                c_px = csx + (sq_s - c_img.get_width()) // 2
                c_py = csy + (sq_s - c_img.get_height()) // 2 - 2
                self.screen.blit(c_img, (c_px, c_py))

        # Rendu du déplacement cinématique ralenti (slow-motion 280ms avec spring bounce)
        if self.animation:
            ease = self.animation.progress(now)
            lift = self.animation.lift_height(now)
            scale = self.animation.scale_factor(now)
            
            fx, fy = self.square_to_screen(self.animation.from_sq, flipped)
            tx, ty = self.square_to_screen(self.animation.to_sq, flipped)
            cur_x = fx + (tx - fx) * ease
            cur_y = fy + (ty - fy) * ease + lift
            
            img = self.images.get(self.animation.piece_key)
            if img:
                # Ombre au sol qui suit le déplacement X/Y mais reste sur le plateau (sans lift)
                ground_y = fy + (ty - fy) * ease
                sh_x = cur_x + (sq_s - self.lifted_shadow_surface.get_width()) // 2
                sh_y = ground_y + sq_s - self.lifted_shadow_surface.get_height() - 2
                self.screen.blit(self.lifted_shadow_surface, (sh_x, sh_y))
                
                # Image avec léger grossissement dynamique
                if abs(scale - 1.0) > 0.02:
                    sw = int(img.get_width() * scale)
                    sh = int(img.get_height() * scale)
                    cur_img = pygame.transform.smoothscale(img, (sw, sh))
                else:
                    cur_img = img
                    sw, sh = img.get_width(), img.get_height()

                px = cur_x + (sq_s - sw) // 2
                py = cur_y + (sq_s - sh) // 2 - 2
                self.screen.blit(cur_img, (px, py))
                
            # Pièce secondaire (Tour lors du roque)
            if self.animation.secondary:
                s_from, s_to, s_key = self.animation.secondary
                s_fx, s_fy = self.square_to_screen(s_from, flipped)
                s_tx, s_ty = self.square_to_screen(s_to, flipped)
                s_cur_x = s_fx + (s_tx - s_fx) * ease
                s_cur_y = s_fy + (s_ty - s_fy) * ease
                s_img = self.images.get(s_key)
                if s_img:
                    sh_x = s_cur_x + (sq_s - self.shadow_surface.get_width()) // 2
                    sh_y = s_cur_y + sq_s - self.shadow_surface.get_height() - 4
                    self.screen.blit(self.shadow_surface, (sh_x, sh_y))
                    
                    px = s_cur_x + (sq_s - s_img.get_width()) // 2
                    py = s_cur_y + (sq_s - s_img.get_height()) // 2 - 2
                    self.screen.blit(s_img, (px, py))

        # Rendu de la pièce en cours de glissement à la souris (Drag & Drop)
        if selected_square is not None and dragged_pos is not None:
            piece = board.piece_at(selected_square)
            if piece:
                color = 'w' if piece.color == chess.WHITE else 'b'
                key = f"{color}{piece.symbol().upper()}"
                if key in self.images:
                    img = self.images[key]
                    mx, my = dragged_pos
                    # Zoom 1.15x lors du drag
                    dw = int(img.get_width() * 1.15)
                    dh = int(img.get_height() * 1.15)
                    drag_img = pygame.transform.smoothscale(img, (dw, dh))
                    
                    # Ombre flottante décalée
                    self.screen.blit(self.lifted_shadow_surface, 
                                     (mx - self.lifted_shadow_surface.get_width()//2, my + 26))
                    self.screen.blit(drag_img, (mx - dw//2, my - dh//2 - 12))
