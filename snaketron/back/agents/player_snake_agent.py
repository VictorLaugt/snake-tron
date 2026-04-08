from __future__ import annotations

from collections import deque

from back.agents.abstract_snake_agent import AbstractSnakeAgent
from back.direction import opposite_dir

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Sequence, Optional

    from back.type_hints import Direction, Position
    from back.world import SnakeWorld


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

    def decide_direction(self) -> Direction:
        if len(self.dir_requests) > 0:
            self.dir = self.dir_requests.popleft()
        return self.dir

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
