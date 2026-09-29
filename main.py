import pygame


# Window and timing settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
FPS = 60

# Road layout
ROAD_WIDTH = 510
ROAD_LEFT = (SCREEN_WIDTH - ROAD_WIDTH) // 2
ROAD_RIGHT = ROAD_LEFT + ROAD_WIDTH
LANE_WIDTH = ROAD_WIDTH // 3
EDGE_LINE_WIDTH = 6
LANE_LINE_WIDTH = 5
DASH_HEIGHT = 42
DASH_GAP = 34
ROAD_SCROLL_MULTIPLIER = 3.0

# Player layout and steering
PLAYER_BODY_WIDTH = 70
PLAYER_HEIGHT = 132
PLAYER_WHEEL_OVERHANG = 5
PLAYER_STEER_SPEED = 300  # Horizontal pixels per second.
PLAYER_START_X = SCREEN_WIDTH / 2
PLAYER_Y = SCREEN_HEIGHT - 172

# Speed and acceleration settings (temporary game-speed units)
MIN_SPEED = 0.0
MAX_SPEED = 180.0
ACCELERATION = 75.0
BRAKE_DECELERATION = 120.0
COAST_DECELERATION = 30.0

# Colors
TERRAIN_COLOR = (27, 67, 42)
TERRAIN_STRIPE_COLOR = (24, 61, 38)
ROAD_COLOR = (47, 49, 53)
ROAD_SHOULDER_COLOR = (65, 67, 70)
WHITE = (240, 240, 235)
BLACK = (18, 18, 20)
CAR_RED = (202, 42, 48)
CAR_RED_DARK = (145, 25, 31)
WINDOW_COLOR = (91, 145, 166)
WINDOW_HIGHLIGHT = (153, 199, 214)


def draw_terrain(surface):
    """Draw dark grass on both sides of the highway."""
    surface.fill(TERRAIN_COLOR)

    # Subtle stripes give the otherwise flat terrain a little visual depth.
    stripe_width = 24
    for x in range(0, ROAD_LEFT, stripe_width * 2):
        pygame.draw.rect(
            surface, TERRAIN_STRIPE_COLOR, (x, 0, stripe_width, SCREEN_HEIGHT)
        )
    for x in range(ROAD_RIGHT, SCREEN_WIDTH, stripe_width * 2):
        pygame.draw.rect(
            surface, TERRAIN_STRIPE_COLOR, (x, 0, stripe_width, SCREEN_HEIGHT)
        )


def draw_road(surface, dash_offset):
    """Draw the road, its solid edges, and its moving lane dividers."""
    pygame.draw.rect(surface, ROAD_SHOULDER_COLOR, (ROAD_LEFT - 12, 0, 12, SCREEN_HEIGHT))
    pygame.draw.rect(surface, ROAD_COLOR, (ROAD_LEFT, 0, ROAD_WIDTH, SCREEN_HEIGHT))
    pygame.draw.rect(surface, ROAD_SHOULDER_COLOR, (ROAD_RIGHT, 0, 12, SCREEN_HEIGHT))

    pygame.draw.line(
        surface, WHITE, (ROAD_LEFT, 0), (ROAD_LEFT, SCREEN_HEIGHT), EDGE_LINE_WIDTH
    )
    pygame.draw.line(
        surface, WHITE, (ROAD_RIGHT, 0), (ROAD_RIGHT, SCREEN_HEIGHT), EDGE_LINE_WIDTH
    )

    dash_cycle = DASH_HEIGHT + DASH_GAP
    for divider_number in (1, 2):
        divider_x = ROAD_LEFT + LANE_WIDTH * divider_number
        dash_y = -dash_cycle + dash_offset

        while dash_y < SCREEN_HEIGHT:
            pygame.draw.rect(
                surface,
                WHITE,
                (
                    divider_x - LANE_LINE_WIDTH // 2,
                    int(dash_y),
                    LANE_LINE_WIDTH,
                    DASH_HEIGHT,
                ),
            )
            dash_y += dash_cycle


def draw_player_car(surface, player_x, player_y):
    """Draw the top-down car at the supplied center-x and top-y position."""
    car_center_x = round(player_x)
    car_top = round(player_y)
    car_left = car_center_x - PLAYER_BODY_WIDTH // 2

    # Wheels sit slightly outside the body so they remain visible from above.
    wheel_width = 11
    wheel_height = 31
    for wheel_x in (
        car_left - PLAYER_WHEEL_OVERHANG,
        car_left + PLAYER_BODY_WIDTH - 6,
    ):
        pygame.draw.rect(
            surface,
            BLACK,
            (wheel_x, car_top + 22, wheel_width, wheel_height),
            border_radius=4,
        )
        pygame.draw.rect(
            surface,
            BLACK,
            (wheel_x, car_top + 88, wheel_width, wheel_height),
            border_radius=4,
        )

    # The tapered nose is at the top, showing the car's forward direction.
    body_points = [
        (car_center_x - 24, car_top),
        (car_center_x + 24, car_top),
        (car_left + PLAYER_BODY_WIDTH, car_top + 28),
        (car_left + PLAYER_BODY_WIDTH, car_top + PLAYER_HEIGHT - 12),
        (car_center_x + 25, car_top + PLAYER_HEIGHT),
        (car_center_x - 25, car_top + PLAYER_HEIGHT),
        (car_left, car_top + PLAYER_HEIGHT - 12),
        (car_left, car_top + 28),
    ]
    pygame.draw.polygon(surface, CAR_RED_DARK, body_points)
    pygame.draw.polygon(surface, CAR_RED, body_points, width=4)

    # Front windshield, side windows, and rear window form the cabin.
    pygame.draw.polygon(
        surface,
        WINDOW_COLOR,
        [
            (car_center_x - 22, car_top + 35),
            (car_center_x + 22, car_top + 35),
            (car_center_x + 27, car_top + 59),
            (car_center_x - 27, car_top + 59),
        ],
    )
    pygame.draw.line(
        surface,
        WINDOW_HIGHLIGHT,
        (car_center_x - 15, car_top + 39),
        (car_center_x + 12, car_top + 39),
        2,
    )
    pygame.draw.rect(
        surface,
        WINDOW_COLOR,
        (car_center_x - 27, car_top + 65, 20, 34),
        border_radius=3,
    )
    pygame.draw.rect(
        surface,
        WINDOW_COLOR,
        (car_center_x + 7, car_top + 65, 20, 34),
        border_radius=3,
    )
    pygame.draw.polygon(
        surface,
        WINDOW_COLOR,
        [
            (car_center_x - 26, car_top + 105),
            (car_center_x + 26, car_top + 105),
            (car_center_x + 20, car_top + 120),
            (car_center_x - 20, car_top + 120),
        ],
    )

    # Small headlights reinforce which end of the car faces forward.
    pygame.draw.rect(surface, (255, 236, 151), (car_left + 12, car_top + 8, 12, 6))
    pygame.draw.rect(surface, (255, 236, 151), (car_left + 46, car_top + 8, 12, 6))


