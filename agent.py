from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
import random

from a_star import shortest_path, EuclidianDistanceHeuristic

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Sequence, Iterator
    from type_hints import Position, Direction
    from world import SnakeWorld


def oposite_dir(d: Direction) -> Direction:
    return (-d[0], -d[1])


class AbstractSnakeAgent(ABC):
    def __init__(self, world: SnakeWorld, initial_pos: Sequence[Position]) -> None:
        assert len(initial_pos) > 0
        self.world = world
        self.initial_pos = initial_pos
        self.pos = deque(initial_pos)
        self.last_tail_pos = None

    def __hash__(self) -> int:
        return hash(id(self))

    def __len__(self) -> int:
        """Returns the length of the snake."""
        return len(self.pos)

    def get_head(self) -> Position:
        """Returns the position of the snake's head."""
        return self.pos[-1]

    def iter_cells(self) -> Iterator[Position]:
        """Iterates over the snake's cells from the head to the tail."""
        return reversed(self.pos)

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
        for other in self.world.iter_alive_agents():
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
        self.dir_requests.clear()

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


class AbstractAISnakeAgent(AbstractSnakeAgent):
    @abstractmethod
    def inspect(self) -> Iterator[Position]:
        """Returns a position iterator which can be used to visually explain the
        AI agent strategy.
        """

class AStarSnakeAgent(AbstractAISnakeAgent):
    def __init__(self, world: SnakeWorld, initial_pos: Sequence[Position], initial_dir: Direction) -> None:
        super().__init__(world, initial_pos)
        self.initial_dir = initial_dir
        self.x_path: list[int] = []
        self.y_path: list[int] = []
        self.dir = initial_dir

    def reset(self) -> None:
        super().reset()
        self.x_path.clear()
        self.y_path.clear()
        self.dir = self.initial_dir

    def get_new_direction(self) -> Direction:
        x, y = self.get_head()

        min_path_len = float('inf')
        path_len = 0
        for (x_food, y_food) in self.world.iter_food():
            heuristic = EuclidianDistanceHeuristic(x_food, y_food)
            x_path, y_path = shortest_path(self.world, (x, y), (x_food, y_food), heuristic)
            path_len = len(x_path)

            if 0 < path_len < min_path_len and x_path[0] == x_food and y_path[0] == y_food:
                min_path_len = path_len
                self.x_path = x_path
                self.y_path = y_path

        if len(self.x_path) > 0:
            self.dir = (self.x_path.pop() - x, self.y_path.pop() - y)
        return self.dir

    def die(self) -> None:
        super().die()
        self.x_path.clear()
        self.y_path.clear()

    def inspect(self) -> Iterator[Position]:
        return zip(self.x_path, self.y_path)
