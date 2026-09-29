"""Step 11 player-car definitions and central registry."""

from game.car import CarConfig


BALANCED_CAR = CarConfig(
    id="car_1",
    name="BALANCED",
    description="Predictable performance on every circuit.",
    body_color=(145, 25, 31),
    accent_color=(217, 53, 60),
    max_speed=180.0,
    acceleration=75.0,
    brake_deceleration=120.0,
    coast_deceleration=30.0,
    steering_speed=300.0,
    curve_pressure_multiplier=1.0,
    nitro_max_speed=220.0,
    nitro_acceleration=135.0,
    nitro_capacity=100.0,
    offroad_acceleration_multiplier=0.35,
    offroad_speed_limit=95.0,
    offroad_deceleration=70.0,
    speed_rating=3,
    acceleration_rating=3,
    handling_rating=3,
    nitro_rating=3,
)

SPEED_CAR = CarConfig(
    id="car_2",
    name="SPEED",
    description="Fast on straights; demanding in corners.",
    body_color=(28, 78, 145),
    accent_color=(61, 158, 232),
    max_speed=192.0,
    acceleration=68.0,
    brake_deceleration=112.0,
    coast_deceleration=26.0,
    steering_speed=270.0,
    curve_pressure_multiplier=1.18,
    nitro_max_speed=232.0,
    nitro_acceleration=122.0,
    nitro_capacity=95.0,
    offroad_acceleration_multiplier=0.30,
    offroad_speed_limit=88.0,
    offroad_deceleration=82.0,
    speed_rating=5,
    acceleration_rating=2,
    handling_rating=2,
    nitro_rating=4,
)

HANDLING_CAR = CarConfig(
    id="car_3",
    name="HANDLING",
    description="Agile in corners; lower maximum speed.",
    body_color=(27, 123, 69),
    accent_color=(75, 211, 119),
    max_speed=173.0,
    acceleration=86.0,
    brake_deceleration=132.0,
    coast_deceleration=34.0,
    steering_speed=340.0,
    curve_pressure_multiplier=0.76,
    nitro_max_speed=212.0,
    nitro_acceleration=150.0,
    nitro_capacity=105.0,
    offroad_acceleration_multiplier=0.43,
    offroad_speed_limit=105.0,
    offroad_deceleration=58.0,
    speed_rating=2,
    acceleration_rating=5,
    handling_rating=5,
    nitro_rating=3,
)


CARS = (BALANCED_CAR, SPEED_CAR, HANDLING_CAR)
CARS_BY_ID = {car.id: car for car in CARS}
