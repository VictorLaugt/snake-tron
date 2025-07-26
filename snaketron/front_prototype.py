from __future__ import annotations

from kivy.config import Config
Config.set('graphics', 'width', '432')
Config.set('graphics', 'height', '891')

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.event import EventDispatcher
from kivy.graphics import Rectangle, Color, Line, Ellipse, InstructionGroup
from kivy.lang import Builder
from kivy.properties import NumericProperty, ListProperty

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout

from kivy.uix.widget import Widget
from kivy.uix.label import Label

from kivy.utils import get_color_from_hex

from dataclasses import dataclass

from direction import UP, DOWN, LEFT, RIGHT

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from world import SnakeWorld
    from agent import AbstractSnakeAgent, AbstractAISnakeAgent, PlayerSnakeAgent

    from kivy.clock import ClockEvent
    from kivy.core.window import WindowBase

    from typing import TypeAlias, Sequence, Iterable, Optional
    from type_hints import Position
    Coordinate: TypeAlias = tuple[float, float]
    ColorValue: TypeAlias = tuple[float, float, float, float]


MINIMAL_TIME_STEP = 0.01


@dataclass
class WorldColors:
    food_outline: ColorValue
    food: ColorValue
    background: ColorValue
    gridline: ColorValue
    gridborder: ColorValue


@dataclass
class SnakeColors:
    head: ColorValue
    tail: ColorValue
    dead: ColorValue
    inspect: ColorValue


class WorldDisplay(FloatLayout):
    square_size = NumericProperty(0.)

    world: SnakeWorld
    ai_snakes: Sequence[AbstractAISnakeAgent]
    world_colors: WorldColors
    snake_colors: dict[int, SnakeColors]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.draw_instr = InstructionGroup()
        self.canvas.add(self.draw_instr)

    def init_logic(
        self,
        world: SnakeWorld,
        ai_snakes: Sequence[AbstractAISnakeAgent],
        world_colors: WorldColors,
        snake_colors: dict[int, SnakeColors]
    ) -> None:
        self.world = world
        self.ai_snakes = ai_snakes
        self.world_colors = world_colors
        self.snake_colors = snake_colors

    def pos_to_coord(self, pos: Position) -> Coordinate:
        return (
            self.x + pos[0] * self.square_size,
            self.y + (self.world.get_height() - 1 - pos[1]) * self.square_size
        )

    def draw_square(self, x: float, y: float, c: ColorValue) -> None:
        self.draw_instr.add(Color(*c))
        self.draw_instr.add(Rectangle(pos=(x, y), size=(self.square_size, self.square_size)))

    def draw_circle(self, x: float, y: float, c: ColorValue) -> None:
        self.draw_instr.add(Color(*c))
        self.draw_instr.add(Ellipse(pos=(x, y), size=(self.square_size, self.square_size)))

    def _draw_world(self) -> None:
        h, w = self.world.get_height(), self.world.get_width()

        # background
        self.draw_instr.add(Color(*self.world_colors.background))
        self.draw_instr.add(Rectangle(pos=self.pos, size=(w*self.square_size, h*self.square_size)))

        # grid lines every 3 cells
        self.draw_instr.add(Color(*self.world_colors.gridline))
        for u in range(3, w, 3):
            x = self.x + u*self.square_size
            y0 = self.y
            y1 = self.y + h*self.square_size
            self.draw_instr.add(Line(points=(x, y0, x, y1)))
        for v in range(3, h, 3):
            y = self.y + (h-v)*self.square_size
            x0 = self.x
            x1 = self.x + w*self.square_size
            self.draw_instr.add(Line(points=(x0, y, x1, y)))

        # grid border
        self.draw_instr.add(Color(*self.world_colors.gridborder))
        self.draw_instr.add(Line(points=(
            self.x, self.y,
            self.x + w*self.square_size, self.y
        )))
        self.draw_instr.add(Line(points=(
            self.x, self.y + h*self.square_size,
            self.x + w*self.square_size, self.y + h*self.square_size
        )))
        self.draw_instr.add(Line(points=(
            self.x, self.y,
            self.x, self.y + h*self.square_size
        )))
        self.draw_instr.add(Line(points=(
            self.x + w*self.square_size, self.y,
            self.x + w*self.square_size, self.y + h*self.square_size
        )))

    def _draw_ai_inspection(self) -> None:
        for snake in self.ai_snakes:
            color = self.snake_colors[snake.get_id()].inspect
            for pos in snake.inspect():
                x, y = self.pos_to_coord(pos)
                self.draw_square(x, y, color)

    def _draw_alive_snakes(self) -> None:
        for snake in self.world.iter_alive_agents():
            colors = self.snake_colors[snake.get_id()]
            cells = list(snake.iter_cells())
            for i, pos in enumerate(cells):
                x, y = self.pos_to_coord(pos)
                self.draw_square(x, y, colors.head if i == 0 else colors.tail)

    def _draw_food(self) -> None:
        for food in self.world.iter_food():
            x, y = self.pos_to_coord(food)
            self.draw_circle(x, y, self.world_colors.food)

    def _draw_killed_snakes(self, dead_snakes: Iterable[AbstractSnakeAgent]) -> None:
        for snake in dead_snakes:
            color = self.snake_colors[snake.get_id()].dead
            for pos in snake.iter_cells():
                x, y = self.pos_to_coord(pos)
                self.draw_square(x, y, color)

    def recompute_square_size(self) -> None:
        self.square_size = min(
            self.height / self.world.get_height(),
            self.width / self.world.get_width()
        )

    def on_square_size(self, instance: Widget, value: float) -> None:
        self.draw()

    def draw(
        self,
        dead_snakes: Iterable[AbstractSnakeAgent]=(),
        ai_explanations: bool=False
    ) -> None:
        self.draw_instr.clear()
        self._draw_world()
        if ai_explanations:
            self._draw_ai_inspection()
        self._draw_alive_snakes()
        self._draw_food()
        self._draw_killed_snakes(dead_snakes)


