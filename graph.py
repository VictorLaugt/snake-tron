from __future__ import annotations

import numpy as np

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import TypeAlias, Iterable
    Position: TypeAlias = tuple[int, int]
    Path: TypeAlias = tuple[list[int], list[int]]


class EuclidianDistanceHeuristic:
    def __init__(self, x_dst: int, y_dst: int) -> None:
        self.x_dst = x_dst
        self.y_dst = y_dst

    def __call__(self, x: int, y: int) -> int:
        dx, dy = self.x_dst - x, self.y_dst - y
        return dx*dx + dy*dy


class GridGraph:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

        # array which represents the state of each (x, y) positions.
        # True: free
        # False: obstacle
        self.vertices = np.ones((self.height, self.width), dtype=bool)

    def __repr__(self):
        return str(self.vertices)

    def free_every_positions(self):
        """Removes the obstacles from every positions"""
        self.vertices[:] = True

    def free_position(self, x: int, y: int):
        """Removes the obstacle on the position (x, y)."""
        self.vertices[y, x] = True

    def obstruct_position(self, x: int, y: int):
        """Puts an obstacle on the position (x, y)."""
        self.vertices[y, x] = False

    def is_free(self, x: int, y: int) -> bool:
        """Returns True if the position (x, y) is not obstructed by an obstacle,
        False otherwise.
        """
        return self.vertices[y, x]

    def iter_neighbors(self, position: Position) -> Iterable[Position]:
        """Iterates over each neighbor of `position`."""
        x, y = position

        y_up, x_up = y-1, x
        y_down, x_down = y+1, x
        y_left, x_left = y, x-1
        y_right, x_right = y, x+1

        if y_up >= 0 and self.vertices[y_up, x_up]:
            yield x_up, y_up
        if y_down < self.height and self.vertices[y_down, x_down]:
            yield x_down, y_down
        if x_left >= 0 and self.vertices[y_left, x_left]:
            yield x_left, y_left
        if x_right < self.width and self.vertices[y_right, x_right]:
            yield x_right, y_right


class PeriodicGridGraph(GridGraph):
    def iter_neighbors(self, position):
        x, y = position

        y_up, x_up = (y-1) % self.height, x
        y_down, x_down = (y+1) % self.height, x
        y_left, x_left = y, (x-1) % self.width
        y_right, x_right = y, (x+1) % self.width

        if self.vertices[y_up, x_up]:
            yield x_up, y_up
        if self.vertices[y_down, x_down]:
            yield x_down, y_down
        if self.vertices[y_left, x_left]:
            yield x_left, y_left
        if self.vertices[y_right, x_right]:
            yield x_right, y_right
