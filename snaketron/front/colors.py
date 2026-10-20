from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from kivy.utils import get_color_from_hex

if TYPE_CHECKING:
    from front.type_hints import *

__all__ = ['UIColors', 'WorldColors', 'SnakeColors', 'SnakeColorManager']


@dataclass
class UIColors:
    swipe_zone_bg: ColorValue
    app_background: ColorValue


@dataclass
class WorldColors:
    food_outline: ColorValue
    food: ColorValue
    background: ColorValue
    gridline: ColorValue
    gridborder: ColorValue


@dataclass
class SnakeColors:
    head: ColorValue
    tail: ColorValue
    head_decay_first: ColorValue
    head_decay_final: ColorValue
    tail_decay_first: ColorValue
    tail_decay_final: ColorValue
    inspect: ColorValue


class SnakeColorManager:
    def __init__(self, colors: dict) -> None:
        self.colors = colors['snakes']
        self.head_color_wheel = colors['snakes']['head_color_wheel']
        self.tail_color_wheel = colors['snakes']['tail_color_wheel']
        self.snake_colors_mapping: dict[int, SnakeColors] = {}

    def add_snake(self, snake_id: int) -> SnakeColors:
        assert snake_id not in self.snake_colors_mapping.keys()
        snake_colors = SnakeColors(
            head=get_color_from_hex(self.head_color_wheel[snake_id % len(self.head_color_wheel)]),
            tail=get_color_from_hex(self.tail_color_wheel[snake_id % len(self.tail_color_wheel)]),
            head_decay_first=get_color_from_hex(self.colors['head_decay_first']),
            head_decay_final=get_color_from_hex(self.colors['head_decay_final']),
            tail_decay_first=get_color_from_hex(self.colors['tail_decay_first']),
            tail_decay_final=get_color_from_hex(self.colors['tail_decay_final']),
            inspect=get_color_from_hex(self.colors['inspect'])
        )
        self.snake_colors_mapping[snake_id] = snake_colors
        return snake_colors

    def remove_snake(self, snake_id: int) -> None:
        self.snake_colors_mapping.pop(snake_id)

    def get_snake_colors(self, snake_id: int) -> SnakeColors:
        assert snake_id in self.snake_colors_mapping.keys()
        return self.snake_colors_mapping.get(snake_id)
