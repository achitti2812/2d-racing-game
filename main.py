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
RELATIVE_MOTION_SCALE = 1.25

# Player layout and steering
PLAYER_BODY_WIDTH = 70
PLAYER_HEIGHT = 132
PLAYER_WHEEL_OVERHANG = 5
PLAYER_STEER_SPEED = 300  # Horizontal pixels per second.
PLAYER_START_X = SCREEN_WIDTH / 2
PLAYER_Y = SCREEN_HEIGHT - 172

# Opponent car layout
OPPONENT_WIDTH = 62
OPPONENT_HEIGHT = 116

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


def draw_opponent_car(surface, opponent):
    """Draw a compact top-down race car with a rear wing and center stripe."""
    car_center_x = round(opponent["x"])
    car_top = round(opponent["y"])
    car_left = car_center_x - OPPONENT_WIDTH // 2
    body_color = opponent["color"]
    accent_color = opponent["accent_color"]

    # Four exposed wheels distinguish the rivals from the player's car.
    wheel_width = 9
    wheel_height = 25
    for wheel_x in (car_left - 4, car_left + OPPONENT_WIDTH - 5):
        pygame.draw.rect(
            surface,
            BLACK,
            (wheel_x, car_top + 20, wheel_width, wheel_height),
            border_radius=3,
        )
        pygame.draw.rect(
            surface,
            BLACK,
            (wheel_x, car_top + 74, wheel_width, wheel_height),
            border_radius=3,
        )

    body_points = [
        (car_center_x - 19, car_top),
        (car_center_x + 19, car_top),
        (car_left + OPPONENT_WIDTH, car_top + 24),
        (car_left + OPPONENT_WIDTH - 3, car_top + OPPONENT_HEIGHT - 13),
        (car_center_x + 22, car_top + OPPONENT_HEIGHT),
        (car_center_x - 22, car_top + OPPONENT_HEIGHT),
        (car_left + 3, car_top + OPPONENT_HEIGHT - 13),
        (car_left, car_top + 24),
    ]
    pygame.draw.polygon(surface, body_color, body_points)
    pygame.draw.polygon(surface, BLACK, body_points, width=2)

    # A racing stripe, dark cockpit, and rear wing create a distinct silhouette.
    pygame.draw.rect(
        surface,
        accent_color,
        (car_center_x - 4, car_top + 5, 8, OPPONENT_HEIGHT - 15),
    )
    pygame.draw.polygon(
        surface,
        WINDOW_COLOR,
        [
            (car_center_x - 19, car_top + 34),
            (car_center_x + 19, car_top + 34),
            (car_center_x + 23, car_top + 57),
            (car_center_x - 23, car_top + 57),
        ],
    )
    pygame.draw.polygon(
        surface,
        WINDOW_COLOR,
        [
            (car_center_x - 22, car_top + 64),
            (car_center_x + 22, car_top + 64),
            (car_center_x + 18, car_top + 83),
            (car_center_x - 18, car_top + 83),
        ],
    )
    pygame.draw.rect(
        surface,
        accent_color,
        (car_left - 3, car_top + OPPONENT_HEIGHT - 13, OPPONENT_WIDTH + 6, 7),
        border_radius=2,
    )
    pygame.draw.rect(surface, BLACK, (car_left - 3, car_top + 10, 10, 5))
    pygame.draw.rect(
        surface, BLACK, (car_left + OPPONENT_WIDTH - 7, car_top + 10, 10, 5)
    )


def create_opponents():
    """Create the three persistent rivals in a simple starting formation."""
    opponent_specs = [
        ("BLUE", 0, 445.0, 125.0, (45, 143, 207), (225, 240, 248)),
        ("GOLD", 1, 330.0, 155.0, (224, 164, 43), (75, 51, 14)),
        ("PURPLE", 2, 445.0, 140.0, (137, 83, 190), (236, 224, 247)),
    ]
    opponents = []

    for identifier, lane, start_y, speed, color, accent_color in opponent_specs:
        lane_center_x = ROAD_LEFT + LANE_WIDTH * (lane + 0.5)
        start_distance = (PLAYER_Y - start_y) / RELATIVE_MOTION_SCALE
        opponents.append(
            {
                "id": identifier,
                "lane": lane,
                "x": lane_center_x,
                "y": start_y,
                "speed": speed,
                "distance": start_distance,
                "color": color,
                "accent_color": accent_color,
            }
        )

    return opponents


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


def update_road(dash_offset, player_speed, delta_time):
    """Advance the repeating road markings according to player speed."""
    dash_cycle = DASH_HEIGHT + DASH_GAP
    road_scroll_speed = player_speed * ROAD_SCROLL_MULTIPLIER
    return (dash_offset + road_scroll_speed * delta_time) % dash_cycle


def update_race_distances(player_distance, player_speed, opponents, delta_time):
    """Advance every competitor's persistent logical race distance."""
    player_distance += player_speed * delta_time
    for opponent in opponents:
        opponent["distance"] += opponent["speed"] * delta_time
    return player_distance


def update_opponent_positions(opponents, player_distance):
    """Convert each rival's distance lead or deficit into a screen position."""
    for opponent in opponents:
        distance_difference = opponent["distance"] - player_distance
        opponent["y"] = PLAYER_Y - distance_difference * RELATIVE_MOTION_SCALE


def calculate_player_position(player_distance, opponents):
    """Return the player's temporary rank among all four race cars."""
    opponents_ahead = sum(
        opponent["distance"] > player_distance for opponent in opponents
    )
    return opponents_ahead + 1


def draw_hud(
    surface, title_font, label_font, control_font, player_speed, player_position
):
    """Draw the temporary Step 4 labels, speed, position, and control hint."""
    panel = pygame.Surface((165, 111), pygame.SRCALPHA)
    panel.fill((10, 12, 14, 175))
    surface.blit(panel, (18, 18))

    title = title_font.render("2D RACING", True, WHITE)
    step_label = label_font.render("STEP 4", True, (190, 206, 196))
    speed_label = label_font.render(f"SPEED: {round(player_speed)}", True, WHITE)
    position_label = label_font.render(
        f"POSITION: {player_position}/4", True, WHITE
    )
    surface.blit(title, (30, 27))
    surface.blit(step_label, (30, 52))
    surface.blit(speed_label, (30, 75))
    surface.blit(position_label, (30, 98))

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
    player_x = PLAYER_START_X
    player_speed = MIN_SPEED
    player_distance = 0.0
    opponents = create_opponents()

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

            dash_offset = update_road(dash_offset, player_speed, delta_time)
            player_distance = update_race_distances(
                player_distance, player_speed, opponents, delta_time
            )
            update_opponent_positions(opponents, player_distance)
            player_position = calculate_player_position(player_distance, opponents)

            draw_terrain(screen)
            draw_road(screen, dash_offset)
            for opponent in opponents:
                if -OPPONENT_HEIGHT - 20 <= opponent["y"] <= SCREEN_HEIGHT + 20:
                    draw_opponent_car(screen, opponent)
            draw_player_car(screen, player_x, PLAYER_Y)
            draw_hud(
                screen,
                title_font,
                label_font,
                control_font,
                player_speed,
                player_position,
            )

            pygame.display.flip()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
