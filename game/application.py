"""High-level menus, settings, pause, race, and persistence coordination."""

import random

import pygame

from game import settings
from game.audio import AudioManager
from game.cars import CARS, CARS_BY_ID
from game.profile import PlayerProfile, create_default_profile
from game.race import Race
from game.save_manager import SaveDataError, SaveManager
from game.settings_manager import SettingsDataError, SettingsManager
from game.tracks import TRACKS
from screens import main_menu, pause_menu
from screens.car_select import CarSelectScreen
from screens.main_menu import MainMenuScreen
from screens.pause_menu import PauseMenuScreen
from screens.profile_screen import ProfileScreen
from screens.profile_setup import ProfileSetupScreen
from screens.settings import BACK, CHANGED, MOVE, SettingsScreen
from screens.track_select import TrackSelectScreen


class GameApplication:
    """Own application state while keeping gameplay and persistence separate."""

    def __init__(
        self,
        save_manager=None,
        settings_manager=None,
        audio_manager=None,
    ):
        self.save_manager = save_manager or SaveManager()
        profile_load = self.save_manager.load_profile()
        self.profile = profile_load.profile

        self.settings_manager = settings_manager or SettingsManager()
        settings_load = self.settings_manager.load_settings()
        self.user_settings = settings_load.settings
        self.settings_message = settings_load.message
        self.audio = audio_manager or AudioManager(self.user_settings)
        self.audio.set_user_settings(self.user_settings)

        self.profile_setup = ProfileSetupScreen(profile_load.message)
        self.main_menu = MainMenuScreen()
        self.profile_screen = ProfileScreen()
        self.car_select = CarSelectScreen(CARS)
        self.track_select = TrackSelectScreen(TRACKS)
        self.pause_menu = PauseMenuScreen()
        self.settings_screen = SettingsScreen()

        self.selected_car = (
            CARS_BY_ID[self.profile.selected_car_id]
            if self.profile is not None
            else None
        )
        self.race = None
        self.race_result_committed = False
        self.progression_update = None
        self.persistence_message = ""
        self.settings_return_state = settings.MAIN_MENU
        self.screen_shake_timer = 0.0
        self.screen_shake_amplitude = 0
        self._shake_random = random.Random()
        self._race_surface = pygame.Surface(
            (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
        )
        self._fps_font = pygame.font.Font(None, 19)
        self.quit_requested = False
        self.state = (
            settings.MAIN_MENU
            if self.profile is not None
            else settings.PROFILE_SETUP
        )

    def handle_event(self, event):
        if self.state == settings.PROFILE_SETUP:
            self._handle_profile_setup(event)
        elif self.state == settings.MAIN_MENU:
            self._handle_main_menu(event)
        elif self.state == settings.PROFILE_SCREEN:
            if self.profile_screen.handle_event(event) == settings.MAIN_MENU:
                self.audio.play_sfx("menu_select")
                self.state = settings.MAIN_MENU
        elif self.state == settings.CAR_SELECTION:
            self._handle_car_selection(event)
        elif self.state == settings.TRACK_SELECTION:
            self._handle_track_selection(event)
        elif self.state == settings.RACE_SCREEN and self.race is not None:
            self._handle_race_event(event)
        elif self.state == settings.PAUSED and self.race is not None:
            self._handle_pause_event(event)
        elif self.state == settings.SETTINGS_SCREEN:
            self._handle_settings_event(event)

    def update(self, delta_time):
        if self.state == settings.PROFILE_SETUP:
            self.profile_setup.update(delta_time)
        elif self.state == settings.CAR_SELECTION:
            self.car_select.update(delta_time)
        elif self.state == settings.TRACK_SELECTION:
            self.track_select.update(delta_time)
        elif self.state == settings.RACE_SCREEN and self.race is not None:
            self.race.update(delta_time)
            self._process_race_presentation_events()
            self.screen_shake_timer = max(
                0.0, self.screen_shake_timer - delta_time
            )
            if (
                self.race.state == settings.FINISHED
                and not self.race_result_committed
            ):
                self._commit_race_result()

    def draw(self, surface, current_fps=0.0):
        if self.state == settings.PROFILE_SETUP:
            self.profile_setup.draw(surface)
        elif self.state == settings.MAIN_MENU:
            self.main_menu.draw(surface, self.profile)
        elif self.state == settings.PROFILE_SCREEN:
            self.profile_screen.draw(surface, self.profile)
        elif self.state == settings.CAR_SELECTION:
            self.car_select.draw(surface, self.profile)
        elif self.state == settings.TRACK_SELECTION:
            self.track_select.draw(surface, self.selected_car, self.profile)
        elif self.state == settings.SETTINGS_SCREEN:
            self.settings_screen.draw(
                surface, self.user_settings, self.settings_message
            )
        elif self.state in (settings.RACE_SCREEN, settings.PAUSED):
            self._draw_race(surface)
            if self.state == settings.PAUSED:
                self.pause_menu.draw(surface)

        if self.user_settings.show_fps:
            self._draw_fps(surface, current_fps)

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
        self.audio.play_sfx("menu_select")
        self.state = settings.MAIN_MENU

    def _handle_main_menu(self, event):
        action = self.main_menu.handle_event(event)
        if action == main_menu.MOVE:
            self.audio.play_sfx("menu_move")
        elif action == main_menu.CONTINUE:
            self.audio.play_sfx("menu_select")
            self.state = settings.CAR_SELECTION
        elif action == main_menu.OPEN_PROFILE:
            self.audio.play_sfx("menu_select")
            self.state = settings.PROFILE_SCREEN
        elif action == main_menu.OPEN_SETTINGS:
            self.audio.play_sfx("menu_select")
            self._open_settings(settings.MAIN_MENU)
        elif action == main_menu.QUIT:
            self.audio.play_sfx("menu_select")
            self.quit_requested = True

    def _handle_car_selection(self, event):
        selected_car = self.car_select.handle_event(event, self.profile)
        if selected_car == settings.MAIN_MENU:
            self.audio.play_sfx("menu_select")
            self.state = settings.MAIN_MENU
            return
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
        self.audio.play_sfx("menu_select")
        self.state = settings.TRACK_SELECTION

    def _handle_track_selection(self, event):
        selected_track = self.track_select.handle_event(event, self.profile)
        if selected_track == settings.CAR_SELECTION:
            self.audio.play_sfx("menu_select")
            self.state = settings.CAR_SELECTION
            return
        if selected_track is None:
            return

        self.race = Race(selected_track, self.selected_car)
        self.race_result_committed = False
        self.progression_update = None
        self.persistence_message = ""
        self.screen_shake_timer = 0.0
        self.audio.play_sfx("menu_select")
        self.state = settings.RACE_SCREEN

    def _handle_race_event(self, event):
        if (
            self.race.state != settings.FINISHED
            and event.type == pygame.KEYDOWN
            and event.key in (pygame.K_p, pygame.K_ESCAPE)
        ):
            self.pause_menu.reset_selection()
            self.audio.play_sfx("menu_select")
            self.state = settings.PAUSED
            return

        requested_state = self.race.handle_event(event)
        if requested_state is None:
            return
        self.audio.play_sfx("menu_select")
        if requested_state == settings.RACE_RESTARTED:
            self.race_result_committed = False
            self.progression_update = None
            self.persistence_message = ""
            self.screen_shake_timer = 0.0
        elif requested_state == settings.TRACK_SELECTION:
            self._discard_race(settings.TRACK_SELECTION)
        elif requested_state == settings.CAR_SELECTION:
            self._discard_race(settings.CAR_SELECTION)
        elif requested_state == settings.PROFILE_SCREEN:
            self._discard_race(settings.PROFILE_SCREEN)
        elif requested_state == settings.MAIN_MENU:
            self._discard_race(settings.MAIN_MENU)

    def _handle_pause_event(self, event):
        action = self.pause_menu.handle_event(event)
        if action == pause_menu.MOVE:
            self.audio.play_sfx("menu_move")
        elif action == pause_menu.RESUME:
            self.audio.play_sfx("menu_select")
            self.state = settings.RACE_SCREEN
        elif action == pause_menu.RESTART:
            self.audio.play_sfx("menu_select")
            self.race.reset_race()
            self.race_result_committed = False
            self.progression_update = None
            self.persistence_message = ""
            self.screen_shake_timer = 0.0
            self.state = settings.RACE_SCREEN
        elif action == pause_menu.OPEN_SETTINGS:
            self.audio.play_sfx("menu_select")
            self._open_settings(settings.PAUSED)
        elif action == pause_menu.QUIT_TO_MENU:
            self.audio.play_sfx("menu_select")
            self._discard_race(settings.MAIN_MENU)

    def _open_settings(self, return_state):
        self.settings_return_state = return_state
        self.state = settings.SETTINGS_SCREEN

    def _handle_settings_event(self, event):
        action = self.settings_screen.handle_event(event, self.user_settings)
        if action == MOVE:
            self.audio.play_sfx("menu_move")
        elif action == CHANGED:
            self.audio.set_user_settings(self.user_settings)
            if not self.user_settings.screen_shake:
                self.screen_shake_timer = 0.0
            try:
                self.settings_manager.save_settings(self.user_settings)
                self.settings_message = ""
            except SettingsDataError as error:
                self.settings_message = str(error)
            self.audio.play_sfx("menu_select")
        elif action == BACK:
            self.audio.play_sfx("menu_select")
            self.state = self.settings_return_state

    def _discard_race(self, destination):
        self.race = None
        self.progression_update = None
        self.persistence_message = ""
        self.screen_shake_timer = 0.0
        self.state = destination

    def _process_race_presentation_events(self):
        for event_name in self.race.consume_presentation_events():
            self.audio.play_sfx(event_name)
            if event_name == "collision" and self.user_settings.screen_shake:
                self.screen_shake_timer = settings.COLLISION_SHAKE_DURATION
                self.screen_shake_amplitude = settings.COLLISION_SHAKE_AMPLITUDE

    def _commit_race_result(self):
        # Guard first: results may be drawn for hundreds of frames or revisited.
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

        if progression_update.new_unlock_names:
            self.audio.play_sfx("unlock")

    def _draw_race(self, surface):
        self.race.draw(
            self._race_surface,
            self.progression_update,
            self.persistence_message,
        )
        offset_x = 0
        offset_y = 0
        if (
            self.state == settings.RACE_SCREEN
            and self.user_settings.screen_shake
            and self.screen_shake_timer > 0.0
        ):
            offset_x = self._shake_random.randint(
                -self.screen_shake_amplitude, self.screen_shake_amplitude
            )
            offset_y = self._shake_random.randint(
                -self.screen_shake_amplitude, self.screen_shake_amplitude
            )
        surface.fill((5, 7, 9))
        surface.blit(self._race_surface, (offset_x, offset_y))

    def _draw_fps(self, surface, current_fps):
        fps_text = self._fps_font.render(
            f"FPS {round(current_fps)}", True, (175, 233, 190)
        )
        panel = pygame.Surface(
            (fps_text.get_width() + 12, fps_text.get_height() + 8),
            pygame.SRCALPHA,
        )
        panel.fill((7, 10, 12, 205))
        x = settings.SCREEN_WIDTH - panel.get_width() - 8
        surface.blit(panel, (x, 8))
        surface.blit(fps_text, (x + 6, 12))
