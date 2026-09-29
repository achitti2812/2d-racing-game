"""Player-versus-opponent collision checks and arcade response."""

from game import settings


def find_player_collision(player, opponents):
    """Return the first opponent whose current hitbox overlaps the player."""
    player_hitbox = player.get_hitbox()
    for opponent in opponents:
        if player_hitbox.colliderect(opponent.get_hitbox()):
            return opponent
    return None


def handle_collision(player, opponent):
    """Apply the unchanged speed loss, knockback, and protection timers."""
    player.speed *= settings.COLLISION_SPEED_RETENTION
    player.speed = max(
        settings.MIN_SPEED,
        min(player.speed, player.car_config.max_speed),
    )

    if player.x < opponent.x:
        knockback_direction = -1
    elif player.x > opponent.x:
        knockback_direction = 1
    else:
        space_to_left = player.x - player.min_x
        space_to_right = player.max_x - player.x
        knockback_direction = -1 if space_to_left >= space_to_right else 1

    player.x += knockback_direction * settings.COLLISION_KNOCKBACK_DISTANCE
    player.x = max(player.min_x, min(player.x, player.max_x))
    player.collision_cooldown = settings.COLLISION_COOLDOWN_DURATION
    player.crash_message_timer = settings.CRASH_MESSAGE_DURATION
