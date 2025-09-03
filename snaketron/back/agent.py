from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from typing import TYPE_CHECKING

from back.a_star import shortest_path
from back.direction import opposite_dir

if TYPE_CHECKING:
    from typing import Iterable, Iterator, Optional, Sequence, Type

    from back.type_hints import Direction, Position
    from back.world import AbstractHeuristic, SnakeWorld


class AbstractSnakeAgent(ABC):
    def __init__(
        self,
        world: SnakeWorld,
        initial_pos: Sequence[Position],
        alive: bool
    ) -> None:
        assert len(initial_pos) > 0
        self.agent_id = -1
        self.world = world
        self.alive = alive
        self.initial_pos = initial_pos
        self.pos = deque(initial_pos)
        self.last_tail_pos = None

    def get_id(self) -> int:
        return self.agent_id

    def set_id(self, agent_id: int) -> None:
        self.agent_id = agent_id

    def get_world(self) -> SnakeWorld:
        """Returns the world in which the snake evolves."""
        return self.world

    def get_initial_length(self) -> int:
        """Returns the length of the snake it spawns in the world."""
        return len(self.initial_pos)

    def __len__(self) -> int:
        """Returns the length of the snake."""
        return len(self.pos)

    def get_head(self) -> Position:
        """Returns the position of the snake's head."""
        return self.pos[-1]

    def iter_cells(self) -> Iterator[Position]:
        """Iterates over the snake's cells from the head to the tail."""
        return reversed(self.pos)

    def reset(self, pos: Optional[Sequence[Position]]=None, d: Optional[Direction]=None) -> None:
        """Resets the snake to make it ready to spawn in the world."""
        self.alive = True
        self.pos.clear()
        if pos is None:
            self.pos.extendleft(self.initial_pos)
        else:
            self.pos.extendleft(pos)

    def move(self, d: Direction) -> None:
        """Moves once the snake in the direction `d`."""
        new_head = self.world.get_neighbor(self.pos[-1], d)
        self.world.incr_obstacle_count(new_head, 1)
        self.pos.append(new_head)
        self.last_tail_pos = self.pos.popleft()
        self.world.incr_obstacle_count(self.last_tail_pos, -1)

    def check_self_collision(self) -> int:
        """Returns the length which should be cutted from the snake's tail if it
        collides with its head, 0 otherwise.
        """
        head = self.pos[-1]
        if self.world.get_obstacle_count(head) > 1:
            return (self.pos.index(head) + 1) % len(self.pos)
        return 0

    def cut(self, cut_length: int) -> None:
        """Removes the `cut_length` last cells from the snake."""
        for _ in range(cut_length):
            self.world.incr_obstacle_count(self.pos.popleft(), -1)

    def grow(self, growth: int) -> bool:
        """Adds `growth` cells at the end of the snake's tail."""
        if self.last_tail_pos is not None:
            self.pos.appendleft(self.last_tail_pos)
            self.world.incr_obstacle_count(self.last_tail_pos, 1)
            self.last_tail_pos = None
            return True
        return False

    def collides_another(self) -> Optional[AbstractSnakeAgent]:
        """Checks whether the snake collides with another snake of the world.
        Returns the collided snake if found, otherwise None.
        """
        head = self.pos[-1]
        if self.world.get_obstacle_count(head) > 1:
            for other in self.world.iter_alive_agents():
                if self is not other and head in other.pos:
                    return other

    def die(self) -> None:
        """Kills the snake."""
        self.alive = False
        for p in self.pos:
            self.world.incr_obstacle_count(p, -1)

    def is_alive(self) -> bool:
        """Returns True if the snake is alive, False otherwise."""
        return self.alive

    @abstractmethod
    def decide_direction(self) -> None:
        """Makes the snake decide its next direction."""

    @abstractmethod
    def get_direction(self) -> Direction:
        """Returns the direction in which the snake want to move."""


class PlayerSnakeAgent(AbstractSnakeAgent):
    """Implements a snake agent which can be controlled by a request queuing system."""
    def __init__(
        self,
        world: SnakeWorld,
        initial_pos: Sequence[Position],
        initial_dir: Direction,
        alive: bool=True
    ) -> None:
        super().__init__(world, initial_pos, alive)
        self.initial_dir = initial_dir
        self.dir = initial_dir
        self.dir_requests: deque[Direction] = deque((), maxlen=5)

    def reset(self, pos: Optional[Sequence[Position]]=None, d: Optional[Direction]=None) -> None:
        super().reset(pos)
        if d is None:
            self.dir = self.initial_dir
        else:
            self.dir = d
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
            if request != opposite_dir(last_dir):
                self.dir_requests.append(request)


