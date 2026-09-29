import pygame


# Window and timing settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
FPS = 60

# Race states and timing
COUNTDOWN = "COUNTDOWN"
RACING = "RACING"
FINISHED = "FINISHED"
COUNTDOWN_DURATION = 3.0
GO_DISPLAY_DURATION = 0.8
RACE_DISTANCE = 9000.0
START_LINE_DISTANCE = 200.0
POST_FINISH_DECELERATION = 90.0

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

# Fair body-sized collision boxes exclude wheels and small decorations.
PLAYER_HITBOX_WIDTH = 56
PLAYER_HITBOX_HEIGHT = 118
OPPONENT_HITBOX_WIDTH = 50
OPPONENT_HITBOX_HEIGHT = 104
SHOW_HITBOXES = False

# Speed and acceleration settings (temporary game-speed units)
MIN_SPEED = 0.0
MAX_SPEED = 180.0
ACCELERATION = 75.0
BRAKE_DECELERATION = 120.0
COAST_DECELERATION = 30.0

# Arcade collision response
COLLISION_SPEED_RETENTION = 0.45
COLLISION_KNOCKBACK_DISTANCE = 58.0
COLLISION_COOLDOWN_DURATION = 1.25
CRASH_MESSAGE_DURATION = 0.8
PLAYER_FLASH_INTERVAL = 0.18

# Start/finish line appearance
CHECKER_SIZE = 15
CHECKER_ROWS = 2

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
CAR_FLASH_LIGHT = (255, 214, 214)
CAR_FLASH_OUTLINE = (255, 245, 245)


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


def draw_player_car(surface, player_x, player_y, is_flashing=False):
    """Draw the top-down car at the supplied center-x and top-y position."""
    car_center_x = round(player_x)
    car_top = round(player_y)
    car_left = car_center_x - PLAYER_BODY_WIDTH // 2
    body_fill_color = CAR_FLASH_LIGHT if is_flashing else CAR_RED_DARK
    body_outline_color = CAR_FLASH_OUTLINE if is_flashing else CAR_RED

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
    pygame.draw.polygon(surface, body_fill_color, body_points)
    pygame.draw.polygon(surface, body_outline_color, body_points, width=4)

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
                "finished": False,
                "finish_time": None,
                "finish_position": None,
            }
        )

    return opponents


def reset_race():
    """Create fresh race-specific state without reinitializing Pygame."""
    return {
        "state": COUNTDOWN,
        "player_x": PLAYER_START_X,
        "player_speed": MIN_SPEED,
        "player_distance": 0.0,
        "camera_distance": 0.0,
        "player_finished": False,
        "player_finish_time": None,
        "player_finish_position": None,
        "player_position": 4,
        "opponents": create_opponents(),
        "finishing_order": [],
        "race_timer": 0.0,
        "countdown_timer": COUNTDOWN_DURATION,
        "go_timer": 0.0,
        "dash_offset": 0.0,
        "collision_cooldown": 0.0,
        "crash_message_timer": 0.0,
    }


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


def update_race_distances(race, delta_time):
    """Advance unfinished racers and return their previous distances."""
    previous_distances = {"PLAYER": race["player_distance"]}
    for opponent in race["opponents"]:
        previous_distances[opponent["id"]] = opponent["distance"]

    if not race["player_finished"]:
        race["player_distance"] += race["player_speed"] * delta_time

    for opponent in race["opponents"]:
        if not opponent["finished"]:
            opponent["distance"] += opponent["speed"] * delta_time

    return previous_distances


def update_opponent_positions(opponents, camera_distance):
    """Convert each rival's distance lead or deficit into a screen position."""
    for opponent in opponents:
        distance_difference = opponent["distance"] - camera_distance
        opponent["y"] = PLAYER_Y - distance_difference * RELATIVE_MOTION_SCALE


