from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from itertools import chain

from a_star import shortest_path
from world import oposite_dir, UP, DOWN, LEFT, RIGHT

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Sequence, Iterator, Type
    from type_hints import Position, Direction
    from world import SnakeWorld, AbstractHeuristic


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
    def decide_direction(self) -> None:
        """Makes the snake decide its next direction."""

    @abstractmethod
    def get_direction(self) -> Direction:
        """Returns the direction in which the snake want to move."""


class PlayerSnakeAgent(AbstractSnakeAgent):
    """Implements an agent which can be controlled by a request queuing system."""
    def __init__(self, world: SnakeWorld, initial_pos: Sequence[Position], initial_dir: Direction) -> None:
        assert initial_dir in (UP, DOWN, LEFT, RIGHT)

        super().__init__(world, initial_pos)
        self.initial_dir = initial_dir
        self.dir = initial_dir
        self.dir_requests: deque[Direction] = deque((), maxlen=5)

    def reset(self) -> None:
        super().reset()
        self.dir = self.initial_dir
        self.dir_requests.clear()

    def decide_direction(self) -> None:
        if len(self.dir_requests) > 0:
            self.dir = self.dir_requests.popleft()

    def get_direction(self) -> Direction:
        return self.dir

    def add_dir_request(self, request: Direction) -> None:
        """Queues a new direction request in which to move the snake."""
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
    """Implement a snake agent which always tries to grow."""
    def __init__(
        self,
        world: SnakeWorld,
        initial_pos: Sequence[Position],
        initial_dir: Direction,
        heuristic_type: Type[AbstractHeuristic],
        latency: int=0,
        caution: int=0
    ) -> None:
        assert initial_dir in (UP, DOWN, LEFT, RIGHT)
        assert latency >= 0
        assert caution >= 0

        super().__init__(world, initial_pos)
        self.heuristic_type = heuristic_type

        self.initial_dir = initial_dir
        self.x_path: list[int] = []
        self.y_path: list[int] = []
        self.dir_path: list[Direction] = []
        self.dir = self.initial_dir

        self.latency = latency
        self.cooldown = 0

        self.caution = caution

    def reset(self) -> None:
        super().reset()
        self.x_path.clear()
        self.y_path.clear()
        self.dir_path.clear()
        self.dir = self.initial_dir
        self.cooldown = 0

    def anticipate_latency(self) -> list[Position]:
        """Add virtual obstacles in the world to avoid positions in front of
        other snakes' heads.
        """
        latency_anticipation = []
        for other in self.world.iter_alive_agents():
            if self is not other:
                p = other.get_head()
                d = other.get_direction()
                for _ in range(self.latency):
                    p = self.world.get_neighbor(p, d)
                    self.world.add_obstacle(p)
                    latency_anticipation.append(p)
        return latency_anticipation

    def take_caution(self) -> list[list[Position]]:
        """Add virtual obstacles in the world to avoid positions that are too
        close to other snakes' heads.
        """
        caution_layers = []
        for other in self.world.iter_alive_agents():
            if self is not other:
                layer = (other.get_head(),)
                for _ in range(self.caution):
                    new_layer = []
                    for p in layer:
                        for n, d in self.world.iter_free_neighbors(p):
                            self.world.add_obstacle(n)
                            new_layer.append(n)
                    caution_layers.append(new_layer)
                    layer = new_layer
        return caution_layers

    def compute_path_nearest_food(self) -> None:
        head = self.get_head()
        min_path_len = float('inf')
        path_len = 0
        for food in self.world.iter_food():
            if self.world.pos_is_free(food):
                heuristic = self.heuristic_type(food[0], food[1])
                x_path, y_path, dir_path = shortest_path(self.world, head, food, heuristic)
                path_len = len(dir_path)

                if 0 < path_len < min_path_len and x_path[0] == food[0] and y_path[0] == food[1]:
                    min_path_len = path_len
                    self.x_path = x_path
                    self.y_path = y_path
                    self.dir_path = dir_path

    def compute_path_attack(self, potential_targets: Sequence[AbstractSnakeAgent]) -> bool:
        self_head = self.get_head()
        for other in potential_targets:
            if self is not other:
                other_head = colision_pos = other.get_head()
                direction = other.get_direction()

                for colision_distance in range(1, 10):
                    colision_pos = self.world.get_neighbor(colision_pos, direction)
                    if not self.world.pos_is_free(colision_pos):
                        break

                    heuristic = self.heuristic_type(colision_pos[0], colision_pos[1])
                    x_path, y_path, dir_path = shortest_path(self.world, self_head, colision_pos, heuristic)
                    path_len = len(dir_path)

                    if 0 < path_len < colision_distance and x_path[0] == colision_pos[0] and y_path[0] == colision_pos[1]:
                        ...

    def compute_path(self) -> None:
        latency_anticipation = self.anticipate_latency()
        caution_layers = self.take_caution()

        self.compute_path_nearest_food()

        for pos in chain(latency_anticipation, *caution_layers):
            self.world.pop_obstacle(pos)

    def decide_direction(self) -> None:
        if self.cooldown == 0 or len(self.dir_path) == 0:
            self.compute_path()
            self.cooldown = self.latency
        else:
            self.cooldown -= 1

        if len(self.dir_path) > 0:
            self.x_path.pop()
            self.y_path.pop()
            self.dir = self.dir_path.pop()

    def get_direction(self) -> Direction:
        return self.dir

    def die(self) -> None:
        super().die()
        self.x_path.clear()
        self.y_path.clear()
        self.dir_path.clear()

    def inspect(self) -> Iterator[Position]:
        return zip(self.x_path, self.y_path)


# TODO: implement an AI agent which try to attack its enemies
