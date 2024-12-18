from __future__ import annotations

from abc import ABC, abstractmethod
import random

import snake_back
import a_star



def direction_repr(direction):
    if direction == snake_back.UP:
        return 'up'
    elif direction == snake_back.DOWN:
        return 'down'
    elif direction == snake_back.LEFT:
        return 'left'
    elif direction == snake_back.RIGHT:
        return 'right'
    else:
        return repr(direction)


INF = float('inf')

class SnakeAi(ABC):
    def __init__(self, world):
        self.set_world(world)

    @abstractmethod
    def set_world(self, world):
        """Initializes the ai to evolve in the given world."""

    @abstractmethod
    def reset(self):
        """Resets the ai."""

    @abstractmethod
    def get_input(self):
        """Returns the next direction in which the ai wants to move the snake."""

    def inspect(self):
        """Returns an iterable of positions to represent the intention of the ai."""
        return
        yield


class RandomSnakeAi(SnakeAi):
    """Implements a dumb snake ai which plays randomly."""
    possible_inputs = (
        snake_back.UP,
        snake_back.DOWN,
        snake_back.LEFT,
        snake_back.RIGHT
    )

    def __init__(self, world):
        super().__init__(world)

    def set_world(self, world):
        pass

    def reset(self):
        pass

    def get_input(self):
        return random.choice(self.possible_inputs)


class NaiveSnakeAi(SnakeAi):
    """Implements a naive snake that always follows the shortest path to the
    nearest food, even if it means getting stuck in the long term.

    TODO: Make the ai agent aware of the world obstacles:
        - call self.graph.obstruct_position when an obstacle appear
        - call self.graph.free_position when an obstacle disapear

    TODO: Make a variant of the agent which recomputes its path at each snake movement
    """
    def __init__(self, world):
        self.world: snake_back.AbstractSnakeWorld = None
        self.graph: a_star.GridGraph = None
        super().__init__(world)

    def set_world(self, world):
        self.world = world
        if isinstance(world, snake_back.PeriodicSnakeWorld):
            self.graph = a_star.PeriodicGridGraph(self.world.world_width, self.world.world_height)
        else:
            self.graph = a_star.GridGraph(self.world.world_width, self.world.world_height)
        self.reset()

    def reset(self):
        self.graph.free_every_positions()
        self.snake_position = self.world.snake.copy()
        self.path_x = []
        self.path_y = []

    def _reached_target(self):
        return len(self.path_x) == 0

    def _acquire_target(self):
        for x, y in self.snake_position:
            self.graph.free_position(x, y)

        self.snake_position = self.world.snake.copy()
        for x, y in self.snake_position:
            self.graph.obstruct_position(x, y)

        min_length = INF
        shortest_path_x = None
        for food in self.world.food_locations:
            path_x, path_y = self.graph.shortest_path(self.world.snake[0], food)
            length = len(path_x)
            if 0 < length < min_length and (path_x[0], path_y[0]) in self.world.food_locations:
                min_length = length
                shortest_path_x = path_x
                shortest_path_y = path_y
        if shortest_path_x is not None:
            self.path_x = shortest_path_x
            self.path_y = shortest_path_y

    def _get_next_direction(self):
        if self._reached_target():
            return None
        else:
            x, y = self.world.snake[0]
            x_next, y_next = self.path_x.pop(), self.path_y.pop()
            return x_next - x, y_next - y

    def get_input(self):
        if self._reached_target():
            self._acquire_target()
        return self._get_next_direction()

    def inspect(self):
        return zip(self.path_x, self.path_y)
