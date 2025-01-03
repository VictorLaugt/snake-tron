from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque

from a_star import shortest_path
from world import oposite_dir, UP, DOWN, LEFT, RIGHT

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Sequence, Iterable, Iterator, Type, Optional
    from type_hints import Position, Direction
    from world import SnakeWorld, AbstractHeuristic


class AbstractSnakeAgent(ABC):
    def __init__(self, world: SnakeWorld, initial_pos: Sequence[Position]) -> None:
        assert len(initial_pos) > 0

        self.agent_id = -1
        self.world = world
        self.initial_pos = initial_pos
        self.pos = deque(initial_pos)
        self.last_tail_pos = None

    def get_id(self) -> int:
        return self.agent_id

    def set_id(self, agent_id: int) -> None:
        self.agent_id = agent_id

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
        for other in self.world.get_alive_agents():
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

        self.danger_zones: list[list[list[Position]]] = []
        self.caution_radius = caution

        self.target: Optional[AbstractSnakeAgent] = None

    def reset(self) -> None:
        super().reset()
        self.x_path.clear()
        self.y_path.clear()
        self.dir_path.clear()
        self.dir = self.initial_dir
        self.cooldown = 0
        self.target = None

    def start_avoid(self, dangerous_agents: Iterable[AbstractSnakeAgent]) -> list[list[Position]]:
        """Add virtual obstacles in the world to avoid positions that are to close
        to the dangerous snakes' heads.
        """
        danger_layers = []
        for agent in dangerous_agents:
            layer = (agent.get_head(),)
            for _ in range(self.caution_radius):
                new_layer = []
                for position in layer:
                    for neighbor, direction in self.world.iter_free_neighbors(position):
                        self.world.add_obstacle(neighbor)
                        new_layer.append(neighbor)
                danger_layers.append(new_layer)
                layer = new_layer
        return danger_layers

    def stop_avoid(self, danger_layers: list[list[Position]]) -> None:
        """Removes the virtual obstacles from the world."""
        for layer in danger_layers:
            for position in layer:
                self.world.pop_obstacle(position)

    def compute_shortest_path(
        self,
        destinations: Iterable[Position],
        inf_len: int,
        sup_len: int|float = float('inf')
    ) -> Optional[int]:
        """Tries to computes the shortest path from the snake's head to one of
        the destination positions, and whose length is strictly between inf_len
        and sup_len. If success, returns the index of the selected destination,
        else returns None.
        """
        head = self.get_head()
        destination_idx = None
        current_min = float('inf')
        path_len = 0

        for i, dst in enumerate(destinations):
            if self.world.pos_is_free(dst):
                heuristic = self.heuristic_type(dst[0], dst[1])
                x_path, y_path, dir_path = shortest_path(self.world, head, dst, heuristic)
                path_len = len(dir_path)

                if inf_len < path_len < min(current_min, sup_len) and x_path[0] == dst[0] and y_path[0] == dst[1]:
                    destination_idx = i
                    current_min = path_len
                    self.x_path = x_path
                    self.y_path = y_path
                    self.dir_path = dir_path

        return destination_idx

    def compute_path_to_nearest_food(self) -> bool:
        destination_idx = self.compute_shortest_path(self.world.iter_food(), 0, float('inf'))
        return destination_idx is not None

    def compute_path(self) -> None:
        # TODO: implement the attacking behavior
        dangerous_agents = [agent for agent in self.world.get_alive_agents() if self is not agent]
        danger_zone = self.start_avoid(dangerous_agents)

        success = self.compute_path_to_nearest_food()
        self.stop_avoid(danger_zone)

        if not success:
            self.compute_path_to_nearest_food()

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
