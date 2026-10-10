import pygame
import chess
import sys
import random
import time
import math
from queue import Queue
from constants import *
from network import NetworkManager
from ai import ChessAI
from audio import SoundManager
from ui import UI, Button, TextInput
from modals import PromotionModal, AISettingsModal, LocalSettingsModal, GameOverModal
from animations import PieceCinematicAnimation, ConfettiParticleSystem, RippleEffect

class GameApp:
    def __init__(self):
        pygame.init()
        pygame.key.set_repeat(400, 50)
        
        self.window_width = SCREEN_WIDTH
        self.window_height = SCREEN_HEIGHT
        self.is_fullscreen = False
        
        self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
        pygame.display.set_caption("Échecs P2P Pro — Stockfish 19 Edition")
        
        # Chargement de l'icône originale officielle
        icon_path = resource_path(os.path.join("assets", "icon.png"))
        if not os.path.exists(icon_path):
            icon_path = resource_path("icon.png")
        if os.path.exists(icon_path):
            try:
                icon_surf = pygame.image.load(icon_path)
                pygame.display.set_icon(icon_surf)
            except Exception:
                pass

        self.clock = pygame.time.Clock()
        self.ui = UI(self.screen)
        self.sounds = SoundManager()
        self.confetti = ConfettiParticleSystem()
        
        self.state = "MENU"
        self.mode = "local"
        self.board = chess.Board()
        self.network = NetworkManager()
        self.ai = ChessAI()
        self.ai_move_queue = Queue()
        
        self.player_color = chess.WHITE
        self.flipped = False
        self.selected_square = None
        self.dragged_pos = None
        self.drag_start_pos = None
        self.is_dragging = False
        self.last_move = None
        self.ai_threatened_squares = set()
        self.waiting_for_ai = False
        self.game_over = False
        
        # Time controls
        self.time_limit = 0  # 0 = Unlimited
        self.white_time = 0.0
        self.black_time = 0.0
        self.last_clock_tick = None
        
        # Move History (SAN)
        self.move_history = []  # list of {"num": int, "white": str, "black": str}
        self.history_scroll = 0
        self.replay_index = 0   # Half-move index currently displayed (len(move_stack) = live)
        
        # Tactical Annotations (Right-Click Drag Arrows & Single-Click Circles)
        self.arrows = set()     # Set of (from_sq, to_sq) tuples
        self.circles = set()    # Set of square integers
        self.right_drag_start = None
        self.right_drag_hover = None
        
        # Themes & Visual Customization
        self.current_theme = DEFAULT_THEME
        self.ui.set_theme(self.current_theme)
        
        # Stockfish Advantage Bar (Eval Bar)
        self.eval_enabled = True
        self.current_eval_score = 0
        self.current_eval_text = "0.0"
        self.current_eval_ratio = 0.5
        self.target_eval_ratio = 0.5
        
        # Chat
        self.active_tab = "history"  # "history" or "chat"
        self.chat_messages = []  # list of {"sender": str, "text": str, "is_me": bool}
        self.chat_scroll = 0
        self.unread_chat = 0
        self.chat_input = TextInput((PANEL_X + 15, 498, PANEL_WIDTH - 30, 36), placeholder="Message... (Entrée)", max_chars=50)
        
        # Hosting custom server name
        self.server_name = "Salon de Thomas"
        self.host_name_input = TextInput((SCREEN_WIDTH//2 - 210, 175, 420, 42), 
                                         initial_text=self.server_name, max_chars=30)
        self.host_time_buttons = [
            (Button((SCREEN_WIDTH//2 - 210, 255, 100, 38), "Illimité", font_size=14), 0),
            (Button((SCREEN_WIDTH//2 - 100, 255, 100, 38), "3 min", font_size=14), 180),
            (Button((SCREEN_WIDTH//2 + 10, 255, 100, 38), "5 min", font_size=14), 300),
            (Button((SCREEN_WIDTH//2 + 120, 255, 100, 38), "10 min", font_size=14), 600),
        ]
        self.host_selected_time = 0
        
        # Modals
        self.active_modal = None
        self.pending_promotion = None  # (from_sq, to_sq)
        
        # Menu Buttons (Tactiles 3D)
        cx = SCREEN_WIDTH // 2 - 170
        btn_w, btn_h = 340, 52
        self.btn_ai = Button((cx, 260, btn_w, btn_h), "1. Jouer contre l'IA (Stockfish 19)", 
                             bg_color=COLOR_EMERALD, text_color=pygame.Color("white"), font_size=17)
        self.btn_host = Button((cx, 324, btn_w, btn_h), "2. Créer une Partie Réseau (Hôte)", 
                              bg_color=COLOR_INDIGO, text_color=pygame.Color("white"), font_size=17)
        self.btn_join = Button((cx, 388, btn_w, btn_h), "3. Rejoindre une Partie (Client)", font_size=17)
        self.btn_local = Button((cx, 452, btn_w, btn_h), "4. Jouer à Deux (Sur ce PC)", font_size=17)
        self.btn_quit = Button((cx, 516, btn_w, btn_h), "Quitter le Jeu", 
                               bg_color=pygame.Color("#EF4444"), text_color=pygame.Color("white"), font_size=16)
        
        # In-Game Side Panel Quick Toolbar Buttons
        self.btn_theme = Button((PANEL_X + 15, 80, 76, 26), "🎨 Bois", font_size=12)
        self.btn_mute = Button((PANEL_X + 99, 80, 76, 26), "🔊 Son", font_size=12)
        self.btn_flip = Button((PANEL_X + 183, 80, 76, 26), "🔄 Inverser", font_size=12)
        self.btn_eval_toggle = Button((PANEL_X + 267, 80, 76, 26), "📊 Éval", font_size=12)
        
        # In-Game Side Panel Tabs
        self.tab_btn_history = Button((PANEL_X + 15, 142, 160, 28), "Historique", font_size=13)
        self.tab_btn_chat = Button((PANEL_X + 183, 142, 160, 28), "Chat", font_size=13)
        
        # History Replay Control Buttons
        r_x = PANEL_X + 79
        self.btn_replay_first = Button((r_x, 468, 44, 28), "< <", font_size=13)
        self.btn_replay_prev = Button((r_x + 52, 468, 44, 28), "<", font_size=13)
        self.btn_replay_next = Button((r_x + 104, 468, 44, 28), ">", font_size=13)
        self.btn_replay_last = Button((r_x + 156, 468, 44, 28), "> >", font_size=13)
        self.btn_replay_live = Button((r_x, 502, 200, 26), "Revenir au direct ▶", font_size=12,
                                      bg_color=COLOR_INDIGO, text_color=pygame.Color("white"))
        
        self.btn_resign = Button((PANEL_X + 15, 550, PANEL_WIDTH - 30, 38), "Abandonner", 
                                 bg_color=pygame.Color("#FEE2E2"), hover_color=pygame.Color("#FECACA"), 
                                 text_color=pygame.Color("#DC2626"), edge_color=pygame.Color("#FCA5A5"), font_size=15)
        self.btn_back = Button((PANEL_X + 15, 596, PANEL_WIDTH - 30, 38), "Menu Principal", font_size=15)

        self.recalculate_layout(self.window_width, self.window_height)

    def recalculate_layout(self, width, height):
        """Mise à l'échelle responsive dynamique de tous les éléments UI."""
        self.window_width = max(MIN_WIDTH, width)
        self.window_height = max(MIN_HEIGHT, height)
        self.ui.recalculate_layout(self.window_width, self.window_height)
        
        w = self.window_width
        h = self.window_height
        
        # 1. Repositionnement Menu
        cx = w // 2 - 170
        btn_w, btn_h = 340, 50
        menu_y = int(h * 0.35)
        self.btn_ai.rect = pygame.Rect(cx, menu_y, btn_w, btn_h)
        self.btn_host.rect = pygame.Rect(cx, menu_y + 60, btn_w, btn_h)
        self.btn_join.rect = pygame.Rect(cx, menu_y + 120, btn_w, btn_h)
        self.btn_local.rect = pygame.Rect(cx, menu_y + 180, btn_w, btn_h)
        self.btn_quit.rect = pygame.Rect(cx, menu_y + 240, btn_w, btn_h)

        # 2. Repositionnement Lobby
        self.host_name_input.rect = pygame.Rect(w // 2 - 210, 175, 420, 42)
        for i, (btn, _) in enumerate(self.host_time_buttons):
            bx = w // 2 - 210 + i * 110
            btn.rect = pygame.Rect(bx, 255, 100, 38)

        # 3. Repositionnement Panneau de jeu latéral
        p_x = self.ui.panel_x
        p_w = self.ui.panel_width
        p_y = self.ui.board_y - BOARD_FRAME
        p_h = self.ui.full_board_size

        t_btn_w = max(55, (p_w - 30 - 3 * 8) // 4)
        self.btn_theme.rect = pygame.Rect(p_x + 15, p_y + 36, t_btn_w, 28)
        self.btn_mute.rect = pygame.Rect(p_x + 15 + (t_btn_w + 8), p_y + 36, t_btn_w, 28)
        self.btn_flip.rect = pygame.Rect(p_x + 15 + (t_btn_w + 8) * 2, p_y + 36, t_btn_w, 28)
        self.btn_eval_toggle.rect = pygame.Rect(p_x + 15 + (t_btn_w + 8) * 3, p_y + 36, t_btn_w, 28)

        tab_w = (p_w - 38) // 2
        self.tab_btn_history.rect = pygame.Rect(p_x + 15, p_y + 98, tab_w, 30)
        self.tab_btn_chat.rect = pygame.Rect(p_x + 15 + tab_w + 8, p_y + 98, tab_w, 30)

        self.btn_back.rect = pygame.Rect(p_x + 15, p_y + p_h - 48, p_w - 30, 38)
        self.btn_resign.rect = pygame.Rect(p_x + 15, p_y + p_h - 94, p_w - 30, 38)
        self.chat_input.rect = pygame.Rect(p_x + 15, p_y + p_h - 142, p_w - 30, 36)

        rw = 44
        rx_start = p_x + (p_w - (rw * 4 + 18)) // 2
        self.btn_replay_first.rect = pygame.Rect(rx_start, p_y + p_h - 180, rw, 28)
        self.btn_replay_prev.rect = pygame.Rect(rx_start + rw + 6, p_y + p_h - 180, rw, 28)
        self.btn_replay_next.rect = pygame.Rect(rx_start + (rw + 6) * 2, p_y + p_h - 180, rw, 28)
        self.btn_replay_last.rect = pygame.Rect(rx_start + (rw + 6) * 3, p_y + p_h - 180, rw, 28)
        self.btn_replay_live.rect = pygame.Rect(p_x + (p_w - 200) // 2, p_y + p_h - 142, 200, 28)

    def reset_game(self, player_color=chess.WHITE, time_limit=0):
        self.board = chess.Board()
        self.selected_square = None
        self.dragged_pos = None
        self.drag_start_pos = None
        self.is_dragging = False
        self.last_move = None
        self.ai_threatened_squares = set()
        self.waiting_for_ai = False
        self.game_over = False
        self.player_color = player_color
        self.flipped = (player_color == chess.BLACK)
        self.active_modal = None
        self.pending_promotion = None
        self.time_limit = time_limit
        self.white_time = float(time_limit)
        self.black_time = float(time_limit)
        self.last_clock_tick = time.time()
        self.move_history = []
        self.history_scroll = 0
        self.chat_messages = []
        self.chat_scroll = 0
        self.unread_chat = 0
        self.active_tab = "history"
        self.replay_index = 0
        self.arrows.clear()
        self.circles.clear()
        self.right_drag_start = None
        self.right_drag_hover = None
        self.current_eval_ratio = 0.5
        self.target_eval_ratio = 0.5
        self.current_eval_text = "0.0"
        self.confetti.stop()
        self.request_eval()
        while not self.ai_move_queue.empty():
            try:
                self.ai_move_queue.get_nowait()
            except Exception:
                break

    def cycle_theme(self):
        new_key = self.ui.cycle_theme()
        self.current_theme = new_key
        name_short = THEMES[new_key]["name"].split()[0]
        self.btn_theme.text = f"🎨 {name_short}"
        return new_key

    def request_eval(self, board=None):
        if not self.eval_enabled:
            return
        target_board = board if board is not None else self.get_display_board()
        def _on_eval(cp, text):
            self.current_eval_score = cp
            self.current_eval_text = text
            ratio = 1.0 / (1.0 + 10.0 ** (-max(-1500, min(1500, cp)) / 400.0))
            self.target_eval_ratio = max(0.04, min(0.96, ratio))
        self.ai.evaluate_board_async(target_board, _on_eval)

    def is_replaying(self):
        return self.replay_index < len(self.board.move_stack)

    def get_display_board(self):
        if not self.is_replaying():
            return self.board
        b = chess.Board()
        for m in self.board.move_stack[:self.replay_index]:
            b.push(m)
        return b

    def step_replay(self, delta):
        total = len(self.board.move_stack)
        prev_idx = self.replay_index
        self.replay_index = max(0, min(total, self.replay_index + delta))
        if self.replay_index != prev_idx:
            self.request_eval()

    def format_clock(self, seconds_left):
        if self.time_limit == 0:
            return "∞"
        s = max(0, int(seconds_left))
        m = s // 60
        sec = s % 60
        return f"{m:02d}:{sec:02d}"

    def compute_material_stats(self, board):
        vals = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}
        w_rem = {chess.PAWN: 0, chess.KNIGHT: 0, chess.BISHOP: 0, chess.ROOK: 0, chess.QUEEN: 0}
        b_rem = {chess.PAWN: 0, chess.KNIGHT: 0, chess.BISHOP: 0, chess.ROOK: 0, chess.QUEEN: 0}
        
        for sq in chess.SQUARES:
            p = board.piece_at(sq)
            if p and p.piece_type in vals:
                if p.color == chess.WHITE:
                    w_rem[p.piece_type] += 1
                else:
                    b_rem[p.piece_type] += 1
                    
        total_types = {chess.PAWN: 8, chess.KNIGHT: 2, chess.BISHOP: 2, chess.ROOK: 2, chess.QUEEN: 1}
        w_caps = {}
        b_caps = {}
        for pt, tot in total_types.items():
            sym = chess.piece_symbol(pt).upper()
            w_caps[sym] = max(0, tot - b_rem[pt])
            b_caps[sym] = max(0, tot - w_rem[pt])
            
        w_val = sum(cnt * vals[pt] for pt, cnt in w_rem.items())
        b_val = sum(cnt * vals[pt] for pt, cnt in b_rem.items())
        
        diff_w = max(0, w_val - b_val)
        diff_b = max(0, b_val - w_val)
        return w_caps, b_caps, diff_w, diff_b

    def get_player_name(self):
        if self.mode == "ai":
            return "Vous"
        elif self.mode == "p2p":
            return self.server_name if self.network.is_host else "Client"
        return "Joueur 1 (Blancs)"

    def get_player_rating(self):
        if self.mode == "ai":
            return "1850"
        elif self.mode == "p2p":
            return "P2P"
        return "1500"

    def get_opponent_name(self):
        if self.mode == "ai":
            return self.ai.engine_name.split('(')[0].strip()
        elif self.mode == "p2p":
            return "Adversaire"
        else:
            return "Joueur 2 (Noirs)"

    def get_opponent_rating(self):
        if self.mode == "ai":
            presets = {1: "800", 2: "1500", 3: "2200", 4: "3600 GM"}
            return presets.get(self.ai.difficulty, "3600")
        elif self.mode == "p2p":
            return "P2P"
        return "1500"

    def execute_move(self, move, animated=True):
        if move in self.board.legal_moves:
            moving_piece = self.board.piece_at(move.from_square)
            captured_piece = self.board.piece_at(move.to_square)
            
            # Detect en passant
            if moving_piece and moving_piece.piece_type == chess.PAWN and self.board.is_en_passant(move):
                ep_sq = chess.square(chess.square_file(move.to_square), chess.square_rank(move.from_square))
                captured_piece = self.board.piece_at(ep_sq)

            is_capture = (captured_piece is not None)
            
            # Animation details
            color_prefix = 'w' if moving_piece.color == chess.WHITE else 'b'
            piece_key = f"{color_prefix}{moving_piece.symbol().upper()}"
            
            secondary = None
            if moving_piece.piece_type == chess.KING:
                if move.from_square == chess.E1 and move.to_square == chess.G1:
                    secondary = (chess.H1, chess.F1, "wR")
                elif move.from_square == chess.E1 and move.to_square == chess.C1:
                    secondary = (chess.A1, chess.D1, "wR")
                elif move.from_square == chess.E8 and move.to_square == chess.G8:
                    secondary = (chess.H8, chess.F8, "bR")
                elif move.from_square == chess.E8 and move.to_square == chess.C8:
                    secondary = (chess.A8, chess.D8, "bR")

            captured_info = None
            if is_capture and captured_piece:
                c_col = 'w' if captured_piece.color == chess.WHITE else 'b'
                c_key = f"{c_col}{captured_piece.symbol().upper()}"
                c_sq = move.to_square
                if moving_piece.piece_type == chess.PAWN and self.board.is_en_passant(move):
                    c_sq = chess.square(chess.square_file(move.to_square), chess.square_rank(move.from_square))
                captured_info = (c_sq, c_key)

            # Record SAN before pushing
            san_str = self.board.san(move)
            if moving_piece.color == chess.WHITE:
                self.move_history.append({"num": len(self.move_history) + 1, "white": san_str, "black": ""})
            else:
                if not self.move_history or self.move_history[-1]["black"] != "":
                    self.move_history.append({"num": len(self.move_history) + 1, "white": "...", "black": san_str})
                else:
                    self.move_history[-1]["black"] = san_str
            self.history_scroll = max(0, len(self.move_history) - 14)

            # Push move
            was_replaying = self.is_replaying()
            self.board.push(move)
            if not was_replaying:
                self.replay_index = len(self.board.move_stack)
            else:
                self.replay_index = min(self.replay_index, len(self.board.move_stack))
            self.last_move = move
            self.selected_square = None
            self.dragged_pos = None
            self.drag_start_pos = None
            self.is_dragging = False
            self.arrows.clear()
            self.circles.clear()
            self.request_eval()

            # Start cinematic slow-motion animation (280ms)
            if animated:
                self.ui.start_animation(
                    move.from_square, move.to_square, piece_key, 
                    secondary=secondary, captured=captured_info, duration_ms=280,
                    is_capture=is_capture, is_check=self.board.is_check()
                )

            if self.mode != "ai" or moving_piece.color == self.player_color:
                self.ai_threatened_squares = set()

            is_over = self.board.is_game_over(claim_draw=True)
            if is_over:
                self.trigger_game_over()
            else:
                self.sounds.play_for_move(self.board, is_capture=is_capture, is_game_over=False)
            return True
        return False

    def compute_ai_threats(self, move):
        threats = set()
        if not move:
            self.ai_threatened_squares = threats
            return
        to_sq = move.to_square
        ai_piece = self.board.piece_at(to_sq)
        if ai_piece:
            player_color = self.board.turn
            for sq in self.board.attacks(to_sq):
                target = self.board.piece_at(sq)
                if target and target.color == player_color:
                    threats.add(sq)
        self.ai_threatened_squares = threats

    def trigger_game_over(self):
        self.game_over = True
        self.sounds.play_gameover()
        if self.board.is_checkmate():
            winner = "Noirs" if self.board.turn == chess.WHITE else "Blancs"
            msg = f"ÉCHEC ET MAT ! Victoire des {winner}"
            sub = "Partie terminée par décision magistrale"
            # Déclenchement de la pluie de confettis festifs
            self.confetti.trigger(self.window_width, self.window_height, 150)
        elif self.board.is_stalemate():
            msg = "PAT ! Partie Nulle"
            sub = "Le roi n'a aucun coup légal et n'est pas en échec"
        elif self.board.is_insufficient_material():
            msg = "NULLE : Matériel Insuffisant"
            sub = "Aucun joueur ne peut mater"
        else:
            msg = "PARTIE NULLE"
            sub = "Répétition de coups ou règle des 50 coups"
        self.active_modal = GameOverModal(msg, sub, center_pos=(self.window_width//2, self.window_height//2))

    def trigger_timeout(self, loser_color):
        self.game_over = True
        winner = "Noirs" if loser_color == chess.WHITE else "Blancs"
        self.sounds.play_gameover()
        self.active_modal = GameOverModal("TEMPS ÉCOULÉ !", f"Victoire des {winner} au chronomètre",
                                          center_pos=(self.window_width//2, self.window_height//2))
        if self.mode == "p2p":
            loser_str = "white" if loser_color == chess.WHITE else "black"
            self.network.send_timeout(loser_str)

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0  # Delta time en secondes pour physique fluide
            mouse_pos = pygame.mouse.get_pos()
            events = pygame.event.get()
            
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    if not self.is_fullscreen:
                        new_w = max(MIN_WIDTH, event.w)
                        new_h = max(MIN_HEIGHT, event.h)
                        self.screen = pygame.display.set_mode((new_w, new_h), pygame.RESIZABLE)
                        self.recalculate_layout(new_w, new_h)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self.is_fullscreen = not self.is_fullscreen
                    if self.is_fullscreen:
                        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                        cur_w, cur_h = self.screen.get_size()
                        self.recalculate_layout(cur_w, cur_h)
                    else:
                        self.screen = pygame.display.set_mode((DEFAULT_WIDTH, DEFAULT_HEIGHT), pygame.RESIZABLE)
                        self.recalculate_layout(DEFAULT_WIDTH, DEFAULT_HEIGHT)

            # Mise à jour des confettis
            if self.confetti.is_active:
                self.confetti.update(dt)

            if self.state == "MENU":
                self.draw_menu(mouse_pos, events)
            elif self.state == "LOBBY_HOST":
                self.draw_lobby_host(mouse_pos, events)
            elif self.state == "LOBBY_JOIN":
                self.draw_lobby_join(mouse_pos, events)
            elif self.state == "PLAY":
                self.draw_play(mouse_pos, events)
            
            # Affichage de la pluie de confettis par-dessus le plateau
            if self.confetti.is_active:
                self.confetti.draw(self.screen)

            # Rendu de la modale active par-dessus
            if self.active_modal:
                self.active_modal.draw(self.screen, mouse_pos)
                self.handle_modal_events(events, mouse_pos)
                
            pygame.display.flip()
            
        self.network.close()
        self.ai.close()
        pygame.quit()
        sys.exit()

    def handle_modal_events(self, events, mouse_pos):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                action = self.active_modal.handle_click(mouse_pos)
                if isinstance(self.active_modal, AISettingsModal):
                    if action == "START":
                        diff = self.active_modal.selected_diff
                        col = self.active_modal.selected_color
                        t_val = self.active_modal.selected_time
                        if col == "RANDOM":
                            col = random.choice([chess.WHITE, chess.BLACK])
                        self.ai.start(diff_level=diff)
                        self.mode = "ai"
                        self.reset_game(player_color=col, time_limit=t_val)
                        self.state = "PLAY"
                        self.active_modal = None
                    elif action == "CANCEL":
                        self.active_modal = None

                elif isinstance(self.active_modal, LocalSettingsModal):
                    if action == "START":
                        t_val = self.active_modal.selected_time
                        self.mode = "local"
                        self.reset_game(player_color=chess.WHITE, time_limit=t_val)
                        self.state = "PLAY"
                        self.active_modal = None
                    elif action == "CANCEL":
                        self.active_modal = None
                        
                elif isinstance(self.active_modal, PromotionModal):
                    if action in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
                        from_sq, to_sq = self.pending_promotion
                        move = chess.Move(from_sq, to_sq, promotion=action)
                        if self.execute_move(move) and self.mode == "p2p":
                            self.network.send_move(move.uci())
                        self.active_modal = None
                        self.pending_promotion = None
                        
                elif isinstance(self.active_modal, GameOverModal):
                    if action == "REPLAY":
                        if self.mode == "p2p":
                            self.network.send_rematch()
                        self.reset_game(self.player_color, time_limit=self.time_limit)
                        self.active_modal = None
                    elif action == "MENU":
                        if self.mode == "p2p":
                            self.network.close()
                            self.network = NetworkManager()
                        self.state = "MENU"
                        self.active_modal = None

    def draw_menu(self, mouse_pos, events):
        self.screen.fill(COLOR_BG_DARK)
        
        w = self.window_width
        h = self.window_height
        
        # Carte blanche flottante pour le conteneur du Menu (Style Material 3)
        menu_card_w = 420
        menu_card_h = 440
        menu_card_x = w // 2 - menu_card_w // 2
        menu_card_y = int(h * 0.28)
        
        # Ombre douce
        sh_surf = pygame.Surface((menu_card_w, menu_card_h), pygame.SRCALPHA)
        pygame.draw.rect(sh_surf, (15, 23, 42, 25), (0, 0, menu_card_w, menu_card_h), border_radius=18)
        self.screen.blit(sh_surf, (menu_card_x, menu_card_y + 4))

        # Carte blanche
        menu_card = pygame.Rect(menu_card_x, menu_card_y, menu_card_w, menu_card_h)
        pygame.draw.rect(self.screen, COLOR_BG_CARD, menu_card, border_radius=18)
        pygame.draw.rect(self.screen, COLOR_BORDER, menu_card, width=2, border_radius=18)

        # Header Badge
        badge_font = pygame.font.SysFont('Segoe UI', 12, bold=True)
        badge = badge_font.render("OFFLINE P2P LAN • STOCKFISH 19 ENGINES • AUDIO & CHAT", True, COLOR_EMERALD)
        self.screen.blit(badge, (w//2 - badge.get_width()//2, int(h * 0.08)))
        
        # Title
        title_font = pygame.font.SysFont('Segoe UI', 44, bold=True)
        title = title_font.render("ÉCHECS P2P PRO", True, COLOR_TEXT_MAIN)
        self.screen.blit(title, (w//2 - title.get_width()//2, int(h * 0.12)))
        
        # Subtitle
        sub_font = pygame.font.SysFont('Segoe UI', 15)
        sub = sub_font.render("Jeu d'échecs en réseau local sans internet avec IA Grand Maître", True, COLOR_TEXT_MUTED)
        self.screen.blit(sub, (w//2 - sub.get_width()//2, int(h * 0.20)))
        
        # Draw Menu Buttons
        self.btn_ai.draw(self.screen, mouse_pos)
        self.btn_host.draw(self.screen, mouse_pos)
        self.btn_join.draw(self.screen, mouse_pos)
        self.btn_local.draw(self.screen, mouse_pos)
        self.btn_quit.draw(self.screen, mouse_pos)
        
        if not self.active_modal:
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.btn_ai.rect.collidepoint(mouse_pos):
                        self.active_modal = AISettingsModal(center_pos=(w//2, h//2))
                    elif self.btn_host.rect.collidepoint(mouse_pos):
                        self.mode = "p2p"
                        self.network.host_game(server_name=self.server_name)
                        self.reset_game(chess.WHITE, time_limit=self.host_selected_time)
                        self.state = "LOBBY_HOST"
                    elif self.btn_join.rect.collidepoint(mouse_pos):
                        self.mode = "p2p"
                        self.network.discover_games()
                        self.state = "LOBBY_JOIN"
                    elif self.btn_local.rect.collidepoint(mouse_pos):
                        self.active_modal = LocalSettingsModal(center_pos=(w//2, h//2))
                    elif self.btn_quit.rect.collidepoint(mouse_pos):
                        pygame.quit()
                        sys.exit()

    def draw_lobby_host(self, mouse_pos, events):
        self.screen.fill(COLOR_BG_DARK)
        w = self.window_width
        
        card = pygame.Rect(w//2 - 250, 110, 500, 480)
        
        sh_surf = pygame.Surface((500, 480), pygame.SRCALPHA)
        pygame.draw.rect(sh_surf, (15, 23, 42, 25), (0, 0, 500, 480), border_radius=16)
        self.screen.blit(sh_surf, (card.x, card.y + 4))

        pygame.draw.rect(self.screen, COLOR_BG_CARD, card, border_radius=16)
        pygame.draw.rect(self.screen, COLOR_BORDER, card, width=2, border_radius=16)
        
        f1 = pygame.font.SysFont('Segoe UI', 24, bold=True)
        f2 = pygame.font.SysFont('Segoe UI', 15)
        f_lbl = pygame.font.SysFont('Segoe UI', 15, bold=True)
        
        t1 = f1.render("Héberger une Partie Réseau", True, COLOR_TEXT_MAIN)
        self.screen.blit(t1, (card.x + (card.w - t1.get_width())//2, card.y + 25))
        
        # Server name
        lbl_name = f_lbl.render("Nom de votre Salon / Serveur :", True, COLOR_TEXT_MUTED)
        self.screen.blit(lbl_name, (w//2 - 210, 148))
        self.host_name_input.draw(self.screen, mouse_pos)
        
        # Time control
        lbl_time = f_lbl.render("Cadence de jeu (Horloge) :", True, COLOR_TEXT_MUTED)
        self.screen.blit(lbl_time, (w//2 - 210, 228))
        for btn, t_val in self.host_time_buttons:
            btn.is_active = (self.host_selected_time == t_val)
            btn.draw(self.screen, mouse_pos)
            
        # Status box
        status_box = pygame.Rect(w//2 - 210, 310, 420, 85)
        pygame.draw.rect(self.screen, pygame.Color("#F8FAFC"), status_box, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_BORDER, status_box, width=1, border_radius=8)
        
        t_st1 = f2.render("• Diffusion UDP en direct sur le réseau local (LAN)", True, COLOR_EMERALD)
        t_st2 = f2.render("• En attente de connexion du Joueur 2...", True, COLOR_TEXT_MUTED)
        self.screen.blit(t_st1, (status_box.x + 15, status_box.y + 18))
        self.screen.blit(t_st2, (status_box.x + 15, status_box.y + 46))
        
        for m in self.network.get_messages():
            if m["type"] == "connected":
                self.time_limit = self.host_selected_time
                self.network.send_config(self.time_limit, server_name=self.server_name)
                self.reset_game(chess.WHITE, time_limit=self.time_limit)
                self.state = "PLAY"
                
        btn_cancel = Button((card.x + 125, card.y + 410, 250, 48), "Annuler l'Hébergement", font_size=16)
        btn_cancel.draw(self.screen, mouse_pos)
        
        for event in events:
            res = self.host_name_input.handle_event(event)
            if res in ("CHANGE", "SUBMIT"):
                self.server_name = self.host_name_input.text or "Partie P2P"
                self.network.set_server_name(self.server_name)
                
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_cancel.rect.collidepoint(mouse_pos):
                    self.network.close()
                    self.network = NetworkManager()
                    self.state = "MENU"
                for btn, t_val in self.host_time_buttons:
                    if btn.rect.collidepoint(mouse_pos):
                        self.host_selected_time = t_val

    def draw_lobby_join(self, mouse_pos, events):
        self.screen.fill(COLOR_BG_DARK)
        
        f_title = pygame.font.SysFont('Segoe UI', 28, bold=True)
        f_sub = pygame.font.SysFont('Segoe UI', 16)
        
        t1 = f_title.render("Recherche de Parties en Local", True, COLOR_TEXT_MAIN)
        self.screen.blit(t1, (80, 50))
        t2 = f_sub.render("Les serveurs hébergés sur votre box / réseau WiFi s'affichent ci-dessous :", True, COLOR_TEXT_MUTED)
        self.screen.blit(t2, (80, 90))
        
        y = 140
        buttons = []
        for ip, name in self.network.get_discovered_servers().items():
            btn = Button((80, y, 520, 56), f"Rejoindre : {name}  [{ip}]", 
                         bg_color=COLOR_EMERALD, text_color=pygame.Color("white"), font_size=17)
            btn.draw(self.screen, mouse_pos)
            buttons.append((btn, ip))
            y += 70
            
        if not buttons:
            wait_box = pygame.Rect(80, 140, 520, 100)
            pygame.draw.rect(self.screen, COLOR_BG_CARD, wait_box, border_radius=10)
            pygame.draw.rect(self.screen, COLOR_BORDER, wait_box, width=1, border_radius=10)
            txt = f_sub.render("Écoute du réseau UDP en cours... Aucun hôte détecté pour le moment.", True, COLOR_TEXT_MUTED)
            self.screen.blit(txt, (wait_box.x + 20, wait_box.y + 40))
            
        btn_back = Button((80, self.window_height - 90, 200, 48), "Retour au Menu", font_size=16)
        btn_back.draw(self.screen, mouse_pos)
        
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_back.rect.collidepoint(mouse_pos):
                    self.network.close()
                    self.network = NetworkManager()
                    self.state = "MENU"
                for btn, ip in buttons:
                    if btn.rect.collidepoint(mouse_pos):
                        if self.network.connect_to(ip):
                            self.reset_game(player_color=chess.BLACK, time_limit=0)
                            self.state = "PLAY"

    def draw_play(self, mouse_pos, events):
        self.screen.fill(COLOR_BG_DARK)
        
        # 1. Update Countdown Clock
        if self.time_limit > 0 and not self.game_over and not self.board.is_game_over(claim_draw=True):
            now = time.time()
            if self.last_clock_tick is not None:
                dt = now - self.last_clock_tick
                if self.board.turn == chess.WHITE:
                    self.white_time = max(0.0, self.white_time - dt)
                    if self.white_time <= 0.0:
                        self.trigger_timeout(chess.WHITE)
                else:
                    self.black_time = max(0.0, self.black_time - dt)
                    if self.black_time <= 0.0:
                        self.trigger_timeout(chess.BLACK)
            self.last_clock_tick = now
        else:
            self.last_clock_tick = time.time()

        # 2. Process Network messages
        if self.mode == "p2p":
            for m in self.network.get_messages():
                if m["type"] == "move":
                    self.execute_move(chess.Move.from_uci(m["data"]), animated=True)
                elif m["type"] == "chat":
                    sender = m.get("sender", "Adversaire")
                    text = m.get("text", "")
                    self.chat_messages.append({"sender": sender, "text": text, "is_me": False})
                    if self.active_tab != "chat":
                        self.unread_chat += 1
                elif m["type"] == "config":
                    new_limit = m.get("time_limit", 0)
                    self.time_limit = new_limit
                    self.white_time = float(new_limit)
                    self.black_time = float(new_limit)
                    self.last_clock_tick = time.time()
                elif m["type"] == "timeout":
                    if not self.game_over:
                        loser = m.get("loser", "white")
                        loser_col = chess.WHITE if loser == "white" else chess.BLACK
                        self.game_over = True
                        winner = "Noirs" if loser_col == chess.WHITE else "Blancs"
                        self.sounds.play_gameover()
                        self.active_modal = GameOverModal("TEMPS ÉCOULÉ !", f"Victoire des {winner} au chronomètre",
                                                          center_pos=(self.window_width//2, self.window_height//2))
                elif m["type"] == "rematch":
                    self.reset_game(self.player_color, time_limit=self.time_limit)
                elif m["type"] == "resign":
                    winner = "Blancs" if self.player_color == chess.WHITE else "Noirs"
                    self.game_over = True
                    self.sounds.play_gameover()
                    self.active_modal = GameOverModal("VICTOIRE !", "L'adversaire a abandonné la partie",
                                                      center_pos=(self.window_width//2, self.window_height//2))
                elif m["type"] == "disconnected":
                    self.game_over = True
                    self.sounds.play_gameover()
                    self.active_modal = GameOverModal("Adversaire déconnecté", "L'autre joueur a quitté la partie",
                                                      center_pos=(self.window_width//2, self.window_height//2))
                    
        # 3. Process AI move queue on main thread
        while not self.ai_move_queue.empty():
            ai_move = self.ai_move_queue.get()
            if not self.game_over and not self.board.is_game_over(claim_draw=True):
                self.execute_move(ai_move, animated=True)
                self.compute_ai_threats(ai_move)
            self.waiting_for_ai = False

        is_ai_turn = (self.mode == "ai" and 
                      ((self.player_color == chess.WHITE and self.board.turn == chess.BLACK) or
                       (self.player_color == chess.BLACK and self.board.turn == chess.WHITE)))
                       
        if is_ai_turn and not self.waiting_for_ai and not self.game_over and not self.board.is_game_over(claim_draw=True):
            self.waiting_for_ai = True
            def ai_done(move):
                if move:
                    self.ai_move_queue.put(move)
                else:
                    self.waiting_for_ai = False
            self.ai.get_move_async(self.board, ai_done)

        # 4. Smooth Eval Bar Interpolation
        self.current_eval_ratio += (self.target_eval_ratio - self.current_eval_ratio) * 0.15

        # 5. Draw 3D Board and Pieces
        disp_board = self.get_display_board()
        self.ui.draw_3d_board(flipped=self.flipped)
        
        if not self.is_replaying():
            sel_sq = self.selected_square
            lst_mv = self.last_move
            th_sqs = self.ai_threatened_squares
        else:
            sel_sq = None
            lst_mv = self.board.move_stack[self.replay_index - 1] if self.replay_index > 0 else None
            th_sqs = None

        self.ui.draw_highlights(disp_board, sel_sq, lst_mv, threatened_squares=th_sqs, flipped=self.flipped)

        # Annotations (Cercles sous les pièces)
        self.ui.draw_annotations(self.circles, set(), flipped=self.flipped, draw_circles=True, draw_arrows=False)

        # Pièces d'échecs (avec slow-motion et soulèvement 1.15x)
        self.ui.draw_pieces(disp_board, sel_sq, 
                            dragged_pos=self.dragged_pos if (self.is_dragging and not self.is_replaying()) else None, 
                            flipped=self.flipped)

        # Annotations (Flèches au-dessus des pièces)
        preview = (self.right_drag_start, self.right_drag_hover) if (self.right_drag_start is not None and self.right_drag_hover is not None) else None
        self.ui.draw_annotations(set(), self.arrows, preview_arrow=preview, flipped=self.flipped, draw_circles=False, draw_arrows=True)

        # Bandeau de Replay
        if self.is_replaying():
            banner_w = 270
            banner_h = 24
            banner_x = self.ui.board_x + (self.ui.board_size - banner_w) // 2
            banner_y = self.ui.board_y + self.ui.board_size - 32
            b_surf = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)
            pygame.draw.rect(b_surf, (15, 23, 42, 220), (0, 0, banner_w, banner_h), border_radius=6)
            pygame.draw.rect(b_surf, COLOR_GOLD, (0, 0, banner_w, banner_h), width=1, border_radius=6)
            f_rep = pygame.font.SysFont('Segoe UI', 11, bold=True)
            txt = f_rep.render(f"◀ REPLAY (Coup {self.replay_index}/{len(self.board.move_stack)}) — LECTURE SEULE", True, COLOR_GOLD)
            b_surf.blit(txt, (banner_w//2 - txt.get_width()//2, banner_h//2 - txt.get_height()//2))
            self.screen.blit(b_surf, (banner_x, banner_y))

        # Stockfish Advantage Bar (Eval Bar)
        if self.eval_enabled:
            self.ui.draw_eval_bar(EVAL_BAR_X, self.ui.board_y - BOARD_FRAME, EVAL_BAR_WIDTH, self.ui.full_board_size, 
                                  self.current_eval_ratio, self.current_eval_text, flipped=self.flipped)

        # Top & Bottom Player Cards
        self._draw_player_cards(disp_board)

        # Side Panel
        self.draw_side_panel(mouse_pos)

        # In-Game Input
        if not self.active_modal:
            self.handle_game_input(events, mouse_pos)

    def _draw_player_cards(self, board):
        w_caps, b_caps, w_diff, b_diff = self.compute_material_stats(board)
        
        card_w = self.ui.full_board_size
        top_y = max(6, self.ui.board_y - BOARD_FRAME - 36)
        bot_y = min(self.window_height - 36, self.ui.board_y + self.ui.board_size + BOARD_FRAME + 6)
        
        top_rect = pygame.Rect(self.ui.board_x - BOARD_FRAME, top_y, card_w, 30)
        bot_rect = pygame.Rect(self.ui.board_x - BOARD_FRAME, bot_y, card_w, 30)

        if self.mode == "ai":
            if self.player_color == chess.WHITE:
                w_name, w_rating, w_bot = self.get_player_name(), self.get_player_rating(), False
                b_name, b_rating, b_bot = self.get_opponent_name(), self.get_opponent_rating(), True
            else:
                w_name, w_rating, w_bot = self.get_opponent_name(), self.get_opponent_rating(), True
                b_name, b_rating, b_bot = self.get_player_name(), self.get_player_rating(), False
        elif self.mode == "p2p":
            if self.player_color == chess.WHITE:
                w_name, w_rating, w_bot = self.get_player_name(), self.get_player_rating(), False
                b_name, b_rating, b_bot = self.get_opponent_name(), self.get_opponent_rating(), False
            else:
                w_name, w_rating, w_bot = self.get_opponent_name(), self.get_opponent_rating(), False
                b_name, b_rating, b_bot = self.get_player_name(), self.get_player_rating(), False
        else:
            w_name, w_rating, w_bot = "Joueur 1 (Blancs)", "1500", False
            b_name, b_rating, b_bot = "Joueur 2 (Noirs)", "1500", False

        is_w_active = (board.turn == chess.WHITE and not self.game_over and not board.is_game_over(claim_draw=True) and not self.is_replaying())
        is_b_active = (board.turn == chess.BLACK and not self.game_over and not board.is_game_over(claim_draw=True) and not self.is_replaying())
        w_clk = self.format_clock(self.white_time)
        b_clk = self.format_clock(self.black_time)
        w_warn = (self.time_limit > 0 and self.white_time < 30)
        b_warn = (self.time_limit > 0 and self.black_time < 30)

        white_pkg = {
            "name": w_name, "rating": w_rating, "avatar": "bot" if w_bot else "human",
            "active": is_w_active, "clock": w_clk, "warn": w_warn,
            "caps": w_caps, "diff": w_diff, "cap_col": 'b'
        }
        black_pkg = {
            "name": b_name, "rating": b_rating, "avatar": "bot" if b_bot else "human",
            "active": is_b_active, "clock": b_clk, "warn": b_warn,
            "caps": b_caps, "diff": b_diff, "cap_col": 'w'
        }

        if not self.flipped:
            top_pkg = black_pkg
            bot_pkg = white_pkg
        else:
            top_pkg = white_pkg
            bot_pkg = black_pkg

        self.ui.draw_player_card(top_rect, top_pkg["name"], top_pkg["rating"],
                                 avatar_type=top_pkg["avatar"], is_active_turn=top_pkg["active"],
                                 clock_str=top_pkg["clock"], clock_warn=top_pkg["warn"],
                                 captured_pieces=top_pkg["caps"], material_diff=top_pkg["diff"],
                                 is_top=True, captures_color=top_pkg["cap_col"])

        self.ui.draw_player_card(bot_rect, bot_pkg["name"], bot_pkg["rating"],
                                 avatar_type=bot_pkg["avatar"], is_active_turn=bot_pkg["active"],
                                 clock_str=bot_pkg["clock"], clock_warn=bot_pkg["warn"],
                                 captured_pieces=bot_pkg["caps"], material_diff=bot_pkg["diff"],
                                 is_top=False, captures_color=bot_pkg["cap_col"])

    def draw_side_panel(self, mouse_pos):
        panel_h = self.ui.full_board_size
        p_x = self.ui.panel_x
        p_y = self.ui.board_y - BOARD_FRAME
        p_w = self.ui.panel_width
        panel_rect = pygame.Rect(p_x, p_y, p_w, panel_h)
        
        # Ombre portée de la carte panneau
        sh_surf = pygame.Surface((p_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(sh_surf, (15, 23, 42, 25), (0, 0, p_w, panel_h), border_radius=14)
        self.screen.blit(sh_surf, (p_x, p_y + 4))

        # Panneau blanc Material 3
        pygame.draw.rect(self.screen, COLOR_BG_CARD, panel_rect, border_radius=14)
        pygame.draw.rect(self.screen, COLOR_BORDER, panel_rect, width=2, border_radius=14)
        
        f_head = pygame.font.SysFont('Segoe UI', 16, bold=True)
        
        mode_str = "IA Solo" if self.mode == "ai" else ("Réseau P2P" if self.mode == "p2p" else "2J Local")
        lbl_mode = f_head.render(mode_str, True, COLOR_TEXT_MAIN)
        self.screen.blit(lbl_mode, (p_x + 15, panel_rect.y + 10))

        if self.board.is_check():
            chk_txt = f_head.render("⚠ ÉCHEC !", True, pygame.Color(239, 68, 68))
            self.screen.blit(chk_txt, (p_x + p_w - chk_txt.get_width() - 15, panel_rect.y + 10))

        # Quick Toolbar
        self.btn_mute.is_active = self.sounds.muted
        self.btn_flip.is_active = self.flipped
        self.btn_eval_toggle.is_active = self.eval_enabled
        self.btn_theme.draw(self.screen, mouse_pos)
        self.btn_mute.draw(self.screen, mouse_pos)
        self.btn_flip.draw(self.screen, mouse_pos)
        self.btn_eval_toggle.draw(self.screen, mouse_pos)

        # Dynamic Status
        self._draw_status_indicator()

        # Tabs
        self.tab_btn_history.is_active = (self.active_tab == "history")
        chat_label = "Chat" if self.unread_chat == 0 else f"Chat ({self.unread_chat})"
        self.tab_btn_chat.text = chat_label
        self.tab_btn_chat.is_active = (self.active_tab == "chat")
        
        self.tab_btn_history.draw(self.screen, mouse_pos)
        self.tab_btn_chat.draw(self.screen, mouse_pos)

        # Tab Content
        if self.active_tab == "history":
            self._draw_history_tab(mouse_pos)
        else:
            self._draw_chat_tab(mouse_pos)

        # Bottom Buttons
        self.btn_resign.draw(self.screen, mouse_pos)
        self.btn_back.draw(self.screen, mouse_pos)

    def _draw_status_indicator(self):
        p_x = self.ui.panel_x
        p_y = self.ui.board_y - BOARD_FRAME
        p_w = self.ui.panel_width
        indicator_rect = pygame.Rect(p_x + 15, p_y + 68, p_w - 30, 24)
        now_ticks = pygame.time.get_ticks()
        f_ind = pygame.font.SysFont('Segoe UI', 12, bold=True)
        
        if self.mode == "ai" and self.waiting_for_ai:
            pulse = (math.sin(now_ticks / 180.0) + 1.0) / 2.0
            glow_col = (int(79 + pulse * 40), int(70 + pulse * 40), int(229 + pulse * 26))
            pygame.draw.rect(self.screen, pygame.Color("#EEF2FF"), indicator_rect, border_radius=6)
            pygame.draw.rect(self.screen, glow_col, indicator_rect, width=1, border_radius=6)
            
            dot_rad = int(3 + pulse * 2)
            pygame.draw.circle(self.screen, glow_col, (indicator_rect.x + 13, indicator_rect.centery), dot_rad)
            dot_count = (now_ticks // 350) % 4
            txt = f_ind.render(f"Stockfish réfléchit{'.' * dot_count}", True, COLOR_INDIGO)
            self.screen.blit(txt, (indicator_rect.x + 24, indicator_rect.centery - txt.get_height() // 2))
        elif self.mode == "ai":
            pygame.draw.rect(self.screen, pygame.Color("#F8FAFC"), indicator_rect, border_radius=6)
            pygame.draw.rect(self.screen, COLOR_BORDER, indicator_rect, width=1, border_radius=6)
            is_my_turn = (self.board.turn == self.player_color)
            if is_my_turn and not self.game_over:
                pygame.draw.circle(self.screen, COLOR_EMERALD, (indicator_rect.x + 13, indicator_rect.centery), 4)
                txt = f_ind.render("À votre tour de jouer", True, COLOR_EMERALD_DARK)
            else:
                pygame.draw.circle(self.screen, COLOR_GOLD, (indicator_rect.x + 13, indicator_rect.centery), 4)
                txt = f_ind.render("Prêt", True, COLOR_TEXT_MUTED)
            self.screen.blit(txt, (indicator_rect.x + 24, indicator_rect.centery - txt.get_height() // 2))
        elif self.mode == "p2p":
            pygame.draw.rect(self.screen, pygame.Color("#F8FAFC"), indicator_rect, border_radius=6)
            pygame.draw.rect(self.screen, COLOR_BORDER, indicator_rect, width=1, border_radius=6)
            is_my_turn = (self.board.turn == self.player_color)
            if is_my_turn and not self.game_over:
                pygame.draw.circle(self.screen, COLOR_EMERALD, (indicator_rect.x + 13, indicator_rect.centery), 4)
                txt = f_ind.render("À votre tour de jouer", True, COLOR_EMERALD_DARK)
            else:
                pulse = (math.sin(now_ticks / 250.0) + 1.0) / 2.0
                p_col = (int(100 + pulse * 40), int(116 + pulse * 40), int(139 + pulse * 40))
                pygame.draw.circle(self.screen, p_col, (indicator_rect.x + 13, indicator_rect.centery), 4)
                dot_count = (now_ticks // 400) % 4
                txt = f_ind.render(f"En attente de l'adversaire{'.' * dot_count}", True, COLOR_TEXT_MUTED)
            self.screen.blit(txt, (indicator_rect.x + 24, indicator_rect.centery - txt.get_height() // 2))
        else:  # local
            pygame.draw.rect(self.screen, pygame.Color("#F8FAFC"), indicator_rect, border_radius=6)
            pygame.draw.rect(self.screen, COLOR_BORDER, indicator_rect, width=1, border_radius=6)
            t_col = (30, 41, 59) if self.board.turn == chess.WHITE else (100, 116, 139)
            pygame.draw.circle(self.screen, t_col, (indicator_rect.x + 13, indicator_rect.centery), 4)
            who = "Trait aux Blancs" if self.board.turn == chess.WHITE else "Trait aux Noirs"
            txt = f_ind.render(who, True, COLOR_TEXT_MAIN)
            self.screen.blit(txt, (indicator_rect.x + 24, indicator_rect.centery - txt.get_height() // 2))

    def _draw_history_tab(self, mouse_pos):
        p_x = self.ui.panel_x
        p_y = self.ui.board_y - BOARD_FRAME
        p_w = self.ui.panel_width
        
        container_h = max(200, self.ui.full_board_size - 280)
        container = pygame.Rect(p_x + 15, p_y + 134, p_w - 30, container_h)
        pygame.draw.rect(self.screen, pygame.Color("#F8FAFC"), container, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_BORDER, container, width=1, border_radius=8)
        
        # Header
        f_hdr = pygame.font.SysFont('Segoe UI', 13, bold=True)
        f_row = pygame.font.SysFont('Segoe UI', 13)
        
        h_no = f_hdr.render("#", True, COLOR_GOLD_HOVER)
        h_w = f_hdr.render("Blancs", True, COLOR_TEXT_MUTED)
        h_b = f_hdr.render("Noirs", True, COLOR_TEXT_MUTED)
        
        self.screen.blit(h_no, (container.x + 12, container.y + 8))
        self.screen.blit(h_w, (container.x + 55, container.y + 8))
        self.screen.blit(h_b, (container.x + 160, container.y + 8))
        pygame.draw.line(self.screen, COLOR_BORDER, (container.x + 8, container.y + 28), 
                         (container.x + container.w - 8, container.y + 28), 1)
        
        visible_rows = max(5, (container_h - 36) // 24)
        max_scroll = max(0, len(self.move_history) - visible_rows)
        start_idx = max(0, min(max_scroll, self.history_scroll))
        end_idx = min(len(self.move_history), start_idx + visible_rows)
        
        y = container.y + 34
        for i in range(start_idx, end_idx):
            entry = self.move_history[i]
            if (i % 2) == 0:
                pygame.draw.rect(self.screen, pygame.Color("#F1F5F9"), 
                                 (container.x + 4, y - 2, container.w - 8, 22), border_radius=4)
            
            white_half_idx = i * 2 + 1
            black_half_idx = i * 2 + 2
            
            if self.is_replaying() and self.replay_index == white_half_idx:
                pygame.draw.rect(self.screen, pygame.Color(254, 243, 199),
                                 (container.x + 50, y - 2, 85, 22), border_radius=4)
                pygame.draw.rect(self.screen, COLOR_GOLD,
                                 (container.x + 50, y - 2, 85, 22), width=1, border_radius=4)
            elif self.is_replaying() and self.replay_index == black_half_idx:
                pygame.draw.rect(self.screen, pygame.Color(254, 243, 199),
                                 (container.x + 155, y - 2, 85, 22), border_radius=4)
                pygame.draw.rect(self.screen, COLOR_GOLD,
                                 (container.x + 155, y - 2, 85, 22), width=1, border_radius=4)

            t_num = f_row.render(f"{entry['num']}.", True, COLOR_GOLD_HOVER)
            t_w = f_row.render(entry["white"], True, COLOR_TEXT_MAIN)
            t_b = f_row.render(entry["black"], True, COLOR_TEXT_MAIN)
            
            self.screen.blit(t_num, (container.x + 10, y))
            self.screen.blit(t_w, (container.x + 55, y))
            self.screen.blit(t_b, (container.x + 160, y))
            y += 24

        # Replay Navigation Buttons Bar
        self.btn_replay_first.draw(self.screen, mouse_pos)
        self.btn_replay_prev.draw(self.screen, mouse_pos)
        self.btn_replay_next.draw(self.screen, mouse_pos)
        self.btn_replay_last.draw(self.screen, mouse_pos)
        
        if self.is_replaying():
            self.btn_replay_live.draw(self.screen, mouse_pos)

    def _draw_chat_tab(self, mouse_pos):
        p_x = self.ui.panel_x
        p_y = self.ui.board_y - BOARD_FRAME
        p_w = self.ui.panel_width
        
        container_h = max(200, self.ui.full_board_size - 280)
        container = pygame.Rect(p_x + 15, p_y + 134, p_w - 30, container_h)
        pygame.draw.rect(self.screen, pygame.Color("#F8FAFC"), container, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_BORDER, container, width=1, border_radius=8)
        
        f_sender = pygame.font.SysFont('Segoe UI', 11, bold=True)
        f_msg = pygame.font.SysFont('Segoe UI', 13)
        
        chat_lines = []
        max_px_width = container.w - 24
        for msg in self.chat_messages:
            words = msg["text"].split(' ')
            lines = []
            cur_line = ""
            for w in words:
                test_line = (cur_line + " " + w).strip()
                if f_msg.size(test_line)[0] <= max_px_width:
                    cur_line = test_line
                else:
                    if cur_line:
                        lines.append(cur_line)
                    cur_line = w
            if cur_line:
                lines.append(cur_line)
            if not lines:
                lines = [""]
            for idx, ln in enumerate(lines):
                sender_label = f"{msg['sender']}: " if idx == 0 else "   "
                chat_lines.append((sender_label, ln, msg.get("is_me", False), idx == 0))

        visible_lines = max(4, (container_h - 20) // 26)
        total_lines = len(chat_lines)
        max_scroll = max(0, total_lines - visible_lines)
        start = max(0, total_lines - visible_lines - self.chat_scroll)
        end = min(total_lines, start + visible_lines)
        
        y = container.y + 10
        for i in range(start, end):
            sender_str, text_str, is_me, is_first = chat_lines[i]
            sender_col = COLOR_EMERALD if is_me else COLOR_INDIGO
            s_surf = f_sender.render(sender_str, True, sender_col)
            m_surf = f_msg.render(text_str, True, COLOR_TEXT_MAIN)
            
            self.screen.blit(s_surf, (container.x + 10, y))
            self.screen.blit(m_surf, (container.x + 10 + s_surf.get_width(), y - 1))
            y += 26
            
        if not self.chat_messages:
            f_empty = pygame.font.SysFont('Segoe UI', 13)
            e_surf = f_empty.render("Aucun message", True, COLOR_TEXT_MUTED)
            self.screen.blit(e_surf, (container.x + 20, container.y + 30))

        if total_lines > visible_lines:
            f_sc = pygame.font.SysFont('Segoe UI', 11)
            sc_info = f_sc.render(f"▲▼ {start+1}-{end}/{total_lines}", True, COLOR_TEXT_MUTED)
            self.screen.blit(sc_info, (container.x + container.w - sc_info.get_width() - 8, container.y + container.h - 18))
            
        self.chat_input.draw(self.screen, mouse_pos)

    def send_chat_message(self):
        text = self.chat_input.text.strip()
        if not text:
            return
        sender = "Moi"
        if self.mode == "p2p":
            sender = self.server_name if self.network.is_host else "Client"
            self.network.send_chat(sender, text)
            
        self.chat_messages.append({"sender": "Moi", "text": text, "is_me": True})
        self.chat_input.text = ""
        self.chat_scroll = 0
        
        if self.mode == "ai":
            responses = ["Bonne partie !", "Bien joué !", "Concentration...", "Joli coup !", "À vous de jouer !"]
            self.chat_messages.append({"sender": "Stockfish", "text": random.choice(responses), "is_me": False})

    def handle_game_input(self, events, mouse_pos):
        can_move = True
        if self.game_over:
            can_move = False
        if self.is_replaying():
            can_move = False
        if self.mode == "p2p" and self.board.turn != self.player_color:
            can_move = False
        if self.mode == "ai" and self.board.turn != self.player_color:
            can_move = False

        for event in events:
            if self.active_tab == "chat":
                res = self.chat_input.handle_event(event)
                if res == "SUBMIT":
                    self.send_chat_message()

            if event.type == pygame.MOUSEWHEEL:
                if self.active_tab == "history":
                    max_scroll = max(0, len(self.move_history) - 11)
                    self.history_scroll = max(0, min(max_scroll, self.history_scroll - event.y))
                elif self.active_tab == "chat":
                    self.chat_scroll = max(0, self.chat_scroll + event.y)

            elif event.type == pygame.KEYDOWN:
                if not self.chat_input.is_active:
                    if event.key == pygame.K_f:
                        self.flipped = not self.flipped
                    elif event.key == pygame.K_m:
                        self.sounds.toggle_mute()
                        self.btn_mute.text = "🔇 Muet" if self.sounds.muted else "🔊 Son"
                    elif event.key == pygame.K_LEFT:
                        self.step_replay(-1)
                    elif event.key == pygame.K_RIGHT:
                        self.step_replay(1)
                    elif event.key == pygame.K_HOME:
                        self.replay_index = 0
                        self.request_eval()
                    elif event.key == pygame.K_END:
                        self.replay_index = len(self.board.move_stack)
                        self.request_eval()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                sq = self.ui.screen_to_square(mouse_pos[0], mouse_pos[1], flipped=self.flipped)
                if sq is not None:
                    self.right_drag_start = sq
                    self.right_drag_hover = sq

            elif event.type == pygame.MOUSEMOTION:
                if self.right_drag_start is not None:
                    sq = self.ui.screen_to_square(mouse_pos[0], mouse_pos[1], flipped=self.flipped)
                    self.right_drag_hover = sq
                if self.selected_square is not None and self.drag_start_pos is not None:
                    dx = mouse_pos[0] - self.drag_start_pos[0]
                    dy = mouse_pos[1] - self.drag_start_pos[1]
                    if abs(dx) > 6 or abs(dy) > 6:
                        self.is_dragging = True
                        self.dragged_pos = mouse_pos

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
                if self.right_drag_start is not None:
                    end_sq = self.ui.screen_to_square(mouse_pos[0], mouse_pos[1], flipped=self.flipped)
                    if end_sq is not None:
                        if end_sq == self.right_drag_start:
                            if end_sq in self.circles:
                                self.circles.remove(end_sq)
                            else:
                                self.circles.add(end_sq)
                        else:
                            arrow_tuple = (self.right_drag_start, end_sq)
                            if arrow_tuple in self.arrows:
                                self.arrows.remove(arrow_tuple)
                            else:
                                self.arrows.add(arrow_tuple)
                self.right_drag_start = None
                self.right_drag_hover = None

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.arrows or self.circles:
                    self.arrows.clear()
                    self.circles.clear()

                if self.btn_theme.rect.collidepoint(mouse_pos):
                    self.cycle_theme()
                    return
                elif self.btn_mute.rect.collidepoint(mouse_pos):
                    self.sounds.toggle_mute()
                    self.btn_mute.text = "🔇 Muet" if self.sounds.muted else "🔊 Son"
                    return
                elif self.btn_flip.rect.collidepoint(mouse_pos):
                    self.flipped = not self.flipped
                    return
                elif self.btn_eval_toggle.rect.collidepoint(mouse_pos):
                    self.eval_enabled = not self.eval_enabled
                    if self.eval_enabled:
                        self.request_eval()
                    return

                if self.active_tab == "history":
                    if self.btn_replay_first.rect.collidepoint(mouse_pos):
                        self.replay_index = 0
                        self.request_eval()
                        return
                    elif self.btn_replay_prev.rect.collidepoint(mouse_pos):
                        self.step_replay(-1)
                        return
                    elif self.btn_replay_next.rect.collidepoint(mouse_pos):
                        self.step_replay(1)
                        return
                    elif self.btn_replay_last.rect.collidepoint(mouse_pos):
                        self.replay_index = len(self.board.move_stack)
                        self.request_eval()
                        return
                    elif self.is_replaying() and self.btn_replay_live.rect.collidepoint(mouse_pos):
                        self.replay_index = len(self.board.move_stack)
                        self.request_eval()
                        return
                    
                    table_x = self.ui.panel_x + 15
                    table_y = self.ui.board_y - BOARD_FRAME + 134 + 34
                    table_w = self.ui.panel_width - 30
                    if table_x <= mouse_pos[0] <= table_x + table_w and table_y <= mouse_pos[1] <= table_y + 11 * 24:
                        rel_y = mouse_pos[1] - table_y
                        max_scroll = max(0, len(self.move_history) - 11)
                        start_idx = max(0, min(max_scroll, self.history_scroll))
                        row_clicked = start_idx + (rel_y // 24)
                        if 0 <= row_clicked < len(self.move_history):
                            rel_x = mouse_pos[0] - table_x
                            if 50 <= rel_x < 150:
                                self.replay_index = row_clicked * 2 + 1
                                self.request_eval()
                                return
                            elif 150 <= rel_x < 260 and self.move_history[row_clicked].get("black"):
                                self.replay_index = row_clicked * 2 + 2
                                self.request_eval()
                                return

                if self.tab_btn_history.rect.collidepoint(mouse_pos):
                    self.active_tab = "history"
                    return
                elif self.tab_btn_chat.rect.collidepoint(mouse_pos):
                    self.active_tab = "chat"
                    self.unread_chat = 0
                    self.chat_input.is_active = True
                    return

                if self.btn_resign.rect.collidepoint(mouse_pos) and not self.game_over:
                    winner = "Noirs" if self.player_color == chess.WHITE else "Blancs"
                    if self.mode == "p2p":
                        self.network.send_resign()
                    self.game_over = True
                    self.sounds.play_gameover()
                    self.active_modal = GameOverModal("ABANDON", f"Victoire des {winner}",
                                                      center_pos=(self.window_width//2, self.window_height//2))
                    return
                elif self.btn_back.rect.collidepoint(mouse_pos):
                    if self.mode == "p2p":
                        self.network.close()
                        self.network = NetworkManager()
                    self.state = "MENU"
                    return

                if not self.is_replaying():
                    sq = self.ui.screen_to_square(mouse_pos[0], mouse_pos[1], flipped=self.flipped)
                    if sq is not None and can_move:
                        piece = self.board.piece_at(sq)
                        if self.selected_square is None:
                            if piece and piece.color == self.board.turn:
                                self.selected_square = sq
                                self.drag_start_pos = mouse_pos
                                self.is_dragging = False
                                self.dragged_pos = None
                        else:
                            if not self.try_execute_player_move(self.selected_square, sq, animated=True):
                                if piece and piece.color == self.board.turn:
                                    self.selected_square = sq
                                    self.drag_start_pos = mouse_pos
                                    self.is_dragging = False
                                    self.dragged_pos = None
                                else:
                                    self.selected_square = None
                                    self.is_dragging = False
                                    self.dragged_pos = None
                                    self.drag_start_pos = None

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if not self.is_replaying() and self.is_dragging and self.selected_square is not None and can_move:
                    target_sq = self.ui.screen_to_square(mouse_pos[0], mouse_pos[1], flipped=self.flipped)
                    if target_sq is not None and target_sq != self.selected_square:
                        self.try_execute_player_move(self.selected_square, target_sq, animated=False)
                self.is_dragging = False
                self.dragged_pos = None
                self.drag_start_pos = None

    def try_execute_player_move(self, from_sq, to_sq, animated=True):
        piece = self.board.piece_at(from_sq)
        if not piece:
            return False

        if piece.piece_type == chess.PAWN:
            to_rank = chess.square_rank(to_sq)
            if (piece.color == chess.WHITE and to_rank == 7) or (piece.color == chess.BLACK and to_rank == 0):
                test_move = chess.Move(from_sq, to_sq, promotion=chess.QUEEN)
                if test_move in self.board.legal_moves:
                    self.pending_promotion = (from_sq, to_sq)
                    self.active_modal = PromotionModal(piece.color, self.ui.images,
                                                       center_pos=(self.window_width//2, self.window_height//2))
                    self.selected_square = None
                    return True

        move = chess.Move(from_sq, to_sq)
        if self.execute_move(move, animated=animated):
            if self.mode == "p2p":
                self.network.send_move(move.uci())
            return True
        return False

if __name__ == "__main__":
    app = GameApp()
    app.run()