def update_finish_status(race, previous_distances, frame_start_time, delta_time):
    """Record newly finished racers in interpolated, deterministic order."""
    finish_candidates = []
    tie_order = {"PLAYER": 0, "BLUE": 1, "PURPLE": 2, "GOLD": 3}

    racers = [
        (
            "PLAYER",
            race["player_finished"],
            race["player_distance"],
            previous_distances["PLAYER"],
        )
    ]
    racers.extend(
        (
            opponent["id"],
            opponent["finished"],
            opponent["distance"],
            previous_distances[opponent["id"]],
        )
        for opponent in race["opponents"]
    )

    for racer_id, already_finished, new_distance, previous_distance in racers:
        if already_finished or new_distance < RACE_DISTANCE:
            continue

        distance_this_frame = new_distance - previous_distance
        if distance_this_frame > 0.0:
            crossing_fraction = (RACE_DISTANCE - previous_distance) / distance_this_frame
            crossing_fraction = max(0.0, min(crossing_fraction, 1.0))
        else:
            crossing_fraction = 0.0
        crossing_time = frame_start_time + crossing_fraction * delta_time
        finish_candidates.append((crossing_time, tie_order[racer_id], racer_id))

    finish_candidates.sort()

    for crossing_time, _, racer_id in finish_candidates:
        finish_position = len(race["finishing_order"]) + 1
        race["finishing_order"].append(racer_id)

        if racer_id == "PLAYER":
            race["player_finished"] = True
            race["player_distance"] = RACE_DISTANCE
            race["player_finish_time"] = crossing_time
            race["player_finish_position"] = finish_position
            race["collision_cooldown"] = 0.0
            race["crash_message_timer"] = 0.0
        else:
            opponent = next(
                car for car in race["opponents"] if car["id"] == racer_id
            )
            opponent["finished"] = True
            opponent["distance"] = RACE_DISTANCE
            opponent["finish_time"] = crossing_time
            opponent["finish_position"] = finish_position

    if len(race["finishing_order"]) == 4:
        race["state"] = FINISHED


def calculate_player_position(race):
    """Calculate distance rank while preserving official finished positions."""
    if race["player_finished"]:
        return race["finishing_order"].index("PLAYER") + 1

    finished_opponents = len(race["finishing_order"])
    unfinished_opponents_ahead = sum(
        not opponent["finished"]
        and opponent["distance"] > race["player_distance"]
        for opponent in race["opponents"]
    )
    return finished_opponents + unfinished_opponents_ahead + 1


def get_visible_opponents(opponents):
    """Return unfinished rivals currently near the visible play area."""
    return [
        opponent
        for opponent in opponents
        if not opponent["finished"]
        and -OPPONENT_HEIGHT - 20 <= opponent["y"] <= SCREEN_HEIGHT + 20
    ]


def get_player_hitbox(player_x, player_y):
    """Return a fair collision rectangle centered within the player's body."""
    return pygame.Rect(
        round(player_x - PLAYER_HITBOX_WIDTH / 2),
        round(player_y + (PLAYER_HEIGHT - PLAYER_HITBOX_HEIGHT) / 2),
        PLAYER_HITBOX_WIDTH,
        PLAYER_HITBOX_HEIGHT,
    )


def get_opponent_hitbox(opponent):
    """Return a fair collision rectangle centered within an opponent's body."""
    return pygame.Rect(
        round(opponent["x"] - OPPONENT_HITBOX_WIDTH / 2),
        round(opponent["y"] + (OPPONENT_HEIGHT - OPPONENT_HITBOX_HEIGHT) / 2),
        OPPONENT_HITBOX_WIDTH,
        OPPONENT_HITBOX_HEIGHT,
    )


def handle_collision(
    player_speed, player_x, opponent, player_min_x, player_max_x
):
    """Apply the speed loss and a small horizontal push away from a rival."""
    player_speed *= COLLISION_SPEED_RETENTION
    player_speed = max(MIN_SPEED, min(player_speed, MAX_SPEED))

    if player_x < opponent["x"]:
        knockback_direction = -1
    elif player_x > opponent["x"]:
        knockback_direction = 1
    else:
        # For a centered impact, choose the direction with more available road.
        space_to_left = player_x - player_min_x
        space_to_right = player_max_x - player_x
        knockback_direction = -1 if space_to_left >= space_to_right else 1

    player_x += knockback_direction * COLLISION_KNOCKBACK_DISTANCE
    player_x = max(player_min_x, min(player_x, player_max_x))
    return player_speed, player_x


