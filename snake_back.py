from collections import deque
from random import randrange
from abc import ABC, abstractmethod

from typing import Tuple


# directions
Direction = Tuple[int, int]
UP: Direction =    (0,  -1)
DOWN: Direction =  (0,  1)
LEFT: Direction =  (-1, 0)
RIGHT: Direction = (1,  0)


def oposite(direction):
    return (-direction[0], -direction[1])


class AbstractSnakeWorld(ABC):
    """Abstract class for a snake game backend.


    Usage
    ---------------------------------------------------------------------------
    A class which inherits from AbstractSnakeWorld implements a snake game
    backend is it implements the following methods:
    - get_new_food_position
    - moved_square
    - obstacle_hit
    - win

    Then, the instances of such classes can be used throught the following
    methods:
    - reset: Reset the game. (Must be used at least once before starting the
    first game)
    - add_request: Adds a new requested direction in which the snake must move
    - move_snake: Advances the game one step


    Attributes
    ---------------------------------------------------------------------------
    snake: List[Tuple[int, int]]
        Positions of the snake squares. ``snake[0]`` is the snake's head and
        ``snake[1:]`` is the snake's tail.

    food_locations: List[Tuple[int, int]]
        Positions of the foods.

    direction: Tuple[int, int]
        Direction in which the snake is currently moving.

    score: int
        Current score
    """
    def __init__(self, food_number, initial_snake, initial_dir):
        # game constants
        self.initial_direction = initial_dir
        self.initial_snake_position = initial_snake
        self.food_number = food_number

        # game variables
        self.snake = []
        self.food_locations = []
        self.requests = deque((), maxlen=5)
        self.direction = None
        self.score = 0

    def reset(self) -> None:
        """Resets the game variables."""
        self.snake.clear()
        self.snake.extend(self.initial_snake_position)

        self.food_locations.clear()
        for _ in range(self.food_number):
            self.food_locations.append(self.get_new_food_position())

        self.direction = self.initial_direction
        self.requests.clear()

        self.score = len(self.snake)

    def add_request(self, requested_direction: Direction) -> None:
        """Adds a new requested direction in which to move the snake."""
        if len(self.requests) < self.requests.maxlen:
            if len(self.requests) > 0:
                last_direction = self.requests[-1]
            else:
                last_direction = self.direction
            if requested_direction != oposite(last_direction):
                self.requests.append(requested_direction)

    def move_snake(self) -> bool:
        """Moves the snake in the next requested direction.
        Makes the snake grows if it eats a food.
        Returns False if the snake hits an obstacle or its tail, True otherwise.
        """
        # determines the current direction
        if self.requests:
            self.direction = self.requests.popleft()

        # computes the head next position and detects a possible collision with
        # a wall
        head = self.moved_square(self.snake[0], self.direction)
        if self.obstacle_hit(head):
            return False

        # moves the snake tail and detects a possible collision between its head
        # and its tail
        tail_end = self.snake[-1]
        for i in range(len(self.snake)-1, 0, -1):
            tail_square = self.snake[i-1]
            self.snake[i] = tail_square
            if head == tail_square:
                return False
        self.snake[0] = head

        # makes the snake grow if it eats
        for i, food in enumerate(self.food_locations):
            if head == food:
                self.snake.append(tail_end)
                self.score += 1
                self.food_locations[i] = self.get_new_food_position()
                break

        return True

    @abstractmethod
    def get_new_food_position(self) -> Tuple[int, int]:
        """Returns the position of a new food."""

    @abstractmethod
    def moved_square(self, square: Tuple[int, int], direction: Direction) -> Tuple[int, int]:
        """Returns the position of `square` moved in `direction`."""

    @abstractmethod
    def obstacle_hit(self, square: Tuple[int, int]) -> bool:
        """Returns True if `square` touches an obstacle (other than the snake's
        tail), False otherwise.
        """

    @abstractmethod
    def win(self) -> bool:
        """Returns True if the game is won, False otherwise."""



class SnakeWorld(AbstractSnakeWorld):
    """Implements a snake game backend.

    Attributes
    ---------------------------------------------------------------------------
    see AbstractSnakeWorld attributes
    world_width: int
        width of the snake world

    world_height: int
        height of the snake world
    """
    def __init__(self, world_width, world_height, food_number, initial_snake, initial_dir):
        super().__init__(food_number, initial_snake, initial_dir)
        self.world_width = world_width   # x-axis length
        self.world_height = world_height # y-axis length
        self.max_snake_size = (world_height * world_width) - food_number

    def __repr__(self):
        array = [[None]*self.world_width for y in range(self.world_height)]
        for x in range(self.world_width):
            for y in range(self.world_height):
                square = (x, y)
                if square == self.snake[0]:
                    square_repr = 'X'
                elif square in self.snake:
                    square_repr = 'O'
                elif square in self.food_locations:
                    square_repr = '*'
                else:
                    square_repr = '.'
                array[y][x] = square_repr
        return '\n'.join(''.join(row) for row in array)

    def get_new_food_position(self) -> Tuple[int, int]:
        while True:
            new_food = (randrange(self.world_width), randrange(self.world_height))
            if new_food not in self.snake and new_food not in self.food_locations:
                return new_food

    def moved_square(self, square, direction):
        return (square[0] + direction[0], square[1] + direction[1])

    def obstacle_hit(self, square):
        return not (0 <= square[0] < self.world_width and
                    0 <= square[1] <= self.world_height)

    def win(self):
        return len(self.snake) >= self.max_snake_size


class PeriodicSnakeWorld(SnakeWorld):
    """Implements a periodic snake game backend.

    Attributes
    ---------------------------------------------------------------------------
    see SnakeWorld attributes
    """
    def moved_square(self, square, direction):
        return (
            (square[0] + direction[0]) % self.world_width,
            (square[1] + direction[1]) % self.world_height
        )

    def obstacle_hit(self, square):
        return False
