import chess
import pygame

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
        if not getattr(self, "_skip_dim", False):
            w, h = screen.get_size()
            dim = pygame.Surface((w, h), pygame.SRCALPHA)
            dim_alpha = self.transition.get_dim_alpha() if getattr(self, "transition", None) else 120
            dim.fill((15, 23, 42, dim_alpha))
            screen.blit(dim, (0, 0))


        # Ombre portée de la modale
        sh_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        pygame.draw.rect(sh_surf, (15, 23, 42, 40), (0, 0, self.rect.w, self.rect.h), border_radius=14)
        screen.blit(sh_surf, (self.rect.x, self.rect.y + 4))

        # Carte modale blanche
        pygame.draw.rect(screen, COLOR_BG_CARD, self.rect, border_radius=14)
        pygame.draw.rect(screen, COLOR_BORDER_STRONG, self.rect, width=2, border_radius=14)

        font = pygame.font.SysFont('DejaVu Sans', 16, bold=True)
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

def draw_wrapped_text(surface, text, font, color, rect, max_lines=2, line_spacing=2):
    """Utility to render wrapped text inside a bounding rectangle."""
    words = text.split(' ')
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        if font.size(test_line)[0] <= rect.width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            if len(lines) >= max_lines:
                break
    if current_line and len(lines) < max_lines:
        lines.append(' '.join(current_line))

    y = rect.y
    for line in lines[:max_lines]:
        txt_surf = font.render(line, True, color)
        surface.blit(txt_surf, (rect.x, y))
        y += font.get_linesize() + line_spacing


