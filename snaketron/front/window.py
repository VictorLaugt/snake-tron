from __future__ import annotations

from itertools import chain
from typing import TYPE_CHECKING

from front.controls import (KeyBoardControls, PlayerSwipeControl,
                            SwipeControlZone)
from front.world_display import SnakeColors, WorldColors
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import get_color_from_hex, platform

if TYPE_CHECKING:
    from typing import Sequence

    from back.agent import (AbstractAISnakeAgent, AbstractSnakeAgent,
                            PlayerSnakeAgent)
    from back.world import SnakeWorld
    from kivy.clock import ClockEvent
    from kivy.uix.widget import Widget


MINIMAL_TIME_STEP = 0.01


class SnakeTronWindow(BoxLayout):
    app_background_color = ListProperty(get_color_from_hex('#000000'))

    world: SnakeWorld
    player_agents: Sequence[PlayerSnakeAgent]
    swipe_zones: list[SwipeControlZone]
    swipe_controls: list[PlayerSwipeControl]
    keyboard_controls: list[KeyBoardControls]
    paused: bool
    full_speed: bool
    ai_explanations: bool
    regular_time_step: float
    time_step: float
    clock_event: ClockEvent

    def on_kv_post(self, base_widget: Widget) -> None:
        self.swipe_zones = []
        for child in self.children:
            if isinstance(child, SwipeControlZone):
                self.swipe_zones.append(child)

        if platform in ('linux', 'win', 'macosx'):
            screen_width, screen_height = Window.system_size
            width, height = int(432/891 * screen_height), screen_height
            scale = screen_width / width
            if scale < 1:
                width, height = int(width * scale), int(height * scale)
            Window.size = (width, height)


    def init_logic(
        self,
        world: SnakeWorld,
        player_agents: Sequence[PlayerSnakeAgent],
        ai_agents: Sequence[AbstractAISnakeAgent],
        time_step: float,
        ai_explanations: bool,
        colors: dict
    ) -> None:
        # link to the backend
        self.world = world
        self.player_agents = player_agents
        self.world.reset()

        # game speed
        self.paused = False
        self.full_speed = False
        self.ai_explanations = ai_explanations
        self.regular_time_step = time_step
        self.time_step = time_step

        # colors
        self.app_background_color = get_color_from_hex(colors['ui']['background'])
        swipe_zone_bg_color = get_color_from_hex(colors['ui']['swipe_zone_bg_color'])

        agent_colors = {}
        head_color_wheel = colors['snakes']['head_color_wheel']
        tail_color_wheel = colors['snakes']['tail_color_wheel']
        agents: list[AbstractSnakeAgent] = list(chain(player_agents, ai_agents))
        for a in agents:
            agent_id = a.get_id()
            agent_colors[agent_id] = SnakeColors(
                head=get_color_from_hex(head_color_wheel[agent_id % len(head_color_wheel)]),
                tail=get_color_from_hex(tail_color_wheel[agent_id % len(tail_color_wheel)]),
                dead=get_color_from_hex(colors['snakes']['dead']),
                inspect=get_color_from_hex(colors['snakes']['inspect'])
            )

        world_colors = WorldColors(
            food_outline=get_color_from_hex(colors['world']['food_outline']),
            food=get_color_from_hex(colors['world']['food']),
            background=get_color_from_hex(colors['world']['background']),
            gridline=get_color_from_hex(colors['world']['gridline']),
            gridborder=get_color_from_hex(colors['world']['gridborder'])
        )
        self.ids.world_display.init_logic(world, ai_agents, world_colors, agent_colors)
        self.ids.score_board.init_logic(agents, agent_colors)

        # player keyboard inputs
        keyboard_control_sets = (
            ('up', 'left', 'down', 'right'),
            ('z', 'q', 's', 'd'),
            ('i', 'j', 'k',  'l')
        )
        self.keyboard_controls = []
        for i in range(min(len(player_agents), len(keyboard_control_sets))):
            kb_controls = KeyBoardControls()
            kb_controls.init_logic(player_agents[i], *keyboard_control_sets[i])
            self.keyboard_controls.append(kb_controls)

        # player touchscreen inputs
        self.swipe_controls = []
        control_zones = [[] for _ in range(len(self.swipe_zones))]
        for i, p in enumerate(player_agents):
            player_id = p.get_id()
            swipe_controls = PlayerSwipeControl()
            swipe_controls.init_logic(p, agent_colors[player_id], swipe_zone_bg_color)
            control_zones[i%len(self.swipe_zones)].append(swipe_controls)
            self.swipe_controls.append(swipe_controls)
        for i in range(len(self.swipe_zones)):
            self.swipe_zones[i].init_logic(control_zones[i])

        self.clock_event = Clock.schedule_interval(self.game_step, self.time_step)

    def game_step(self, dt: float) -> None:
        deads = self.world.simulate()
        self.ids.world_display.draw(deads, self.ai_explanations)
        self.ids.score_board.update_scores()
        for controller in self.swipe_controls:
            controller.update_direction_display()

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        if self.paused:
            Clock.unschedule(self.clock_event)
        else:
            self.clock_event = Clock.schedule_interval(self.game_step, self.time_step)

    def toggle_fullspeed(self) -> None:
        self.full_speed = not self.full_speed
        if self.full_speed:
            self.set_time_step(MINIMAL_TIME_STEP)
        else:
            self.set_time_step(self.regular_time_step)

    def set_time_step(self, new_time_step: float) -> None:
        self.time_step = new_time_step
        if not self.paused:
            Clock.unschedule(self.clock_event)
            self.clock_event = Clock.schedule_interval(self.game_step, self.time_step)

    def toggle_ai_explanations(self) -> None:
        self.ai_explanations = not self.ai_explanations
