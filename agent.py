from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
import random

from a_star import shortest_path

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Sequence
    from type_hints import Position, Direction
    from world import SnakeWorld


INF = float('inf')

UP: Direction = (0,-1)
DOWN: Direction = (0,1)
LEFT: Direction = (-1,0)
RIGHT: Direction = (1,0)


def direction_repr(direction):
    if direction == UP:
        return 'up'
    elif direction == DOWN:
        return 'down'
    elif direction == LEFT:
        return 'left'
    elif direction == RIGHT:
        return 'right'
    else:
        return repr(direction)


def oposite_dir(d: Direction) -> Direction:
    return (-d[0], -d[1])


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


class AbstractSnakeAgent(ABC):
    def __init__(self, world: SnakeWorld, initial_pos: Sequence[Position]) -> None:
        assert len(initial_pos) > 0
        self.world = world
        self.initial_pos = initial_pos
        self.pos = deque(initial_pos)
        self.last_tail_pos = None

    def __len__(self) -> int:
        """Returns the length of the snake."""
        return len(self.pos)

    def get_head(self) -> Position:
        """Returns the position of the snake's head."""
        return self.pos[-1]

    def reset(self) -> None:
        """Reset the snake agent to make it ready to start a new game."""
        self.pos.clear()
        self.pos.extendleft(self.initial_pos)

    def move(self, d: Direction) -> None:
        """Moves once the snake in the direction `d`."""
        new_head = self.world.get_neighbor(self.pos[-1], d)
        self.world.add_obstacle(new_head)
        self.pos.append(new_head)
        self.last_tail_pos = self.pos.popleft()
        self.world.pop_obstacle(self.last_tail_pos)

    def check_self_collision(self) -> int:
        """Returns the length which should be cutted from the snake's tail if it
        collides with its head. Else, returns 0.
        """
        return (self.pos.index(self.pos[-1]) + 1) % len(self.pos)

    def cut(self, cut_length: int) -> None:
        """Removes the `cut_length` last cells from the snake."""
        for _ in range(cut_length):
            self.world.pop_obstacle(self.pos.popleft())

    def grow(self) -> bool:
        """Adds a cell at the end of the snake's tail."""
        if self.last_tail_pos is not None:
            self.pos.appendleft(self.last_tail_pos)
            self.world.add_obstacle(self.last_tail_pos)
            self.last_tail_pos = None
            return True
        return False

    def collides_another(self) -> bool:
        """Returns True if the snake collides another snake of the world, False
        otherwise.
        """
        for other in self.world.iter_agents():
            if self is not other and self.pos[-1] in other.pos:
                return True
        return False

    def die(self) -> None:
        """Kills the snake."""
        for p in self.pos:
            self.world.pop_obstacle(p)

    @abstractmethod
    def get_new_direction(self) -> Direction:
        """Returns the direction in which the snake wants to move."""


class PlayerSnakeAgent(AbstractSnakeAgent):
    def __init__(self, world: SnakeWorld, initial_pos: Sequence[Position], initial_dir: Direction) -> None:
        super().__init__(world, initial_pos)
        self.initial_dir = initial_dir
        self.dir = initial_dir
        self.dir_requests: deque[Direction] = deque((), maxlen=5)

    def reset(self) -> None:
        super().reset()
        self.dir = self.initial_dir

    def get_new_direction(self) -> Direction:
        if len(self.dir_requests) > 0:
            self.dir = self.dir_requests.popleft()
        return self.dir

    def add_dir_request(self, request: Direction) -> None:
        """Registers a new direction request in which to move the snake."""
        if len(self.dir_requests) < self.dir_requests.maxlen:
            if len(self.dir_requests) > 0:
                last_dir = self.dir_requests[-1]
            else:
                last_dir = self.dir
            if request != oposite_dir(last_dir):
                self.dir_requests.append(request)


class AStarSnakeAgent(AbstractSnakeAgent): pass
# class AStarSnakeAgent(AbstractSnakeAgent):
#     """Implements a snake that always follows the shortest path to the nearest food,
#     even if it means getting stuck in the long term.

#     """
#     def __init__(self, initial_snake, initial_dir):
#         self.initial_direction = initial_dir
#         self.initial_snake = initial_snake

#         self.snake: list[Position] = []
#         self.ob



#         self.world = world
#         self.snake = snake

#         self.path_x: list[int] = []
#         self.path_y: list[int] = []

#         self.direction: Direction = initial_direction

#     def reset(self):
#         self.graph.free_every_positions()
#         self.snake_position = self.world.snake.copy()
#         self.path_x = []
#         self.path_y = []
#         self.direction_x = None
#         self.direction_y = None

#     def get_direction(self):
#         x, y = self.world.snake[0]

#         min_length = INF
#         length = 0
#         for food in self.world.food_locations:
#             heuristic = EuclidianDistanceHeuristic(*food)
#             path_x, path_y = shortest_path(self.world.graph, (x, y), food, heuristic)
#             length = len(path_x)

#             if 0 < length < min_length and path_x[0] == food[0] and path_y[0] == food[1]:
#                 min_length = length
#                 shortest_path_x = path_x
#                 shortest_path_y = path_y

#         if length > 0:
#             self.path_x = shortest_path_x
#             self.path_y = shortest_path_y
#             self.direction = (shortest_path_x.pop() - x, shortest_path_y.pop() - y)

#         return self.direction

#     def inspect(self):
#         return zip(self.path_x, self.path_y)
