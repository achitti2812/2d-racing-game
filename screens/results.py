"""Temporary race-results overlay."""

import pygame

from game import settings


def ordinal(position):
    """Return the ordinal label used by the four-racer results screen."""
    suffixes = {1: "st", 2: "nd", 3: "rd", 4: "th"}
    return f"{position}{suffixes.get(position, 'th')}"


def draw_results(
    surface,
    title_font,
    results_font,
    small_font,
    finishing_order,
    player_finish_position,
    player_finish_time,
    track_name,
    car_name,
):
    """Draw the complete finishing order and navigation prompts."""
    overlay = pygame.Surface(
        (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA
    )
    overlay.fill((5, 7, 9, 220))
    surface.blit(overlay, (0, 0))

    panel_rect = pygame.Rect(175, 75, 450, 550)
    pygame.draw.rect(surface, (24, 28, 32), panel_rect, border_radius=12)
    pygame.draw.rect(
        surface, settings.WHITE, panel_rect, width=2, border_radius=12
    )

    title = title_font.render("RACE COMPLETE", True, settings.WHITE)
    surface.blit(
        title,
        title.get_rect(center=(settings.SCREEN_WIDTH // 2, 125)),
    )

    track_text = small_font.render(
        f"TRACK: {track_name}", True, (190, 206, 196)
    )
    surface.blit(
        track_text,
        track_text.get_rect(center=(settings.SCREEN_WIDTH // 2, 158)),
    )

    car_text = small_font.render(
        f"CAR: {car_name}", True, (190, 206, 196)
    )
    surface.blit(
        car_text,
        car_text.get_rect(center=(settings.SCREEN_WIDTH // 2, 184)),
    )

    order_y = 225
    for index, racer_id in enumerate(finishing_order, start=1):
        color = (
            (255, 220, 92) if racer_id == "PLAYER" else settings.WHITE
        )
        order_text = results_font.render(
            f"{index}. {racer_id}", True, color
        )
        surface.blit(
            order_text,
            order_text.get_rect(
                center=(settings.SCREEN_WIDTH // 2, order_y)
            ),
        )
        order_y += 48

    finish_position_text = results_font.render(
        f"YOU FINISHED: {ordinal(player_finish_position)}",
        True,
        (255, 220, 92),
    )
    finish_time_text = results_font.render(
        f"YOUR TIME: {player_finish_time:.1f}s", True, settings.WHITE
    )
    restart_text = small_font.render(
        "R - Race Again", True, settings.WHITE
    )
    track_select_text = small_font.render(
        "T - Track Selection", True, settings.WHITE
    )
    car_select_text = small_font.render(
        "C - Car Selection", True, settings.WHITE
    )

    surface.blit(
        finish_position_text,
        finish_position_text.get_rect(
            center=(settings.SCREEN_WIDTH // 2, 435)
        ),
    )
    surface.blit(
        finish_time_text,
        finish_time_text.get_rect(
            center=(settings.SCREEN_WIDTH // 2, 480)
        ),
    )
    surface.blit(
        restart_text,
        restart_text.get_rect(center=(settings.SCREEN_WIDTH // 2, 535)),
    )
    surface.blit(
        track_select_text,
        track_select_text.get_rect(
            center=(settings.SCREEN_WIDTH // 2, 565)
        ),
    )
    surface.blit(
        car_select_text,
        car_select_text.get_rect(
            center=(settings.SCREEN_WIDTH // 2, 595)
        ),
    )