def get_control_input():
    """Read continuous steering, acceleration, and braking input."""
    keys = pygame.key.get_pressed()

    steer_left = keys[pygame.K_a] or keys[pygame.K_LEFT]
    steer_right = keys[pygame.K_d] or keys[pygame.K_RIGHT]
    steering_direction = int(steer_right) - int(steer_left)

    accelerate_pressed = keys[pygame.K_w] or keys[pygame.K_UP]
    brake_pressed = keys[pygame.K_s] or keys[pygame.K_DOWN]

    return steering_direction, accelerate_pressed, brake_pressed


def update_player_speed(player_speed, accelerate_pressed, brake_pressed, delta_time):
    """Apply acceleration, braking, or natural coasting to player speed."""
    if accelerate_pressed and not brake_pressed:
        player_speed += ACCELERATION * delta_time
    elif brake_pressed and not accelerate_pressed:
        player_speed -= BRAKE_DECELERATION * delta_time
    elif not accelerate_pressed and not brake_pressed:
        player_speed -= COAST_DECELERATION * delta_time
    # If both are pressed, acceleration and braking cancel with no speed change.

    return max(MIN_SPEED, min(player_speed, MAX_SPEED))


def draw_hud(surface, title_font, label_font, control_font, player_speed):
    """Draw the temporary Step 3 labels, speed, and control hint."""
    panel = pygame.Surface((150, 88), pygame.SRCALPHA)
    panel.fill((10, 12, 14, 175))
    surface.blit(panel, (18, 18))

    title = title_font.render("2D RACING", True, WHITE)
    step_label = label_font.render("STEP 3", True, (190, 206, 196))
    speed_label = label_font.render(f"SPEED: {round(player_speed)}", True, WHITE)
    surface.blit(title, (30, 27))
    surface.blit(step_label, (30, 52))
    surface.blit(speed_label, (30, 75))

    control_text = "W/UP ACCELERATE   S/DOWN BRAKE   A/D OR LEFT/RIGHT STEER"
    control_hint = control_font.render(control_text, True, WHITE)
    hint_padding = 8
    hint_width = control_hint.get_width() + hint_padding * 2
    hint_panel = pygame.Surface(
        (hint_width, control_hint.get_height() + hint_padding * 2), pygame.SRCALPHA
    )
    hint_panel.fill((10, 12, 14, 150))
    hint_x = SCREEN_WIDTH - hint_width - 18
    surface.blit(hint_panel, (hint_x, 18))
    surface.blit(control_hint, (hint_x + hint_padding, 18 + hint_padding))


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("2D Racing Game")
    clock = pygame.time.Clock()

    title_font = pygame.font.Font(None, 29)
    label_font = pygame.font.Font(None, 22)
    control_font = pygame.font.Font(None, 18)

    running = True
    dash_offset = 0.0
    dash_cycle = DASH_HEIGHT + DASH_GAP
    player_x = PLAYER_START_X
    player_speed = MIN_SPEED

    # Include the wheel overhang when keeping the whole visible car on the road.
    player_half_width = PLAYER_BODY_WIDTH / 2 + PLAYER_WHEEL_OVERHANG
    player_min_x = ROAD_LEFT + player_half_width
    player_max_x = ROAD_RIGHT - player_half_width

    try:
        while running:
            # tick() caps the loop at 60 FPS and reports elapsed milliseconds.
            delta_time = clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            steering_direction, accelerate_pressed, brake_pressed = get_control_input()

            player_x += steering_direction * PLAYER_STEER_SPEED * delta_time
            player_x = max(player_min_x, min(player_x, player_max_x))

            player_speed = update_player_speed(
                player_speed, accelerate_pressed, brake_pressed, delta_time
            )

            # The car stays fixed vertically; road motion suggests forward speed.
            road_scroll_speed = player_speed * ROAD_SCROLL_MULTIPLIER
            dash_offset = (dash_offset + road_scroll_speed * delta_time) % dash_cycle

            draw_terrain(screen)
            draw_road(screen, dash_offset)
            draw_player_car(screen, player_x, PLAYER_Y)
            draw_hud(screen, title_font, label_font, control_font, player_speed)

            pygame.display.flip()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
