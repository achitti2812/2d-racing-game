"""Persistent audio and presentation settings screen."""

import pygame

from game import settings
from ui import components, theme


BACK = "BACK"
CHANGED = "CHANGED"
MOVE = "MOVE"


class SettingsScreen:
    ROWS = (
        ("MASTER VOLUME", "master_volume", "volume"),
        ("SFX VOLUME", "sfx_volume", "volume"),
        ("MUSIC VOLUME", "music_volume", "volume"),
        ("DISPLAY FPS", "show_fps", "boolean"),
        ("SCREEN SHAKE", "screen_shake", "boolean"),
    )

    def __init__(self):
        self.selected_index = 0
        self.title_font = pygame.font.Font(None, 58)
        self.item_font = pygame.font.Font(None, 29)
        self.footer_font = pygame.font.Font(None, 20)
        self.message_font = pygame.font.Font(None, 18)

    def handle_event(self, event, user_settings):
        if event.type != pygame.KEYDOWN:
            return None
        if event.key in (pygame.K_ESCAPE, pygame.K_b):
            return BACK
        if event.key in (pygame.K_UP, pygame.K_w):
            self.selected_index = (self.selected_index - 1) % len(self.ROWS)
            return MOVE
        if event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected_index = (self.selected_index + 1) % len(self.ROWS)
            return MOVE

        _, attribute, value_type = self.ROWS[self.selected_index]
        if event.key in (pygame.K_LEFT, pygame.K_a):
            self._change_value(user_settings, attribute, value_type, -1)
            return CHANGED
        if event.key in (pygame.K_RIGHT, pygame.K_d):
            self._change_value(user_settings, attribute, value_type, 1)
            return CHANGED
        if (
            event.key in (pygame.K_RETURN, pygame.K_KP_ENTER)
            and value_type == "boolean"
        ):
            setattr(user_settings, attribute, not getattr(user_settings, attribute))
            return CHANGED
        return None

    @staticmethod
    def _change_value(user_settings, attribute, value_type, direction):
        current_value = getattr(user_settings, attribute)
        if value_type == "volume":
            changed = round(current_value * 10 + direction) / 10
            setattr(user_settings, attribute, max(0.0, min(changed, 1.0)))
        else:
            setattr(user_settings, attribute, not current_value)

    def draw(self, surface, user_settings, message=""):
        components.draw_background(surface)
        title = self.title_font.render("SETTINGS", True, theme.TEXT)
        surface.blit(
            title,
            title.get_rect(center=(settings.SCREEN_WIDTH // 2, 86)),
        )

        panel_rect = pygame.Rect(145, 145, 510, 390)
        components.draw_panel(surface, panel_rect)
        for index, (label, attribute, value_type) in enumerate(self.ROWS):
            selected = index == self.selected_index
            row_rect = pygame.Rect(175, 180 + index * 66, 450, 50)
            if selected:
                pygame.draw.rect(
                    surface, (32, 64, 76), row_rect, border_radius=7
                )
                pygame.draw.rect(
                    surface, theme.ACCENT, row_rect, width=2, border_radius=7
                )
            value = getattr(user_settings, attribute)
            if value_type == "volume":
                value_text = f"{round(value * 100):d}%"
            else:
                value_text = "ON" if value else "OFF"
            color = theme.ACCENT_BRIGHT if selected else theme.TEXT
            name_surface = self.item_font.render(label, True, color)
            value_surface = self.item_font.render(value_text, True, color)
            surface.blit(name_surface, (195, row_rect.y + 14))
            surface.blit(
                value_surface,
                value_surface.get_rect(midright=(605, row_rect.centery)),
            )

        if message:
            rendered = self.message_font.render(message, True, theme.WARNING)
            surface.blit(
                rendered,
                rendered.get_rect(center=(settings.SCREEN_WIDTH // 2, 580)),
            )

        components.draw_footer(
            surface,
            self.footer_font,
            "UP / DOWN - Select    LEFT / RIGHT - Change    ESC / B - Back",
        )
