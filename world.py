from __future__ import annotations

from abc import ABC, abstractmethod
from random import randrange
import numpy as np

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Iterator
    from type_hints import Position, Direction
    from agent import AbstractSnakeAgent


class AbstractHeuristic(ABC):
    @abstractmethod
    def __call__(self, x: int, y: int) -> int:
        pass


class EuclidianDistanceHeuristic(AbstractHeuristic):
    def __init__(self, x_dst: int, y_dst: int) -> None:
        self.x_dst = x_dst
        self.y_dst = y_dst

    def __call__(self, x: int, y: int) -> int:
        dx, dy = self.x_dst - x, self.y_dst - y
        return dx*dx + dy*dy


class SnakeWorld:
    def __init__(self, width: int, height: int, n_food: int) -> None:
        self.width = width
        self.height = height
        self.n_food = n_food

        self.vertices = np.ones((self.height, self.width), dtype=bool)
        self.food_pos: list[Position] = []
        self.snake_agents: list[AbstractSnakeAgent] = []

    def reset(self) -> None:
        self.food_pos.clear()
        for _ in range(self.n_food):
            self.food_pos.append(self._get_new_food_pos())
        for agent in self.snake_agents:
            agent.reset()
        assert np.all(self.vertices)

    def __repr__(self) -> str:
        array = [['.']*self.world_width for y in range(self.world_height)]
        for x, y in self.food_pos:
            array[y][x] = '*'
        for agent in self.snake_agents:
            x, y = agent.snake_pos[0]
            array[y][x] = '@'
            for x, y in agent.snake_pos[1:]:
                array[y][x] = 'O'
        return '\n'.join(''.join(row) for row in array)

    def _get_new_food_pos(self) -> Position:
        assert self.vertices.sum() > len(self.food_pos)
        while True:
            new_food = (randrange(self.world_width), randrange(self.world_height))
            if self.pos_is_free(new_food) and new_food not in self.food_pos:
                return new_food

    def moved_pos(self, p: Position, d: Direction) -> Position:
        return (p[0] + d[0]) % self.width, (p[1] + d[1]) % self.height


    def eat_food(self, pos: Position) -> bool:
        for i in range(self.n_food):
            if pos == self.food_pos[i]:
                self.food_pos[i] = self._get_new_food_pos()
                return True
        return False

    def pos_is_free(self, pos: Position) -> bool:
        return self.vertices[pos[1], pos[0]]

    def free_pos(self, pos: Position) -> None:
        self.vertices[pos[1], pos[0]] = True

    def obstruct_pos(self, pos: Position) -> None:
        self.vertices[pos[1], pos[0]] = False

    def iter_neighbors(self, pos: Position) -> Iterator[Position]:
        """Iterates over each neighbor of `position`."""
        x, y = pos

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
