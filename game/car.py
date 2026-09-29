"""Player-car configuration model."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CarConfig:
    """Immutable driving, visual, and presentation data for one player car."""

    id: str
    name: str
    description: str
    body_color: tuple
    accent_color: tuple
    max_speed: float
    acceleration: float
    brake_deceleration: float
    coast_deceleration: float
    steering_speed: float
    curve_pressure_multiplier: float
    nitro_max_speed: float
    nitro_acceleration: float
    nitro_capacity: float
    offroad_acceleration_multiplier: float
    offroad_speed_limit: float
    offroad_deceleration: float
    speed_rating: int
    acceleration_rating: int
    handling_rating: int
    nitro_rating: int

    def __post_init__(self):
        positive_values = (
            self.max_speed,
            self.acceleration,
            self.brake_deceleration,
            self.coast_deceleration,
            self.steering_speed,
            self.curve_pressure_multiplier,
            self.nitro_max_speed,
            self.nitro_acceleration,
            self.nitro_capacity,
            self.offroad_acceleration_multiplier,
            self.offroad_speed_limit,
            self.offroad_deceleration,
        )
        if any(value <= 0.0 for value in positive_values):
            raise ValueError("All car performance values must be positive.")
        if self.nitro_max_speed <= self.max_speed:
            raise ValueError("Nitro maximum speed must exceed normal speed.")

        ratings = (
            self.speed_rating,
            self.acceleration_rating,
            self.handling_rating,
            self.nitro_rating,
        )
        if any(rating < 1 or rating > 5 for rating in ratings):
            raise ValueError("Car display ratings must be between 1 and 5.")
