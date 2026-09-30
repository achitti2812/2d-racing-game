"""Low-cost visual effects that do not modify gameplay state."""

import random

import pygame

from game import settings


def draw_speed_streaks(surface, speed, nitro_active, camera_distance):
    """Draw sparse deterministic edge streaks above the speed threshold."""
    if speed < settings.SPEED_STREAK_THRESHOLD:
        return
    intensity = min(
        1.0,
        (speed - settings.SPEED_STREAK_THRESHOLD)
        / max(1.0, 230.0 - settings.SPEED_STREAK_THRESHOLD),
    )
    if nitro_active:
        intensity = min(1.0, intensity + 0.30)
    count = 4 + round(intensity * 10)
    length = 20 + round(intensity * 48)
    alpha = 45 + round(intensity * 95)
    color = (115, 227, 255, alpha) if nitro_active else (230, 236, 238, alpha)
    effect_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    seed = int(camera_distance * 2.0) // 20
    random_source = random.Random(seed)
    motion_offset = int(camera_distance * settings.RELATIVE_MOTION_SCALE) % 90
    for index in range(count):
        side = -1 if index % 2 == 0 else 1
        edge_x = random_source.randint(10, 105)
        x = edge_x if side < 0 else settings.SCREEN_WIDTH - edge_x
        y = (random_source.randint(-80, settings.SCREEN_HEIGHT) + motion_offset) % 780 - 40
        slant = -4 if side < 0 else 4
        pygame.draw.line(
            effect_surface,
            color,
            (x, y),
            (x + slant, y + length),
            2 if intensity < 0.75 else 3,
        )
    surface.blit(effect_surface, (0, 0))
