#Pydroid should import kivy
from __future__ import annotations

from itertools import chain
from pathlib import Path

from front import SnakeTronApp
from agent import PlayerSnakeAgent, AStarSnakeAgent, AStarOffensiveSnakeAgent
from world import SnakeWorld, EuclidianDistanceHeuristic, EuclidianDistancePeriodicHeuristic, ManhattanDistanceHeuristic
from direction import UP, DOWN, LEFT, RIGHT

"""
TODO:
 - amélioration des contrôles par swipes pour qu'il soit possible d'entrer plusieurs directions d'affilé sans lever le doigt
 - interface back-front orientée évènements pour que le front n'ai pas besoin de redessiner l'entièreté du monde à chaque étape de jeu
 - étudier la possibilité de ne pas recalculer les chemins les plus courts à chaque étape mais de les conserver dans un cache
"""

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Sequence
    from agent import AbstractAISnakeAgent


def define_opponents(
    player_agents: list[PlayerSnakeAgent],
    ai_agents: list[AStarOffensiveSnakeAgent]
) -> None:
    if len(player_agents) >= 1:
        for ai in ai_agents:
            for player in player_agents:
                ai.add_opponent(player)

    else:
        half = len(ai_agents) // 2
        for agent in ai_agents[half:]:
            for opponent in ai_agents[:half]:
                agent.add_opponent(opponent)


def build_game(
    height: int,
    width: int,
    n_food: int,
    n_snakes: int,
    n_players: int,
    respawn_cooldown: int
) -> tuple[SnakeWorld, Sequence[PlayerSnakeAgent], Sequence[AbstractAISnakeAgent]]:
    if not (0 <= n_snakes <= 4):
        raise ValueError("Too many snakes")
    if not (0 <= n_players <= n_snakes):
        raise ValueError("Too many players")

    dx = int(0.2 * width)
    dy = 1
    init_length = int(0.36 * height)

    x_left = dx
    x_right = width - dx - 1

    blue_init_pos = [(x_left, y) for y in range(init_length-1+dy, -1+dy, -1)]
    yellow_init_pos = [(x_right, y) for y in range(init_length-1+dy, -1+dy, -1)]
    purple_init_pos = [(x_left, y) for y in range(height-1-dy, height-1-init_length-dy, -1)]
    green_init_pos = [(x_right, y) for y in range(height-1-dy, height-1-init_length-dy, -1)]

    blue_init_dir = DOWN
    yellow_init_dir = DOWN
    purple_init_dir = DOWN
    green_init_dir = DOWN

    attack_anticipation = int(0.3*(height + width))

    world = SnakeWorld(width, height, n_food, respawn_cooldown)
    player_agents: list[PlayerSnakeAgent] = []
    ai_agents: list[AStarOffensiveSnakeAgent] = []

    if n_players >= 1:
        player_agents.append(PlayerSnakeAgent(world, blue_init_pos, blue_init_dir))
    elif n_snakes >= 1:
        ai_agents.append(AStarOffensiveSnakeAgent(
            world, blue_init_pos, blue_init_dir,
            # EuclidianDistancePeriodicHeuristic,
            EuclidianDistanceHeuristic,
            latency=0, caution=1, attack_anticipation=attack_anticipation
        ))

    if n_players >= 2:
        player_agents.append(PlayerSnakeAgent(world, yellow_init_pos, yellow_init_dir))
    elif n_snakes >= 2:
        ai_agents.append(AStarOffensiveSnakeAgent(
            world, yellow_init_pos, yellow_init_dir,
            # EuclidianDistancePeriodicHeuristic,
            EuclidianDistanceHeuristic,
            latency=0, caution=1, attack_anticipation=attack_anticipation
        ))

    if n_players >= 3:
        player_agents.append(PlayerSnakeAgent(world, purple_init_pos, purple_init_dir))
    elif n_snakes >= 3:
        ai_agents.append(AStarOffensiveSnakeAgent(
            world, purple_init_pos, purple_init_dir,
            EuclidianDistanceHeuristic,
            latency=0, caution=1, attack_anticipation=attack_anticipation
        ))

    if n_players >= 4:
        player_agents.append(PlayerSnakeAgent(world, green_init_pos, green_init_dir))
    elif n_snakes >= 4:
        ai_agents.append(AStarOffensiveSnakeAgent(
            world, green_init_pos, green_init_dir,
            ManhattanDistanceHeuristic,
            latency=0, caution=3, attack_anticipation=attack_anticipation
        ))

    define_opponents(player_agents, ai_agents)

    for agent in chain(player_agents, ai_agents):
        world.attach_agent(agent)

    return world, player_agents, ai_agents


height, width = 21, 21
# height, width = 23, 23
# height, width = 25, 25
# height, width = 30, 30
# height, width = 40, 40

n_snakes = 4
n_players = 2
respawn_cooldown = 10
n_food = n_snakes - 1

# time_step = 0.2
# time_step = 0.25
time_step = 0.3


world, player_agents, ai_agents = build_game(
    height, width,
    n_food, n_snakes, n_players,
    respawn_cooldown
)
gui = SnakeTronApp(
    world, player_agents, ai_agents,
    time_step, ai_explanations=False,
    layout_file=Path('mobile_layout.kv'),
    color_file=Path('colors', 'dark.json')
)
gui.run()
