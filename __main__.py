#Pydroid should import tkinter
from __future__ import annotations

from itertools import chain
import argparse

from front import SnakeGameWindow, MobileSnakeGameWindow
from agent import PlayerSnakeAgent, AStarSnakeAgent, AStarOffensiveSnakeAgent
from world import SnakeWorld, EuclidianDistanceHeuristic, EuclidianDistancePeriodicHeuristic,  ManhattanDistanceHeuristic
from direction import UP, DOWN, LEFT, RIGHT

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Sequence
    from agent import AbstractAISnakeAgent


def build_game(
    height: int,
    width: int,
    n_food: int,
    n_players: int,
    respawn_cooldown: int
) -> tuple[SnakeWorld, Sequence[PlayerSnakeAgent], Sequence[AbstractAISnakeAgent]]:
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
    else:
        ai_agents.append(AStarOffensiveSnakeAgent(
            world, blue_init_pos, blue_init_dir,
            EuclidianDistancePeriodicHeuristic,
            latency=0, caution=1, attack_anticipation=attack_anticipation
        ))

    if n_players >= 2:
        player_agents.append(PlayerSnakeAgent(world, yellow_init_pos, yellow_init_dir))
    else:
        ai_agents.append(AStarOffensiveSnakeAgent(
            world, yellow_init_pos, yellow_init_dir,
            EuclidianDistancePeriodicHeuristic,
            latency=0, caution=1, attack_anticipation=attack_anticipation
        ))

    if n_players >= 3:
        player_agents.append(PlayerSnakeAgent(world, purple_init_pos, purple_init_dir))
    else:
        ai_agents.append(AStarOffensiveSnakeAgent(
            world, purple_init_pos, purple_init_dir,
            EuclidianDistanceHeuristic,
            latency=0, caution=1, attack_anticipation=attack_anticipation
        ))

    if n_players >= 4:
        player_agents.append(PlayerSnakeAgent(world, green_init_pos, green_init_dir))
    else:
        ai_agents.append(AStarOffensiveSnakeAgent(
            world, green_init_pos, green_init_dir,
            ManhattanDistanceHeuristic,
            latency=0, caution=3, attack_anticipation=attack_anticipation
        ))

    for ai in ai_agents:
        for player in player_agents:
            ai.add_opponent(player)

    for agent in chain(player_agents, ai_agents):
        world.attach_agent(agent)

    return world, player_agents, ai_agents


parser = argparse.ArgumentParser()
parser.add_argument('--players', type=int, default=1, help='number of players')
parser.add_argument('--food', type=int, default=2, help='number of food')
parser.add_argument('--respawn-cooldown', type=int, default=15, help='')
args = parser.parse_args()

# height, width = 25, 25
height, width = 20, 20
# height, width = 30, 30
# height, width = 40, 40
world, player_agents, ai_agents = build_game(
    height,
    width,
    n_food=args.food,
    n_players=args.players,
    respawn_cooldown=args.respawn_cooldown
)

gui = SnakeGameWindow(
# gui = MobileSnakeGameWindow(
    world,
    player_agents=player_agents,
    ai_agents=ai_agents,
    explain_ai=False,
    # ui_size_coeff=1000/max(height, width),
    ui_size_coeff=500/max(height, width),
    # time_step=100
    time_step=150
    # time_step=200
    # time_step=250
)
gui.mainloop()
