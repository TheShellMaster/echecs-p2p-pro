"""
animations.py - Moteur cinématique d'animation, easing slow-motion,
ondes de choc (shockwave ripples) et système de particules festives.
"""

import math
import random
import pygame

def ease_out_cubic(t: float) -> float:
    """Décélération progressive cubique ultra-douce."""
    t = max(0.0, min(1.0, float(t)))
    return 1.0 - (1.0 - t) ** 3

def ease_out_back(t: float, overshoot: float = 1.35) -> float:
    """Rebond élastique avec léger dépassement (spring bounce settle)."""
    t = max(0.0, min(1.0, float(t)))
    c1 = overshoot
    c3 = c1 + 1.0
    return 1.0 + c3 * ((t - 1.0) ** 3) + c1 * ((t - 1.0) ** 2)

def ease_out_quad(t: float) -> float:
    t = max(0.0, min(1.0, float(t)))
    return 1.0 - (1.0 - t) * (1.0 - t)

def spring_settle(t: float, damping: float = 12.0, freq: float = 18.0) -> float:
    """Oscillation amortie pour atterrissage réaliste."""
    if t >= 1.0:
        return 1.0
    if t <= 0.0:
        return 0.0
    return 1.0 - math.exp(-damping * t) * math.cos(freq * t)

class PieceCinematicAnimation:
    """
    Gère le déplacement cinématique ralenti (slow-motion 280ms)
    avec soulèvement vertical, grossissement 1.15x et atterrissage spring bounce.
    """
    def __init__(self, from_sq, to_sq, piece_key, start_time, duration_ms=280, 
                 secondary=None, captured=None, is_capture=False, is_check=False):
        self.from_sq = from_sq
        self.to_sq = to_sq
        self.piece_key = piece_key
        self.start_time = start_time
        self.duration_ms = max(50, duration_ms)
        self.secondary = secondary    # (from_sq, to_sq, piece_key) pour le roque
        self.captured = captured      # (square, piece_key) pour pièce prise
        self.is_capture = is_capture
        self.is_check = is_check

    def raw_t(self, current_time: int) -> float:
        elapsed = current_time - self.start_time
        return max(0.0, min(1.0, elapsed / float(self.duration_ms)))

    def is_finished(self, current_time: int) -> bool:
        return (current_time - self.start_time) >= self.duration_ms

    def progress(self, current_time: int) -> float:
        """Position interpolée avec spring bounce en fin de course."""
        t = self.raw_t(current_time)
        # 0.0 à 0.82 : glissement cubic doux ; 0.82 à 1.0 : atterrissage spring bounce
        if t < 0.82:
            norm = t / 0.82
            return ease_out_cubic(norm) * 0.96
        else:
            settle_t = (t - 0.82) / 0.18
            return 0.96 + (0.04 * ease_out_back(settle_t, overshoot=1.2))

    def lift_height(self, current_time: int) -> float:
        """Soulèvement vertical z-axis (effet arc parabolique)."""
        t = self.raw_t(current_time)
        # Arc parabolique maximal au milieu du vol : -12 pixels
        return -14.0 * math.sin(t * math.pi)

    def scale_factor(self, current_time: int) -> float:
        """Agrandissement dynamique de la pièce en plein vol (jusqu'à 1.15x)."""
        t = self.raw_t(current_time)
        return 1.0 + 0.15 * math.sin(t * math.pi)

