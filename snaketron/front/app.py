from __future__ import annotations

import json
from typing import TYPE_CHECKING

from front.controls import *
from front.score_board import *
from front.window import *
from front.world_display import *

from kivy.app import App
from kivy.lang import Builder
from kivy.utils import platform
from kivy.core.window import Window

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Sequence

    from back.agents import PlayerSnakeAgent, AbstractAISnakeAgent
    from back.events import EventReceiver
    from back.world import SnakeWorld


class SnakeTronApp(App):
    def __init__(
        self,
        event_receiver: EventReceiver,
        world: SnakeWorld,
        player_agents: Sequence[PlayerSnakeAgent],
        ai_agents: Sequence[AbstractAISnakeAgent],
        time_step: float,
        ai_explanations: bool,
        layout_dir: Path,
        color_file: Path,
        input_sensitivity: float,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.event_receiver = event_receiver
        self.world = world
        self.player_agents = player_agents
        self.ai_agents = ai_agents
        self.time_step = time_step
        self.ai_explanations = ai_explanations
        self.layout_dir = layout_dir
        self.color_file = color_file
        self.input_sensitivity = input_sensitivity

    def build(self) -> SnakeTronWindow:
        for layout_file in self.layout_dir.rglob('*.kv'):
            Builder.load_file(str(layout_file))

        with self.color_file.open(mode='r') as fp:
            colors = json.load(fp)

        if platform in ('linux', 'win', 'macosx'):
            screen_width, screen_height = Window.system_size
            width, height = int(432/891 * screen_height), screen_height
            scale = screen_width / width
            if scale < 1:
                width, height = int(width * scale), int(height * scale)
            Window.size = (width, height)

        main_window = SnakeTronWindow()
        main_window.init_logic(
            self.event_receiver,
            self.world,
            self.player_agents,
            self.ai_agents,
            self.time_step,
            self.ai_explanations,
            colors,
            self.input_sensitivity
        )
        return main_window
