from __future__ import annotations

from abc import ABC, abstractmethod
import tkinter as tk
from itertools import chain
from dataclasses import dataclass

from direction import UP, DOWN, LEFT, RIGHT, away_from_center

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import TypeAlias, Sequence, Iterable
    from type_hints import Position
    from world import SnakeWorld
    from agent import AbstractSnakeAgent, PlayerSnakeAgent, AbstractAISnakeAgent
    Coordinate: TypeAlias = tuple[float, float]


TAG_WORLD = 'game'
TAG_INSPECT = 'inspect'


@dataclass
class SnakeColors:
    head_color: str
    tail_color: str
    dead_color: str
    inspect_color: str

class AbstractGameWindow(tk.Tk, ABC):
    """Implements a frontend for a snake game. The user can control the snake
    with the arrow keys.
    """
    HEAD_COLORS = ('#0066CC', '#D19300', '#9400D3', '#008000')
    TAIL_COLORS = ('#0088EE', '#F3B500', '#EE82EE', '#006400')
    LAST_COLOR_IDX = len(HEAD_COLORS)-1

    FOOD_OUTLINE_COLOR = '#FF6666'
    FOOD_COLOR = '#FF0000'
    DEAD_COLOR = '#8B0000'
    INSPECT_COLOR = '#000060'
    BACKGROUND_COLOR = '#000030'
    GRIDLINE_COLOR = '#000090'

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

        # game speed
        self.regular_time_step = time_step
        self.time_step = time_step
        self.fullspeed = False

        # ai inspection
        self.explain_ai = explain_ai

        # snake colors
        self.square_side_size = ui_size_coeff
        self.snake_colors: list[SnakeColors] = [None] * (len(player_agents) + len(ai_agents))
        for snake in chain(self.player_snakes, self.ai_snakes):
            color_idx = min(snake.get_id(), self.LAST_COLOR_IDX)
            colors = SnakeColors(
                self.HEAD_COLORS[color_idx],
                self.TAIL_COLORS[color_idx],
                self.DEAD_COLOR,
                self.INSPECT_COLOR
            )
            self.snake_colors[snake.get_id()] = colors

        # world appearance
        self.configure(bg='black')
        self.grid_display = tk.Canvas(
            self,
            width=self.world.get_width() * self.square_side_size,
            height=self.world.get_height() * self.square_side_size,
            bg=self.BACKGROUND_COLOR,
            highlightthickness=0
        )
        self.draw_grid_lines()
        self.grid_display.grid(row=0, column=0, columnspan=4, pady=self.square_side_size, padx=self.square_side_size)

        # score board
        self.score_board = tk.Frame(self)
        self.score_labels = [None] * (len(player_agents) + len(ai_agents))
        for snake in chain(self.player_snakes, self.ai_snakes):
            score_label = tk.Label(
                self.score_board,
                text="0", fg="white", bg=self.snake_colors[snake.get_id()].head_color
            )
            score_label.pack(side="left")
            self.score_labels[snake.get_id()] = score_label
        self.score_board.grid(row=1, column=0)

        # user interactions
        self.config_user_interactions()

        self.next_step = self.after_idle(self.start_game)

    @abstractmethod
    def config_user_interactions(self) -> None:
        """Binds the user inputs"""

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

    def draw_grid_lines(self) -> None:
        h, w = self.world.get_height(), self.world.get_width()
        for u in range(3, w, 3):
            x0, y0 = self.pos_to_coord((u, 0))
            x1, y1 = self.pos_to_coord((u, h))
            self.grid_display.create_line(x0, y0, x1, y1, fill=self.GRIDLINE_COLOR)
        for v in range(3, h, 3):
            x0, y0 = self.pos_to_coord((0, v))
            x1, y1 = self.pos_to_coord((w, v))
            self.grid_display.create_line(x0, y0, x1, y1, fill=self.GRIDLINE_COLOR)

    def draw_square(self, x: float, y: float, **kwargs) -> None:
        shift = self.square_side_size
        # return self.grid_display.create_rectangle(x, y, x + shift, y + shift, fill=color, tag=tag)
        return self.grid_display.create_rectangle(x, y, x + shift, y + shift, **kwargs)

    def draw_circle(self, x: float, y: float, **kwargs) -> None:
        shift = self.square_side_size
        return self.grid_display.create_oval(x, y, x + shift, y + shift, **kwargs)

    def draw_world(self, dead_snakes: Iterable[AbstractSnakeAgent]) -> None:
        self.grid_display.delete(TAG_WORLD)

        # draws the snakes
        for snake in self.world.iter_alive_agents():
            colors = self.snake_colors[snake.get_id()]
            cells = snake.iter_cells()
            x, y = self.pos_to_coord(next(cells))
            self.draw_square(x, y, fill=colors.head_color, outline=colors.tail_color, tag=TAG_WORLD)
            for pos in cells:
                x, y = self.pos_to_coord(pos)
                self.draw_square(x, y, fill=colors.tail_color, outline=colors.tail_color, tag=TAG_WORLD)

        # draws the food
        for food in self.world.iter_food():
            x, y = self.pos_to_coord(food)
            self.draw_circle(x, y, fill=self.FOOD_COLOR, outline=self.FOOD_OUTLINE_COLOR, tag=TAG_WORLD)

        # draws the snakes which died during the last step
        for snake in dead_snakes:
            colors = self.snake_colors[snake.get_id()]
            for pos in snake.iter_cells():
                x, y = self.pos_to_coord(pos)
                self.draw_square(x, y, fill=colors.dead_color, outline=colors.dead_color, tag=TAG_WORLD)

    def draw_ai_inspection(self) -> None:
        self.grid_display.delete(TAG_INSPECT)
        for snake in self.ai_snakes:
            colors = self.snake_colors[snake.get_id()]
            for pos in snake.inspect():
                x, y = self.pos_to_coord(pos)
                self.draw_square(x, y, fill=colors.inspect_color, outline=colors.inspect_color, tag=TAG_INSPECT)

    def update_scores(self) -> None:
        for snake in chain(self.player_snakes, self.ai_snakes):
            self.score_labels[snake.get_id()].config(text=str(len(snake)))

    def draw(self, dead_snakes: Iterable[AbstractSnakeAgent]) -> None:
        """Draws the entire game."""
        if self.explain_ai:
            self.draw_ai_inspection()
        self.draw_world(dead_snakes)
        self.update_scores()

    def start_game(self) -> None:
        """Draws the world and start the game loop after a small time delay."""
        self.draw(())
        self.next_step = self.after(5*self.time_step, self.game_step)

    def game_step(self) -> None:
        """Simulates and displays one step of the game."""
        self.draw(self.world.simulate())
        self.next_step = self.after(self.time_step, self.game_step)

    def toggle_pause(self) -> None:
        """Pauses or resumes the game."""
        if self.game_paused:
            self.next_step = self.after_idle(self.game_step)
            self.game_paused = False
        else:
            self.after_cancel(self.next_step)
            self.next_step = None
            self.game_paused = True

    def toggle_ai_explanation(self) -> None:
        self.explain_ai = not self.explain_ai
        self.grid_display.delete(TAG_INSPECT)
        self.draw(())

    def toggle_fullspeed(self) -> None:
        self.fullspeed = not self.fullspeed
        self.time_step = 1 if self.fullspeed else self.regular_time_step

    def reset_game(self) -> None:
        """Reset the game."""
        if self.game_paused:
            self.game_paused = False
        else:
            self.after_cancel(self.next_step)
        self.next_step = None
        self.world.reset()
        self.start_game()