class RippleEffect:
    """
    Onde de choc circulaire translucide s'étendant à partir d'une case
    lors d'une capture, d'un coup tactique ou d'un échec au roi.
    """
    def __init__(self, center_pos, color=(16, 185, 129), max_radius=65, duration_ms=450):
        self.center_x, self.center_y = center_pos
        self.color = color
        self.max_radius = max_radius
        self.duration_ms = max(50, duration_ms)
        self.start_time = pygame.time.get_ticks()

    def is_finished(self, current_time: int) -> bool:
        return (current_time - self.start_time) >= self.duration_ms

    def draw(self, surface: pygame.Surface, current_time: int):
        elapsed = current_time - self.start_time
        t = max(0.0, min(1.0, elapsed / float(self.duration_ms)))
        if t >= 1.0:
            return

        # Anneau 1
        ease_r = ease_out_cubic(t)
        radius1 = max(4, int(self.max_radius * ease_r))
        alpha1 = int(220 * (1.0 - t))

        # Surface transparente dédiée
        diam = int(self.max_radius * 2 + 10)
        s = pygame.Surface((diam, diam), pygame.SRCALPHA)
        center = (diam // 2, diam // 2)

        r_col1 = (self.color[0], self.color[1], self.color[2], alpha1)
        width1 = max(1, int(4 * (1.0 - t * 0.7)))
        pygame.draw.circle(s, r_col1, center, radius1, width=width1)

        # Anneau 2 avec léger retard
        if t > 0.15:
            t2 = (t - 0.15) / 0.85
            radius2 = max(2, int((self.max_radius * 0.7) * ease_out_cubic(t2)))
            alpha2 = int(160 * (1.0 - t2))
            r_col2 = (self.color[0], self.color[1], self.color[2], alpha2)
            pygame.draw.circle(s, r_col2, center, radius2, width=2)

        # Lueur de centre douce
        if t < 0.4:
            c_alpha = int(90 * (1.0 - t / 0.4))
            pygame.draw.circle(s, (self.color[0], self.color[1], self.color[2], c_alpha), center, int(radius1 * 0.4))

        surface.blit(s, (self.center_x - diam // 2, self.center_y - diam // 2))

class ConfettiParticle:
    """Particule individuelle pour célébration de victoire."""
    def __init__(self, x, y, width_bounds):
        self.x = x
        self.y = y
        self.vx = random.uniform(-2.5, 2.5)
        self.vy = random.uniform(-6.0, -1.0)  # Impulsion initiale vers le haut
        self.gravity = random.uniform(5.5, 8.5)
        self.width_bounds = width_bounds
        
        # Forme & dimensions
        self.size = random.uniform(6, 12)
        self.shape = random.choice(['rect', 'circle', 'star'])
        self.angle = random.uniform(0, 360)
        self.rot_speed = random.uniform(-280, 280)
        self.wobble_phase = random.uniform(0, math.pi * 2)
        self.wobble_speed = random.uniform(3.0, 6.0)

        # Palette vibrante Material 3
        palette = [
            (16, 185, 129),   # Émeraude
            (245, 158, 11),   # Or / Ambre
            (79, 70, 229),    # Indigo
            (236, 72, 153),   # Rose fuchsia
            (6, 182, 212),    # Cyan
            (250, 204, 21),   # Jaune éclatant
            (255, 255, 255),  # Blanc pur
        ]
        self.color = random.choice(palette)
        self.alpha = 255
        self.lifetime = random.uniform(3.0, 5.0)
        self.age = 0.0

    def update(self, dt: float) -> bool:
        self.age += dt
        if self.age >= self.lifetime:
            return False

        # Physique : gravité + oscillation d'air horizontale
        self.vy += self.gravity * dt
        self.wobble_phase += self.wobble_speed * dt
        air_drift = math.sin(self.wobble_phase) * 1.5

        self.x += (self.vx + air_drift) * 60.0 * dt
        self.y += self.vy * 60.0 * dt
        self.angle += self.rot_speed * dt

        # Fading vers la fin de vie
        remaining = self.lifetime - self.age
        if remaining < 1.0:
            self.alpha = max(0, int(255 * (remaining / 1.0)))

        return True

    def draw(self, surface: pygame.Surface):
        if self.alpha <= 0:
            return

        rad = int(self.size)
        s_size = rad * 2 + 4
        s = pygame.Surface((s_size, s_size), pygame.SRCALPHA)
        center = (s_size // 2, s_size // 2)

        col = (self.color[0], self.color[1], self.color[2], self.alpha)

        if self.shape == 'circle':
            pygame.draw.circle(s, col, center, rad // 2)
        elif self.shape == 'star':
            # Étoile à 4 branches
            arm = rad // 2
            pygame.draw.line(s, col, (center[0] - arm, center[1]), (center[0] + arm, center[1]), width=2)
            pygame.draw.line(s, col, (center[0], center[1] - arm), (center[0], center[1] + arm), width=2)
        else: # rect / ribbon
            rw = max(3, int(self.size))
            rh = max(2, int(self.size * 0.5))
            rect_surf = pygame.Surface((rw, rh), pygame.SRCALPHA)
            rect_surf.fill(col)
            rotated = pygame.transform.rotate(rect_surf, self.angle)
            r_center = rotated.get_rect(center=(self.x, self.y))
            surface.blit(rotated, r_center)
            return

        surface.blit(s, (self.x - s_size // 2, self.y - s_size // 2))

class ConfettiParticleSystem:
    """Gestionnaire de pluie de confettis pour célébrer un mat."""
    def __init__(self):
        self.particles = []
        self.is_active = False

    def trigger(self, screen_width: int, screen_height: int, count: int = 140):
        self.is_active = True
        self.particles.clear()
        for _ in range(count):
            spawn_x = random.uniform(20, screen_width - 20)
            spawn_y = random.uniform(-40, screen_height * 0.4)
            p = ConfettiParticle(spawn_x, spawn_y, screen_width)
            self.particles.append(p)

    def stop(self):
        self.is_active = False
        self.particles.clear()

    def update(self, dt: float):
        if not self.particles:
            self.is_active = False
            return
        self.particles = [p for p in self.particles if p.update(dt)]
        if not self.particles:
            self.is_active = False

    def draw(self, surface: pygame.Surface):
        if not self.particles:
            return
        for p in self.particles:
            p.draw(surface)


class ModalTransition:
    """
    Gère la transition d'ouverture fluide d'un dialogue modal (~220ms).
    Fournit l'échelle dynamique avec rebond élastique (ease_out_back),
    l'assombrissement progressif du voile (ease_out_cubic),
    et l'opacité du contenu.
    """
    def __init__(self, start_time: int | None = None, duration_ms: int = 220):
        self.start_time = pygame.time.get_ticks() if start_time is None else start_time
        self.duration_ms = max(1, duration_ms)

    def progress(self, current_time: int | None = None) -> float:
        now = pygame.time.get_ticks() if current_time is None else current_time
        elapsed = now - self.start_time
        return max(0.0, min(1.0, elapsed / float(self.duration_ms)))

    def is_finished(self, current_time: int | None = None) -> bool:
        now = pygame.time.get_ticks() if current_time is None else current_time
        return (now - self.start_time) >= self.duration_ms

    def get_scale(self, current_time: int | None = None) -> float:
        """
        Interpole l'échelle d'ouverture de 0.90 à 1.0 via ease_out_back(progress, overshoot=1.12).
        """
        p = self.progress(current_time)
        return 0.90 + 0.10 * ease_out_back(p, overshoot=1.12)

    def get_dim_alpha(self, current_time: int | None = None) -> int:
        """
        Interpole l'opacité d'assombrissement du voile d'arrière-plan de 0 à 130 via ease_out_cubic(progress).
        """
        p = self.progress(current_time)
        return int(130 * ease_out_cubic(p))

    def get_content_alpha(self, current_time: int | None = None) -> int:
        """
        Interpole l'opacité du contenu modal de 0 à 255 via ease_out_cubic(progress).
        """
        p = self.progress(current_time)
        return int(255 * ease_out_cubic(p))
