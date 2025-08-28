from __future__ import annotations

from kivy.properties import ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.utils import get_color_from_hex

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from back.agent import AbstractSnakeAgent
    from front.world_display import SnakeColors

    from typing import Sequence


class ColoredLabel(Label):
    box_color = ListProperty(get_color_from_hex('#FFFFFF'))


class ScoreBoard(BoxLayout):
    snakes: Sequence[AbstractSnakeAgent]
    snake_colors: dict[int, SnakeColors]
    labels: dict[int, Label]

    def init_logic(
        self,
        snakes: Sequence[AbstractSnakeAgent],
        snake_colors: dict[int, SnakeColors]
    ) -> None:
        self.snakes = snakes
        self.snake_colors = snake_colors
        self.labels = {}
        for snake in self.snakes:
            snake_id = snake.get_id()
            label = ColoredLabel(
                text=str(len(snake)),
                color=(1, 1, 1, 1),
                box_color=self.snake_colors[snake_id].tail
            )
            self.labels[snake_id] = label
            self.add_widget(label)

    def update_scores(self) -> None:
        for snake in self.snakes:
            self.labels[snake.get_id()].text = str(len(snake))
