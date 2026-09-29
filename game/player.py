"""Player car state, controls, movement, drawing, and hitbox."""

import pygame

from game import settings


class Player:
    """The human-controlled race car."""

    def __init__(self):
        self.x = settings.PLAYER_START_X
        self.y = settings.PLAYER_Y
        self.speed = settings.MIN_SPEED
        self.distance = 0.0
        self.finished = False
        self.finish_time = None
        self.finish_position = None
        self.collision_cooldown = 0.0
        self.crash_message_timer = 0.0
        self.nitro_capacity = settings.NITRO_CAPACITY
        self.nitro_amount = self.nitro_capacity
        self.nitro_active = False
        self.nitro_recharge_delay = 0.0

    @property
    def min_x(self):
        half_width = (
            settings.PLAYER_BODY_WIDTH / 2 + settings.PLAYER_WHEEL_OVERHANG
        )
        return settings.ROAD_LEFT + half_width

    @property
    def max_x(self):
        half_width = (
            settings.PLAYER_BODY_WIDTH / 2 + settings.PLAYER_WHEEL_OVERHANG
        )
        return settings.ROAD_RIGHT - half_width

    def get_control_input(self):
        """Read continuous steering, acceleration, and braking input."""
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

    def update_controls(self, delta_time):
        """Apply held controls using the existing frame-independent behavior."""
        (
            steering_direction,
            accelerate_pressed,
            brake_pressed,
            nitro_pressed,
        ) = self.get_control_input()

        self.x += steering_direction * settings.PLAYER_STEER_SPEED * delta_time
        self.x = max(self.min_x, min(self.x, self.max_x))

        self.nitro_active = (
            accelerate_pressed
            and nitro_pressed
            and not brake_pressed
            and self.nitro_amount > 0.0
        )

        # Braking takes priority over both normal acceleration and nitro.
        if brake_pressed:
            self.speed -= settings.BRAKE_DECELERATION * delta_time
        elif self.nitro_active:
            self.speed += settings.NITRO_ACCELERATION * delta_time
            self.speed = min(self.speed, settings.NITRO_MAX_SPEED)
        elif accelerate_pressed:
            if self.speed > settings.PLAYER_MAX_SPEED:
                self.speed = max(
                    settings.PLAYER_MAX_SPEED,
                    self.speed
                    - settings.NITRO_OVERSPEED_DECELERATION * delta_time,
                )
            else:
                self.speed = min(
                    settings.PLAYER_MAX_SPEED,
                    self.speed + settings.ACCELERATION * delta_time,
                )
        elif self.speed > settings.PLAYER_MAX_SPEED:
            self.speed = max(
                settings.PLAYER_MAX_SPEED,
                self.speed
                - settings.NITRO_OVERSPEED_DECELERATION * delta_time,
            )
        else:
            self.speed -= settings.COAST_DECELERATION * delta_time

        self.speed = max(
            settings.MIN_SPEED, min(self.speed, settings.NITRO_MAX_SPEED)
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
            # Holding Space on its own cannot propel, drain, or recharge.
            if self.nitro_recharge_delay <= 0.0 and not nitro_pressed:
                self.nitro_amount = min(
                    self.nitro_capacity,
                    self.nitro_amount
                    + settings.NITRO_RECHARGE_RATE * delta_time,
                )

    def stop_nitro(self):
        """Immediately disable boost without changing the remaining amount."""
        self.nitro_active = False

    def update_collision_timers(self, delta_time):
        self.collision_cooldown = max(
            0.0, self.collision_cooldown - delta_time
        )
        self.crash_message_timer = max(
            0.0, self.crash_message_timer - delta_time
        )

    def coast_after_finish(self, delta_time):
        """Slow the post-finish camera motion without accepting controls."""
        self.speed = max(
            settings.MIN_SPEED,
            self.speed - settings.POST_FINISH_DECELERATION * delta_time,
        )

    def get_hitbox(self):
        """Return a fair collision rectangle centered within the car body."""
        return pygame.Rect(
            round(self.x - settings.PLAYER_HITBOX_WIDTH / 2),
            round(
                self.y
                + (settings.PLAYER_HEIGHT - settings.PLAYER_HITBOX_HEIGHT) / 2
            ),
            settings.PLAYER_HITBOX_WIDTH,
            settings.PLAYER_HITBOX_HEIGHT,
        )

    def _draw_nitro_exhaust(self, surface, car_center_x, car_top):
        """Draw simple twin exhaust flames behind the car while boosting."""
        exhaust_y = car_top + settings.PLAYER_HEIGHT - 2
        for horizontal_offset in (-18, 18):
            exhaust_x = car_center_x + horizontal_offset
            pygame.draw.polygon(
                surface,
                settings.NITRO_BLUE,
                [
                    (exhaust_x - 6, exhaust_y),
                    (exhaust_x + 6, exhaust_y),
                    (exhaust_x + 3, exhaust_y + 20),
                    (exhaust_x, exhaust_y + 30),
                    (exhaust_x - 3, exhaust_y + 20),
                ],
            )
            pygame.draw.polygon(
                surface,
                settings.NITRO_CYAN,
                [
                    (exhaust_x - 3, exhaust_y),
                    (exhaust_x + 3, exhaust_y),
                    (exhaust_x + 1, exhaust_y + 13),
                    (exhaust_x, exhaust_y + 21),
                    (exhaust_x - 1, exhaust_y + 13),
                ],
            )

    def draw(self, surface):
        """Draw the existing top-down player car design."""
        is_flashing = (
            self.collision_cooldown > 0.0
            and int(
                self.collision_cooldown / settings.PLAYER_FLASH_INTERVAL
            )
            % 2
            == 0
        )
        car_center_x = round(self.x)
        car_top = round(self.y)
        car_left = car_center_x - settings.PLAYER_BODY_WIDTH // 2
        body_fill_color = (
            settings.CAR_FLASH_LIGHT if is_flashing else settings.CAR_RED_DARK
        )
        body_outline_color = (
            settings.CAR_FLASH_OUTLINE if is_flashing else settings.CAR_RED
        )

        if self.nitro_active:
            self._draw_nitro_exhaust(surface, car_center_x, car_top)

        wheel_width = 11
        wheel_height = 31
        for wheel_x in (
            car_left - settings.PLAYER_WHEEL_OVERHANG,
            car_left + settings.PLAYER_BODY_WIDTH - 6,
        ):
            pygame.draw.rect(
                surface,
                settings.BLACK,
                (wheel_x, car_top + 22, wheel_width, wheel_height),
                border_radius=4,
            )
            pygame.draw.rect(
                surface,
                settings.BLACK,
                (wheel_x, car_top + 88, wheel_width, wheel_height),
                border_radius=4,
            )

        body_points = [
            (car_center_x - 24, car_top),
            (car_center_x + 24, car_top),
            (car_left + settings.PLAYER_BODY_WIDTH, car_top + 28),
            (
                car_left + settings.PLAYER_BODY_WIDTH,
                car_top + settings.PLAYER_HEIGHT - 12,
            ),
            (car_center_x + 25, car_top + settings.PLAYER_HEIGHT),
            (car_center_x - 25, car_top + settings.PLAYER_HEIGHT),
            (car_left, car_top + settings.PLAYER_HEIGHT - 12),
            (car_left, car_top + 28),
        ]
        pygame.draw.polygon(surface, body_fill_color, body_points)
        pygame.draw.polygon(surface, body_outline_color, body_points, width=4)

        pygame.draw.polygon(
            surface,
            settings.WINDOW_COLOR,
            [
                (car_center_x - 22, car_top + 35),
                (car_center_x + 22, car_top + 35),
                (car_center_x + 27, car_top + 59),
                (car_center_x - 27, car_top + 59),
            ],
        )
        pygame.draw.line(
            surface,
            settings.WINDOW_HIGHLIGHT,
            (car_center_x - 15, car_top + 39),
            (car_center_x + 12, car_top + 39),
            2,
        )
        pygame.draw.rect(
            surface,
            settings.WINDOW_COLOR,
            (car_center_x - 27, car_top + 65, 20, 34),
            border_radius=3,
        )
        pygame.draw.rect(
            surface,
            settings.WINDOW_COLOR,
            (car_center_x + 7, car_top + 65, 20, 34),
            border_radius=3,
        )
        pygame.draw.polygon(
            surface,
            settings.WINDOW_COLOR,
            [
                (car_center_x - 26, car_top + 105),
                (car_center_x + 26, car_top + 105),
                (car_center_x + 20, car_top + 120),
                (car_center_x - 20, car_top + 120),
            ],
        )

        pygame.draw.rect(
            surface,
            (255, 236, 151),
            (car_left + 12, car_top + 8, 12, 6),
        )
        pygame.draw.rect(
            surface,
            (255, 236, 151),
            (car_left + 46, car_top + 8, 12, 6),
        )
