from __future__ import annotations

from abc import ABC, abstractmethod
from random import randrange
import numpy as np

from agent import PlayerSnakeAgent, AStarSnakeAgent

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Iterator, Sequence, Optional
    from type_hints import Position, Direction
    from agent import AbstractSnakeAgent


class AbstractGridGraph(ABC):
    @abstractmethod
    def get_width(self) -> int:
        pass

    @abstractmethod
    def get_height(self) -> int:
        pass

    @abstractmethod
    def iter_free_neighbors(self) -> Iterator[Position]:
        pass


class SnakeWorld(AbstractGridGraph):
    def __init__(self, width: int, height: int, n_food: int) -> None:
        assert width > 0 and height > 0
        assert n_food >= 0

        self.width = width
        self.height = height
        self.initial_n_food = n_food
        self.initial_agents: list[AbstractSnakeAgent] = []

        self.obstacle_count = np.zeros((self.width, self.height), dtype=np.uint8)
        self.food_pos: set[Position] = set()
        self.alive_agents: list[AbstractSnakeAgent] = []

    def __repr__(self) -> str:
        repr_grid = [['  .  '  for x in range(self.width)] for y in range(self.height)]
        for y in range(self.height):
            for x in range(self.width):
                repr_grid[y][x] = f" {self.obstacle_count[x, y]:03d} "
                if (x, y) in self.food_pos:
                    repr_grid[y][x] = "  *  "
        return '\n'.join(''.join(row) for row in repr_grid) + '\n'

    # ---- private
    def _consume_food(self, p: Position) -> bool:
        """If a food and only one snake head is at position `p`, despawn this food
        and returns True. Else, returns False.
        """
        if p in self.food_pos:
            head_count = sum((agent.get_head() == p) for agent in self.alive_agents)
            if head_count == 1:
                self.food_pos.remove(p)
                return True
        return False

    def _find_available_food_pos(self, max_try: int=20) -> Optional[Position]:
        """Tries to find an available position to spawn a new food and returns
        it if found.
        """
        for _ in range(max_try):
            pos = (randrange(self.width), randrange(self.height))
            if self.obstacle_count[pos] == 0 and pos not in self.food_pos:
                return pos

    def _spawn_missing_food(self) -> None:
        for _ in range(self.initial_n_food - len(self.food_pos)):
            pos = self._find_available_food_pos()
            if pos is None:
                break
            self.food_pos.add(pos)


    # ---- public
    def get_width(self) -> int:
        return self.width

    def get_height(self) -> int:
        return self.height


    def pop_obstacle(self, p: Position) -> None:
        """Removes an obstacle from the position `p`."""
        assert self.obstacle_count[p] > 0
        self.obstacle_count[p] -= 1

    def add_obstacle(self, p: Position) -> None:
        """Puts an obstacle on the position `p`."""
        self.obstacle_count[p] += 1

    def pos_is_free(self, p: Position) -> bool:
        """Returns True if there is no obstacle on the position `p`, False otherwise."""
        return self.obstacle_count[p] == 0


    def get_neighbor(self, p: Position, d: Direction) -> Position:
        """Returns the neighbor of position `p` in the direction `d`."""
        return (p[0] + d[0]) % self.width, (p[1] + d[1]) % self.height

    def iter_free_neighbors(self, p: Position) -> Iterator[Position]:
        """Iterates over each neighbor of position `p` which does not contains
        any obstacle.
        """
        x, y = p
        up = (x, (y-1) % self.height)
        down = (x, (y+1) % self.height)
        left = ((x-1) % self.width, y)
        right = ((x+1) % self.width, y)

        if self.obstacle_count[up] == 0:
            yield up
        if self.obstacle_count[down] == 0:
            yield down
        if self.obstacle_count[left] == 0:
            yield left
        if self.obstacle_count[right] == 0:
            yield right


    def iter_food(self) -> Iterator[Position]:
        """Iterates over each food position of the world."""
        yield from self.food_pos


    def new_player_agent(self, initial_pos: Sequence[Position], initial_dir: Direction) -> PlayerSnakeAgent:
        """Adds a new playable agent in the world and returns it."""
        agent = PlayerSnakeAgent(self, initial_pos, initial_dir)
        self.initial_agents.append(agent)
        return agent

    def new_a_star_agent(self, initial_pos: Sequence[Position], initial_dir: Direction) -> AStarSnakeAgent:
        """Adds a new A* ai agent in the world and returns it."""
        agent = AStarSnakeAgent(self, initial_pos, initial_dir)
        self.initial_agents.append(agent)
        return agent

    def iter_alive_agents(self) -> Iterator[AbstractSnakeAgent]:
        """Iterates over the agents of the world which are still alive."""
        yield from self.alive_agents


    def reset(self) -> None:
        """Reset the world and all its agents to make them ready to start a new game."""
        self.obstacle_count.fill(0)

        self.food_pos.clear()
        self._spawn_missing_food()

        self.alive_agents.clear()
        for agent in self.initial_agents:
            agent.reset()
            self.alive_agents.append(agent)
            for pos in agent.iter_cells():
                self.obstacle_count[pos] += 1

    def simulate(self) -> list[AbstractSnakeAgent]:
        """Simulates one step of the world evolution and returns the agents
        which died during this simulation step.
        """
        # moves the snakes
        directions: list[Direction] = []
        for agent in self.alive_agents:
            directions.append(agent.get_new_direction())
        for agent, d in zip(self.alive_agents, directions):
            agent.move(d)

        # resolves the snakes which eat their own tail
        cut_lengths: list[int] = []
        for agent in self.alive_agents:
            cut_lengths.append(agent.check_self_collision())
        for agent, cut_len in zip(self.alive_agents, cut_lengths):
            agent.cut(cut_len)

        # resolves the snakes which eat food and grow
        growing: list[AbstractSnakeAgent] = []
        for agent in self.alive_agents:
            if self._consume_food(agent.get_head()):
                growing.append(agent)
        for agent in growing:
            agent.grow()

        # kills each snake which collides another snake
        deads: list[AbstractSnakeAgent] = []
        for agent in self.alive_agents:
            if agent.collides_another():
                agent.die()
                deads.append(agent)
        for agent in deads:
            self.alive_agents.remove(agent)

        # respawn the foods which has been eaten
        self._spawn_missing_food()

        return deads
