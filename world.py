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

        self.vertices = np.ones((self.height, self.width), dtype=bool)
        self.food_pos: list[Position] = []
        self.snake_agents: list[AbstractSnakeAgent] = []

    def __repr__(self) -> str:
        array = [['.']*self.world_width for y in range(self.world_height)]
        for x, y in self.food_pos:
            array[y][x] = '*'
        for agent in self.snake_agents:
            x, y = agent.snake_pos[0]
            array[y][x] = '@'
            for x, y in agent.snake_pos[1:]:
                array[y][x] = 'O'
        return '\n'.join(''.join(row) for row in array)


    # ---- private
    def _get_new_food_pos(self) -> Optional[Position]:
        if sum(len(agent) for agent in self.snake_agents) + len(self.food_pos) >= self.width * self.height:
            return None
        while True:
            new_food = (randrange(self.world_width), randrange(self.world_height))
            if self.pos_is_free(new_food) and new_food not in self.food_pos:
                return new_food


    # ---- public
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

    def reset(self) -> None:
        """Reset the world and all its agents to make them ready to start a new game."""
        self.food_pos.clear()
        for _ in range(self.n_food):
            new_food = self._get_new_food_pos()
            if new_food is not None:
                self.food_pos.append(new_food)
        for agent in self.snake_agents:
            agent.reset()
        assert np.all(self.vertices)


    def eat_food(self, p: Position) -> bool:
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


    def pos_is_free(self, p: Position) -> bool:
        """Returns True if no obstacle is on the position `p`, False otherwise."""
        return self.vertices[p[1], p[0]]

    def free_pos(self, p: Position) -> None:
        """Removes any obstacle from the position `p`."""
        self.vertices[p[1], p[0]] = True

    def obstruct_pos(self, p: Position) -> None:
        """Put an obstacle on the position `p`."""
        self.vertices[p[1], p[0]] = False


    def get_neighbor(self, p: Position, d: Direction) -> Position:
        """Returns the neighbor of position `p` in the direction `d`."""
        return (p[0] + d[0]) % self.width, (p[1] + d[1]) % self.height

    def iter_free_neighbors(self, p: Position) -> Iterator[Position]:
        """Iterates over each neighbor of position `p` which does not contains
        any obstacle.
        """
        x, y = p

        y_up, x_up = (y-1) % self.height, x
        y_down, x_down = (y+1) % self.height, x
        y_left, x_left = y, (x-1) % self.width
        y_right, x_right = y, (x+1) % self.width

        if self.vertices[y_up, x_up]:
            yield x_up, y_up
        if self.vertices[y_down, x_down]:
            yield x_down, y_down
        if self.vertices[y_left, x_left]:
            yield x_left, y_left
        if self.vertices[y_right, x_right]:
            yield x_right, y_right
