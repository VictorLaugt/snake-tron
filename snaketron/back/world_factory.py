from __future__ import annotations

from itertools import chain

from back.agents import *
from back.direction import *
from back.grid_graph import *
from back.world import SnakeWorld


class SnakeWorldFactory:
    @staticmethod
    def define_opponents(
        player_agents: list[PlayerSnakeAgent],
        ai_agents: list[OffensiveAISnakeAgent]
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

    @classmethod
    def build(
        cls,
        n_snakes: int,
        n_players: int,
        respawn_cooldown: int
    ) -> SnakeWorld:
        if not (0 <= n_snakes <= 4):
            raise ValueError("Too many snakes")
        if not (0 <= n_players <= n_snakes):
            raise ValueError("Too many players")

        n_food = max(n_snakes - 1, 1)
        height = width = 3*n_snakes + 9

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

        attack_anticipation = int(0.15*(height + width))

        world = SnakeWorld(width, height, n_food, respawn_cooldown)
        player_agents: list[PlayerSnakeAgent] = []
        ai_agents: list[OffensiveAISnakeAgent] = []

        if n_players >= 1:
            player_agents.append(PlayerSnakeAgent(world, blue_init_pos, blue_init_dir))
        elif n_snakes >= 1:
            ai_agents.append(OffensiveAISnakeAgent(
                world, blue_init_pos, blue_init_dir,
                # EuclidianDistancePeriodicHeuristic,
                EuclidianDistanceHeuristic,
                latency=3, caution=4, attack_anticipation=attack_anticipation
            ))

        if n_players >= 2:
            player_agents.append(PlayerSnakeAgent(world, yellow_init_pos, yellow_init_dir))
        elif n_snakes >= 2:
            ai_agents.append(OffensiveAISnakeAgent(
                world, yellow_init_pos, yellow_init_dir,
                # EuclidianDistancePeriodicHeuristic,
                EuclidianDistanceHeuristic,
                latency=3, caution=4, attack_anticipation=attack_anticipation
            ))

        if n_players >= 3:
            player_agents.append(PlayerSnakeAgent(world, purple_init_pos, purple_init_dir))
        elif n_snakes >= 3:
            ai_agents.append(OffensiveAISnakeAgent(
                world, purple_init_pos, purple_init_dir,
                EuclidianDistanceHeuristic,
                latency=3, caution=6, attack_anticipation=attack_anticipation
            ))

        if n_players >= 4:
            player_agents.append(PlayerSnakeAgent(world, green_init_pos, green_init_dir))
        elif n_snakes >= 4:
            ai_agents.append(OffensiveAISnakeAgent(
                world, green_init_pos, green_init_dir,
                ManhattanDistanceHeuristic,
                latency=3, caution=4, attack_anticipation=attack_anticipation
            ))

        cls.define_opponents(player_agents, ai_agents)

        for agent in chain(player_agents, ai_agents):
            world.attach_agent(agent)

        return world
