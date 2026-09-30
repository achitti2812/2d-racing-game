"""First-launch keyboard profile creation screen."""

import pygame

from game import settings
from game.profile import MAX_PLAYER_NAME_LENGTH, normalize_player_name


class ProfileSetupScreen:
    def __init__(self, initial_message=""):
        self.name_text = ""
        self.message = initial_message
        self.cursor_timer = 0.0
        self.title_font = pygame.font.Font(None, 54)
        self.name_font = pygame.font.Font(None, 38)
        self.label_font = pygame.font.Font(None, 25)
        self.message_font = pygame.font.Font(None, 20)

    def update(self, delta_time):
        self.cursor_timer = (self.cursor_timer + delta_time) % 1.0

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return None

        if event.key == pygame.K_BACKSPACE:
            self.name_text = self.name_text[:-1]
            self.message = ""
            return None
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            try:
                return normalize_player_name(self.name_text)
            except ValueError as error:
                self.message = str(error)
                return None

        character = event.unicode
        if (
            character
            and len(self.name_text) < MAX_PLAYER_NAME_LENGTH
            and (character.isalnum() or character in " -_")
        ):
            self.name_text += character
            self.message = ""
        return None

    def draw(self, surface):
        surface.fill((14, 18, 23))

        title = self.title_font.render(
            "CREATE PLAYER PROFILE", True, settings.WHITE
        )
        surface.blit(
            title,
            title.get_rect(center=(settings.SCREEN_WIDTH // 2, 130)),
        )

        instruction = self.label_font.render(
            "Enter a name using up to 20 letters, numbers, spaces, - or _",
            True,
            (178, 191, 200),
        )
        surface.blit(
            instruction,
            instruction.get_rect(center=(settings.SCREEN_WIDTH // 2, 188)),
        )

        input_rect = pygame.Rect(170, 250, 460, 64)
        pygame.draw.rect(surface, (28, 34, 41), input_rect, border_radius=8)
        pygame.draw.rect(
            surface, (91, 167, 220), input_rect, width=2, border_radius=8
        )
        label = self.label_font.render("NAME", True, (164, 180, 190))
        surface.blit(label, (input_rect.x, input_rect.y - 32))

        visible_name = self.name_text
        if self.cursor_timer < 0.5:
            visible_name += "|"
        name_surface = self.name_font.render(
            visible_name, True, settings.WHITE
        )
        surface.blit(name_surface, (input_rect.x + 16, input_rect.y + 16))

        confirm = self.label_font.render(
            "ENTER - Confirm", True, settings.WHITE
        )
        surface.blit(
            confirm,
            confirm.get_rect(center=(settings.SCREEN_WIDTH // 2, 365)),
        )

        if self.message:
            self._draw_wrapped_message(surface, self.message, 425)

    def _draw_wrapped_message(self, surface, message, start_y):
        words = message.split()
        lines = []
        current_line = ""
        for word in words:
            candidate = f"{current_line} {word}".strip()
            if self.message_font.size(candidate)[0] <= 650:
                current_line = candidate
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        for line_index, line in enumerate(lines):
            rendered = self.message_font.render(
                line, True, (247, 151, 106)
            )
            surface.blit(
                rendered,
                rendered.get_rect(
                    center=(
                        settings.SCREEN_WIDTH // 2,
                        start_y + line_index * 24,
                    )
                ),
            )
