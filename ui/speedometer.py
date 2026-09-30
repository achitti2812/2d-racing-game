"""Procedural analog speedometer used by the race HUD."""

import math

import pygame


GAUGE_MAX_SPEED = 240.0
GAUGE_START_ANGLE = 135.0
GAUGE_SWEEP_ANGLE = 270.0
GAUGE_SIZE = 158
_FONTS = {}


def speed_to_angle(speed):
    """Map an arcade speed from 0-240 onto the gauge's 270-degree sweep."""
    ratio = max(0.0, min(speed / GAUGE_MAX_SPEED, 1.0))
    return GAUGE_START_ANGLE + ratio * GAUGE_SWEEP_ANGLE


def draw_speedometer(
    surface,
    position,
    actual_speed,
    displayed_speed,
    nitro_active,
):
    """Draw a compact gauge whose needle uses the visual smoothed speed."""
    gauge = pygame.Surface((GAUGE_SIZE, GAUGE_SIZE), pygame.SRCALPHA)
    center = (GAUGE_SIZE // 2, GAUGE_SIZE // 2)
    radius = 69

    pygame.draw.circle(gauge, (6, 10, 14, 220), center, radius)
    pygame.draw.circle(gauge, (55, 72, 82, 235), center, radius, 2)

    ring_color = (82, 224, 242) if nitro_active else (92, 116, 126)
    _draw_arc(gauge, center, radius - 5, 135.0, 337.5, ring_color, 3)
    boost_color = (77, 231, 255) if nitro_active else (242, 100, 71)
    _draw_arc(gauge, center, radius - 5, 337.5, 405.0, boost_color, 4)

    number_font = _get_font(15)
    for speed in range(0, 241, 10):
        angle = speed_to_angle(speed)
        major_tick = speed % 40 == 0
        outer = _point_on_circle(center, radius - 8, angle)
        inner_radius = radius - (19 if major_tick else 14)
        inner = _point_on_circle(center, inner_radius, angle)
        tick_color = boost_color if speed >= 180 else (220, 228, 226)
        pygame.draw.line(
            gauge,
            tick_color,
            inner,
            outer,
            3 if major_tick else 1,
        )
        if major_tick:
            label_position = _point_on_circle(center, radius - 31, angle)
            label = number_font.render(str(speed), True, (190, 202, 204))
            gauge.blit(label, label.get_rect(center=label_position))

    needle_angle = speed_to_angle(displayed_speed)
    needle_color = (99, 239, 255) if nitro_active else (255, 210, 68)
    needle_end = _point_on_circle(center, radius - 24, needle_angle)
    needle_tail = _point_on_circle(center, 9, needle_angle + 180.0)
    pygame.draw.line(gauge, (0, 0, 0, 150), needle_tail, needle_end, 5)
    pygame.draw.line(gauge, needle_color, needle_tail, needle_end, 3)
    pygame.draw.circle(gauge, (20, 26, 30), center, 7)
    pygame.draw.circle(gauge, needle_color, center, 4)

    value_font = _get_font(25)
    label_font = _get_font(14)
    value = value_font.render(str(round(actual_speed)), True, (245, 246, 242))
    speed_label = label_font.render("SPEED", True, (166, 185, 191))
    gauge.blit(value, value.get_rect(center=(center[0], center[1] + 28)))
    gauge.blit(
        speed_label,
        speed_label.get_rect(center=(center[0], center[1] + 44)),
    )

    surface.blit(gauge, position)


def _draw_arc(surface, center, radius, start_angle, end_angle, color, width):
    points = [
        _point_on_circle(
            center,
            radius,
            start_angle + (end_angle - start_angle) * step / 48,
        )
        for step in range(49)
    ]
    pygame.draw.lines(surface, color, False, points, width)


def _point_on_circle(center, radius, angle_degrees):
    angle = math.radians(angle_degrees)
    return (
        round(center[0] + math.cos(angle) * radius),
        round(center[1] + math.sin(angle) * radius),
    )


def _get_font(size):
    if size not in _FONTS:
        _FONTS[size] = pygame.font.Font(None, size)
    return _FONTS[size]
