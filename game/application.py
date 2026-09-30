"""High-level profile, selection, race, and persistence coordination."""

from game import settings
from game.cars import CARS, CARS_BY_ID
from game.profile import PlayerProfile, create_default_profile
from game.race import Race
from game.save_manager import SaveDataError, SaveManager
from game.tracks import TRACKS
from screens.car_select import CarSelectScreen
from screens.profile_screen import ProfileScreen
from screens.profile_setup import ProfileSetupScreen
from screens.track_select import TrackSelectScreen


class GameApplication:
    """Own non-gameplay application state and commit progression once."""

    def __init__(self, save_manager=None):
        self.save_manager = save_manager or SaveManager()
        load_result = self.save_manager.load_profile()
        self.profile = load_result.profile
        self.profile_setup = ProfileSetupScreen(load_result.message)
        self.profile_screen = ProfileScreen()
        self.car_select = CarSelectScreen(CARS)
        self.track_select = TrackSelectScreen(TRACKS)
        self.selected_car = (
            CARS_BY_ID[self.profile.selected_car_id]
            if self.profile is not None
            else None
        )
        self.race = None
        self.race_result_committed = False
        self.progression_update = None
        self.persistence_message = ""
        self.state = (
            settings.PROFILE_SCREEN
            if self.profile is not None
            else settings.PROFILE_SETUP
        )

    def handle_event(self, event):
        if self.state == settings.PROFILE_SETUP:
            self._handle_profile_setup(event)
        elif self.state == settings.PROFILE_SCREEN:
            if self.profile_screen.handle_event(event):
                self.state = settings.CAR_SELECTION
        elif self.state == settings.CAR_SELECTION:
            self._handle_car_selection(event)
        elif self.state == settings.TRACK_SELECTION:
            self._handle_track_selection(event)
        elif self.state == settings.RACE_SCREEN and self.race is not None:
            self._handle_race_event(event)

    def update(self, delta_time):
        if self.state == settings.PROFILE_SETUP:
            self.profile_setup.update(delta_time)
        elif self.state == settings.CAR_SELECTION:
            self.car_select.update(delta_time)
        elif self.state == settings.TRACK_SELECTION:
            self.track_select.update(delta_time)
        elif self.state == settings.RACE_SCREEN and self.race is not None:
            self.race.update(delta_time)
            if (
                self.race.state == settings.FINISHED
                and not self.race_result_committed
            ):
                self._commit_race_result()

    def draw(self, surface):
        if self.state == settings.PROFILE_SETUP:
            self.profile_setup.draw(surface)
        elif self.state == settings.PROFILE_SCREEN:
            self.profile_screen.draw(surface, self.profile)
        elif self.state == settings.CAR_SELECTION:
            self.car_select.draw(surface, self.profile)
        elif self.state == settings.TRACK_SELECTION:
            self.track_select.draw(
                surface, self.selected_car, self.profile
            )
        elif self.race is not None:
            self.race.draw(
                surface,
                self.progression_update,
                self.persistence_message,
            )

    def _handle_profile_setup(self, event):
        player_name = self.profile_setup.handle_event(event)
        if player_name is None:
            return

        new_profile = create_default_profile(player_name)
        try:
            self.save_manager.save_profile(new_profile)
        except SaveDataError as error:
            self.profile_setup.message = str(error)
            return

        self.profile = new_profile
        self.selected_car = CARS_BY_ID[self.profile.selected_car_id]
        self.persistence_message = ""
        self.state = settings.PROFILE_SCREEN

    def _handle_car_selection(self, event):
        selected_car = self.car_select.handle_event(event, self.profile)
        if selected_car is None:
            return

        candidate = PlayerProfile.from_dict(self.profile.to_dict())
        candidate.select_car(selected_car.id)
        try:
            self.save_manager.save_profile(candidate)
        except SaveDataError as error:
            self.car_select.show_message(str(error), duration=3.0)
            return

        self.profile = candidate
        self.selected_car = selected_car
        self.persistence_message = ""
        self.state = settings.TRACK_SELECTION

    def _handle_track_selection(self, event):
        selected_track = self.track_select.handle_event(event, self.profile)
        if selected_track is None:
            return

        self.race = Race(selected_track, self.selected_car)
        self.race_result_committed = False
        self.progression_update = None
        self.persistence_message = ""
        self.state = settings.RACE_SCREEN

    def _handle_race_event(self, event):
        requested_state = self.race.handle_event(event)
        if requested_state == settings.RACE_RESTARTED:
            self.race_result_committed = False
            self.progression_update = None
            self.persistence_message = ""
        elif requested_state == settings.TRACK_SELECTION:
            self.race = None
            self.progression_update = None
            self.state = settings.TRACK_SELECTION
        elif requested_state == settings.CAR_SELECTION:
            self.race = None
            self.progression_update = None
            self.state = settings.CAR_SELECTION
        elif requested_state == settings.PROFILE_SCREEN:
            self.race = None
            self.progression_update = None
            self.state = settings.PROFILE_SCREEN

    def _commit_race_result(self):
        # Set the guard before mutation/save attempts so a failure cannot cause
        # the many results-screen frames to count the same race repeatedly.
        self.race_result_committed = True
        race_result = self.race.get_result()
        if race_result is None:
            return

        candidate = PlayerProfile.from_dict(self.profile.to_dict())
        try:
            progression_update = candidate.record_race(race_result)
        except ValueError as error:
            self.persistence_message = str(error)
            return

        self.profile = candidate
        self.progression_update = progression_update
        try:
            self.save_manager.save_profile(self.profile)
            self.persistence_message = ""
        except SaveDataError as error:
            self.persistence_message = str(error)