def update_countdown(race, delta_time):
    """Advance the non-blocking 3-2-1 timer and start active racing."""
    race["countdown_timer"] = max(0.0, race["countdown_timer"] - delta_time)
    if race["countdown_timer"] <= 0.0:
        race["state"] = RACING
        race["go_timer"] = GO_DISPLAY_DURATION


def update_active_race(race, delta_time, player_min_x, player_max_x):
    """Update controls, race progress, finishes, collisions, and road motion."""
    frame_start_time = race["race_timer"]
    race["race_timer"] += delta_time
    race["go_timer"] = max(0.0, race["go_timer"] - delta_time)
    race["collision_cooldown"] = max(
        0.0, race["collision_cooldown"] - delta_time
    )
    race["crash_message_timer"] = max(
        0.0, race["crash_message_timer"] - delta_time
    )

    player_was_finished = race["player_finished"]
    if not player_was_finished:
        steering_direction, accelerate_pressed, brake_pressed = get_control_input()
        race["player_x"] += steering_direction * PLAYER_STEER_SPEED * delta_time
        race["player_x"] = max(
            player_min_x, min(race["player_x"], player_max_x)
        )
        race["player_speed"] = update_player_speed(
            race["player_speed"],
            accelerate_pressed,
            brake_pressed,
            delta_time,
        )
    else:
        # After finishing, coast the camera and road smoothly to a stop.
        race["player_speed"] = max(
            MIN_SPEED,
            race["player_speed"] - POST_FINISH_DECELERATION * delta_time,
        )
        race["camera_distance"] += race["player_speed"] * delta_time

    previous_distances = update_race_distances(race, delta_time)

    if not player_was_finished:
        # Follow the player's progress. Any crossing overshoot lets the line pass
        # just behind the car before post-finish camera coasting takes over.
        race["camera_distance"] = race["player_distance"]

    update_finish_status(race, previous_distances, frame_start_time, delta_time)
    update_opponent_positions(race["opponents"], race["camera_distance"])
    race["player_position"] = calculate_player_position(race)

    if race["state"] == RACING and not race["player_finished"]:
        player_hitbox = get_player_hitbox(race["player_x"], PLAYER_Y)
        for opponent in get_visible_opponents(race["opponents"]):
            if race["collision_cooldown"] > 0.0:
                break
            if player_hitbox.colliderect(get_opponent_hitbox(opponent)):
                race["player_speed"], race["player_x"] = handle_collision(
                    race["player_speed"],
                    race["player_x"],
                    opponent,
                    player_min_x,
                    player_max_x,
                )
                race["collision_cooldown"] = COLLISION_COOLDOWN_DURATION
                race["crash_message_timer"] = CRASH_MESSAGE_DURATION
                break

    race["dash_offset"] = update_road(
        race["dash_offset"], race["player_speed"], delta_time
    )


