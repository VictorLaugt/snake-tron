from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.graphics import InstructionGroup
from kivy.properties import NumericProperty
from kivy.uix.floatlayout import FloatLayout

from events.back2front_protocol import *
from front.colors import SnakeColors, WorldColors
from front.pause_menu import PauseMenuInvoker
from front.world_display.arena_drawer import ArenaDrawer
from front.world_display.food_draw_updater import FoodDrawUpdater
from front.world_display.snake_draw_updater import SnakeDrawUpdater

if TYPE_CHECKING:
    from kivy.uix.widget import Widget

    from back.type_hints import *
    from front.score_board import ScoreBoard
    from front.type_hints import *
    from front.window import SnakeTronWindow

__all__ = ['WorldDisplay']


def canvas_children_debug_repr(canvas):
    return "[" + ",\n".join(repr(element) for element in canvas.children) + "]"

class WorldDisplay(FloatLayout):
    square_size = NumericProperty(0.)

    def init_logic(
        self,
        main_window: SnakeTronWindow,
        score_board: ScoreBoard,
        world_colors: WorldColors,
        pause_command_touch_max_length: float
    ) -> None:
        self.main_window = main_window
        self.score_board = score_board

        # draws graphical elements of the world
        self.arena_drawer = ArenaDrawer(self, world_colors)
        self.food_draw_updater = FoodDrawUpdater(self, world_colors)
        self.snake_draw_updaters: dict[int, SnakeDrawUpdater] = {}
        self.world_graphical_elements = InstructionGroup()
        self.world_graphical_elements.add(self.arena_drawer.get_graphical_elements())
        self.world_graphical_elements.add(self.food_draw_updater.get_graphical_elements())

        # displays or hide the pause menu when requested
        self.pause_invoker = PauseMenuInvoker(
            main_window, pause_command_touch_max_length,
            size_hint=(None, None), size=self.size,
            pos=self.to_window(self.x, self.y)
        )

        # The pause menu is displayed on top of every world graphical element
        self.canvas.add(self.world_graphical_elements)
        self.add_widget(self.pause_invoker)


    def pos_to_coord(self, pos: Position) -> Coordinate:
        return (
            self.x + float(pos[0]) * self.square_size,
            self.y + (self.arena_drawer.get_height() - 1 - float(pos[1])) * self.square_size
        )

    def _recompute_square_size(self) -> None:
        self.square_size = min(
            self.height / self.arena_drawer.get_height(),
            self.width / self.arena_drawer.get_width()
        )

    def on_square_size(self, instance: Widget, value: float) -> None:
        self.arena_drawer.erase_and_draw()
        self.food_draw_updater.reset()
        for updater in self.snake_draw_updaters.values():
            updater.reset()

        self.pause_invoker.size = self.size
        self.pause_invoker.pos = self.to_window(self.x, self.y)

    def on_pos(self, instance: Widget, value: tuple[float, float]) -> None:
        self._recompute_square_size()

    def on_size(self, instance: Widget, value: tuple[float, float]) -> None:
        self._recompute_square_size()


    def add_snake(self, snake_id: int, colors: SnakeColors) -> None:
        assert snake_id not in self.snake_draw_updaters.keys()
        updater = SnakeDrawUpdater(self, colors, n_decay_steps=4)
        self.snake_draw_updaters[snake_id] = updater
        self.world_graphical_elements.add(updater.get_graphical_elements())

    def remove_snake(self, snake_id: int) -> None:
        updater = self.snake_draw_updaters.pop(snake_id)
        self.world_graphical_elements.remove(updater.get_graphical_elements())
        updater.erase()

    def get_snake_dir(self, snake_id: int) -> Direction:
        self.snake_draw_updaters[snake_id].get_head_dir()


    def arena_update_size(self, width: int, height: int) -> None:
        self.arena_drawer.update_size(width, height)

    def arena_spawn_food(self, food_pos: Position, time_step: float) -> None:
        self.food_draw_updater.spawn_food(food_pos, time_step)

    def arena_eat_food(self, food_pos: Position, by: int, time_step: float) -> None:
        consumer_head_pos = self.snake_draw_updaters[by].get_head_pos()
        self.food_draw_updater.eat_food(food_pos, consumer_head_pos, time_step)

    def arena_despawn_food(self, food_pos: Position, time_step: float) -> None:
        self.food_draw_updater.despawn_food(food_pos, time_step)

    def snake_spawn(self, snake_id: int, time_step: float, event: SnakeSpawn) -> None:
        updater = self.snake_draw_updaters[snake_id]
        updater.update_draw_snake_spawn(time_step, event)
        self.score_board.update_score(snake_id, updater.get_snake_len())

    def snake_die(self, snake_id: int, time_step: float, event: SnakeDie) -> None:
        self.snake_draw_updaters[snake_id].update_draw_snake_die(time_step, event)

    def snake_move(self, snake_id: int, time_step: float, event: SnakeMovement) -> None:
        updater = self.snake_draw_updaters[snake_id]
        updater.update_draw_snake_move(time_step, event)
        self.score_board.update_score(snake_id, updater.get_snake_len())
