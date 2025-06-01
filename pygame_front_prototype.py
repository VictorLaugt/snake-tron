import pygame
from itertools import chain
from dataclasses import dataclass
from direction import UP, DOWN, LEFT, RIGHT

# Couleurs Pygame = RGB
@dataclass
class SnakeColors:
    head_color: tuple
    tail_color: tuple
    dead_color: tuple
    inspect_color: tuple

class PygameGameWindow:
    HEAD_COLORS = [(0, 102, 204), (209, 147, 0), (148, 0, 211), (0, 128, 0)]
    TAIL_COLORS = [(0, 136, 238), (243, 181, 0), (238, 130, 238), (0, 100, 0)]

    FOOD_COLOR = (255, 0, 0)
    FOOD_OUTLINE = (255, 102, 102)
    DEAD_COLOR = (139, 0, 0)
    INSPECT_COLOR = (0, 0, 96)
    BG_COLOR = (0, 0, 48)
    GRIDLINE_COLOR = (0, 0, 144)

    def __init__(self, snake_world, player_agents, ai_agents, explain_ai, square_size, fps):
        pygame.init()
        self.world = snake_world
        self.world.reset()

        self.player_snakes = player_agents
        self.ai_snakes = ai_agents
        self.snake_colors = [None] * (len(player_agents) + len(ai_agents))
        self.square_size = square_size
        self.fps = fps
        self.explain_ai = explain_ai

        self.width = self.world.get_width() * square_size
        self.height = self.world.get_height() * square_size

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Snake Game")

        self.clock = pygame.time.Clock()
        self.running = True
        self.paused = False

        for snake in chain(player_agents, ai_agents):
            idx = min(snake.get_id(), len(self.HEAD_COLORS) - 1)
            self.snake_colors[snake.get_id()] = SnakeColors(
                self.HEAD_COLORS[idx],
                self.TAIL_COLORS[idx],
                self.DEAD_COLOR,
                self.INSPECT_COLOR
            )

    def draw_square(self, x, y, color, outline=None):
        rect = pygame.Rect(x, y, self.square_size, self.square_size)
        pygame.draw.rect(self.screen, color, rect)
        if outline:
            pygame.draw.rect(self.screen, outline, rect, 1)

    def draw_circle(self, x, y, color, outline=None):
        center = (x + self.square_size // 2, y + self.square_size // 2)
        radius = self.square_size // 2
        pygame.draw.circle(self.screen, color, center, radius)
        if outline:
            pygame.draw.circle(self.screen, outline, center, radius, 1)

    def pos_to_coord(self, pos):
        return pos[0] * self.square_size, pos[1] * self.square_size

    def draw_grid(self):
        for x in range(0, self.width, self.square_size * 3):
            pygame.draw.line(self.screen, self.GRIDLINE_COLOR, (x, 0), (x, self.height))
        for y in range(0, self.height, self.square_size * 3):
            pygame.draw.line(self.screen, self.GRIDLINE_COLOR, (0, y), (self.width, y))

    def draw_world(self, dead_snakes):
        self.screen.fill(self.BG_COLOR)
        self.draw_grid()

        for snake in self.world.iter_alive_agents():
            colors = self.snake_colors[snake.get_id()]
            cells = list(snake.iter_cells())
            if not cells:
                continue
            x, y = self.pos_to_coord(cells[0])
            self.draw_square(x, y, colors.head_color, colors.tail_color)
            for pos in cells[1:]:
                x, y = self.pos_to_coord(pos)
                self.draw_square(x, y, colors.tail_color, colors.tail_color)

        for food in self.world.iter_food():
            x, y = self.pos_to_coord(food)
            self.draw_circle(x, y, self.FOOD_COLOR, self.FOOD_OUTLINE)

        for snake in dead_snakes:
            colors = self.snake_colors[snake.get_id()]
            for pos in snake.iter_cells():
                x, y = self.pos_to_coord(pos)
                self.draw_square(x, y, colors.dead_color)

        if self.explain_ai:
            for snake in self.ai_snakes:
                for pos in snake.inspect():
                    x, y = self.pos_to_coord(pos)
                    self.draw_square(x, y, self.INSPECT_COLOR)

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_RETURN:
                    self.world.reset()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_e:
                    self.explain_ai = not self.explain_ai

        keys = pygame.key.get_pressed()
        for idx, snake in enumerate(self.player_snakes):
            if idx == 0:
                if keys[pygame.K_UP]:
                    snake.add_dir_request(UP)
                elif keys[pygame.K_DOWN]:
                    snake.add_dir_request(DOWN)
                elif keys[pygame.K_LEFT]:
                    snake.add_dir_request(LEFT)
                elif keys[pygame.K_RIGHT]:
                    snake.add_dir_request(RIGHT)

    def run(self):
        while self.running:
            self.handle_input()
            if not self.paused:
                dead = self.world.simulate()
                self.draw_world(dead)
            pygame.display.flip()
            self.clock.tick(self.fps)

        pygame.quit()
