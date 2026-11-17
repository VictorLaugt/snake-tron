from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.properties import ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.utils import get_color_from_hex

from front.colors import SnakeColors

if TYPE_CHECKING:
    from front.world_display import *

__all__ = ['ScoreBoard']


class ColoredLabel(Label):
    box_color = ListProperty(get_color_from_hex('#000000'))


class ScoreBoard(BoxLayout):
    def init_logic(self) -> None:
        self.labels: dict[int, Label] = {}

    def add_snake(self, snake_id: int, colors: SnakeColors) -> None:
        assert snake_id not in self.labels.keys()
        label = ColoredLabel(
            text='',
            color=get_color_from_hex('#FFFFFF'),
            box_color=colors.tail
        )
        self.labels[snake_id] = label
        self.add_widget(label)

    def remove_snake(self, snake_id: int) -> None:
        label = self.labels.pop(snake_id)
        self.remove_widget(label)

    def update_score(self, snake_id: int, score: int) -> None:
        self.labels[snake_id].text = str(score)
