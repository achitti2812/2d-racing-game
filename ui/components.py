"""Focused procedural helpers shared by the new menu screens."""

import pygame

from game import settings
from ui import theme


def draw_background(surface):
    surface.fill(theme.BACKGROUND)
    stripe_width = 70
    for x in range(-settings.SCREEN_HEIGHT, settings.SCREEN_WIDTH, stripe_width):
        pygame.draw.polygon(
            surface,
            theme.BACKGROUND_STRIPE,
            (
                (x, 0),
                (x + 26, 0),
                (x + settings.SCREEN_HEIGHT + 26, settings.SCREEN_HEIGHT),
                (x + settings.SCREEN_HEIGHT, settings.SCREEN_HEIGHT),
            ),
        )


def draw_panel(surface, rect, border_color=theme.PANEL_BORDER):
    pygame.draw.rect(surface, theme.PANEL, rect, border_radius=12)
    pygame.draw.rect(surface, border_color, rect, width=2, border_radius=12)
    pygame.draw.line(
        surface,
        theme.ACCENT,
        (rect.x + 18, rect.y),
        (rect.x + min(105, rect.width - 18), rect.y),
        3,
    )


def draw_menu_item(surface, font, text, center, selected):
    rect = pygame.Rect(0, 0, 390, 56)
    rect.center = center
    if selected:
        shape = (
            (rect.x + 10, rect.y),
            (rect.right, rect.y),
            (rect.right - 10, rect.bottom),
            (rect.x, rect.bottom),
        )
        pygame.draw.polygon(surface, (32, 64, 76), shape)
        pygame.draw.lines(surface, theme.ACCENT, True, shape, 2)
        color = theme.ACCENT_BRIGHT
        prefix = ">  "
    else:
        color = theme.TEXT
        prefix = "   "
    rendered = font.render(prefix + text, True, color)
    surface.blit(rendered, rendered.get_rect(center=rect.center))


def draw_footer(surface, font, text):
    rendered = font.render(text, True, theme.MUTED)
    surface.blit(
        rendered,
        rendered.get_rect(center=(settings.SCREEN_WIDTH // 2, 670)),
    )
