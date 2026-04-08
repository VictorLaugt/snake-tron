
from __future__ import annotations

from abc import abstractmethod

from back.agents.abstract_snake_agent import AbstractSnakeAgent
from back.a_star import shortest_path

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Optional, Sequence, Iterable, Iterator, Type
    from back.type_hints import Direction, Position
    from back.world import AbstractHeuristic, SnakeWorld


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

    # TODO: move the latency/cooldown mechanism into the mixin level of the class inheritance
    #
    # impact on constructor arguments: latency
    # impact on attributes: self.latency, self.cooldown
    # impact on the reset method: self.cooldown
    #
    # def decide_direction(self) -> Direction:
    #     self.update_path()  # the update_path method will be responsible to handle the cooldown mechanism
    #     if len(self.dir_path) > 0:
    #         self.x_path.pop()
    #         self.y_path.pop()
    #         self.dir = self.dir_path.pop()
    #     return self.dir
    def decide_direction(self) -> Direction:
        if self.cooldown == 0 or len(self.dir_path) == 0:
            self.update_path()
            self.cooldown = self.latency
        else:
            self.cooldown -= 1

        if len(self.dir_path) > 0:
            self.x_path.pop()
            self.y_path.pop()
            self.dir = self.dir_path.pop()
        return self.dir

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
