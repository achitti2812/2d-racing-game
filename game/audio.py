"""No-asset procedural audio with silent fallback support."""

from array import array
import math
import random

import pygame


class AudioManager:
    """Generate short arcade SFX and centralize mixer volume controls."""

    def __init__(self, user_settings, force_silent=False):
        self.user_settings = user_settings
        self.available = False
        self.sounds = {}
        self._random = random.Random(13)

        if force_silent:
            return
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(
                    frequency=22050,
                    size=-16,
                    channels=2,
                    buffer=512,
                )
            mixer_config = pygame.mixer.get_init()
            if mixer_config is None or mixer_config[1] != -16:
                return
            self.sample_rate, _, self.channel_count = mixer_config
            self._build_sounds()
            self.available = True
            self._apply_music_volume()
        except (pygame.error, OSError, ValueError):
            self.available = False
            self.sounds = {}

    def _build_sounds(self):
        self.sounds = {
            "menu_move": self._tone(520, 0.045, 0.13),
            "menu_select": self._sequence(((660, 0.045), (840, 0.07)), 0.16),
            "countdown": self._tone(440, 0.10, 0.18),
            "go": self._sequence(((660, 0.07), (940, 0.15)), 0.20),
            "collision": self._noise(0.16, 0.24),
            "nitro": self._chirp(360, 920, 0.18, 0.18),
            "finish": self._sequence(
                ((660, 0.08), (830, 0.08), (1040, 0.16)), 0.20
            ),
            "unlock": self._sequence(((740, 0.10), (980, 0.16)), 0.18),
        }

    def play_sfx(self, name):
        if not self.available:
            return
        sound = self.sounds.get(name)
        if sound is None:
            return
        sound.set_volume(
            self.user_settings.master_volume
            * self.user_settings.sfx_volume
        )
        sound.play()

    def set_user_settings(self, user_settings):
        self.user_settings = user_settings
        self._apply_music_volume()

    def start_music(self, path, loops=-1):
        """Future asset hook; failures remain non-fatal."""
        if not self.available or not path:
            return
        try:
            pygame.mixer.music.load(str(path))
            self._apply_music_volume()
            pygame.mixer.music.play(loops)
        except (pygame.error, OSError):
            return

    def stop_music(self):
        if self.available:
            try:
                pygame.mixer.music.stop()
            except pygame.error:
                pass

    def _apply_music_volume(self):
        if not self.available:
            return
        pygame.mixer.music.set_volume(
            self.user_settings.master_volume
            * self.user_settings.music_volume
        )

    def _tone(self, frequency, duration, amplitude):
        samples = []
        frame_count = max(1, int(self.sample_rate * duration))
        for frame in range(frame_count):
            elapsed = frame / self.sample_rate
            envelope = self._envelope(frame, frame_count)
            samples.append(
                math.sin(2.0 * math.pi * frequency * elapsed)
                * amplitude
                * envelope
            )
        return self._sound_from_samples(samples)

    def _chirp(self, start_frequency, end_frequency, duration, amplitude):
        samples = []
        frame_count = max(1, int(self.sample_rate * duration))
        phase = 0.0
        for frame in range(frame_count):
            progress = frame / max(1, frame_count - 1)
            frequency = start_frequency + (
                end_frequency - start_frequency
            ) * progress
            phase += 2.0 * math.pi * frequency / self.sample_rate
            samples.append(
                math.sin(phase)
                * amplitude
                * self._envelope(frame, frame_count)
            )
        return self._sound_from_samples(samples)

    def _noise(self, duration, amplitude):
        frame_count = max(1, int(self.sample_rate * duration))
        samples = [
            self._random.uniform(-1.0, 1.0)
            * amplitude
            * self._envelope(frame, frame_count)
            for frame in range(frame_count)
        ]
        return self._sound_from_samples(samples)

    def _sequence(self, notes, amplitude):
        samples = []
        gap_frames = int(self.sample_rate * 0.018)
        for frequency, duration in notes:
            frame_count = max(1, int(self.sample_rate * duration))
            for frame in range(frame_count):
                elapsed = frame / self.sample_rate
                samples.append(
                    math.sin(2.0 * math.pi * frequency * elapsed)
                    * amplitude
                    * self._envelope(frame, frame_count)
                )
            samples.extend([0.0] * gap_frames)
        return self._sound_from_samples(samples)

    def _sound_from_samples(self, samples):
        pcm = array("h")
        for sample in samples:
            value = round(max(-1.0, min(sample, 1.0)) * 32767)
            for _ in range(self.channel_count):
                pcm.append(value)
        return pygame.mixer.Sound(buffer=pcm.tobytes())

    @staticmethod
    def _envelope(frame, frame_count):
        attack = max(1, int(frame_count * 0.08))
        if frame < attack:
            return frame / attack
        return max(0.0, (frame_count - frame) / max(1, frame_count - attack))
