from __future__ import annotations

from itertools import chain
from typing import TYPE_CHECKING

from front.controls import (PlayerKeyBoardControl, PlayerSwipeControl,
                            SwipeControlZone)
from front.world_display import SnakeColors, WorldColors
from kivy.clock import Clock
from kivy.properties import ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import get_color_from_hex

if TYPE_CHECKING:
    from typing import Iterable, Sequence

    from front.type_hints import ColorValue
    from back.agents import AbstractSnakeAgent, AbstractAISnakeAgent, PlayerSnakeAgent
    from back.events import EventReceiver
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
    keyboard_controls: list[PlayerKeyBoardControl]
    paused: bool
    full_speed: bool
    regular_time_step: float
    time_step: float
    clock_event: ClockEvent

    def on_kv_post(self, base_widget: Widget) -> None:
        self.swipe_zones = []
        for child in self.children:
            if isinstance(child, SwipeControlZone):
                self.swipe_zones.append(child)

        self.ids.button_pause.bind(on_press=lambda _: self.toggle_pause())
        self.ids.button_toggle_ai_explanations.bind(on_press=lambda _: self.toggle_ai_explanations())
        self.ids.button_toggle_fullspeed.bind(on_press=lambda _: self.toggle_fullspeed())

    def _set_time_step(self, new_time_step: float) -> None:
        self.time_step = new_time_step
        if not self.paused:
            Clock.unschedule(self.clock_event)
            self.clock_event = Clock.schedule_interval(self.game_step, self.time_step)

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        if self.paused:
            Clock.unschedule(self.clock_event)
        else:
            self.clock_event = Clock.schedule_interval(self.game_step, self.time_step)

    def toggle_fullspeed(self) -> None:
        self.full_speed = not self.full_speed
        if self.full_speed:
            self._set_time_step(MINIMAL_TIME_STEP)
        else:
            self._set_time_step(self.regular_time_step)

    def toggle_ai_explanations(self) -> None:
        self.ids.world_display.toggle_ai_explanations()


    def init_logic(
        self,
        event_receiver: EventReceiver,
        world: SnakeWorld,
        player_agents: Sequence[PlayerSnakeAgent],
        ai_agents: Sequence[AbstractAISnakeAgent],
        time_step: float,
        ai_explanations: bool,
        colors: dict,
        input_sensitivity: float,
    ) -> None:
        agents: list[AbstractSnakeAgent] = list(chain(player_agents, ai_agents))

        # link to the backend
        self.world = world
        self.player_agents = player_agents
        self.world.reset()

        # game speed
        self.paused = False
        self.full_speed = False
        self.regular_time_step = time_step
        self.time_step = time_step
        self.clock_event = Clock.schedule_interval(self.game_step, self.time_step)

        # colors
        world_colors = self._create_world_colors(colors)
        agent_colors = self._create_agent_colors(colors, agents)
        swipe_zone_bg_color = get_color_from_hex(colors['ui']['swipe_zone_bg_color'])
        self.app_background_color = get_color_from_hex(colors['ui']['background'])

        # propagates logic to child widgets
        self.ids.world_display.init_logic(
            event_receiver, world, ai_agents, world_colors, agent_colors
        )
        self.ids.score_board.init_logic(agents, agent_colors)
        self._init_logic_keyboard_inputs(player_agents)
        self._init_logic_touchscreen_inputs(
            player_agents, swipe_zone_bg_color, agent_colors, input_sensitivity
        )

        if ai_explanations:
            self.toggle_ai_explanations()

    def _create_agent_colors(self, colors: dict, agents: Iterable[AbstractSnakeAgent]) -> dict[int, SnakeColors]:
        agent_colors = {}
        head_color_wheel = colors['snakes']['head_color_wheel']
        tail_color_wheel = colors['snakes']['tail_color_wheel']
        for a in agents:
            agent_id = a.get_id()
            agent_colors[agent_id] = SnakeColors(
                head=get_color_from_hex(head_color_wheel[agent_id % len(head_color_wheel)]),
                tail=get_color_from_hex(tail_color_wheel[agent_id % len(tail_color_wheel)]),
                head_decay_first=get_color_from_hex(colors['snakes']['head_decay_first']),
                head_decay_final=get_color_from_hex(colors['snakes']['head_decay_final']),
                tail_decay_first=get_color_from_hex(colors['snakes']['tail_decay_first']),
                tail_decay_final=get_color_from_hex(colors['snakes']['tail_decay_final']),
                inspect=get_color_from_hex(colors['snakes']['inspect'])
            )
        return agent_colors

    def _create_world_colors(self, colors: dict) -> WorldColors:
        return WorldColors(
            food_outline=get_color_from_hex(colors['world']['food_outline']),
            food=get_color_from_hex(colors['world']['food']),
            background=get_color_from_hex(colors['world']['background']),
            gridline=get_color_from_hex(colors['world']['gridline']),
            gridborder=get_color_from_hex(colors['world']['gridborder'])
        )

    def _init_logic_keyboard_inputs(self, player_agents: Sequence[PlayerSnakeAgent]) -> None:
        keyboard_control_sets = (
            ('up', 'left', 'down', 'right'),
            ('z', 'q', 's', 'd'),
            ('i', 'j', 'k',  'l')
        )
        self.keyboard_controls = []
        for i in range(min(len(player_agents), len(keyboard_control_sets))):
            kb_controls = PlayerKeyBoardControl()
            kb_controls.init_logic(player_agents[i], *keyboard_control_sets[i])
            self.keyboard_controls.append(kb_controls)

    def _init_logic_touchscreen_inputs(
        self,
        player_agents: Sequence[PlayerSnakeAgent],
        swipe_zone_bg_color: ColorValue,
        agent_colors: dict[int, SnakeColors],
        input_sensitivity: float
    ) -> None:
        self.swipe_controls = []
        control_zones = [[] for _ in range(len(self.swipe_zones))]
        for i, p in enumerate(player_agents):
            player_id = p.get_id()
            swipe_controls = PlayerSwipeControl()
            swipe_controls.init_logic(
                p, agent_colors[player_id], swipe_zone_bg_color, 1/input_sensitivity
            )
            control_zones[i%len(self.swipe_zones)].append(swipe_controls)
            self.swipe_controls.append(swipe_controls)
        for i in range(len(self.swipe_zones)):
            self.swipe_zones[i].init_logic(control_zones[i])


    def game_step(self, dt: float) -> None:
        self.world.simulate()
        self.ids.world_display.update_draw(self.time_step)
        self.ids.score_board.update_scores()
        for controller in self.swipe_controls:
            controller.update_direction_display()