def draw_hud(
    surface,
    title_font,
    label_font,
    control_font,
    player_speed,
    player_position,
    progress,
    elapsed_time,
):
    """Draw the temporary Step 6 race information and control hint."""
    panel = pygame.Surface((175, 157), pygame.SRCALPHA)
    panel.fill((10, 12, 14, 175))
    surface.blit(panel, (18, 18))

    title = title_font.render("2D RACING", True, WHITE)
    step_label = label_font.render("STEP 6", True, (190, 206, 196))
    speed_label = label_font.render(f"SPEED: {round(player_speed)}", True, WHITE)
    position_label = label_font.render(
        f"POSITION: {player_position}/4", True, WHITE
    )
    progress_label = label_font.render(f"PROGRESS: {round(progress)}%", True, WHITE)
    minutes = int(elapsed_time // 60)
    seconds = elapsed_time % 60
    time_label = label_font.render(
        f"TIME: {minutes:02d}:{seconds:04.1f}", True, WHITE
    )
    surface.blit(title, (30, 27))
    surface.blit(step_label, (30, 52))
    surface.blit(speed_label, (30, 75))
    surface.blit(position_label, (30, 98))
    surface.blit(progress_label, (30, 121))
    surface.blit(time_label, (30, 144))

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


def draw_crash_message(surface, crash_font):
    """Draw a short, high-contrast crash notification."""
    crash_text = crash_font.render("CRASH!", True, (255, 82, 72))
    crash_shadow = crash_font.render("CRASH!", True, BLACK)
    crash_rect = crash_text.get_rect(center=(SCREEN_WIDTH // 2, 165))
    surface.blit(crash_shadow, crash_rect.move(3, 3))
    surface.blit(crash_text, crash_rect)


def world_distance_to_screen_y(world_distance, camera_distance):
    """Convert a fixed world distance into its current vertical screen position."""
    return PLAYER_Y - (world_distance - camera_distance) * RELATIVE_MOTION_SCALE


def draw_checkered_line(surface, center_y):
    """Draw a two-row black-and-white line across the drivable road."""
    line_height = CHECKER_SIZE * CHECKER_ROWS
    line_top = round(center_y - line_height / 2)
    if line_top > SCREEN_HEIGHT or line_top + line_height < 0:
        return

    column_count = (ROAD_WIDTH + CHECKER_SIZE - 1) // CHECKER_SIZE
    for row in range(CHECKER_ROWS):
        for column in range(column_count):
            square_x = ROAD_LEFT + column * CHECKER_SIZE
            square_width = min(CHECKER_SIZE, ROAD_RIGHT - square_x)
            square_color = WHITE if (row + column) % 2 == 0 else BLACK
            pygame.draw.rect(
                surface,
                square_color,
                (
                    square_x,
                    line_top + row * CHECKER_SIZE,
                    square_width,
                    CHECKER_SIZE,
                ),
            )

    pygame.draw.rect(
        surface, WHITE, (ROAD_LEFT, line_top, ROAD_WIDTH, line_height), width=1
    )


def draw_race_lines(surface, camera_distance):
    """Draw the start and finish lines only while near the camera."""
    start_line_y = world_distance_to_screen_y(
        START_LINE_DISTANCE, camera_distance
    )
    finish_line_y = world_distance_to_screen_y(RACE_DISTANCE, camera_distance)
    draw_checkered_line(surface, start_line_y)
    draw_checkered_line(surface, finish_line_y)


def draw_start_signal(surface, countdown_font, race):
    """Draw 3-2-1 during setup and a short GO message after racing starts."""
    signal_text = None
    signal_color = WHITE

    if race["state"] == COUNTDOWN:
        if race["countdown_timer"] > 2.0:
            signal_text = "3"
        elif race["countdown_timer"] > 1.0:
            signal_text = "2"
        else:
            signal_text = "1"
    elif race["go_timer"] > 0.0:
        signal_text = "GO!"
        signal_color = (92, 235, 116)

    if signal_text is None:
        return

    shadow = countdown_font.render(signal_text, True, BLACK)
    text = countdown_font.render(signal_text, True, signal_color)
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 55))
    surface.blit(shadow, text_rect.move(4, 4))
    surface.blit(text, text_rect)


def ordinal(position):
    """Return the ordinal label used by the four-racer results screen."""
    suffixes = {1: "st", 2: "nd", 3: "rd", 4: "th"}
    return f"{position}{suffixes.get(position, 'th')}"


def draw_results(surface, results_title_font, results_font, small_font, race):
    """Draw the temporary complete finishing order and restart prompt."""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((5, 7, 9, 220))
    surface.blit(overlay, (0, 0))

    panel_rect = pygame.Rect(175, 75, 450, 550)
    pygame.draw.rect(surface, (24, 28, 32), panel_rect, border_radius=12)
    pygame.draw.rect(surface, WHITE, panel_rect, width=2, border_radius=12)

    title = results_title_font.render("RACE COMPLETE", True, WHITE)
    surface.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 125)))

    order_y = 205
    for index, racer_id in enumerate(race["finishing_order"], start=1):
        color = (255, 220, 92) if racer_id == "PLAYER" else WHITE
        order_text = results_font.render(f"{index}. {racer_id}", True, color)
        surface.blit(order_text, order_text.get_rect(center=(SCREEN_WIDTH // 2, order_y)))
        order_y += 48

    finish_position_text = results_font.render(
        f"YOU FINISHED: {ordinal(race['player_finish_position'])}",
        True,
        (255, 220, 92),
    )
    finish_time_text = results_font.render(
        f"YOUR TIME: {race['player_finish_time']:.1f}s", True, WHITE
    )
    restart_text = small_font.render("Press R to Race Again", True, WHITE)

    surface.blit(
        finish_position_text,
        finish_position_text.get_rect(center=(SCREEN_WIDTH // 2, 435)),
    )
    surface.blit(
        finish_time_text,
        finish_time_text.get_rect(center=(SCREEN_WIDTH // 2, 480)),
    )
    surface.blit(
        restart_text,
        restart_text.get_rect(center=(SCREEN_WIDTH // 2, 560)),
    )


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("2D Racing Game")
    clock = pygame.time.Clock()

    title_font = pygame.font.Font(None, 29)
    label_font = pygame.font.Font(None, 22)
    control_font = pygame.font.Font(None, 18)
    crash_font = pygame.font.Font(None, 52)
    countdown_font = pygame.font.Font(None, 110)
    results_title_font = pygame.font.Font(None, 54)
    results_font = pygame.font.Font(None, 34)
    results_small_font = pygame.font.Font(None, 26)

    running = True
    race = reset_race()

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
                elif (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_r
                    and race["state"] == FINISHED
                ):
                    race = reset_race()

            if not running:
                break

            if race["state"] == COUNTDOWN:
                update_countdown(race, delta_time)
            elif race["state"] == RACING:
                update_active_race(race, delta_time, player_min_x, player_max_x)

            visible_opponents = get_visible_opponents(race["opponents"])
            player_hitbox = get_player_hitbox(race["player_x"], PLAYER_Y)
            opponent_hitboxes = [
                (opponent, get_opponent_hitbox(opponent))
                for opponent in visible_opponents
            ]

            draw_terrain(screen)
            draw_road(screen, race["dash_offset"])
            draw_race_lines(screen, race["camera_distance"])
            for opponent in visible_opponents:
                draw_opponent_car(screen, opponent)

            is_flashing = (
                race["collision_cooldown"] > 0.0
                and int(race["collision_cooldown"] / PLAYER_FLASH_INTERVAL) % 2
                == 0
            )
            draw_player_car(
                screen, race["player_x"], PLAYER_Y, is_flashing
            )

            if SHOW_HITBOXES:
                pygame.draw.rect(screen, (80, 255, 130), player_hitbox, 2)
                for _, opponent_hitbox in opponent_hitboxes:
                    pygame.draw.rect(screen, (255, 194, 73), opponent_hitbox, 2)

            progress = max(
                0.0, min(race["player_distance"] / RACE_DISTANCE, 1.0)
            ) * 100.0
            displayed_time = (
                race["player_finish_time"]
                if race["player_finish_time"] is not None
                else race["race_timer"]
            )
            draw_hud(
                screen,
                title_font,
                label_font,
                control_font,
                race["player_speed"],
                race["player_position"],
                progress,
                displayed_time,
            )
            if race["crash_message_timer"] > 0.0:
                draw_crash_message(screen, crash_font)
            draw_start_signal(screen, countdown_font, race)

            if race["state"] == FINISHED:
                draw_results(
                    screen,
                    results_title_font,
                    results_font,
                    results_small_font,
                    race,
                )

            pygame.display.flip()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
