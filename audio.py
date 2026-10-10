import os
import math
import wave
import struct
import random
import pygame
from constants import resource_path

SOUND_FILES = ["move.wav", "capture.wav", "check.wav", "gameover.wav"]

def _generate_wav(filepath, duration, sample_rate, sample_func):
    n_samples = int(duration * sample_rate)
    raw = [sample_func(i / sample_rate, duration) for i in range(n_samples)]
    peak = max((abs(x) for x in raw), default=1.0)
    norm_factor = 0.85 / max(peak, 0.85)
    samples = [int(max(-1.0, min(1.0, x * norm_factor)) * 32767) for x in raw]
        
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with wave.open(filepath, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        data = struct.pack('<' + 'h' * len(samples), *samples)
        wf.writeframes(data)

def _move_synth(t, dur):
    att = min(1.0, t / 0.003)
    env = att * math.exp(-t * 52)
    # Warm wood tap resonance
    res1 = math.sin(2 * math.pi * 220 * t)
    res2 = 0.45 * math.sin(2 * math.pi * 440 * t)
    res3 = 0.25 * math.sin(2 * math.pi * 110 * t)
    noise = (math.sin(t * 12345.67) % 2 - 1) * math.exp(-t * 160) * 0.35
    return (res1 + res2 + res3 + noise) * env * 0.8

def _capture_synth(t, dur):
    att = min(1.0, t / 0.002)
    env = att * math.exp(-t * 36)
    click = (math.sin(t * 98765.43) % 2 - 1) * math.exp(-t * 130) * 0.55
    c1 = math.sin(2 * math.pi * 380 * t)
    c2 = 0.7 * math.sin(2 * math.pi * 650 * t)
    c3 = 0.35 * math.sin(2 * math.pi * 190 * t)
    return (click + c1 + c2 + c3) * env * 0.55

def _check_synth(t, dur):
    att = min(1.0, t / 0.005)
    env = att * math.exp(-t * 5.5)
    mod = 1.0 + 0.15 * math.sin(2 * math.pi * 6 * t)
    b1 = math.sin(2 * math.pi * 784 * t)
    b2 = 0.5 * math.sin(2 * math.pi * 1046.5 * t)
    b3 = 0.25 * math.sin(2 * math.pi * 1568 * t)
    return (b1 + b2 + b3) * env * mod * 0.5

def _gameover_synth(t, dur):
    att = min(1.0, t / 0.015)
    env = att * math.exp(-t * 3.0)
    # Rich C Major triad + octave finish chord
    ch1 = math.sin(2 * math.pi * 261.63 * t)
    ch2 = 0.8 * math.sin(2 * math.pi * 329.63 * t)
    ch3 = 0.8 * math.sin(2 * math.pi * 392.00 * t)
    ch4 = 0.5 * math.sin(2 * math.pi * 523.25 * t)
    return (ch1 + ch2 + ch3 + ch4) * env * 0.35

def ensure_sound_assets(force=False):
    sounds_dir = resource_path(os.path.join("assets", "sounds"))
    generators = {
        "move.wav": (0.09, _move_synth),
        "capture.wav": (0.13, _capture_synth),
        "check.wav": (0.55, _check_synth),
        "gameover.wav": (1.0, _gameover_synth)
    }
    for filename, (dur, synth) in generators.items():
        filepath = os.path.join(sounds_dir, filename)
        if force or not os.path.exists(filepath):
            _generate_wav(filepath, dur, 44100, synth)

class SoundManager:
    def __init__(self):
        self.enabled = False
        self.muted = False
        self.sounds = {}
        
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.enabled = True
        except Exception as e:
            print(f"Audio mixer initialization failed: {e}")
            self.enabled = False
            return

        ensure_sound_assets()
        self._load_sounds()

    def toggle_mute(self):
        self.muted = not self.muted
        return self.muted

    def _load_sounds(self):
        sounds_dir = resource_path(os.path.join("assets", "sounds"))
        for s in SOUND_FILES:
            path = os.path.join(sounds_dir, s)
            name = os.path.splitext(s)[0]
            if os.path.exists(path):
                try:
                    self.sounds[name] = pygame.mixer.Sound(path)
                except Exception as e:
                    print(f"Failed to load sound {path}: {e}")

    def play(self, name):
        if not self.enabled or self.muted:
            return
        snd = self.sounds.get(name)
        if snd:
            try:
                snd.play()
            except Exception:
                pass

    def play_move(self):
        self.play("move")

    def play_capture(self):
        self.play("capture")

    def play_check(self):
        self.play("check")

    def play_gameover(self):
        self.play("gameover")

    def play_for_move(self, board_after_move, is_capture=False, is_game_over=False):
        if is_game_over:
            self.play_gameover()
        elif board_after_move.is_check():
            self.play_check()
        elif is_capture:
            self.play_capture()
        else:
            self.play_move()
