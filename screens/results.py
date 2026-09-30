"""Temporary race-results and progression overlay."""

import pygame

from game import settings
from game.formatting import ordinal


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
    progression_update=None,
    persistence_message="",
):
    """Draw race results, records, unlocks, and navigation prompts."""
    overlay = pygame.Surface(
        (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA
    )
    overlay.fill((5, 7, 9, 220))
    surface.blit(overlay, (0, 0))

    panel_rect = pygame.Rect(130, 30, 540, 640)
    pygame.draw.rect(surface, (24, 28, 32), panel_rect, border_radius=12)
    pygame.draw.rect(
        surface, settings.WHITE, panel_rect, width=2, border_radius=12
    )

    title = title_font.render("RACE COMPLETE", True, settings.WHITE)
    surface.blit(
        title,
        title.get_rect(center=(settings.SCREEN_WIDTH // 2, 72)),
    )

    track_text = small_font.render(
        f"TRACK: {track_name}", True, (190, 206, 196)
    )
    car_text = small_font.render(
        f"CAR: {car_name}", True, (190, 206, 196)
    )
    surface.blit(
        track_text,
        track_text.get_rect(center=(settings.SCREEN_WIDTH // 2, 108)),
    )
    surface.blit(
        car_text,
        car_text.get_rect(center=(settings.SCREEN_WIDTH // 2, 133)),
    )

    order_y = 168
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
        order_y += 38

    finish_position_text = results_font.render(
        f"YOU FINISHED: {ordinal(player_finish_position)}",
        True,
        (255, 220, 92),
    )
    finish_time_text = results_font.render(
        f"YOUR TIME: {player_finish_time:.2f}s", True, settings.WHITE
    )
    best_time = (
        progression_update.best_time
        if progression_update is not None
        else player_finish_time
    )
    best_time_text = small_font.render(
        f"BEST TIME: {best_time:.2f}s", True, (190, 206, 196)
    )
    surface.blit(
        finish_position_text,
        finish_position_text.get_rect(
            center=(settings.SCREEN_WIDTH // 2, 337)
        ),
    )
    surface.blit(
        finish_time_text,
        finish_time_text.get_rect(
            center=(settings.SCREEN_WIDTH // 2, 374)
        ),
    )
    surface.blit(
        best_time_text,
        best_time_text.get_rect(center=(settings.SCREEN_WIDTH // 2, 407)),
    )

    if progression_update is not None and progression_update.new_best_time:
        new_best_text = small_font.render(
            "NEW BEST!", True, (100, 226, 147)
        )
        surface.blit(
            new_best_text,
            new_best_text.get_rect(center=(settings.SCREEN_WIDTH // 2, 434)),
        )

    if progression_update is not None and progression_update.new_unlock_names:
        unlock_title = small_font.render(
            "NEW UNLOCKS!", True, (255, 214, 89)
        )
        surface.blit(
            unlock_title,
            unlock_title.get_rect(center=(settings.SCREEN_WIDTH // 2, 462)),
        )
        for index, unlock_name in enumerate(
            progression_update.new_unlock_names
        ):
            unlock_text = small_font.render(
                unlock_name, True, settings.WHITE
            )
            surface.blit(
                unlock_text,
                unlock_text.get_rect(
                    center=(settings.SCREEN_WIDTH // 2, 487 + index * 24)
                ),
            )

    if persistence_message:
        save_error = small_font.render(
            "SAVE ERROR - progress is not persisted", True, (246, 126, 112)
        )
        surface.blit(
            save_error,
            save_error.get_rect(center=(settings.SCREEN_WIDTH // 2, 528)),
        )

    controls = (
        ("R - Race Again", 548),
        ("T - Track Selection", 571),
        ("C - Car Selection", 594),
        ("P - Profile", 617),
        ("M - Main Menu", 640),
    )
    for control_text, control_y in controls:
        rendered = small_font.render(
            control_text, True, settings.WHITE
        )
        surface.blit(
            rendered,
            rendered.get_rect(center=(settings.SCREEN_WIDTH // 2, control_y)),
        )