class SwipeControlZone(Widget):
    ...


class ColoredLabel(Label):
    box_color = ListProperty([1., 1., 1., 1.])


class ScoreBoard(BoxLayout):
    snakes: Sequence[AbstractSnakeAgent]
    snake_colors: dict[int, SnakeColors]
    labels: dict[int, Label]

    def init_logic(
        self,
        snakes: Sequence[AbstractSnakeAgent],
        snake_colors: dict[int, SnakeColors]
    ) -> None:
        self.snakes = snakes
        self.snake_colors = snake_colors
        self.labels = {}
        for snake in self.snakes:
            snake_id = snake.get_id()
            label = ColoredLabel(
                text=str(len(snake)),
                color=(1, 1, 1, 1),
                box_color=self.snake_colors[snake_id].tail
            )
            self.labels[snake_id] = label
            self.add_widget(label)

    def update_scores(self) -> None:
        for snake in self.snakes:
            self.labels[snake.get_id()].text = str(len(snake))


class KeyBoardControls(EventDispatcher):
    player: PlayerSnakeAgent

    def __init__(self, player: PlayerSnakeAgent) -> None:
        super().__init__()
        self.player = player
        Window.bind(on_key_down=self.on_key_down)

    def on_key_down(
        self,
        window: WindowBase,
        key: int,
        scancode: int,
        codepoint: Optional[str],
        modifiers: Sequence[str]
    ) -> None:
        if key == 273:
            self.player.add_dir_request(UP)
        elif key == 274:
            self.player.add_dir_request(DOWN)
        elif key == 275:
            self.player.add_dir_request(RIGHT)
        elif key == 276:
            self.player.add_dir_request(LEFT)


