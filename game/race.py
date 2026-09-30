"""Race coordination, state transitions, timing, HUD, and finish logic."""

import math
import random

import pygame

from game import settings
from game.collision import find_player_collision, handle_collision
from game.effects import draw_speed_streaks
from game.formatting import ordinal
from game.opponent import create_opponents
from game.player import Player
from game.road import Road
from game.race_result import RaceResult
from game.track import Track
from screens.results import draw_results
from ui.speedometer import draw_speedometer


class Race:
    """Coordinate the player, opponents, road, and current race flow."""

    def __init__(self, track_config, car_config, random_seed=None):
        self.track_config = track_config
        self.car_config = car_config
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
        self.track = Track(self.track_config)
        self.player = Player(self.car_config)
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
        self.finish_message_timer = 0.0
        self.displayed_speed = 0.0
        self._last_countdown_number = None
        self._presentation_events = []

    def handle_event(self, event):
        """Handle race-specific events; the application handles quitting."""
        if event.type != pygame.KEYDOWN or self.state != settings.FINISHED:
            return None
        if event.key == pygame.K_r:
            self.reset_race()
            return settings.RACE_RESTARTED
        elif event.key == pygame.K_t:
            return settings.TRACK_SELECTION
        elif event.key == pygame.K_c:
            return settings.CAR_SELECTION
        elif event.key == pygame.K_p:
            return settings.PROFILE_SCREEN
        elif event.key == pygame.K_m:
            return settings.MAIN_MENU
        return None

    def update(self, delta_time):
        if self.state == settings.COUNTDOWN:
            self._update_countdown(delta_time)
        elif self.state == settings.RACING:
            self._update_active_race(delta_time)
        self._update_speedometer(delta_time)

    def _update_speedometer(self, delta_time):
        """Smooth only the displayed needle without changing actual speed."""
        response = 1.0 - math.exp(-settings.SPEEDOMETER_RESPONSE * delta_time)
        self.displayed_speed += (
            self.player.speed - self.displayed_speed
        ) * response

    def _update_countdown(self, delta_time):
        self.countdown_timer = max(
            0.0, self.countdown_timer - delta_time
        )
        if self.countdown_timer <= 0.0:
            self.state = settings.RACING
            self.go_timer = settings.GO_DISPLAY_DURATION
            self._emit_presentation_event("go")
        else:
            countdown_number = max(1, math.ceil(self.countdown_timer))
            if countdown_number != self._last_countdown_number:
                if self._last_countdown_number is None:
                    self._emit_presentation_event("crowd_start")
                self._last_countdown_number = countdown_number
                self._emit_presentation_event("countdown")

    def _update_active_race(self, delta_time):
        frame_start_time = self.race_timer
        self.race_timer += delta_time
        self.go_timer = max(0.0, self.go_timer - delta_time)
        self.finish_message_timer = max(
            0.0, self.finish_message_timer - delta_time
        )
        self.player.update_collision_timers(delta_time)

        player_was_finished = self.player.finished
        if not player_was_finished:
            nitro_was_active = self.player.nitro_active
            self.player.update_controls(
                delta_time,
                self.track.get_center_x(self.player.distance),
                self.track.get_curve_strength(self.player.distance),
            )
            if self.player.nitro_active and not nitro_was_active:
                self._emit_presentation_event("nitro")
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
                self._emit_presentation_event("collision")
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
            if already_finished or new_distance < self.track.race_distance:
                continue

            distance_this_frame = new_distance - old_distance
            if distance_this_frame > 0.0:
                crossing_fraction = (
                    self.track.race_distance - old_distance
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
                self.player.distance = self.track.race_distance
                self.player.finish_time = crossing_time
                self.player.finish_position = finish_position
                self.player.collision_cooldown = 0.0
                self.player.crash_message_timer = 0.0
                self.finish_message_timer = settings.FINISH_MESSAGE_DURATION
                self._emit_presentation_event("finish")
            else:
                opponent = next(
                    car
                    for car in self.opponents
                    if car.identifier == racer_id
                )
                opponent.finished = True
                opponent.distance = self.track.race_distance
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
            min(self.player.distance / self.track.race_distance, 1.0),
        ) * 100.0

    @property
    def displayed_time(self):
        if self.player.finish_time is not None:
            return self.player.finish_time
        return self.race_timer

    @property
    def crowd_audio_intensity(self):
        return self.road.crowd_intensity_at(self.camera_distance)

    @property
    def tire_audio_intensity(self):
        speed_factor = max(0.0, min((self.player.speed - 120.0) / 90.0, 1.0))
        steering_effort = abs(self.player.steering_input)
        curve_load = min(abs(self.player.curve_force) / 90.0, 1.0)
        return speed_factor * max(steering_effort * 0.68, curve_load)

    def consume_presentation_events(self):
        """Return one-frame events for audio/visual presentation layers."""
        events = tuple(self._presentation_events)
        self._presentation_events.clear()
        return events

    def _emit_presentation_event(self, event_name):
        self._presentation_events.append(event_name)

    def get_result(self):
        """Expose immutable final gameplay data without persistence concerns."""
        if self.state != settings.FINISHED:
            return None
        return RaceResult(
            track_id=self.track_config.id,
            track_name=self.track_config.name,
            car_id=self.car_config.id,
            car_name=self.car_config.name,
            player_position=self.player.finish_position,
            player_time=self.player.finish_time,
            finishing_order=tuple(self.finishing_order),
        )

    def draw(
        self,
        surface,
        progression_update=None,
        persistence_message="",
    ):
        self.road.draw(surface, self.camera_distance)
        draw_speed_streaks(
            surface,
            self.player.speed,
            self.player.nitro_active,
            self.camera_distance,
        )
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
        if self.finish_message_timer > 0.0:
            self._draw_finish_message(surface)
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
                self.track.name,
                self.car_config.name,
                progression_update,
                persistence_message,
            )

    def _draw_hud(self, surface):
        left_panel = pygame.Surface((260, 98), pygame.SRCALPHA)
        left_panel.fill((8, 12, 16, 205))
        surface.blit(left_panel, (16, 16))
        pygame.draw.rect(surface, (70, 90, 102), (16, 16, 260, 98), 2)
        pygame.draw.line(surface, (66, 203, 231), (30, 16), (112, 16), 3)

        title = self.title_font.render("2D RACING", True, settings.WHITE)
        step_label = self.control_font.render(
            "STEP 14", True, (127, 218, 239)
        )
        track_label = self.label_font.render(
            self.track.name.upper(), True, (217, 224, 219)
        )
        car_label = self.control_font.render(
            f"CAR  {self.car_config.name.upper()}",
            True,
            self.car_config.accent_color,
        )
        surface.blit(title, (28, 25))
        surface.blit(step_label, (181, 31))
        surface.blit(track_label, (28, 58))
        surface.blit(car_label, (28, 86))

        right_panel = pygame.Surface((174, 116), pygame.SRCALPHA)
        right_panel.fill((8, 12, 16, 205))
        right_x = settings.SCREEN_WIDTH - 190
        surface.blit(right_panel, (right_x, 16))
        pygame.draw.rect(
            surface, (70, 90, 102), (right_x, 16, 174, 116), 2
        )
        pygame.draw.line(
            surface,
            (255, 218, 92),
            (right_x + 14, 16),
            (right_x + 76, 16),
            3,
        )
        position_value = self.results_font.render(
            f"{self.player_position} / 4", True, (255, 218, 92)
        )
        position_name = self.control_font.render(
            ordinal(self.player_position).upper(), True, (190, 206, 196)
        )
        progress_label = self.control_font.render(
            f"PROGRESS  {round(self.progress)}%", True, settings.WHITE
        )
        minutes = int(self.displayed_time // 60)
        seconds = self.displayed_time % 60
        time_label = self.control_font.render(
            f"TIME  {minutes:02d}:{seconds:04.1f}",
            True,
            settings.WHITE,
        )
        surface.blit(position_value, (right_x + 16, 25))
        surface.blit(position_name, (right_x + 119, 37))
        surface.blit(time_label, (right_x + 16, 78))
        surface.blit(progress_label, (right_x + 16, 101))
        progress_bar = pygame.Rect(right_x + 16, 122, 142, 4)
        pygame.draw.rect(surface, (45, 55, 62), progress_bar)
        pygame.draw.rect(
            surface,
            (72, 205, 231),
            (
                progress_bar.x,
                progress_bar.y,
                round(progress_bar.width * self.progress / 100.0),
                progress_bar.height,
            ),
        )

        draw_speedometer(
            surface,
            (12, settings.SCREEN_HEIGHT - 168),
            self.player.speed,
            self.displayed_speed,
            self.player.nitro_active,
        )

        nitro_panel = pygame.Surface((304, 58), pygame.SRCALPHA)
        nitro_panel.fill((8, 12, 16, 215))
        nitro_x = 290
        nitro_y = 16
        surface.blit(nitro_panel, (nitro_x, nitro_y))
        pygame.draw.rect(
            surface, (70, 90, 102), (nitro_x, nitro_y, 304, 58), 2
        )
        pygame.draw.line(
            surface,
            settings.NITRO_METER_ACTIVE,
            (nitro_x + 12, nitro_y),
            (nitro_x + 82, nitro_y),
            3,
        )
        nitro_status = "BOOST" if self.player.nitro_active else "NITRO"
        if self.player.nitro_amount <= 0.0:
            nitro_status = "NITRO - EMPTY"
        nitro_color = (
            settings.NITRO_METER_ACTIVE
            if self.player.nitro_active
            else settings.WHITE
        )
        nitro_label = self.label_font.render(nitro_status, True, nitro_color)
        surface.blit(nitro_label, (nitro_x + 14, nitro_y + 8))

        meter_rect = pygame.Rect(nitro_x + 120, nitro_y + 12, 168, 18)
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
                (
                    meter_rect.x + 2,
                    meter_rect.y + 2,
                    fill_width,
                    meter_rect.height - 4,
                ),
            )
        pygame.draw.rect(surface, settings.WHITE, meter_rect, width=2)

        nitro_hint = self.control_font.render(
            "W / UP + SPACE", True, (168, 186, 196)
        )
        surface.blit(nitro_hint, (nitro_x + 14, nitro_y + 35))

        pause_hint = self.control_font.render(
            "P / ESC  PAUSE", True, settings.WHITE
        )
        hint_x = settings.SCREEN_WIDTH - pause_hint.get_width() - 18
        surface.blit(pause_hint, (hint_x, settings.SCREEN_HEIGHT - 28))

        if (
            self.player.off_road
            and self.state == settings.RACING
            and not self.player.finished
        ):
            off_road_label = self.label_font.render(
                "OFF ROAD - TRACTION REDUCED", True, (255, 198, 82)
            )
            off_road_panel = pygame.Surface(
                (off_road_label.get_width() + 16, 27), pygame.SRCALPHA
            )
            off_road_panel.fill((35, 23, 10, 190))
            warning_x = (settings.SCREEN_WIDTH - off_road_panel.get_width()) // 2
            surface.blit(off_road_panel, (warning_x, 142))
            surface.blit(off_road_label, (warning_x + 8, 146))

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
        panel_y = 294
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

    def _draw_finish_message(self, surface):
        finish_text = self.crash_font.render(
            "FINISH!", True, (255, 221, 92)
        )
        finish_shadow = self.crash_font.render(
            "FINISH!", True, settings.BLACK
        )
        finish_rect = finish_text.get_rect(
            center=(settings.SCREEN_WIDTH // 2, 175)
        )
        surface.blit(finish_shadow, finish_rect.move(3, 3))
        surface.blit(finish_text, finish_rect)

    def _draw_start_signal(self, surface):
        signal_text = None
        signal_color = settings.WHITE
        pulse_progress = 0.0

        if self.state == settings.COUNTDOWN:
            if self.countdown_timer > 2.0:
                signal_text = "3"
                signal_color = (244, 119, 83)
            elif self.countdown_timer > 1.0:
                signal_text = "2"
                signal_color = (255, 190, 76)
            else:
                signal_text = "1"
                signal_color = (255, 232, 112)
            pulse_progress = 1.0 - (self.countdown_timer % 1.0)
        elif self.go_timer > 0.0:
            signal_text = "GO!"
            signal_color = (92, 235, 116)
            pulse_progress = 1.0 - (
                self.go_timer / settings.GO_DISPLAY_DURATION
            )

        if signal_text is None:
            return

        pulse_size = max(96, round(132 - pulse_progress * 25))
        pulse_font = pygame.font.Font(None, pulse_size)
        glow_radius = max(60, round(88 - pulse_progress * 18))
        glow = pygame.Surface(
            (glow_radius * 2, glow_radius * 2), pygame.SRCALPHA
        )
        pygame.draw.circle(
            glow,
            (*signal_color, 42),
            (glow_radius, glow_radius),
            glow_radius,
        )
        glow_center = (
            settings.SCREEN_WIDTH // 2,
            settings.SCREEN_HEIGHT // 2 - 55,
        )
        surface.blit(glow, glow.get_rect(center=glow_center))

        shadow = pulse_font.render(
            signal_text, True, settings.BLACK
        )
        text = pulse_font.render(
            signal_text, True, signal_color
        )
        text_rect = text.get_rect(
            center=glow_center
        )
        surface.blit(shadow, text_rect.move(4, 4))
        surface.blit(text, text_rect)
