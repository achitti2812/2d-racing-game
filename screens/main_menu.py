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
        self._draw_racing_backdrop(surface)

        shadow = self.title_font.render("2D RACING", True, (0, 0, 0))
        title = self.title_font.render("2D RACING", True, theme.TEXT)
        surface.blit(
            shadow,
            shadow.get_rect(center=(settings.SCREEN_WIDTH // 2 + 4, 109)),
        )
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

    def _draw_racing_backdrop(self, surface):
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        road_points = ((305, 0), (495, 0), (755, 700), (45, 700))
        pygame.draw.polygon(overlay, (18, 23, 29, 205), road_points)
        pygame.draw.lines(
            overlay, (50, 72, 82, 170), False, ((305, 0), (45, 700)), 4
        )
        pygame.draw.lines(
            overlay, (50, 72, 82, 170), False, ((495, 0), (755, 700)), 4
        )
        motion = (pygame.time.get_ticks() // 12) % 100
        for y in range(-100 + motion, 750, 100):
            progress = max(0.0, min(y / 700.0, 1.0))
            half_width = 6 + progress * 24
            pygame.draw.polygon(
                overlay,
                (111, 222, 240, 70),
                (
                    (400 - half_width, y),
                    (400 + half_width, y),
                    (404 + half_width, y + 42),
                    (396 - half_width, y + 42),
                ),
            )
        for x in (32, 82, 718, 768):
            pygame.draw.line(
                overlay, (86, 205, 232, 70), (x, 110), (x, 360), 2
            )
        surface.blit(overlay, (0, 0))
