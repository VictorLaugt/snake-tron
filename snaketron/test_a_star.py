from __future__ import annotations

import tkinter as tk
from world import SnakeWorld, EuclidianDistanceHeuristic
from a_star import shortest_path

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import TypeAlias, Optional
    from type_hints import Position
    from world import AbstractGridGraph
    Coordinate: TypeAlias = tuple[float, float]

class AStarInteractiveTester(tk.Tk):
    def __init__(
        self,
        graph: AbstractGridGraph,
        square_size: int,
        default_src: Optional[Position]=None,
        default_dst: Optional[Position]=None
    ) -> None:
        super().__init__()
        self.graph = graph
        self.obstacles: set[Position] = set()

        self.src = default_src or (0, 0)
        self.dst = default_dst or (0, 0)
        self.click_method = self.commute

        self.square_size = square_size
        self.canvas = tk.Canvas(
            self,
            width=self.graph.get_width() * self.square_size,
            height=self.graph.get_height() * self.square_size,
            bg='grey'
        )
        self.button_set_src = tk.Button(
            self,
            text='Set source (S)',
            command=self.command_set_src
        )
        self.button_set_dst = tk.Button(
            self,
            text='Set destination (D)',
            command=self.command_set_dst
        )
        self.button_compute_path = tk.Button(
            self,
            text='Compute path (Enter)',
            command=self.command_compute_path
        )
        self.button_clear_path = tk.Button(
            self,
            text='Clear path (BackSpace)',
            command=self.command_clear_path
        )
        self.button_clear_obstacles = tk.Button(
            self,
            text='Clear obstacles (Suppr)',
            command=self.command_clear_obstacles
        )

        self.bind('<KeyPress-q>', lambda _: self.destroy())
        self.bind('<Escape>', lambda _: self.destroy())

        self.bind('<KeyPress-s>', lambda _: self.command_set_src())
        self.bind('<KeyPress-d>', lambda _: self.command_set_dst())
        self.bind('<Return>', lambda _: self.command_compute_path())
        self.bind('<BackSpace>', lambda _: self.command_clear_path())
        self.bind('<Delete>', lambda _: self.command_clear_obstacles())
        self.canvas.bind('<Button-1>', self.on_click)

        self.canvas.grid(row=0, column=0, columnspan=5)
        self.button_set_src.grid(row=1, column=0)
        self.button_set_dst.grid(row=1, column=1)
        self.button_compute_path.grid(row=1, column=2)
        self.button_clear_path.grid(row=1, column=3)
        self.button_clear_obstacles.grid(row=1, column=4)

        self.init_canvas()

    # ---- coordinate converters
    def coordinate_to_position(self, x: float, y: float) -> Position:
        return (round(x / self.square_size), round(y / self.square_size))

    def position_to_coordinate(self, u: int, v: int) -> Coordinate:
        return (u * self.square_size, v * self.square_size)

    # ---- drawing methods
    def draw_square(self, u: int, v: int, color, other_tag=None) -> None:
        x1, y1 = self.position_to_coordinate(u, v)
        x2, y2 = self.position_to_coordinate(u+1, v+1)
        tags = ((u, v),) if other_tag is None else ((u, v), other_tag)
        self.canvas.create_rectangle(
            x1, y1,
            x2, y2,
            fill=color,
            tags=tags
        )

    def erase_square(self, tag: str|int) -> None:
        self.canvas.delete(tag)

    def init_canvas(self) -> None:
        for u in range(self.graph.get_width()):
            x1, y1 = self.position_to_coordinate(u, 0)
            x2, y2 = self.position_to_coordinate(u, self.graph.get_height())
            self.canvas.create_line(x1, y1, x2, y2)
        for v in range(self.graph.get_width()):
            x1, y1 = self.position_to_coordinate(0, v)
            x2, y2 = self.position_to_coordinate(self.graph.get_width(), v)
            self.canvas.create_line(x1, y1, x2, y2)
        self.set_src(*self.src)
        self.set_dst(*self.dst)

    # ---- event handlers
    def on_click(self, event: tk.Event) -> None:
        x, y = event.x - self.square_size / 2, event.y - self.square_size / 2
        u, v = self.coordinate_to_position(x, y)
        self.click_method(u, v)

    def command_set_src(self) -> None:
        self.click_method = self.set_src

    def command_set_dst(self) -> None:
        self.click_method = self.set_dst

    def command_clear_path(self) -> None:
        self.canvas.delete('path')

    def command_clear_obstacles(self) -> None:
        self.canvas.delete('obstacle')
        for u, v in self.obstacles:
            self.graph.pop_obstacle((u, v))
        self.obstacles.clear()

    def command_compute_path(self) -> None:
        # erase old path
        self.canvas.delete('path')

        # compute new path
        path_u, path_v, path_dir = shortest_path(
            self.graph,
            self.src,
            self.dst,
            EuclidianDistanceHeuristic(*self.dst)
        )

        # display new path
        print(f'source={self.src}, destination={self.dst}')
        print(f'{path_u=}', f'{path_v=}', sep='\n', end='\n'*2)
        for u, v in zip(path_u, path_v):
            self.draw_square(u, v, 'yellow', other_tag='path')


    # ---- graph setters
    def set_src(self, u: int, v: int) -> None:
        self.src = u, v
        self.canvas.delete('src')
        self.draw_square(u, v, 'blue', other_tag='src')
        self.click_method = self.commute

    def set_dst(self, u: int, v: int) -> None:
        self.dst = u, v
        self.canvas.delete('dst')
        self.draw_square(u, v, 'green', other_tag='dst')
        self.click_method = self.commute

    def commute(self, u: int, v: int) -> None:
        if self.graph.pos_is_free((u, v)):
            self.graph.add_obstacle((u, v))
            self.obstacles.add((u, v))
            self.draw_square(u, v, 'black', other_tag='obstacle')
        else:
            self.graph.pop_obstacle((u, v))
            self.obstacles.remove((u, v))
            self.canvas.delete((u, v))


if __name__ == '__main__':
    app = AStarInteractiveTester(
        SnakeWorld(20, 20, 0),
        square_size=40,
        default_src=(5, 9),
        default_dst=(14, 9)
    )
    app.mainloop()
