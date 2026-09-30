"""Immutable completed-race data exposed to progression code."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RaceResult:
    track_id: str
    track_name: str
    car_id: str
    car_name: str
    player_position: int
    player_time: float
    finishing_order: tuple