class AbstractAISnakeAgent(AbstractSnakeAgent):
    def __init__(
        self,
        world: SnakeWorld,
        initial_pos: Sequence[Position],
        initial_dir: Direction,
        heuristic_type: Type[AbstractHeuristic],
        latency: int=0,
        alive: bool=True
    ) -> None:
        assert latency >= 0
        super().__init__(world, initial_pos, alive)

        self.initial_dir = initial_dir
        self.x_path: list[int] = []
        self.y_path: list[int] = []
        self.dir_path: list[Direction] = []
        self.dir = self.initial_dir

        self.heuristic_type = heuristic_type

        self.latency = latency
        self.cooldown = 0

    def reset(self, pos: Optional[Sequence[Position]]=None, d: Optional[Direction]=None) -> None:
        super().reset(pos)
        self.x_path.clear()
        self.y_path.clear()
        self.dir_path.clear()
        if d is None:
            self.dir = self.initial_dir
        else:
            self.dir = d
        self.cooldown = 0

    def die(self) -> None:
        super().die()
        self.x_path.clear()
        self.y_path.clear()
        self.dir_path.clear()

    def decide_direction(self) -> None:
        if self.cooldown == 0 or len(self.dir_path) == 0:
            self.update_path()
            self.cooldown = self.latency
        else:
            self.cooldown -= 1

        if len(self.dir_path) > 0:
            self.x_path.pop()
            self.y_path.pop()
            self.dir = self.dir_path.pop()

    def get_direction(self) -> Direction:
        return self.dir

    def inspect(self) -> Iterator[Position]:
        """Iterates over the positions of the path the AI snake is following."""
        return zip(self.x_path, self.y_path)

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
        inf_len = max(inf_len, 0)

        head = self.get_head()
        destination_idx = None
        current_min = float('inf')
        path_len = 0

        for i, dst in enumerate(destinations):
            if self.world.get_obstacle_count(dst) == 0:
                heuristic = self.heuristic_type(self.get_world(), dst[0], dst[1])
                x_path, y_path, dir_path = shortest_path(self.world, head, dst, heuristic, max_iteraton=450)
                path_len = len(dir_path)

                if inf_len < path_len < min(current_min, sup_len) and x_path[0] == dst[0] and y_path[0] == dst[1]:
                    destination_idx = i
                    current_min = path_len
                    self.x_path = x_path
                    self.y_path = y_path
                    self.dir_path = dir_path

        return destination_idx

    @abstractmethod
    def update_path(self) -> None:
        """Updates the path the AI agent is following."""


class AStarSnakeAgent(AbstractAISnakeAgent):
    """Implement a snake agent which always tries to grow."""
    def __init__(
        self,
        world: SnakeWorld,
        initial_pos: Sequence[Position],
        initial_dir: Direction,
        heuristic_type: Type[AbstractHeuristic],
        latency: int=0,
        caution: int=0,
        alive: bool=True
    ) -> None:
        assert caution >= 0
        super().__init__(world, initial_pos, initial_dir, heuristic_type, latency, alive)
        self.caution_radius = caution

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
                        self.world.incr_obstacle_count(neighbor, 1)
                        new_layer.append(neighbor)
                danger_layers.append(new_layer)
                layer = new_layer
        return danger_layers

    def stop_avoid(self, danger_layers: list[list[Position]]) -> None:
        """Removes the virtual obstacles from the world."""
        for layer in danger_layers:
            for position in layer:
                self.world.incr_obstacle_count(position, -1)

    def compute_path_to_nearest_food(self) -> bool:
        """Tries to compute the shortest path to the nearest food.
        Returns True if success, False otherwise.
        """
        return self.compute_shortest_path(self.world.iter_food(), 0, float('inf')) is not None

    def update_path(self) -> None:
        danger_zone = self.start_avoid(a for a in self.world.iter_alive_agents() if self is not a)
        success = self.compute_path_to_nearest_food()
        self.stop_avoid(danger_zone)

        if not success:
            self.compute_path_to_nearest_food()


class AStarOffensiveSnakeAgent(AStarSnakeAgent):
    def __init__(
        self,
        world: SnakeWorld,
        initial_pos: Sequence[Position],
        initial_dir: Direction,
        heuristic_type: Type[AbstractHeuristic],
        latency: int=0,
        caution: int=0,
        attack_anticipation: int=15,
        alive: bool=True
    ) -> None:
        super().__init__(world, initial_pos, initial_dir, heuristic_type, latency, caution, alive)
        self.attack_anticipation = attack_anticipation
        self.target: Optional[AbstractSnakeAgent] = None
        self.opponents: list[AbstractSnakeAgent] = []

    def add_opponent(self, opponent: AbstractAISnakeAgent) -> None:
        self.opponents.append(opponent)

    def reset(self, pos: Optional[Sequence[Position]]=None, d: Optional[Direction]=None) -> None:
        super().reset(pos, d)
        self.target = None

    def compute_attack_path(self, potential_targets: Sequence[AbstractSnakeAgent]) -> bool:
        """Tries to compute a path to attack one of the given target.
        Returns True if sucess, False otherwise.
        """
        # initialize the list of potential attack destinations
        impact_positions = [a.get_head() for a in potential_targets]

        for impact_delay in range(1, self.attack_anticipation+1):
            # update the list of potential attack destinations
            new_potential_targets: list[AbstractSnakeAgent] = []
            new_impact_positions: list[Position] = []
            for agent, pos in zip(potential_targets, impact_positions):
                pos = self.world.get_neighbor(pos, agent.get_direction())
                if self.world.get_obstacle_count(pos) == 0:
                    new_impact_positions.append(pos)
                    new_potential_targets.append(agent)
            potential_targets = new_potential_targets
            impact_positions = new_impact_positions


            for agent in potential_targets:
                i = self.compute_shortest_path(impact_positions, impact_delay - len(self), impact_delay)
                if i is not None:
                    self.target = potential_targets[i]
                    return True

        self.target = None
        return False

    def update_path(self) -> None:
        if self.target is not None and self.target.is_alive():
            success = self.compute_attack_path((self.target,))
        else:
            success = self.compute_attack_path([a for a in self.opponents if a.is_alive()])

        if not success:
            super().update_path()
