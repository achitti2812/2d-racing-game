"""Temporary keyboard-driven track selection screen."""

import pygame

from game import settings
from game.progression import TRACK_UNLOCK_HINTS


class TrackSelectScreen:
    """Render the track registry and translate number keys into a selection."""

    def __init__(self, track_configs):
        self.track_configs = track_configs
        self.title_font = pygame.font.Font(None, 58)
        self.track_font = pygame.font.Font(None, 31)
        self.label_font = pygame.font.Font(None, 24)
        self.description_font = pygame.font.Font(None, 20)
        self.hint_font = pygame.font.Font(None, 25)
        self.message = ""
        self.message_timer = 0.0

    def update(self, delta_time):
        self.message_timer = max(0.0, self.message_timer - delta_time)
        if self.message_timer <= 0.0:
            self.message = ""

    def show_message(self, message, duration=2.0):
        self.message = message
        self.message_timer = duration

    def handle_event(self, event, profile):
        if event.type != pygame.KEYDOWN:
            return None

        key_to_index = {
            pygame.K_1: 0,
            pygame.K_KP1: 0,
            pygame.K_2: 1,
            pygame.K_KP2: 1,
            pygame.K_3: 2,
            pygame.K_KP3: 2,
        }
        selected_index = key_to_index.get(event.key)
        if selected_index is None or selected_index >= len(self.track_configs):
            return None
        selected_track = self.track_configs[selected_index]
        if selected_track.id not in profile.unlocked_track_ids:
            unlock_hint = TRACK_UNLOCK_HINTS.get(
                selected_track.id, "Complete earlier content"
            )
            self.message = (
                f"{selected_track.name} IS LOCKED - {unlock_hint} first."
            )
            self.message_timer = 2.0
            return None
        return selected_track

    def draw(self, surface, selected_car, profile):
        surface.fill((14, 18, 23))

        title = self.title_font.render("SELECT TRACK", True, settings.WHITE)
        surface.blit(
            title,
            title.get_rect(center=(settings.SCREEN_WIDTH // 2, 70)),
        )

        subtitle = self.hint_font.render(
            "Press 1, 2, or 3 to begin", True, (182, 194, 202)
        )
        surface.blit(
            subtitle,
            subtitle.get_rect(center=(settings.SCREEN_WIDTH // 2, 112)),
        )

        for index, track_config in enumerate(self.track_configs, start=1):
            self._draw_track_card(
                surface,
                index,
                track_config,
                track_config.id in profile.unlocked_track_ids,
            )

        footer_text = "Temporary Step 12 development selector"
        if selected_car is not None:
            footer_text = f"SELECTED CAR: {selected_car.name}"
        footer = self.description_font.render(
            footer_text, True, (159, 174, 183)
        )
        surface.blit(
            footer,
            footer.get_rect(center=(settings.SCREEN_WIDTH // 2, 660)),
        )

        if self.message_timer > 0.0 and self.message:
            self._draw_message(surface)

    def _draw_track_card(self, surface, number, track_config, unlocked):
        panel_y = 145 + (number - 1) * 155
        panel_rect = pygame.Rect(100, panel_y, 600, 125)
        pygame.draw.rect(surface, (29, 35, 42), panel_rect, border_radius=10)
        border_color = (
            track_config.shoulder_color if unlocked else (91, 96, 102)
        )
        pygame.draw.rect(
            surface,
            border_color,
            panel_rect,
            width=3,
            border_radius=10,
        )

        swatch_rect = pygame.Rect(120, panel_y + 20, 70, 85)
        pygame.draw.rect(
            surface, track_config.terrain_color, swatch_rect, border_radius=6
        )
        pygame.draw.rect(
            surface,
            track_config.shoulder_color,
            (145, panel_y + 20, 20, 85),
        )
        pygame.draw.rect(
            surface,
            settings.ROAD_COLOR,
            (150, panel_y + 20, 10, 85),
        )

        number_text = self.track_font.render(
            str(number), True, settings.WHITE
        )
        surface.blit(
            number_text,
            number_text.get_rect(center=swatch_rect.center),
        )

        name_text = self.track_font.render(
            track_config.name, True, settings.WHITE
        )
        difficulty_colors = {
            "EASY": (105, 211, 137),
            "MEDIUM": (235, 183, 82),
            "HARD": (239, 112, 105),
        }
        difficulty_text = self.label_font.render(
            track_config.difficulty,
            True,
            difficulty_colors.get(track_config.difficulty, settings.WHITE),
        )
        distance_text = self.description_font.render(
            f"DISTANCE: {round(track_config.race_distance)}",
            True,
            (190, 201, 208),
        )
        description_text = self.description_font.render(
            track_config.description,
            True,
            (172, 184, 191),
        )

        surface.blit(name_text, (215, panel_y + 17))
        surface.blit(difficulty_text, (215, panel_y + 49))
        surface.blit(distance_text, (330, panel_y + 52))
        surface.blit(description_text, (215, panel_y + 82))

        if unlocked:
            status_text = "AVAILABLE"
            status_color = (114, 224, 143)
        else:
            status_text = (
                "LOCKED - "
                + TRACK_UNLOCK_HINTS.get(
                    track_config.id, "Complete earlier content"
                )
            )
            status_color = (244, 157, 104)
        status = self.description_font.render(
            status_text, True, status_color
        )
        surface.blit(status, (215, panel_y + 102))

    def _draw_message(self, surface):
        panel_rect = pygame.Rect(90, 310, 620, 80)
        panel = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        panel.fill((8, 10, 12, 235))
        surface.blit(panel, panel_rect)
        pygame.draw.rect(
            surface,
            (244, 157, 104),
            panel_rect,
            width=2,
            border_radius=8,
        )
        message = self.hint_font.render(
            self.message, True, settings.WHITE
        )
        surface.blit(message, message.get_rect(center=panel_rect.center))
