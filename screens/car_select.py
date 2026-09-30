"""Temporary keyboard-driven player-car selection screen."""

import pygame

from game import settings
from game.progression import CAR_UNLOCK_HINTS


class CarSelectScreen:
    """Render selectable car configurations and display-only stat bars."""

    def __init__(self, car_configs):
        self.car_configs = car_configs
        self.title_font = pygame.font.Font(None, 58)
        self.car_font = pygame.font.Font(None, 32)
        self.label_font = pygame.font.Font(None, 20)
        self.description_font = pygame.font.Font(None, 19)
        self.hint_font = pygame.font.Font(None, 24)
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
        if selected_index is None or selected_index >= len(self.car_configs):
            return None
        selected_car = self.car_configs[selected_index]
        if selected_car.id not in profile.unlocked_car_ids:
            unlock_hint = CAR_UNLOCK_HINTS.get(
                selected_car.id, "Complete earlier content"
            )
            self.message = f"{selected_car.name} IS LOCKED - {unlock_hint} first."
            self.message_timer = 2.0
            return None
        return selected_car

    def draw(self, surface, profile):
        surface.fill((14, 18, 23))

        title = self.title_font.render("SELECT CAR", True, settings.WHITE)
        surface.blit(
            title,
            title.get_rect(center=(settings.SCREEN_WIDTH // 2, 52)),
        )
        subtitle = self.hint_font.render(
            "Press 1, 2, or 3 to continue to track selection",
            True,
            (182, 194, 202),
        )
        surface.blit(
            subtitle,
            subtitle.get_rect(center=(settings.SCREEN_WIDTH // 2, 90)),
        )

        for index, car_config in enumerate(self.car_configs, start=1):
            self._draw_car_card(
                surface,
                index,
                car_config,
                car_config.id in profile.unlocked_car_ids,
                car_config.id == profile.selected_car_id,
            )

        if self.message_timer > 0.0 and self.message:
            self._draw_message(surface)

    def _draw_car_card(
        self, surface, number, car_config, unlocked, selected
    ):
        panel_y = 115 + (number - 1) * 180
        panel_rect = pygame.Rect(50, panel_y, 700, 165)
        pygame.draw.rect(surface, (29, 35, 42), panel_rect, border_radius=10)
        border_color = car_config.accent_color if unlocked else (91, 96, 102)
        pygame.draw.rect(
            surface,
            border_color,
            panel_rect,
            width=3,
            border_radius=10,
        )

        self._draw_car_preview(surface, 115, panel_y + 27, car_config)

        number_text = self.car_font.render(
            str(number), True, car_config.accent_color
        )
        name_text = self.car_font.render(
            car_config.name, True, settings.WHITE
        )
        description_text = self.description_font.render(
            car_config.description, True, (176, 188, 196)
        )
        speed_text = self.description_font.render(
            f"MAX {round(car_config.max_speed)}   NITRO {round(car_config.nitro_max_speed)}",
            True,
            (203, 213, 219),
        )

        surface.blit(number_text, (172, panel_y + 20))
        surface.blit(name_text, (205, panel_y + 20))
        surface.blit(description_text, (172, panel_y + 57))
        surface.blit(speed_text, (172, panel_y + 89))

        if unlocked:
            status_text = "SELECTED / AVAILABLE" if selected else "AVAILABLE"
            status_color = (114, 224, 143)
        else:
            status_text = (
                "LOCKED - "
                + CAR_UNLOCK_HINTS.get(
                    car_config.id, "Complete earlier content"
                )
            )
            status_color = (244, 157, 104)
        status = self.description_font.render(
            status_text, True, status_color
        )
        surface.blit(status, (172, panel_y + 121))

        ratings = (
            ("SPEED", car_config.speed_rating),
            ("ACCEL", car_config.acceleration_rating),
            ("HANDLING", car_config.handling_rating),
            ("NITRO", car_config.nitro_rating),
        )
        for row, (label, rating) in enumerate(ratings):
            self._draw_rating(
                surface,
                label,
                rating,
                505,
                panel_y + 25 + row * 31,
                car_config.accent_color,
            )

    def _draw_car_preview(self, surface, center_x, top_y, car_config):
        car_width = 54
        car_height = 112
        car_left = center_x - car_width // 2
        for wheel_y in (top_y + 18, top_y + 75):
            pygame.draw.rect(
                surface,
                settings.BLACK,
                (car_left - 5, wheel_y, 9, 24),
                border_radius=3,
            )
            pygame.draw.rect(
                surface,
                settings.BLACK,
                (car_left + car_width - 4, wheel_y, 9, 24),
                border_radius=3,
            )

        body_points = (
            (center_x - 18, top_y),
            (center_x + 18, top_y),
            (car_left + car_width, top_y + 23),
            (car_left + car_width - 3, top_y + car_height - 10),
            (center_x + 19, top_y + car_height),
            (center_x - 19, top_y + car_height),
            (car_left + 3, top_y + car_height - 10),
            (car_left, top_y + 23),
        )
        pygame.draw.polygon(surface, car_config.body_color, body_points)
        pygame.draw.polygon(
            surface, car_config.accent_color, body_points, width=3
        )
        pygame.draw.rect(
            surface,
            car_config.accent_color,
            (center_x - 3, top_y + 6, 6, car_height - 12),
        )
        pygame.draw.rect(
            surface,
            settings.WINDOW_COLOR,
            (center_x - 18, top_y + 36, 36, 25),
            border_radius=3,
        )

    def _draw_rating(self, surface, label, rating, x, y, color):
        label_text = self.label_font.render(label, True, settings.WHITE)
        surface.blit(label_text, (x, y))

        bar_x = x + 82
        for index in range(5):
            segment_rect = pygame.Rect(bar_x + index * 21, y + 2, 16, 12)
            segment_color = color if index < rating else (62, 70, 78)
            pygame.draw.rect(
                surface, segment_color, segment_rect, border_radius=2
            )

    def _draw_message(self, surface):
        panel_rect = pygame.Rect(120, 310, 560, 80)
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
