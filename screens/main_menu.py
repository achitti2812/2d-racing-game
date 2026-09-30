"""Keyboard-driven central navigation menu."""

import pygame

from game import settings
from ui import components, theme


CONTINUE = "CONTINUE"
OPEN_PROFILE = "OPEN_PROFILE"
OPEN_SETTINGS = "OPEN_SETTINGS"
QUIT = "QUIT"
MOVE = "MOVE"


class MainMenuScreen:
    ITEMS = (
        ("CONTINUE RACING", CONTINUE),
        ("PROFILE", OPEN_PROFILE),
        ("SETTINGS", OPEN_SETTINGS),
        ("QUIT", QUIT),
    )

    def __init__(self):
        self.selected_index = 0
        self.title_font = pygame.font.Font(None, 76)
        self.subtitle_font = pygame.font.Font(None, 26)
        self.item_font = pygame.font.Font(None, 34)
        self.footer_font = pygame.font.Font(None, 21)

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return None
        if event.key in (pygame.K_UP, pygame.K_w):
            self.selected_index = (self.selected_index - 1) % len(self.ITEMS)
            return MOVE
        if event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected_index = (self.selected_index + 1) % len(self.ITEMS)
            return MOVE
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return self.ITEMS[self.selected_index][1]
        if event.key == pygame.K_ESCAPE:
            return QUIT
        return None

    def draw(self, surface, profile):
        components.draw_background(surface)

        title = self.title_font.render("2D RACING", True, theme.TEXT)
        surface.blit(
            title,
            title.get_rect(center=(settings.SCREEN_WIDTH // 2, 105)),
        )
        accent_line = pygame.Rect(settings.SCREEN_WIDTH // 2 - 95, 145, 190, 4)
        pygame.draw.rect(surface, theme.ACCENT, accent_line, border_radius=2)

        summary = self.subtitle_font.render(
            f"PLAYER: {profile.player_name}    RACES: {profile.total_races}    "
            f"WINS: {profile.total_wins}",
            True,
            theme.MUTED,
        )
        surface.blit(
            summary,
            summary.get_rect(center=(settings.SCREEN_WIDTH // 2, 183)),
        )

        panel_rect = pygame.Rect(185, 225, 430, 295)
        components.draw_panel(surface, panel_rect)
        for index, (label, _) in enumerate(self.ITEMS):
            components.draw_menu_item(
                surface,
                self.item_font,
                label,
                (settings.SCREEN_WIDTH // 2, 275 + index * 68),
                index == self.selected_index,
            )

        components.draw_footer(
            surface,
            self.footer_font,
            "UP / DOWN - Navigate    ENTER - Select    ESC - Quit",
        )
