"""Pause overlay and keyboard navigation."""

import pygame

from game import settings
from ui import components, theme


RESUME = "RESUME"
RESTART = "RESTART"
OPEN_SETTINGS = "OPEN_SETTINGS"
QUIT_TO_MENU = "QUIT_TO_MENU"
MOVE = "MOVE"


class PauseMenuScreen:
    ITEMS = (
        ("RESUME", RESUME),
        ("RESTART RACE", RESTART),
        ("SETTINGS", OPEN_SETTINGS),
        ("QUIT TO MAIN MENU", QUIT_TO_MENU),
    )

    def __init__(self):
        self.selected_index = 0
        self.title_font = pygame.font.Font(None, 64)
        self.item_font = pygame.font.Font(None, 30)
        self.footer_font = pygame.font.Font(None, 20)

    def reset_selection(self):
        self.selected_index = 0

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return None
        if event.key in (pygame.K_p, pygame.K_ESCAPE):
            return RESUME
        if event.key in (pygame.K_UP, pygame.K_w):
            self.selected_index = (self.selected_index - 1) % len(self.ITEMS)
            return MOVE
        if event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected_index = (self.selected_index + 1) % len(self.ITEMS)
            return MOVE
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return self.ITEMS[self.selected_index][1]
        return None

    def draw(self, surface):
        overlay = pygame.Surface(
            (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA
        )
        overlay.fill((4, 7, 10, 205))
        surface.blit(overlay, (0, 0))

        panel_rect = pygame.Rect(175, 95, 450, 500)
        components.draw_panel(surface, panel_rect, theme.ACCENT)
        title = self.title_font.render("PAUSED", True, theme.TEXT)
        surface.blit(
            title,
            title.get_rect(center=(settings.SCREEN_WIDTH // 2, 155)),
        )
        for index, (label, _) in enumerate(self.ITEMS):
            components.draw_menu_item(
                surface,
                self.item_font,
                label,
                (settings.SCREEN_WIDTH // 2, 250 + index * 68),
                index == self.selected_index,
            )

        footer = self.footer_font.render(
            "P / ESC - Resume", True, theme.MUTED
        )
        surface.blit(
            footer,
            footer.get_rect(center=(settings.SCREEN_WIDTH // 2, 555)),
        )
