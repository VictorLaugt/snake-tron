from __future__ import annotations

import json
from typing import TYPE_CHECKING

from front.controls import *
from front.score_board import *
from front.window import *
from front.world_display import *
from kivy.app import App
from kivy.lang import Builder

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Sequence

    from back.agent import AbstractAISnakeAgent, PlayerSnakeAgent
    from back.world import SnakeWorld


class SnakeTronApp(App):
    def __init__(
        self,
        world: SnakeWorld,
        player_agents: Sequence[PlayerSnakeAgent],
        ai_agents: Sequence[AbstractAISnakeAgent],
        time_step: float,
        ai_explanations: bool,
        layout_file: Path,
        color_file: Path,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.world = world
        self.player_agents = player_agents
        self.ai_agents = ai_agents
        self.time_step = time_step
        self.ai_explanations = ai_explanations
        self.layout_file = layout_file
        self.color_file = color_file

    def build(self) -> None:
        with self.layout_file.open(mode='r') as fp:
            layout_string = fp.read()
        Builder.load_string(layout_string)

        with self.color_file.open(mode='r') as fp:
            colors = json.load(fp)

        window = SnakeTronWindow()
        window.init_logic(
            self.world,
            self.player_agents,
            self.ai_agents,
            self.time_step,
            self.ai_explanations,
            colors
        )
        return window
