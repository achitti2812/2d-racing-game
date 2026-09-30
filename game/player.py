"""Player controls, unchanged arcade physics, and polished rotated rendering."""

import pygame

from game import settings


class Player:
    """The human-controlled race car."""

    def __init__(self, car_config):
        self.car_config = car_config
        self.x = settings.PLAYER_START_X
        self.y = settings.PLAYER_Y
        self.speed = settings.MIN_SPEED
        self.distance = 0.0
        self.finished = False
        self.finish_time = None
        self.finish_position = None
        self.collision_cooldown = 0.0
        self.crash_message_timer = 0.0
        self.nitro_capacity = car_config.nitro_capacity
        self.nitro_amount = self.nitro_capacity
        self.nitro_active = False
        self.nitro_recharge_delay = 0.0
        self.track_center_x = settings.PLAYER_START_X
        self.curve_strength = 0.0
        self.curve_force = 0.0
        self.off_road = False
        self.steering_input = 0
        self.throttle_requested = False
        self.braking = False
        self.visual_steer_angle = 0.0
        self.visual_steer_target = 0.0
        self._update_track_limits(self.track_center_x)

    @property
    def car_half_width(self):
        return settings.PLAYER_BODY_WIDTH / 2 + settings.PLAYER_WHEEL_OVERHANG

    def _update_track_limits(self, track_center_x):
        half_road_width = settings.ROAD_WIDTH / 2
        self.road_min_x = track_center_x - half_road_width + self.car_half_width
        self.road_max_x = track_center_x + half_road_width - self.car_half_width
        self.outer_min_x = self.road_min_x - settings.OFF_ROAD_OUTER_MARGIN
        self.outer_max_x = self.road_max_x + settings.OFF_ROAD_OUTER_MARGIN

    def sync_track_state(self, track_center_x, curve_strength):
        self.track_center_x = track_center_x
        self.curve_strength = curve_strength
        self._update_track_limits(track_center_x)
        self.x = max(self.min_x, min(self.x, self.max_x))
        self.off_road = (
            self.x < self.road_min_x - settings.OFF_ROAD_TOLERANCE
            or self.x > self.road_max_x + settings.OFF_ROAD_TOLERANCE
        )

    @property
    def min_x(self):
        return self.outer_min_x

    @property
    def max_x(self):
        return self.outer_max_x

    def get_control_input(self):
        keys = pygame.key.get_pressed()
        steer_left = keys[pygame.K_a] or keys[pygame.K_LEFT]
        steer_right = keys[pygame.K_d] or keys[pygame.K_RIGHT]
        steering_direction = int(steer_right) - int(steer_left)
        accelerate_pressed = keys[pygame.K_w] or keys[pygame.K_UP]
        brake_pressed = keys[pygame.K_s] or keys[pygame.K_DOWN]
        nitro_pressed = keys[pygame.K_SPACE]
        return (
            steering_direction,
            accelerate_pressed,
            brake_pressed,
            nitro_pressed,
        )

    def update_controls(self, delta_time, track_center_x, curve_strength):
        """Apply the existing physics plus visual-only steering orientation."""
        (
            steering_direction,
            accelerate_pressed,
            brake_pressed,
            nitro_pressed,
        ) = self.get_control_input()
        self.steering_input = steering_direction
        self.throttle_requested = accelerate_pressed and not brake_pressed
        self.braking = brake_pressed

        self.sync_track_state(track_center_x, curve_strength)
        self.x += (
            steering_direction
            * self.car_config.steering_speed
            * delta_time
        )

        self.curve_force = (
            -curve_strength
            * self.speed
            * self.speed
            * settings.CURVE_FORCE_MULTIPLIER
            * self.car_config.curve_pressure_multiplier
        )
        self.x += self.curve_force * delta_time
        self.sync_track_state(track_center_x, curve_strength)

        self.nitro_active = (
            accelerate_pressed
            and nitro_pressed
            and not brake_pressed
            and not self.off_road
            and self.nitro_amount > 0.0
        )

        if brake_pressed:
            self.speed -= self.car_config.brake_deceleration * delta_time
        elif self.nitro_active:
            self.speed += self.car_config.nitro_acceleration * delta_time
            self.speed = min(self.speed, self.car_config.nitro_max_speed)
        elif accelerate_pressed:
            acceleration = self.car_config.acceleration
            if self.off_road:
                acceleration *= self.car_config.offroad_acceleration_multiplier
            if self.speed > self.car_config.max_speed:
                self.speed = max(
                    self.car_config.max_speed,
                    self.speed
                    - settings.NITRO_OVERSPEED_DECELERATION * delta_time,
                )
            else:
                self.speed = min(
                    self.car_config.max_speed,
                    self.speed + acceleration * delta_time,
                )
        elif self.speed > self.car_config.max_speed:
            self.speed = max(
                self.car_config.max_speed,
                self.speed
                - settings.NITRO_OVERSPEED_DECELERATION * delta_time,
            )
        else:
            self.speed -= self.car_config.coast_deceleration * delta_time

        self.speed = max(
            settings.MIN_SPEED,
            min(self.speed, self.car_config.nitro_max_speed),
        )
        if self.off_road and self.speed > self.car_config.offroad_speed_limit:
            self.speed = max(
                self.car_config.offroad_speed_limit,
                self.speed
                - self.car_config.offroad_deceleration * delta_time,
            )

        if self.nitro_active:
            self.nitro_amount = max(
                0.0,
                self.nitro_amount - settings.NITRO_DRAIN_RATE * delta_time,
            )
            self.nitro_recharge_delay = settings.NITRO_RECHARGE_DELAY
            if self.nitro_amount <= 0.0:
                self.nitro_active = False
        else:
            self.nitro_recharge_delay = max(
                0.0, self.nitro_recharge_delay - delta_time
            )
            if self.nitro_recharge_delay <= 0.0 and not nitro_pressed:
                self.nitro_amount = min(
                    self.nitro_capacity,
                    self.nitro_amount
                    + settings.NITRO_RECHARGE_RATE * delta_time,
                )

        self.update_visual_steering(steering_direction, delta_time)

    def update_visual_steering(self, steering_direction, delta_time):
        """Smooth a speed-scaled visual angle without changing the hitbox."""
        speed_factor = min(
            1.0, self.speed / settings.VISUAL_STEER_FULL_SPEED
        )
        self.visual_steer_target = (
            -steering_direction
            * settings.MAX_VISUAL_STEER_ANGLE
            * speed_factor
        )
        max_change = settings.VISUAL_STEER_RESPONSE * delta_time
        difference = self.visual_steer_target - self.visual_steer_angle
        if abs(difference) <= max_change:
            self.visual_steer_angle = self.visual_steer_target
        else:
            self.visual_steer_angle += max_change * (
                1.0 if difference > 0.0 else -1.0
            )

    def stop_nitro(self):
        self.nitro_active = False

    def update_collision_timers(self, delta_time):
        self.collision_cooldown = max(
            0.0, self.collision_cooldown - delta_time
        )
        self.crash_message_timer = max(
            0.0, self.crash_message_timer - delta_time
        )

    def coast_after_finish(self, delta_time):
        self.speed = max(
            settings.MIN_SPEED,
            self.speed - settings.POST_FINISH_DECELERATION * delta_time,
        )
        self.steering_input = 0
        self.throttle_requested = False
        self.braking = False
        self.update_visual_steering(0, delta_time)

    def get_hitbox(self):
        return pygame.Rect(
            round(self.x - settings.PLAYER_HITBOX_WIDTH / 2),
            round(
                self.y
                + (settings.PLAYER_HEIGHT - settings.PLAYER_HITBOX_HEIGHT) / 2
            ),
            settings.PLAYER_HITBOX_WIDTH,
            settings.PLAYER_HITBOX_HEIGHT,
        )

    def draw(self, surface):
        """Draw to a local surface, then rotate around the physical center."""
        is_flashing = (
            self.collision_cooldown > 0.0
            and int(
                self.collision_cooldown / settings.PLAYER_FLASH_INTERVAL
            )
            % 2
            == 0
        )
        car_surface = pygame.Surface((130, 210), pygame.SRCALPHA)
        self._draw_local_car(car_surface, is_flashing)
        rotated = pygame.transform.rotozoom(
            car_surface, self.visual_steer_angle, 1.0
        )
        physical_center = (
            round(self.x),
            round(self.y + settings.PLAYER_HEIGHT / 2),
        )
        surface.blit(rotated, rotated.get_rect(center=physical_center))

    def _draw_local_car(self, surface, is_flashing):
        center_x = surface.get_width() // 2
        top = 39
        left = center_x - settings.PLAYER_BODY_WIDTH // 2
        body_fill = (
            settings.CAR_FLASH_LIGHT
            if is_flashing
            else self.car_config.body_color
        )
        accent = (
            settings.CAR_FLASH_OUTLINE
            if is_flashing
            else self.car_config.accent_color
        )

        if self.nitro_active:
            self._draw_local_nitro(surface, center_x, top)

        shadow = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.ellipse(
            shadow,
            (0, 0, 0, 105),
            (left - 7, top + 9, settings.PLAYER_BODY_WIDTH + 18, 132),
        )
        surface.blit(shadow, (4, 5))

        for wheel_x in (
            left - settings.PLAYER_WHEEL_OVERHANG,
            left + settings.PLAYER_BODY_WIDTH - 6,
        ):
            for wheel_y in (top + 22, top + 88):
                pygame.draw.rect(
                    surface,
                    (10, 12, 14),
                    (wheel_x, wheel_y, 11, 31),
                    border_radius=4,
                )

        body_points = (
            (center_x - 24, top),
            (center_x + 24, top),
            (left + settings.PLAYER_BODY_WIDTH, top + 28),
            (left + settings.PLAYER_BODY_WIDTH, top + 120),
            (center_x + 25, top + settings.PLAYER_HEIGHT),
            (center_x - 25, top + settings.PLAYER_HEIGHT),
            (left, top + 120),
            (left, top + 28),
        )
        pygame.draw.polygon(surface, body_fill, body_points)
        pygame.draw.polygon(surface, accent, body_points, width=4)
        pygame.draw.line(
            surface, self._lighten(body_fill), body_points[0], body_points[7], 2
        )

        pygame.draw.rect(
            surface, accent, (center_x - 4, top + 5, 8, 25), border_radius=2
        )
        pygame.draw.rect(
            surface, accent, (center_x - 4, top + 103, 8, 21), border_radius=2
        )
        pygame.draw.polygon(
            surface,
            settings.WINDOW_COLOR,
            (
                (center_x - 22, top + 35),
                (center_x + 22, top + 35),
                (center_x + 27, top + 59),
                (center_x - 27, top + 59),
            ),
        )
        pygame.draw.line(
            surface,
            settings.WINDOW_HIGHLIGHT,
            (center_x - 15, top + 39),
            (center_x + 12, top + 39),
            2,
        )
        pygame.draw.rect(
            surface,
            settings.WINDOW_COLOR,
            (center_x - 27, top + 65, 20, 34),
            border_radius=3,
        )
        pygame.draw.rect(
            surface,
            settings.WINDOW_COLOR,
            (center_x + 7, top + 65, 20, 34),
            border_radius=3,
        )
        pygame.draw.polygon(
            surface,
            (68, 112, 132),
            (
                (center_x - 26, top + 105),
                (center_x + 26, top + 105),
                (center_x + 20, top + 120),
                (center_x - 20, top + 120),
            ),
        )
        for light_x in (left + 12, left + 46):
            pygame.draw.rect(surface, (255, 238, 158), (light_x, top + 8, 12, 6))
            pygame.draw.rect(surface, (239, 66, 55), (light_x, top + 119, 12, 6))

    def _draw_local_nitro(self, surface, center_x, top):
        exhaust_y = top + settings.PLAYER_HEIGHT - 2
        for horizontal_offset in (-18, 18):
            exhaust_x = center_x + horizontal_offset
            pygame.draw.polygon(
                surface,
                settings.NITRO_BLUE,
                (
                    (exhaust_x - 7, exhaust_y),
                    (exhaust_x + 7, exhaust_y),
                    (exhaust_x + 3, exhaust_y + 25),
                    (exhaust_x, exhaust_y + 39),
                    (exhaust_x - 3, exhaust_y + 25),
                ),
            )
            pygame.draw.polygon(
                surface,
                settings.NITRO_CYAN,
                (
                    (exhaust_x - 3, exhaust_y),
                    (exhaust_x + 3, exhaust_y),
                    (exhaust_x, exhaust_y + 28),
                ),
            )

    @staticmethod
    def _lighten(color):
        return tuple(min(255, channel + 45) for channel in color)