class SnakeGameWindow(AbstractGameWindow):
    CONTROL_SETS = (
        ('<Up>', '<Left>', '<Down>', '<Right>'),
        ('<z>', '<q>', '<s>', '<d>'),
        ('<u>', '<h>', '<j>', '<k>'),
    )

    def bind_user_inputs(self, player_snake: PlayerSnakeAgent, control_set: tuple[str, str, str, str]) -> None:
        self.bind_all(control_set[0], lambda _: player_snake.add_dir_request(UP))
        self.bind_all(control_set[1], lambda _: player_snake.add_dir_request(LEFT))
        self.bind_all(control_set[2], lambda _: player_snake.add_dir_request(DOWN))
        self.bind_all(control_set[3], lambda _: player_snake.add_dir_request(RIGHT))

    def config_user_interactions(self) -> None:
        self.bind_all('<space>', lambda _: self.toggle_pause())
        self.bind_all('<Escape>', lambda _: self.destroy())
        self.bind_all('<Return>', lambda _: self.reset_game())
        for snake, control_set in zip(self.player_snakes, self.CONTROL_SETS):
            self.bind_user_inputs(snake, control_set)

        tk.Button(self, text="reset", command=self.reset_game).grid(row=2, column=0)
        tk.Button(self, text="pause", command=self.toggle_pause).grid(row=2, column=1)
        tk.Button(self, text="explain ai", command=self.toggle_ai_explanation).grid(row=2, column=2)
        tk.Button(self, text='full speed', command=self.toggle_fullspeed).grid(row=2, column=3)


class DirectionalCross(tk.Canvas):
    def __init__(self, master, snake: PlayerSnakeAgent, width: int, height: int, bg: str, **kwargs) -> None:
        super().__init__(master, width=width, height=height, bg=bg, **kwargs)
        self.snake = snake
        self.last_dir = snake.get_direction()
        self.width = width
        self.height = height
        self.create_line(0, 0, self.width, self.height, fill='black', dash=(4, 2))
        self.create_line(0, self.height, self.width, 0, fill='black', dash=(4, 2))
        self.bind('<B1-Motion>', self.on_drag)

    def on_drag(self, event) -> None:
        d = away_from_center(event.x, event.y, self.width, self.height)
        if d != self.last_dir:
            self.snake.add_dir_request(d)
            self.last_dir = d


class MobileSnakeGameWindow(AbstractGameWindow):
    def config_user_interactions(self) -> None:
        n_controlable_players = min(3, len(self.player_snakes))
        if n_controlable_players > 0:
            pad_size = 500 // n_controlable_players
            controller_frame = tk.Frame(self, width=500, height=pad_size)
            for i in range(n_controlable_players):
                snake = self.player_snakes[i]
                directional_cross = DirectionalCross(
                    controller_frame, snake,
                    width=pad_size, height=pad_size, bg=self.snake_colors[snake.get_id()].tail_color
                )
                directional_cross.grid(row=0, column=i)
            controller_frame.grid(row=2, column=0, columnspan=4)

        tk.Button(self, text="pause", command=self.toggle_pause).grid(row=3, column=0)
        tk.Button(self, text="explain ai", command=self.toggle_ai_explanation).grid(row=3, column=1)
        tk.Button(self, text='full speed', command=self.toggle_fullspeed).grid(row=3, column=2)
