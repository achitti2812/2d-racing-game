"""Race coordination, state transitions, timing, HUD, and finish logic."""

import random

import pygame

from game import settings
from game.collision import find_player_collision, handle_collision
from game.opponent import create_opponents
from game.player import Player
from game.road import Road
from game.track import Track
from screens.results import draw_results


class Race:
    """Coordinate the player, opponents, road, and current race flow."""

    def __init__(self, random_seed=None):
        self.random_source = random.Random(random_seed)
        self.title_font = pygame.font.Font(None, 29)
        self.label_font = pygame.font.Font(None, 22)
        self.control_font = pygame.font.Font(None, 18)
        self.crash_font = pygame.font.Font(None, 52)
        self.countdown_font = pygame.font.Font(None, 110)
        self.results_title_font = pygame.font.Font(None, 54)
        self.results_font = pygame.font.Font(None, 34)
        self.results_small_font = pygame.font.Font(None, 26)
        self.ai_debug_font = pygame.font.Font(None, 15)
        self.track_debug_font = pygame.font.Font(None, 18)
        self.reset_race()

    def reset_race(self):
        """Reset all race-specific state without reinitializing Pygame."""
        self.state = settings.COUNTDOWN
        self.track = Track()
        self.player = Player()
        self.player.sync_track_state(
            self.track.get_center_x(self.player.distance),
            self.track.get_curve_strength(self.player.distance),
        )
        self.opponents = create_opponents(
            self.track, random_source=self.random_source
        )
        self.road = Road(self.track)
        self.camera_distance = 0.0
        self.player_position = 4
        self.finishing_order = []
        self.race_timer = 0.0
        self.countdown_timer = settings.COUNTDOWN_DURATION
        self.go_timer = 0.0

    def handle_event(self, event):
        """Handle race-specific events; the application handles quitting."""
        if (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_r
            and self.state == settings.FINISHED
        ):
            self.reset_race()

    def update(self, delta_time):
        if self.state == settings.COUNTDOWN:
            self._update_countdown(delta_time)
        elif self.state == settings.RACING:
            self._update_active_race(delta_time)

    def _update_countdown(self, delta_time):
        self.countdown_timer = max(
            0.0, self.countdown_timer - delta_time
        )
        if self.countdown_timer <= 0.0:
            self.state = settings.RACING
            self.go_timer = settings.GO_DISPLAY_DURATION

    def _update_active_race(self, delta_time):
        frame_start_time = self.race_timer
        self.race_timer += delta_time
        self.go_timer = max(0.0, self.go_timer - delta_time)
        self.player.update_collision_timers(delta_time)

        player_was_finished = self.player.finished
        if not player_was_finished:
            self.player.update_controls(
                delta_time,
                self.track.get_center_x(self.player.distance),
                self.track.get_curve_strength(self.player.distance),
            )
        else:
            self.player.coast_after_finish(delta_time)
            self.camera_distance += self.player.speed * delta_time

        for opponent in self.opponents:
            opponent.update_ai(
                self.player.distance, delta_time, self.track
            )

        previous_distances = self._update_race_distances(delta_time)

        self.player.sync_track_state(
            self.track.get_center_x(self.player.distance),
            self.track.get_curve_strength(self.player.distance),
        )

        if not player_was_finished:
            # Preserve crossing overshoot so the finish line passes the car.
            self.camera_distance = self.player.distance

        self._update_finish_status(
            previous_distances, frame_start_time, delta_time
        )
        for opponent in self.opponents:
            opponent.update_screen_position(
                self.camera_distance, self.track
            )
        self.player_position = self._calculate_player_position()

        if (
            self.state == settings.RACING
            and not self.player.finished
            and self.player.collision_cooldown <= 0.0
        ):
            collided_opponent = find_player_collision(
                self.player, self.visible_opponents
            )
            if collided_opponent is not None:
                handle_collision(self.player, collided_opponent)
                self.player.sync_track_state(
                    self.track.get_center_x(self.player.distance),
                    self.track.get_curve_strength(self.player.distance),
                )
                if self.player.off_road:
                    self.player.stop_nitro()

    def _update_race_distances(self, delta_time):
        previous_distances = {"PLAYER": self.player.distance}
        for opponent in self.opponents:
            previous_distances[opponent.identifier] = opponent.distance

        if not self.player.finished:
            self.player.distance += self.player.speed * delta_time
        for opponent in self.opponents:
            opponent.update_distance(delta_time)

        return previous_distances

    def _update_finish_status(
        self, previous_distances, frame_start_time, delta_time
    ):
        finish_candidates = []
        tie_order = {"PLAYER": 0, "BLUE": 1, "PURPLE": 2, "GOLD": 3}

        racers = [
            (
                "PLAYER",
                self.player.finished,
                self.player.distance,
                previous_distances["PLAYER"],
            )
        ]
        racers.extend(
            (
                opponent.identifier,
                opponent.finished,
                opponent.distance,
                previous_distances[opponent.identifier],
            )
            for opponent in self.opponents
        )

        for racer_id, already_finished, new_distance, old_distance in racers:
            if already_finished or new_distance < settings.RACE_DISTANCE:
                continue

            distance_this_frame = new_distance - old_distance
            if distance_this_frame > 0.0:
                crossing_fraction = (
                    settings.RACE_DISTANCE - old_distance
                ) / distance_this_frame
                crossing_fraction = max(
                    0.0, min(crossing_fraction, 1.0)
                )
            else:
                crossing_fraction = 0.0
            crossing_time = (
                frame_start_time + crossing_fraction * delta_time
            )
            finish_candidates.append(
                (crossing_time, tie_order[racer_id], racer_id)
            )

        finish_candidates.sort()

        for crossing_time, _, racer_id in finish_candidates:
            finish_position = len(self.finishing_order) + 1
            self.finishing_order.append(racer_id)

            if racer_id == "PLAYER":
                self.player.finished = True
                self.player.stop_nitro()
                self.player.distance = settings.RACE_DISTANCE
                self.player.finish_time = crossing_time
                self.player.finish_position = finish_position
                self.player.collision_cooldown = 0.0
                self.player.crash_message_timer = 0.0
            else:
                opponent = next(
                    car
                    for car in self.opponents
                    if car.identifier == racer_id
                )
                opponent.finished = True
                opponent.distance = settings.RACE_DISTANCE
                opponent.current_speed = 0.0
                opponent.finish_time = crossing_time
                opponent.finish_position = finish_position

        if len(self.finishing_order) == 4:
            self.state = settings.FINISHED

    def _calculate_player_position(self):
        if self.player.finished:
            return self.finishing_order.index("PLAYER") + 1

        finished_opponents = len(self.finishing_order)
        unfinished_opponents_ahead = sum(
            not opponent.finished
            and opponent.distance > self.player.distance
            for opponent in self.opponents
        )
        return finished_opponents + unfinished_opponents_ahead + 1

    @property
    def visible_opponents(self):
        return [
            opponent for opponent in self.opponents if opponent.is_visible()
        ]

    @property
    def progress(self):
        return max(
            0.0,
            min(self.player.distance / settings.RACE_DISTANCE, 1.0),
        ) * 100.0

    @property
    def displayed_time(self):
        if self.player.finish_time is not None:
            return self.player.finish_time
        return self.race_timer

    def draw(self, surface):
        self.road.draw(surface, self.camera_distance)
        visible_opponents = self.visible_opponents
        for opponent in visible_opponents:
            opponent.draw(surface)
            if settings.SHOW_AI_DEBUG:
                opponent.draw_debug(surface, self.ai_debug_font)
        self.player.draw(surface)

        if settings.SHOW_HITBOXES:
            pygame.draw.rect(
                surface,
                (80, 255, 130),
                self.player.get_hitbox(),
                2,
            )
            for opponent in visible_opponents:
                pygame.draw.rect(
                    surface,
                    (255, 194, 73),
                    opponent.get_hitbox(),
                    2,
                )

        self._draw_hud(surface)
        if settings.SHOW_TRACK_DEBUG:
            self._draw_track_debug(surface)
        if self.player.crash_message_timer > 0.0:
            self._draw_crash_message(surface)
        self._draw_start_signal(surface)

        if self.state == settings.FINISHED:
            draw_results(
                surface,
                self.results_title_font,
                self.results_font,
                self.results_small_font,
                self.finishing_order,
                self.player.finish_position,
                self.player.finish_time,
            )

    def _draw_hud(self, surface):
        panel = pygame.Surface((175, 194), pygame.SRCALPHA)
        panel.fill((10, 12, 14, 175))
        surface.blit(panel, (18, 18))

        title = self.title_font.render("2D RACING", True, settings.WHITE)
        step_label = self.label_font.render(
            "STEP 9", True, (190, 206, 196)
        )
        speed_label = self.label_font.render(
            f"SPEED: {round(self.player.speed)}", True, settings.WHITE
        )
        position_label = self.label_font.render(
            f"POSITION: {self.player_position}/4", True, settings.WHITE
        )
        progress_label = self.label_font.render(
            f"PROGRESS: {round(self.progress)}%", True, settings.WHITE
        )
        minutes = int(self.displayed_time // 60)
        seconds = self.displayed_time % 60
        time_label = self.label_font.render(
            f"TIME: {minutes:02d}:{seconds:04.1f}",
            True,
            settings.WHITE,
        )
        nitro_label = self.label_font.render("NITRO", True, settings.WHITE)

        surface.blit(title, (30, 27))
        surface.blit(step_label, (30, 52))
        surface.blit(speed_label, (30, 75))
        surface.blit(position_label, (30, 98))
        surface.blit(progress_label, (30, 121))
        surface.blit(time_label, (30, 144))
        surface.blit(nitro_label, (30, 167))

        meter_rect = pygame.Rect(30, 188, 140, 12)
        pygame.draw.rect(
            surface, settings.NITRO_METER_BACKGROUND, meter_rect
        )
        nitro_ratio = self.player.nitro_amount / self.player.nitro_capacity
        fill_width = round((meter_rect.width - 4) * nitro_ratio)
        if fill_width > 0:
            fill_color = (
                settings.NITRO_METER_ACTIVE
                if self.player.nitro_active
                else settings.NITRO_METER_FILL
            )
            pygame.draw.rect(
                surface,
                fill_color,
                (meter_rect.x + 2, meter_rect.y + 2, fill_width, 8),
            )
        pygame.draw.rect(surface, settings.WHITE, meter_rect, width=2)

        control_text = (
            "W/UP ACCELERATE   S/DOWN BRAKE   A/D OR LEFT/RIGHT STEER   "
            "SPACE NITRO"
        )
        control_hint = self.control_font.render(
            control_text, True, settings.WHITE
        )
        hint_padding = 8
        hint_width = control_hint.get_width() + hint_padding * 2
        hint_panel = pygame.Surface(
            (
                hint_width,
                control_hint.get_height() + hint_padding * 2,
            ),
            pygame.SRCALPHA,
        )
        hint_panel.fill((10, 12, 14, 150))
        hint_x = settings.SCREEN_WIDTH - hint_width - 18
        surface.blit(hint_panel, (hint_x, 18))
        surface.blit(
            control_hint,
            (hint_x + hint_padding, 18 + hint_padding),
        )

        if (
            self.player.off_road
            and self.state == settings.RACING
            and not self.player.finished
        ):
            off_road_label = self.label_font.render(
                "OFF ROAD", True, (255, 198, 82)
            )
            off_road_panel = pygame.Surface(
                (off_road_label.get_width() + 16, 27), pygame.SRCALPHA
            )
            off_road_panel.fill((35, 23, 10, 190))
            surface.blit(off_road_panel, (18, 218))
            surface.blit(off_road_label, (26, 222))

    def _draw_track_debug(self, surface):
        """Show compact curved-track handling data when explicitly enabled."""
        debug_lines = (
            f"TRACK CENTER {self.player.track_center_x:.1f}",
            f"CURVE {self.player.curve_strength:+.4f}",
            f"FORCE {self.player.curve_force:+.1f}",
            f"OFF ROAD {self.player.off_road}",
        )
        rendered = [
            self.track_debug_font.render(line, True, settings.WHITE)
            for line in debug_lines
        ]
        panel_width = max(line.get_width() for line in rendered) + 16
        panel_height = sum(line.get_height() for line in rendered) + 12
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((8, 10, 12, 185))
        panel_y = 254
        surface.blit(panel, (18, panel_y))
        text_y = panel_y + 6
        for line in rendered:
            surface.blit(line, (26, text_y))
            text_y += line.get_height()

    def _draw_crash_message(self, surface):
        crash_text = self.crash_font.render(
            "CRASH!", True, (255, 82, 72)
        )
        crash_shadow = self.crash_font.render(
            "CRASH!", True, settings.BLACK
        )
        crash_rect = crash_text.get_rect(
            center=(settings.SCREEN_WIDTH // 2, 165)
        )
        surface.blit(crash_shadow, crash_rect.move(3, 3))
        surface.blit(crash_text, crash_rect)

    def _draw_start_signal(self, surface):
        signal_text = None
        signal_color = settings.WHITE

        if self.state == settings.COUNTDOWN:
            if self.countdown_timer > 2.0:
                signal_text = "3"
            elif self.countdown_timer > 1.0:
                signal_text = "2"
            else:
                signal_text = "1"
        elif self.go_timer > 0.0:
            signal_text = "GO!"
            signal_color = (92, 235, 116)

        if signal_text is None:
            return

        shadow = self.countdown_font.render(
            signal_text, True, settings.BLACK
        )
        text = self.countdown_font.render(
            signal_text, True, signal_color
        )
        text_rect = text.get_rect(
            center=(
                settings.SCREEN_WIDTH // 2,
                settings.SCREEN_HEIGHT // 2 - 55,
            )
        )
        surface.blit(shadow, text_rect.move(4, 4))
        surface.blit(text, text_rect)
