from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
import random

from graph import EuclidianDistanceHeuristic
from a_star import shortest_path

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from type_hints import Position, Direction
    from snake_world import SnakeWorld


INF = float('inf')

UP: Direction =    (0,  -1)
DOWN: Direction =  (0,  1)
LEFT: Direction =  (-1, 0)
RIGHT: Direction = (1,  0)


def direction_repr(direction):
    if direction == UP:
        return 'up'
    elif direction == DOWN:
        return 'down'
    elif direction == LEFT:
        return 'left'
    elif direction == RIGHT:
        return 'right'
    else:
        return repr(direction)


def oposite_dir(d: Direction) -> Direction:
    return (-d[0], -d[1])


class AbstractSnakeAgent(ABC):
    ...


class PlayerSnake(AbstractSnakeAgent):
    def __init__(self, world: SnakeWorld, initial_snake_pos: list[Position], initial_snake_dir: Direction) -> None:
        self.world = world
        self.initial_snake_pos = initial_snake_pos
        self.initial_snake_dir = initial_snake_dir

        self.snake_pos: list[Position] = []
        self.snake_dir: Direction = None
        self.dir_requests: deque[Direction] = deque((), maxlen=5)
        self.reset()

    def reset(self) -> None:
        for pos in self.snake_pos:
            self.world.free_pos(pos)
        self.snake_pos.clear()
        self.snake_pos.extend(self.initial_snake_pos)
        self.snake_dir = self.initial_snake_dir
        self.dir_requests.clear()

    def __len__(self) -> int:
        return len(self.snake_pos)

    def add_dir_request(self, request: Direction) -> None:
        """Adds a new requested direction in which to move the snake."""
        if len(self.dir_requests) < self.dir_requests.maxlen:
            if len(self.dir_requests) > 0:
                last_direction = self.dir_requests[-1]
            else:
                last_direction = self.direction
            if request != oposite_dir(last_direction):
                self.dir_requests.append(request)

    def _cut_tail(self, cut_index: int) -> None:
        for i in range(cut_index, len(self.snake_pos)):
            self.world.free_pos(self.snake_pos[i])
        del self.snake_pos[cut_index:]

    def move(self) -> bool:
        """Moves the snake in the next requested direction.
        The snake grows if it eats a food.
        Return True if the snake is still alive after its movement, False otherwise.
        """
        # determines the current direction
        if self.requests:
            self.direction = self.requests.popleft()


        # moves the snake and cuts its tail if its head hits it.
        head = self.world.moved_pos(self.snake_pos[0], self.direction)
        for i in range(len(self.snake_pos)-1, 0, -1):
            self.snake_pos[i] = self.snake_pos[i-1]
            if head == self.snake_pos[i-1]:
                self._cut_tail(i-1)
                break
        self.snake_pos[0] = head

        # detects collision between the head of the snake and an obstacle
        # different from its own tail
        if self.world.pos_is_free(head):
            self.world.obstruct_pos(head)
        else:
            return False

        # makes the snake grow if it eats a food
        tail_end = self.snake_pos[-1]
        if self.world.eat_food(head):
            self.snake_pos.append(tail_end)
            self.world.obstruct_pos(tail_end)

        return True


# class AStarSnake(AbstractSnakeAgent):
#     """Implements a snake that always follows the shortest path to the nearest food,
#     even if it means getting stuck in the long term.

#     TODO: Make the ai agent aware of the world obstacles:
#         - call self.graph.obstruct_position when an obstacle appear
#         - call self.graph.free_position when an obstacle disapear

#     TODO: Make a variant of the agent which recomputes its path at each snake movement
#     """
#     def __init__(self, initial_snake, initial_dir):
#         self.initial_direction = initial_dir
#         self.initial_snake = initial_snake

#         self.snake: list[Position] = []
#         self.ob



#         self.world = world
#         self.snake = snake

#         self.path_x: list[int] = []
#         self.path_y: list[int] = []

#         self.direction: Direction = initial_direction

#     def reset(self):
#         self.graph.free_every_positions()
#         self.snake_position = self.world.snake.copy()
#         self.path_x = []
#         self.path_y = []
#         self.direction_x = None
#         self.direction_y = None

#     def get_direction(self):
#         x, y = self.world.snake[0]

#         min_length = INF
#         length = 0
#         for food in self.world.food_locations:
#             heuristic = EuclidianDistanceHeuristic(*food)
#             path_x, path_y = shortest_path(self.world.graph, (x, y), food, heuristic)
#             length = len(path_x)

#             if 0 < length < min_length and path_x[0] == food[0] and path_y[0] == food[1]:
#                 min_length = length
#                 shortest_path_x = path_x
#                 shortest_path_y = path_y

#         if length > 0:
#             self.path_x = shortest_path_x
#             self.path_y = shortest_path_y
#             self.direction = (shortest_path_x.pop() - x, shortest_path_y.pop() - y)

#         return self.direction

#     def inspect(self):
#         return zip(self.path_x, self.path_y)
