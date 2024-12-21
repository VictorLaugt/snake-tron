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


class SnakeWorld:
    def __init__(self, width: int, height: int, n_food: int) -> None:
        self.width = width
        self.height = height
        self.n_food = n_food

        self.vertices = np.ones((self.width, self.height), dtype=bool)
        self.food_pos: list[Position] = []
        self.snake_agents: list[AbstractSnakeAgent] = []


    # ---- private
    def _get_new_food_pos(self) -> Optional[Position]:
        """Returns an available position to spawn a new food if any, else
        returns None.
        """
        if sum(len(agent) for agent in self.snake_agents) + len(self.food_pos) >= self.width * self.height:
            return None
        while True:
            new_food = (randrange(self.world_width), randrange(self.world_height))
            if self.vertices[new_food] and new_food not in self.food_pos:
                return new_food

    def _eat_food(self, p: Position) -> bool:
        """If there is a food at position `p`, it is removed and replaced by a
        new food at a random position, then True is returned. Otherwise, False
        is returned.
        """
        for i in range(len(self.food_pos)):
            if p == self.food_pos[i]:
                new_food = self._get_new_food_pos()
                if new_food is not None:
                    self.food_pos[i] = new_food
                return True
        return False


    # ---- public
    def reset(self) -> None:
        """Reset the world and all its agents to make them ready to start a new game."""
        self.food_pos.clear()
        for _ in range(self.n_food):
            new_food = self._get_new_food_pos()
            if new_food is not None:
                self.food_pos.append(new_food)
        for agent in self.snake_agents:
            agent.reset()


    def iter_agents(self) -> Iterator[AbstractSnakeAgent]:
        """Iterates over the agents of the world."""
        yield from self.snake_agents

    def new_player_agent(self, initial_pos: Sequence[Position], initial_dir: Direction) -> PlayerSnakeAgent:
        """Adds a new playable agent in the world and returns it."""
        agent = PlayerSnakeAgent(self, initial_pos, initial_dir)
        self.snake_agents.append(agent)
        return agent

    def new_ai_agent(self, initial_pos: Sequence[Position], initial_dir: Direction) -> AStarSnakeAgent:
        """Adds a new ai agent in the world and returns it."""
        agent = AStarSnakeAgent(self, initial_pos, initial_dir)
        self.snake_agents.append(agent)
        return agent


    def pos_is_free(self, p: Position) -> bool:
        """Returns True if no obstacle is on the position `p`, False otherwise."""
        return self.vertices[p]

    def free_pos(self, p: Position) -> None:
        """Removes obstacle from the position `p`."""
        self.vertices[p] = True

    def obstruct_pos(self, p: Position) -> None:
        """Puts an obstacle on the position `p`."""
        self.vertices[p] = False


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

        if self.vertices[up]:
            yield up
        if self.vertices[down]:
            yield down
        if self.vertices[left]:
            yield left
        if self.vertices[right]:
            yield right
