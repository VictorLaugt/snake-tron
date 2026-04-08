from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterator, Optional, Sequence

    from back.type_hints import Direction, Position
    from back.world import SnakeWorld


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
        self.last_tail_pos = self.pos[0]

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
        """Removes the `cut_length` last cells from the snake (`cut_length > 0`)."""
        for _ in range(cut_length):
            self.world.incr_obstacle_count(self.pos.popleft(), -1)

    def grow(self, growth: int) -> None:
        """Adds `growth` cells at the end of the snake's tail (`growth > 0`)."""
        for _ in range(growth):
            self.pos.appendleft(self.last_tail_pos)
        self.world.incr_obstacle_count(self.last_tail_pos, growth)

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
    def decide_direction(self) -> Direction:
        """Makes the snake decide in which direction it want to move,
        and returns it.
        """

    @abstractmethod
    def get_direction(self) -> Direction:
        """Returns the direction in which the snake wants to move."""
