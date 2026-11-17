from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    from back.type_hints import *

__all__ = [
    'AbstractGridGraph', 'AbstractHeuristic', 'EuclidianDistanceHeuristic',
    'ManhattanDistanceHeuristic', 'EuclidianDistancePeriodicHeuristic'
]


class AbstractGridGraph(ABC):
    @abstractmethod
    def get_width(self) -> int:
        pass

    @abstractmethod
    def get_height(self) -> int:
        pass

    @abstractmethod
    def get_neighbor(self, p: Position, d: Direction) -> Position:
        """Returns the neighbor of position `p` in the direction `d`."""

    @abstractmethod
    def iter_free_neighbors(self) -> Iterator[tuple[Position, Direction]]:
        """Iterates over each neighbor of position `p` which does not contains
        any obstacle.
        """


class AbstractHeuristic(ABC):
    @abstractmethod
    def __init__(self, graph: AbstractGridGraph, x_dst: int, y_dst: int) -> None:
        pass

    @abstractmethod
    def __call__(self, x: int, y: int) -> int:
        pass


class EuclidianDistanceHeuristic(AbstractHeuristic):
    def __init__(self, graph: AbstractGridGraph, x_dst: int, y_dst: int) -> None:
        self.x_dst = x_dst
        self.y_dst = y_dst

    def __call__(self, x: int, y: int) -> int:
        dx, dy = self.x_dst - x, self.y_dst - y
        return dx*dx + dy*dy


class ManhattanDistanceHeuristic(AbstractHeuristic):
    def __init__(self, graph: AbstractGridGraph, x_dst: int, y_dst: int) -> None:
        self.x_dst = x_dst
        self.y_dst = y_dst

    def __call__(self, x: int, y: int) -> int:
        return abs(self.x_dst - x) + abs(self.y_dst - y)


class EuclidianDistancePeriodicHeuristic(AbstractHeuristic):
    def __init__(self, graph: AbstractGridGraph, x_dst: int, y_dst: int) -> None:
        self.h = graph.get_height()
        self.w = graph.get_width()
        self.x_dst = x_dst
        self.y_dst = y_dst

    def __call__(self, x: int, y: int) -> int:
        dx, dy = abs(self.x_dst - x), abs(self.y_dst - y)
        dx, dy = min(dx, self.w - dx), min(dy, self.h - dy)
        return dx*dx + dy*dy
