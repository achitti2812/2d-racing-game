"""Temporary keyboard-driven player-car selection screen."""

import pygame

from game import settings


class CarSelectScreen:
    """Render selectable car configurations and display-only stat bars."""

    def __init__(self, car_configs):
        self.car_configs = car_configs
        self.title_font = pygame.font.Font(None, 58)
        self.car_font = pygame.font.Font(None, 32)
        self.label_font = pygame.font.Font(None, 20)
        self.description_font = pygame.font.Font(None, 19)
        self.hint_font = pygame.font.Font(None, 24)

    def handle_event(self, event):
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
        return self.car_configs[selected_index]

    def draw(self, surface):
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
            self._draw_car_card(surface, index, car_config)

    def _draw_car_card(self, surface, number, car_config):
        panel_y = 115 + (number - 1) * 180
        panel_rect = pygame.Rect(50, panel_y, 700, 165)
        pygame.draw.rect(surface, (29, 35, 42), panel_rect, border_radius=10)
        pygame.draw.rect(
            surface,
            car_config.accent_color,
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
