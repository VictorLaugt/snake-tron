from __future__ import annotations

import tkinter as tk
from itertools import chain
from dataclasses import dataclass

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import TypeAlias, Sequence, Iterable
    from type_hints import Position, Direction
    from world import SnakeWorld
    from agent import AbstractSnakeAgent, PlayerSnakeAgent, AbstractAISnakeAgent
    Coordinate: TypeAlias = tuple[float, float]


TAG_WORLD = 'game'
TAG_INSPECT = 'inspect'

UP: Direction = (0,-1)
DOWN: Direction = (0,1)
LEFT: Direction = (-1,0)
RIGHT: Direction = (1,0)


def direction_repr(d: Direction) -> str:
    if d == UP:
        return 'up'
    elif d == DOWN:
        return 'down'
    elif d == LEFT:
        return 'left'
    elif d == RIGHT:
        return 'right'
    else:
        return repr(d)

@dataclass
class SnakeColors:
    head_color: str
    tail_color: str
    dead_color: str
    inspect_colot: str

class SnakeGameWindow(tk.Tk):
    """Implements a frontend for a snake game. The user can control the snake
    with the arrow keys.
    """
    CONTROL_SETS = (
        ('<Up>', '<Left>', '<Down>', '<Right>'),
        ('<z>', '<q>', '<s>', '<d>'),
        ('<u>', '<h>', '<j>', '<k>'),
    )

    HEAD_COLORS = ('dark green', 'dark orange', 'dark violet', 'dark blue')
    TAIL_COLORS = ('green', 'orange', 'violet', 'blue')
    LAST_COLOR_IDX = len(HEAD_COLORS)-1

    FOOD_COLOR = 'red'
    DEAD_COLOR = 'dark red'
    INSPECT_COLOR = 'yellow'

    def __init__(
        self,
        snake_world: SnakeWorld,
        player_agents: Sequence[PlayerSnakeAgent],
        ai_agents: Sequence[AbstractAISnakeAgent],
        explain_ai: bool,
        ui_size_coeff: float,
        time_step: float
    ) -> None:
        super().__init__()

        # interface with the backend
        self.world = snake_world
        self.world.reset()
        self.player_snakes = list(player_agents)
        self.ai_snakes = list(ai_agents)

        # pause system
        self.game_paused = False
        self.next_step = None

        # graphical features
        self.snake_colors: dict[AbstractSnakeAgent, SnakeColors] = {}
        color_idx = 0
        for snake in chain(self.player_snakes, self.ai_snakes):
            colors = SnakeColors(
                self.HEAD_COLORS[color_idx],
                self.TAIL_COLORS[color_idx],
                self.DEAD_COLOR,
                self.INSPECT_COLOR
            )
            self.snake_colors[snake] = colors
            color_idx = min(color_idx+1, self.LAST_COLOR_IDX)

        self.explain_ai = explain_ai
        self.square_side_size = ui_size_coeff
        self.time_step = time_step

        self.grid_display = tk.Canvas(
            self,
            width=self.world.get_width() * self.square_side_size,
            height=self.world.get_height() * self.square_side_size,
            bg='gray'
        )
        self.grid_display.pack()

        # user interactions
        self.bind_all('<space>', lambda _: self.pause())
        self.bind_all('<Escape>', lambda _: self.destroy())
        self.bind_all('<Return>', lambda _: self.reset())
        for snake, control_set in zip(self.player_snakes, self.CONTROL_SETS):
            self.bind_user_inputs(snake, control_set)

        self.next_step = self.after_idle(self.start_game)

    def bind_user_inputs(self, player_snake: PlayerSnakeAgent, control_set: tuple[str, str, str, str]) -> None:
        self.bind_all(control_set[0], lambda _: player_snake.add_dir_request(UP))
        self.bind_all(control_set[1], lambda _: player_snake.add_dir_request(LEFT))
        self.bind_all(control_set[2], lambda _: player_snake.add_dir_request(DOWN))
        self.bind_all(control_set[3], lambda _: player_snake.add_dir_request(RIGHT))

    def pos_to_coord(self, pos: Position) -> Coordinate:
        """Returns the coordinates on the graphical ui canvas which corresponds to the
        square at the position `pos` in the snake world.
        """
        return pos[0] * self.square_side_size, pos[1] * self.square_side_size

    def coord_to_pos(self, x: float, y: float) -> Position:
        """Returns the square position in the snake world which corresponds to the
        `(x, y)` coordinates on the graphical ui canvas.
        """
        return int(x / self.square_side_size), int(y / self.square_side_size)

    def draw_square(self, x: int, y: int, color: str, tag: str) -> None:
        shift = self.square_side_size
        return self.grid_display.create_rectangle(x, y, x + shift, y + shift, fill=color, tag=tag)

    def draw_world(self, dead_snakes: Iterable[AbstractSnakeAgent]) -> None:
        self.grid_display.delete(TAG_WORLD)

        # draws the snakes
        for snake in self.world.iter_alive_agents():
            colors = self.snake_colors[snake]
            cells = snake.iter_cells()
            x, y = self.pos_to_coord(next(cells))
            self.draw_square(x, y, colors.head_color, TAG_WORLD)
            for pos in cells:
                x, y = self.pos_to_coord(pos)
                self.draw_square(x, y, colors.tail_color, TAG_WORLD)

        # draws the food
        for food in self.world.iter_food():
            x, y = self.pos_to_coord(food)
            self.draw_square(x, y, self.FOOD_COLOR, TAG_WORLD)

        # draws the snakes which died during the last step
        for snake in dead_snakes:
            colors = self.snake_colors[snake]
            for pos in snake.iter_cells():
                x, y = self.pos_to_coord(pos)
                self.draw_square(x, y, colors.dead_color, TAG_WORLD)

    def draw_ai_inspection(self) -> None:
        for snake in self.ai_snakes:
            colors = self.snake_colors[snake]
            for pos in snake.inspect():
                x, y = self.pos_to_coord(pos)
                self.draw_square(x, y, colors.inspect_color, TAG_INSPECT)

    def draw(self, dead_snakes: Iterable[AbstractSnakeAgent]) -> None:
        """Draws the entire game."""
        if self.explain_ai:
            self.draw_ai_inspection()
        self.draw_world(dead_snakes)

    def start_game(self) -> None:
        """Draws the world and start the game loop after a small time delay."""
        self.draw(())
        self.next_step = self.after(5*self.time_step, self.game_step)

    def game_step(self) -> None:
        """Simulates and displays one step of the game."""
        self.draw(self.world.simulate())
        self.next_step = self.after(self.time_step, self.game_step)

    def pause(self) -> None:
        """Pauses or resumes the game."""
        self.game_paused = not self.game_paused
        if self.game_paused:
            self.after_cancel(self.next_step)
            self.next_step = None
        else:
            self.next_step = self.after_idle(self.game_step)

    def reset(self) -> None:
        """Reset the game."""
        self.after_cancel(self.next_step)
        self.next_step = None
        self.world.reset()
        self.start_game()