class SnakeTronWindow(BoxLayout):
    world: SnakeWorld
    player_agents: Sequence[PlayerSnakeAgent]
    swipe_zones: list[SwipeControlZone]
    keyboard_controls: KeyBoardControls
    paused: bool
    full_speed: bool
    ai_explanations: bool
    regular_time_step: float
    time_step: float
    clock_event: ClockEvent

    def on_kv_post(self, base_widget: Widget) -> None:
        self.swipe_zones = []
        for child in self.children:
            if isinstance(child, SwipeControlZone):
                self.swipe_zones.append(child)

    def init_logic(
        self,
        world: SnakeWorld,
        player_agents: Sequence[PlayerSnakeAgent],
        ai_agents: Sequence[AbstractAISnakeAgent],
        time_step: float,
        ai_explanations: bool
    ) -> None:
        # link to the backend
        self.world = world
        self.player_agents = player_agents
        self.world.reset()

        # game speed
        self.paused = False
        self.full_speed = False
        self.ai_explanations = ai_explanations
        self.regular_time_step = time_step
        self.time_step = time_step

        # colors
        agent_colors = {}
        head_color_wheel = ('#0066CC', '#D19300', '#9400D3', '#008000')
        tail_color_wheel = ('#0088EE', '#F3B500', '#EE82EE', '#006400')
        agents: list[AbstractSnakeAgent] = list(chain(player_agents, ai_agents))
        for a in agents:
            agent_id = a.get_id()
            agent_colors[agent_id] = SnakeColors(
                head=get_color_from_hex(head_color_wheel[agent_id % len(head_color_wheel)]),
                tail=get_color_from_hex(tail_color_wheel[agent_id % len(tail_color_wheel)]),
                dead=get_color_from_hex('#8B0000'),
                inspect=get_color_from_hex('#000060')
            )

        world_colors = WorldColors(
            food_outline=get_color_from_hex('#FF6666'),
            food=get_color_from_hex('#FF0000'),
            background=get_color_from_hex('#000030'),
            gridline=get_color_from_hex('#000090'),
            gridborder=get_color_from_hex('#005690')
        )
        self.ids.world_display.init_logic(world, ai_agents, world_colors, agent_colors)
        self.ids.score_board.init_logic(agents, agent_colors)

        # player inputs
        if len(player_agents) >= 1:
            self.keyboard_controls = KeyBoardControls(player_agents[0])
        # TODO: dispatch players into the swipe zones and color each swipe zone
        # in its player color

        self.clock_event = Clock.schedule_interval(self.game_step, self.time_step)

    def game_step(self, dt: float) -> None:
        deads = self.world.simulate()
        self.ids.world_display.draw(deads, self.ai_explanations)
        self.ids.score_board.update_scores()

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        if self.paused:
            Clock.unschedule(self.clock_event)
        else:
            self.clock_event = Clock.schedule_interval(self.game_step, self.time_step)

    def toggle_fullspeed(self) -> None:
        self.full_speed = not self.full_speed
        if self.full_speed:
            self.set_time_step(MINIMAL_TIME_STEP)
        else:
            self.set_time_step(self.regular_time_step)

    def set_time_step(self, new_time_step: float) -> None:
        self.time_step = new_time_step
        if not self.paused:
            Clock.unschedule(self.clock_event)
            self.clock_event = Clock.schedule_interval(self.game_step, self.time_step)

    def toggle_ai_explanations(self) -> None:
        self.ai_explanations = not self.ai_explanations


class SnakeTronApp(App):
    def __init__(
        self,
        world: SnakeWorld,
        player_agents: Sequence[PlayerSnakeAgent],
        ai_agents: Sequence[AbstractAISnakeAgent],
        time_step: float,
        ai_explanations: bool,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.world = world
        self.player_agents = player_agents
        self.ai_agents = ai_agents
        self.time_step = time_step
        self.ai_explanations = ai_explanations

    def build(self) -> None:
        Builder.load_file('mobile_layout.kv')
        window = SnakeTronWindow()
        window.init_logic(
            self.world,
            self.player_agents,
            self.ai_agents,
            self.time_step,
            self.ai_explanations
        )
        return window


if __name__ == '__main__':
    from world import SnakeWorld, EuclidianDistanceHeuristic
    from agent import PlayerSnakeAgent, AStarOffensiveSnakeAgent
    from direction import UP, DOWN, LEFT, RIGHT
    from itertools import chain

    world = SnakeWorld(20, 20, 3, 5)
    players = [
        PlayerSnakeAgent(world, [(5,5), (5,6), (5,7)], RIGHT)
    ]
    ais = [
        AStarOffensiveSnakeAgent(world, [(15,7), (15,6), (15,5)], LEFT, EuclidianDistanceHeuristic),
        AStarOffensiveSnakeAgent(world, [(16,7), (16,6), (16,5)], DOWN, EuclidianDistanceHeuristic)
    ]
    for agent in chain(players, ais):
        world.attach_agent(agent)

    gui = SnakeTronApp(world, players, ais, 0.2, False)
    # gui = SnakeTronApp(world, players, ais, 100, False)
    gui.run()
