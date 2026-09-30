"""Cached procedural SFX, engine, boost, tire, and crowd audio."""

from array import array
import math
import random

import pygame


ENGINE_FREQUENCIES = (55, 65, 75, 85, 95, 110, 125, 140)


class AudioManager:
    """Centralize non-blocking procedural audio and race-loop lifecycle."""

    def __init__(self, user_settings, force_silent=False):
        self.user_settings = user_settings
        self.available = False
        self.sounds = {}
        self.engine_sounds = []
        self.engine_channels = []
        self.crowd_channel = None
        self.boost_channel = None
        self.tire_channel = None
        self.race_audio_active = False
        self.race_audio_paused = False
        self.current_engine_band = 0
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
            pygame.mixer.set_num_channels(
                max(24, pygame.mixer.get_num_channels())
            )
            self._build_sounds()
            self.available = True
            self._apply_music_volume()
        except (pygame.error, OSError, ValueError):
            self.available = False
            self.sounds = {}
            self.engine_sounds = []

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
            "crowd_start": self._crowd_burst(0.38, 0.15),
            "crowd_cheer": self._crowd_burst(0.72, 0.23),
        }
        self.engine_sounds = [
            self._engine_loop(frequency) for frequency in ENGINE_FREQUENCIES
        ]
        self.crowd_loop = self._crowd_loop()
        self.boost_loop = self._wind_loop()
        self.tire_loop = self._tire_loop()

    def play_sfx(self, name):
        if not self.available:
            return
        sound = self.sounds.get(name)
        if sound is None:
            return
        sound.set_volume(self._sfx_gain())
        sound.play()

    def start_race_audio(self):
        """Start cached loops once; repeated calls cannot duplicate channels."""
        if self.race_audio_active:
            return
        self.race_audio_active = True
        self.race_audio_paused = False
        if not self.available:
            return

        self.engine_channels = []
        for sound in self.engine_sounds:
            channel = pygame.mixer.find_channel(True)
            channel.play(sound, loops=-1)
            channel.set_volume(0.0)
            self.engine_channels.append(channel)
        self.crowd_channel = pygame.mixer.find_channel(True)
        self.crowd_channel.play(self.crowd_loop, loops=-1)
        self.crowd_channel.set_volume(0.0)
        self.boost_channel = pygame.mixer.find_channel(True)
        self.boost_channel.play(self.boost_loop, loops=-1)
        self.boost_channel.set_volume(0.0)
        self.tire_channel = pygame.mixer.find_channel(True)
        self.tire_channel.play(self.tire_loop, loops=-1)
        self.tire_channel.set_volume(0.0)

    def update_race_audio(
        self,
        speed,
        maximum_speed,
        throttle=False,
        nitro_active=False,
        crowd_intensity=0.0,
        tire_intensity=0.0,
    ):
        """Crossfade cached loops without regenerating or restarting them."""
        if not self.race_audio_active or not self.available:
            return
        normalized_speed = max(0.0, min(speed / max(maximum_speed, 1.0), 1.0))
        band_position = normalized_speed * (len(self.engine_sounds) - 1)
        lower_band = int(band_position)
        upper_band = min(lower_band + 1, len(self.engine_sounds) - 1)
        blend = band_position - lower_band
        self.current_engine_band = round(band_position)

        engine_level = 0.17 + normalized_speed * 0.22
        if throttle:
            engine_level += 0.055
        if nitro_active:
            engine_level += 0.035
        engine_level *= self._sfx_gain()

        for index, channel in enumerate(self.engine_channels):
            weight = 0.0
            if index == lower_band:
                weight = math.sqrt(max(0.0, 1.0 - blend))
            if index == upper_band:
                weight = max(weight, math.sqrt(max(0.0, blend)))
            channel.set_volume(engine_level * weight)

        crowd_intensity = max(0.0, min(crowd_intensity, 1.0))
        tire_intensity = max(0.0, min(tire_intensity, 1.0))
        self.crowd_channel.set_volume(
            self._sfx_gain() * (0.035 + crowd_intensity * 0.10)
        )
        self.boost_channel.set_volume(
            self._sfx_gain() * (0.13 if nitro_active else 0.0)
        )
        self.tire_channel.set_volume(
            self._sfx_gain() * tire_intensity * 0.09
        )

    def get_engine_band(self, speed, maximum_speed):
        normalized = max(0.0, min(speed / max(maximum_speed, 1.0), 1.0))
        return round(normalized * (len(ENGINE_FREQUENCIES) - 1))

    def pause_race_audio(self):
        if not self.race_audio_active or self.race_audio_paused:
            return
        self.race_audio_paused = True
        for channel in self._race_channels():
            channel.pause()

    def resume_race_audio(self):
        if not self.race_audio_active or not self.race_audio_paused:
            return
        self.race_audio_paused = False
        for channel in self._race_channels():
            channel.unpause()

    def stop_race_audio(self):
        for channel in self._race_channels():
            channel.stop()
        self.engine_channels = []
        self.crowd_channel = None
        self.boost_channel = None
        self.tire_channel = None
        self.race_audio_active = False
        self.race_audio_paused = False

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

    def shutdown(self):
        self.stop_race_audio()
        self.stop_music()

    def _race_channels(self):
        channels = list(self.engine_channels)
        channels.extend(
            channel
            for channel in (
                self.crowd_channel,
                self.boost_channel,
                self.tire_channel,
            )
            if channel is not None
        )
        return channels

    def _sfx_gain(self):
        return self.user_settings.master_volume * self.user_settings.sfx_volume

    def _apply_music_volume(self):
        if not self.available:
            return
        pygame.mixer.music.set_volume(
            self.user_settings.master_volume
            * self.user_settings.music_volume
        )

    def _engine_loop(self, frequency):
        duration = 0.4
        frame_count = int(self.sample_rate * duration)
        samples = []
        for frame in range(frame_count):
            elapsed = frame / self.sample_rate
            phase = 2.0 * math.pi * frequency * elapsed
            sample = (
                math.sin(phase) * 0.58
                + math.sin(phase * 2.0) * 0.28
                + math.sin(phase * 3.0) * 0.14
            )
            samples.append(sample * 0.27)
        return self._sound_from_samples(samples)

    def _crowd_loop(self):
        duration = 1.0
        frame_count = int(self.sample_rate * duration)
        phases = [self._random.random() * math.tau for _ in range(6)]
        frequencies = (3, 5, 7, 73, 97, 131)
        samples = []
        for frame in range(frame_count):
            elapsed = frame / self.sample_rate
            murmur = sum(
                math.sin(math.tau * frequency * elapsed + phase)
                for frequency, phase in zip(frequencies, phases)
            ) / len(frequencies)
            samples.append(murmur * 0.24)
        return self._sound_from_samples(samples)

    def _wind_loop(self):
        duration = 0.5
        frame_count = int(self.sample_rate * duration)
        samples = []
        for frame in range(frame_count):
            elapsed = frame / self.sample_rate
            sample = (
                math.sin(math.tau * 410 * elapsed) * 0.35
                + math.sin(math.tau * 615 * elapsed) * 0.25
                + math.sin(math.tau * 915 * elapsed) * 0.18
            )
            samples.append(sample * 0.24)
        return self._sound_from_samples(samples)

    def _tire_loop(self):
        duration = 0.4
        frame_count = int(self.sample_rate * duration)
        samples = []
        for frame in range(frame_count):
            elapsed = frame / self.sample_rate
            sample = (
                math.sin(math.tau * 775 * elapsed)
                + math.sin(math.tau * 1025 * elapsed) * 0.55
            )
            samples.append(sample * 0.13)
        return self._sound_from_samples(samples)

    def _crowd_burst(self, duration, amplitude):
        frame_count = max(1, int(self.sample_rate * duration))
        samples = []
        filtered_noise = 0.0
        for frame in range(frame_count):
            filtered_noise = (
                filtered_noise * 0.82 + self._random.uniform(-1.0, 1.0) * 0.18
            )
            cheer = filtered_noise + math.sin(
                math.tau * 180 * frame / self.sample_rate
            ) * 0.20
            samples.append(
                cheer * amplitude * self._envelope(frame, frame_count)
            )
        return self._sound_from_samples(samples)

    def _tone(self, frequency, duration, amplitude):
        samples = []
        frame_count = max(1, int(self.sample_rate * duration))
        for frame in range(frame_count):
            elapsed = frame / self.sample_rate
            samples.append(
                math.sin(2.0 * math.pi * frequency * elapsed)
                * amplitude
                * self._envelope(frame, frame_count)
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
