"""Lightweight career profile and track-record screen."""

import pygame

from game import settings
from game.cars import CARS, CARS_BY_ID
from game.formatting import ordinal
from game.tracks import TRACKS


class ProfileScreen:
    def __init__(self):
        self.title_font = pygame.font.Font(None, 50)
        self.name_font = pygame.font.Font(None, 38)
        self.section_font = pygame.font.Font(None, 27)
        self.label_font = pygame.font.Font(None, 22)
        self.small_font = pygame.font.Font(None, 19)

    def handle_event(self, event):
        return (
            event.type == pygame.KEYDOWN
            and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER)
        )

    def draw(self, surface, profile):
        surface.fill((14, 18, 23))
        title = self.title_font.render("PLAYER PROFILE", True, settings.WHITE)
        surface.blit(
            title,
            title.get_rect(center=(settings.SCREEN_WIDTH // 2, 48)),
        )
        player_name = self.name_font.render(
            profile.player_name, True, (91, 188, 240)
        )
        surface.blit(
            player_name,
            player_name.get_rect(center=(settings.SCREEN_WIDTH // 2, 88)),
        )

        self._draw_summary_panels(surface, profile)
        self._draw_records(surface, profile)

        continue_text = self.label_font.render(
            "ENTER - Continue to Car Selection", True, settings.WHITE
        )
        surface.blit(
            continue_text,
            continue_text.get_rect(center=(settings.SCREEN_WIDTH // 2, 670)),
        )

    def _draw_summary_panels(self, surface, profile):
        overall_rect = pygame.Rect(70, 125, 315, 155)
        unlock_rect = pygame.Rect(415, 125, 315, 155)
        for panel_rect in (overall_rect, unlock_rect):
            pygame.draw.rect(
                surface, (28, 34, 41), panel_rect, border_radius=9
            )
            pygame.draw.rect(
                surface,
                (66, 78, 88),
                panel_rect,
                width=2,
                border_radius=9,
            )

        overall_title = self.section_font.render(
            "CAREER", True, settings.WHITE
        )
        surface.blit(overall_title, (92, 143))
        win_rate = (
            profile.total_wins / profile.total_races * 100.0
            if profile.total_races
            else 0.0
        )
        overall_lines = (
            f"RACES: {profile.total_races}",
            f"WINS: {profile.total_wins}",
            f"PODIUMS: {profile.total_podiums}",
            f"WIN RATE: {win_rate:.0f}%",
        )
        self._draw_lines(surface, overall_lines, 92, 178)

        unlock_title = self.section_font.render(
            "UNLOCKS", True, settings.WHITE
        )
        surface.blit(unlock_title, (437, 143))
        unlock_lines = (
            f"CARS UNLOCKED: {len(profile.unlocked_car_ids)} / {len(CARS)}",
            f"TRACKS UNLOCKED: {len(profile.unlocked_track_ids)} / {len(TRACKS)}",
            f"SELECTED CAR: {CARS_BY_ID[profile.selected_car_id].name}",
        )
        self._draw_lines(surface, unlock_lines, 437, 184, spacing=30)

    def _draw_records(self, surface, profile):
        panel_rect = pygame.Rect(70, 305, 660, 325)
        pygame.draw.rect(surface, (28, 34, 41), panel_rect, border_radius=9)
        pygame.draw.rect(
            surface, (66, 78, 88), panel_rect, width=2, border_radius=9
        )
        title = self.section_font.render("TRACK RECORDS", True, settings.WHITE)
        surface.blit(title, (92, 322))

        row_y = 365
        for track in TRACKS:
            finish = profile.best_finish_by_track.get(track.id)
            best_time = profile.best_time_by_track.get(track.id)
            finish_text = ordinal(finish) if finish is not None else "--"
            time_text = f"{best_time:.2f}s" if best_time is not None else "--"

            name = self.label_font.render(track.name, True, settings.WHITE)
            record = self.label_font.render(
                f"Best Finish: {finish_text}     Best Time: {time_text}",
                True,
                (180, 194, 202),
            )
            surface.blit(name, (92, row_y))
            surface.blit(record, (92, row_y + 29))
            if track is not TRACKS[-1]:
                pygame.draw.line(
                    surface,
                    (55, 64, 73),
                    (92, row_y + 67),
                    (708, row_y + 67),
                    1,
                )
            row_y += 82

    def _draw_lines(self, surface, lines, x, start_y, spacing=25):
        for index, line in enumerate(lines):
            rendered = self.label_font.render(
                line, True, (190, 202, 210)
            )
            surface.blit(rendered, (x, start_y + index * spacing))