class AIPersonasModal:
    """
    Modale de sélection de l'IA avec Galerie de Personas Material 3 :
    - 4 Cartes Personas avec thème de couleur, avatar, Elo, style et citation :
      Lucas (800 Elo, amber), Éléonore (1400 Elo, emerald), Alexandre (2100 Elo, indigo), Le Monstre (3200+ Elo, rose/cyber).
    - Curseur continu d'Elo (500 à 3200 Elo) interactif avec synchronisation bidirectionnelle.
    - Bascule de Mode : Mode Entraînement (Coach 💡 & Ctrl+Z) vs Mode Classé (Officiel ⚔️).
    - Choix de la couleur (Blancs, Aléatoire, Noirs).
    - Cadence de jeu / Horloge (Sans limite, 3 min Blitz, 5 min, 10 min Rapide).
    - Boutons d'action : 'Lancer le défi' et 'Annuler'.
    - Propriétés de rétrocompatibilité : selected_diff, selected_time, selected_color, selected_elo, training_mode.
    """
    def __init__(self, center_pos=None):
        cx = center_pos[0] if center_pos else SCREEN_WIDTH // 2
        cy = center_pos[1] if center_pos else SCREEN_HEIGHT // 2
        self.rect = pygame.Rect(cx - 370, cy - 280, 740, 560)

        # État par défaut (Le Monstre / 3200 Elo / Diff 4 / Sans limite / Blancs / Entraînement)
        self.selected_persona_id = "monster"
        self.selected_persona = BOT_PERSONAS.get("monster", {
            "name": "Le Monstre Stockfish 19", "elo": 3200, "title": "Grand Maître Surhumain",
            "playstyle": "Calcul NNUE impitoyable & jeu parfait", "quote": "0.00 ou Mat forcé."
        })
        self.selected_elo = 3200
        self.training_mode = True
        self.selected_color = chess.WHITE
        self.selected_time = 0
        self.is_dragging_slider = False

        # 1. Galerie des 4 Personas
        self.persona_order = ["lucas", "eleonore", "alexandre", "monster"]
        card_y = self.rect.y + 54
        card_w = 164
        card_h = 168
        gap = 12
        start_x = self.rect.x + 24

        self.persona_cards = {}
        for i, pid in enumerate(self.persona_order):
            p_data = BOT_PERSONAS.get(pid, {})
            c_rect = pygame.Rect(start_x + i * (card_w + gap), card_y, card_w, card_h)
            self.persona_cards[pid] = {
                "rect": c_rect,
                "data": p_data,
                "diff": i + 1
            }
        self.card_elevations = {pid: 0.0 for pid in self.persona_order}

        # Compatibilité diff_buttons pour anciens tests
        self.diff_buttons = [
            (Button(self.persona_cards["lucas"]["rect"], "1. Lucas (800)", font_size=13), 1),
            (Button(self.persona_cards["eleonore"]["rect"], "2. Éléonore (1400)", font_size=13), 2),
            (Button(self.persona_cards["alexandre"]["rect"], "3. Alexandre (2100)", font_size=13), 3),
            (Button(self.persona_cards["monster"]["rect"], "4. Le Monstre (3200+)", font_size=13), 4),
        ]

        # 2. Curseur Elo Continu (500 à 3200)
        self.min_elo = 500
        self.max_elo = 3200
        self.slider_track_rect = pygame.Rect(self.rect.x + 30, self.rect.y + 258, 680, 8)
        self.slider_touch_rect = pygame.Rect(self.rect.x + 20, self.rect.y + 246, 700, 32)

        # 3. Bascule de Mode de Jeu (Entraînement vs Classé)
        self.btn_mode_training = Button(
            (self.rect.x + 30, self.rect.y + 306, 335, 38),
            "Mode Entraînement · Coach & Ctrl+Z", font_size=13
        )
        self.btn_mode_ranked = Button(
            (self.rect.x + 375, self.rect.y + 306, 335, 38),
            "Mode Classé · Règles officielles", font_size=13
        )
        self.mode_buttons = [
            (self.btn_mode_training, True),
            (self.btn_mode_ranked, False)
        ]

        # 4. Choix de la couleur
        self.color_buttons = [
            (Button((self.rect.x + 30, self.rect.y + 368, 215, 36), "Blancs", font_size=14), chess.WHITE),
            (Button((self.rect.x + 262, self.rect.y + 368, 215, 36), "Aléatoire", font_size=14), "RANDOM"),
            (Button((self.rect.x + 495, self.rect.y + 368, 215, 36), "Noirs", font_size=14), chess.BLACK),
        ]

        # 5. Cadences de jeu (Horloge)
        self.time_buttons = [
            (Button((self.rect.x + 30, self.rect.y + 430, 160, 36), "Sans limite", font_size=13), 0),
            (Button((self.rect.x + 203, self.rect.y + 430, 160, 36), "3 min Blitz", font_size=13), 180),
            (Button((self.rect.x + 376, self.rect.y + 430, 160, 36), "5 min", font_size=13), 300),
            (Button((self.rect.x + 550, self.rect.y + 430, 160, 36), "10 min Rapide", font_size=13), 600),
        ]

        # 6. Boutons d'Action Inférieurs
        self.btn_cancel = Button((self.rect.x + 80, self.rect.y + 494, 260, 44), "Annuler", font_size=15)
        self.btn_start = Button(
            (self.rect.x + 400, self.rect.y + 494, 260, 44),
            "Lancer le défi",
            bg_color=COLOR_EMERALD, text_color=pygame.Color("white"), font_size=16
        )

    @property
    def selected_diff(self):
        """Propriété de rétrocompatibilité (1: Lucas, 2: Éléonore, 3: Alexandre, 4: Le Monstre)."""
        diff_map = {"lucas": 1, "eleonore": 2, "alexandre": 3, "monster": 4}
        if self.selected_persona_id in diff_map:
            return diff_map[self.selected_persona_id]
        if self.selected_elo < 1200:
            return 1
        elif self.selected_elo < 1800:
            return 2
        elif self.selected_elo < 2600:
            return 3
        else:
            return 4

    @selected_diff.setter
    def selected_diff(self, val):
        rev_map = {1: "lucas", 2: "eleonore", 3: "alexandre", 4: "monster"}
        if val in rev_map:
            self.select_persona(rev_map[val])
        elif isinstance(val, int) and val >= 500:
            self.selected_elo = val
            self.select_persona_by_elo(val)

    def select_persona(self, pid):
        """Sélectionne un persona et synchronise instantanément le curseur d'Elo."""
        if pid in BOT_PERSONAS:
            self.selected_persona_id = pid
            self.selected_persona = BOT_PERSONAS[pid]
            self.selected_elo = BOT_PERSONAS[pid]["elo"]
            self.is_dragging_slider = False

    def select_persona_by_elo(self, elo):
        """Associe l'Elo continu au persona le plus représentatif."""
        if elo <= 1000:
            pid = "lucas"
        elif elo <= 1750:
            pid = "eleonore"
        elif elo <= 2650:
            pid = "alexandre"
        else:
            pid = "monster"
        self.selected_persona_id = pid
        self.selected_persona = BOT_PERSONAS.get(pid, self.selected_persona)

    def update_slider(self, mouse_x):
        """Met à jour l'Elo continu à partir de la position de la souris et applique le magnétisme."""
        track_x = self.slider_track_rect.x
        track_w = self.slider_track_rect.w
        rel = max(0.0, min(1.0, (mouse_x - track_x) / track_w))
        val = round(self.min_elo + rel * (self.max_elo - self.min_elo))

        # Magnétisme / Snap vers les 4 personas majeurs
        if abs(val - 800) <= 45:
            val = 800
        elif abs(val - 1400) <= 45:
            val = 1400
        elif abs(val - 2100) <= 45:
            val = 2100
        elif abs(val - 3200) <= 45:
            val = 3200

        self.selected_elo = val

        if val == 800:
            self.selected_persona_id = "lucas"
            self.selected_persona = BOT_PERSONAS["lucas"]
        elif val == 1400:
            self.selected_persona_id = "eleonore"
            self.selected_persona = BOT_PERSONAS["eleonore"]
        elif val == 2100:
            self.selected_persona_id = "alexandre"
            self.selected_persona = BOT_PERSONAS["alexandre"]
        elif val >= 3200:
            self.selected_persona_id = "monster"
            self.selected_persona = BOT_PERSONAS["monster"]
        else:
            self.select_persona_by_elo(val)

    def handle_event(self, event):
        """Gestion fine des événements Pygame pour le glissement tactile du curseur."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.slider_touch_rect.collidepoint(event.pos):
                self.is_dragging_slider = True
                self.update_slider(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging_slider = False
        elif event.type == pygame.MOUSEMOTION and self.is_dragging_slider:
            self.update_slider(event.pos[0])

    def handle_click(self, mouse_pos):
        # 1. Clic sur une carte Persona
        for pid, card in self.persona_cards.items():
            card_hit = card["rect"].inflate(0, 8)
            if card["rect"].collidepoint(mouse_pos) or card_hit.collidepoint(mouse_pos):
                self.select_persona(pid)
                return None


        # 2. Clic sur le curseur d'Elo
        if self.slider_touch_rect.collidepoint(mouse_pos):
            self.is_dragging_slider = True
            self.update_slider(mouse_pos[0])
            return None

        # 3. Clic sur la bascule de Mode
        if self.btn_mode_training.rect.collidepoint(mouse_pos):
            self.training_mode = True
            return None
        if self.btn_mode_ranked.rect.collidepoint(mouse_pos):
            self.training_mode = False
            return None

        # 4. Clic sur la couleur
        for btn, col in self.color_buttons:
            if btn.rect.collidepoint(mouse_pos):
                self.selected_color = col
                return None

        # 5. Clic sur la cadence
        for btn, t_val in self.time_buttons:
            if btn.rect.collidepoint(mouse_pos):
                self.selected_time = t_val
                return None

        # 6. Actions principales
        if self.btn_cancel.rect.collidepoint(mouse_pos):
            return "CANCEL"
        if self.btn_start.rect.collidepoint(mouse_pos):
            return "START"

        return None

    def draw(self, screen, mouse_pos):
        # Synchronisation fluide du glissement continu
        if pygame.mouse.get_pressed()[0] and self.is_dragging_slider:
            self.update_slider(mouse_pos[0])
        elif not pygame.mouse.get_pressed()[0]:
            self.is_dragging_slider = False

        if not getattr(self, "_skip_dim", False):
            w, h = screen.get_size()
            dim = pygame.Surface((w, h), pygame.SRCALPHA)
            dim_alpha = self.transition.get_dim_alpha() if getattr(self, "transition", None) else 130
            dim.fill((15, 23, 42, dim_alpha))
            screen.blit(dim, (0, 0))

        # Ombre portée de la modale
        sh_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        pygame.draw.rect(sh_surf, (15, 23, 42, 35), (0, 0, self.rect.w, self.rect.h), border_radius=18)
        screen.blit(sh_surf, (self.rect.x, self.rect.y + 5))

        # Carte blanche conteneur
        pygame.draw.rect(screen, COLOR_BG_CARD, self.rect, border_radius=18)
        pygame.draw.rect(screen, COLOR_BORDER_STRONG, self.rect, width=2, border_radius=18)

        f_title = pygame.font.SysFont('DejaVu Sans', 20, bold=True)
        f_sec = pygame.font.SysFont('DejaVu Sans', 13, bold=True)
        f_card_name = pygame.font.SysFont('DejaVu Sans', 14, bold=True)
        f_card_sub = pygame.font.SysFont('DejaVu Sans', 11)
        f_card_elo = pygame.font.SysFont('DejaVu Sans', 11, bold=True)
        f_card_body = pygame.font.SysFont('DejaVu Sans', 10)
        f_card_quote = pygame.font.SysFont('DejaVu Sans', 10, italic=True)
        f_badge_icon = pygame.font.SysFont('DejaVu Sans', 13, bold=True)

        # En-tête
        title = f_title.render("Défier l'Ordinateur — Galerie des Personas & Stockfish 19", True, COLOR_TEXT_MAIN)
        screen.blit(title, (self.rect.x + (self.rect.w - title.get_width()) // 2, self.rect.y + 14))

        subtitle = f_card_sub.render("Sélectionnez un profil humanisé ou ajustez précisément la force UCI (500 à 3200+ Elo)", True, COLOR_TEXT_MUTED)
        screen.blit(subtitle, (self.rect.x + (self.rect.w - subtitle.get_width()) // 2, self.rect.y + 36))

        # Thèmes visuels des 4 personas
        themes_map = {
            "amber": {
                "main": COLOR_GOLD, "bg": pygame.Color("#F4EADB"),
                "badge": pygame.Color("#EFE1C7"), "fg": pygame.Color("#8E5D2E"), "letter": "L"
            },
            "emerald": {
                "main": COLOR_EMERALD, "bg": pygame.Color("#E8F0E7"),
                "badge": pygame.Color("#D9E8DB"), "fg": pygame.Color("#2C5C45"), "letter": "É"
            },
            "indigo": {
                "main": COLOR_INDIGO, "bg": pygame.Color("#E9EFED"),
                "badge": pygame.Color("#DCE9E5"), "fg": pygame.Color("#365F59"), "letter": "A"
            },
            "rose": {
                "main": COLOR_ROSE, "bg": pygame.Color("#F8EAE6"),
                "badge": pygame.Color("#F1DED9"), "fg": pygame.Color("#8F4B40"), "letter": "M"
            },
        }

        # Rendu des 4 Cartes Personas avec feedback tactile d'élévation animée
        for pid in self.persona_order:
            card = self.persona_cards[pid]
            cr = card["rect"]
            pdata = card["data"]
            theme = themes_map.get(pdata.get("avatar_theme", "amber"), themes_map["amber"])
            is_selected = (self.selected_persona_id == pid)
            is_hovered = cr.collidepoint(mouse_pos)

            # Animation fluide d'élévation au survol (0.0 -> 1.0)
            target_elev = 1.0 if is_hovered else 0.0
            current_elev = self.card_elevations.get(pid, 0.0)
            current_elev += (target_elev - current_elev) * 0.35
            if abs(target_elev - current_elev) < 0.01:
                current_elev = target_elev
            self.card_elevations[pid] = current_elev

            # Décalage vertical en pixels (-3.5px à -4px au survol)
            offset_y = int(current_elev * -4.0)
            draw_cr = pygame.Rect(cr.x, cr.y + offset_y, cr.w, cr.h)

            # Ombre portée de la carte (intensifiée au survol)
            shadow_alpha = int(22 + current_elev * 38)
            sh_card = pygame.Surface((cr.w, cr.h), pygame.SRCALPHA)
            pygame.draw.rect(sh_card, (15, 23, 42, shadow_alpha), (0, 0, cr.w, cr.h), border_radius=12)
            screen.blit(sh_card, (draw_cr.x, draw_cr.y + 3 + int(current_elev * 3)))

            # Fond de la carte
            card_bg = theme["bg"] if is_selected else (COLOR_BG_HOVER if is_hovered else COLOR_BG_CARD)
            pygame.draw.rect(screen, card_bg, draw_cr, border_radius=12)

            # Bordure de la carte (intensifiée au survol)
            border_c = theme["main"] if is_selected else (COLOR_BORDER_STRONG if is_hovered else COLOR_BORDER)
            border_w = 2 if (is_selected or is_hovered) else 1
            pygame.draw.rect(screen, border_c, draw_cr, width=border_w, border_radius=12)

            # Liseré de surbrillance lumineuse additionnel sur le contour lors du survol
            if is_hovered and not is_selected and current_elev > 0.05:
                glow_card = pygame.Surface((draw_cr.w, draw_cr.h), pygame.SRCALPHA)
                t_col = theme["main"]
                pygame.draw.rect(glow_card, (t_col.r, t_col.g, t_col.b, int(90 * current_elev)),
                                 (0, 0, draw_cr.w, draw_cr.h), width=2, border_radius=12)
                screen.blit(glow_card, (draw_cr.x, draw_cr.y))

            # Badge avatar (Pastille circulaire)
            badge_cx = draw_cr.x + 22
            badge_cy = draw_cr.y + 24
            pygame.draw.circle(screen, theme["badge"], (badge_cx, badge_cy), 14)
            pygame.draw.circle(screen, theme["main"], (badge_cx, badge_cy), 14, width=1)
            icon_txt = f_badge_icon.render(theme["letter"], True, theme["fg"])
            screen.blit(icon_txt, (badge_cx - icon_txt.get_width() // 2, badge_cy - icon_txt.get_height() // 2))

            # Nom & Titre
            name_txt = f_card_name.render(pdata.get("name", pid.title()), True, COLOR_TEXT_MAIN)
            screen.blit(name_txt, (draw_cr.x + 42, draw_cr.y + 13))

            title_txt = f_card_sub.render(pdata.get("title", ""), True, COLOR_TEXT_MUTED)
            screen.blit(title_txt, (draw_cr.x + 42, draw_cr.y + 28))

            # Badge Elo
            elo_val = pdata.get("elo", 1000)
            elo_str = f"{elo_val} Elo" if elo_val < 3200 else "3200+ Elo"
            elo_pill = pygame.Rect(draw_cr.x + 12, draw_cr.y + 48, draw_cr.w - 24, 20)
            pygame.draw.rect(screen, theme["badge"], elo_pill, border_radius=6)
            pygame.draw.rect(screen, theme["main"], elo_pill, width=1, border_radius=6)
            elo_txt = f_card_elo.render(elo_str, True, theme["fg"])
            screen.blit(elo_txt, (elo_pill.centerx - elo_txt.get_width() // 2, elo_pill.centery - elo_txt.get_height() // 2))

            # Style de jeu
            style_label = f_card_body.render("Style :", True, COLOR_TEXT_MAIN)
            screen.blit(style_label, (draw_cr.x + 10, draw_cr.y + 72))
            draw_wrapped_text(screen, pdata.get("playstyle", ""), f_card_body, COLOR_TEXT_MUTED,
                              pygame.Rect(draw_cr.x + 10, draw_cr.y + 85, draw_cr.w - 20, 30), max_lines=2)

            # Citation
            quote_rect = pygame.Rect(draw_cr.x + 10, draw_cr.y + 120, draw_cr.w - 20, 42)
            quote_text = f"« {pdata.get('quote', '')} »"
            draw_wrapped_text(screen, quote_text, f_card_quote, pygame.Color("#475569"), quote_rect, max_lines=2)

            # Pastille de sélection active
            if is_selected:
                check_pill = pygame.Rect(draw_cr.right - 22, draw_cr.top + 6, 16, 16)
                pygame.draw.circle(screen, theme["main"], (check_pill.centerx, check_pill.centery), 8)
                f_chk = pygame.font.SysFont('DejaVu Sans', 10, bold=True)
                chk_txt = f_chk.render("✓", True, pygame.Color("white"))
                screen.blit(chk_txt, (check_pill.centerx - chk_txt.get_width() // 2, check_pill.centery - chk_txt.get_height() // 2))


        # 2. Curseur Continu d'Elo
        sy = self.rect.y + 234
        elo_label = f_sec.render(f"Curseur d'Elo Continu UCI : {self.selected_elo} Elo", True, COLOR_TEXT_MAIN)
        screen.blit(elo_label, (self.rect.x + 30, sy))

        # Précision persona / custom
        matching_p = next((p for p in BOT_PERSONAS.values() if p["elo"] == self.selected_elo), None)
        if matching_p:
            match_txt = f_card_sub.render(f"({matching_p['name']} — Niveau calibré)", True, COLOR_EMERALD_DARK)
        else:
            match_txt = f_card_sub.render("(Niveau personnalisé — Calibrage Stockfish 19 continu)", True, COLOR_INDIGO)
        screen.blit(match_txt, (self.rect.x + 32 + elo_label.get_width(), sy + 1))

        # Piste du slider
        tr = self.slider_track_rect
        pygame.draw.rect(screen, COLOR_BORDER, tr, border_radius=4)

        # Portion remplie
        rel_pos = max(0.0, min(1.0, (self.selected_elo - self.min_elo) / (self.max_elo - self.min_elo)))
        filled_w = int(rel_pos * tr.w)
        if filled_w > 0:
            filled_rect = pygame.Rect(tr.x, tr.y, filled_w, tr.h)
            fill_col = COLOR_EMERALD if self.selected_elo <= 1600 else (COLOR_INDIGO if self.selected_elo <= 2600 else COLOR_ROSE)
            pygame.draw.rect(screen, fill_col, filled_rect, border_radius=4)

        # Curseur / Thumb
        thumb_cx = tr.x + filled_w
        thumb_cy = tr.centery
        sh_thumb = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.circle(sh_thumb, (15, 23, 42, 35), (12, 14), 10)
        screen.blit(sh_thumb, (thumb_cx - 12, thumb_cy - 12))

        thumb_color = COLOR_EMERALD if self.selected_elo <= 1600 else (COLOR_INDIGO if self.selected_elo <= 2600 else COLOR_ROSE)
        pygame.draw.circle(screen, pygame.Color("white"), (thumb_cx, thumb_cy), 10)
        pygame.draw.circle(screen, thumb_color, (thumb_cx, thumb_cy), 10, width=2)
        pygame.draw.circle(screen, thumb_color, (thumb_cx, thumb_cy), 4)

        # Repères sous le slider
        ticks = [
            (500, "500"), (800, "800 (Lucas)"),
            (1400, "1400 (Éléonore)"), (2100, "2100 (Alexandre)"),
            (3200, "3200+ (Monstre)")
        ]
        for t_elo, t_lbl in ticks:
            tx = tr.x + int(((t_elo - self.min_elo) / (self.max_elo - self.min_elo)) * tr.w)
            pygame.draw.line(screen, COLOR_BORDER_STRONG, (tx, tr.bottom + 2), (tx, tr.bottom + 6), width=1)
            t_surf = f_card_body.render(t_lbl, True, COLOR_TEXT_MUTED)
            align_x = tx - t_surf.get_width() // 2
            align_x = max(tr.x, min(tr.right - t_surf.get_width(), align_x))
            screen.blit(t_surf, (align_x, tr.bottom + 8))

        # 3. Bascule de Mode de Jeu (Entraînement vs Classé)
        screen.blit(f_sec.render("Mode de jeu :", True, COLOR_TEXT_MUTED), (self.rect.x + 30, self.rect.y + 288))
        self.btn_mode_training.is_active = self.training_mode
        self.btn_mode_ranked.is_active = not self.training_mode
        self.btn_mode_training.draw(screen, mouse_pos)
        self.btn_mode_ranked.draw(screen, mouse_pos)

        # 4. Choix de la couleur
        screen.blit(f_sec.render("Votre couleur :", True, COLOR_TEXT_MUTED), (self.rect.x + 30, self.rect.y + 350))
        for btn, col in self.color_buttons:
            btn.is_active = (self.selected_color == col)
            btn.draw(screen, mouse_pos)

        # 5. Cadence
        screen.blit(f_sec.render("Cadence de jeu (Horloge) :", True, COLOR_TEXT_MUTED), (self.rect.x + 30, self.rect.y + 412))
        for btn, t_val in self.time_buttons:
            btn.is_active = (self.selected_time == t_val)
            btn.draw(screen, mouse_pos)

        # 6. Boutons inférieurs
        self.btn_cancel.draw(screen, mouse_pos)
        self.btn_start.draw(screen, mouse_pos)


# Alias de rétrocompatibilité pour tests et composants existants
AISettingsModal = AIPersonasModal

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
        if not getattr(self, "_skip_dim", False):
            w, h = screen.get_size()
            dim = pygame.Surface((w, h), pygame.SRCALPHA)
            dim_alpha = self.transition.get_dim_alpha() if getattr(self, "transition", None) else 130
            dim.fill((15, 23, 42, dim_alpha))
            screen.blit(dim, (0, 0))

        # Ombre portée
        sh_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        pygame.draw.rect(sh_surf, (15, 23, 42, 40), (0, 0, self.rect.w, self.rect.h), border_radius=16)
        screen.blit(sh_surf, (self.rect.x, self.rect.y + 4))

        pygame.draw.rect(screen, COLOR_BG_CARD, self.rect, border_radius=16)
        pygame.draw.rect(screen, COLOR_BORDER_STRONG, self.rect, width=2, border_radius=16)

        title_font = pygame.font.SysFont('DejaVu Sans', 22, bold=True)
        sec_font = pygame.font.SysFont('DejaVu Sans', 15, bold=True)

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
        if not getattr(self, "_skip_dim", False):
            w, h = screen.get_size()
            dim = pygame.Surface((w, h), pygame.SRCALPHA)
            dim_alpha = self.transition.get_dim_alpha() if getattr(self, "transition", None) else 130
            dim.fill((15, 23, 42, dim_alpha))
            screen.blit(dim, (0, 0))


        # Ombre
        sh_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        pygame.draw.rect(sh_surf, (15, 23, 42, 45), (0, 0, self.rect.w, self.rect.h), border_radius=16)
        screen.blit(sh_surf, (self.rect.x, self.rect.y + 5))

        pygame.draw.rect(screen, COLOR_BG_CARD, self.rect, border_radius=16)
        pygame.draw.rect(screen, COLOR_GOLD, self.rect, width=2, border_radius=16)

        f1 = pygame.font.SysFont('DejaVu Sans', 24, bold=True)
        f2 = pygame.font.SysFont('DejaVu Sans', 15)

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
