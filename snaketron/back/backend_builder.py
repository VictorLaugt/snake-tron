from __future__ import annotations

import time
from itertools import chain
from typing import TYPE_CHECKING

from back.agents import *
from back.direction import *
from back.grid_graph import *
from back.world import *

if TYPE_CHECKING:
    from events.back2front_protocol import BackendEvent
    from events.front2back_protocol import FrontendEvent
    from events.abstract_pipe import AbstractEventReceiver, AbstractEventSender

__all__ = ['SnakeTronBackend']


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


class SnakeTronBackend:
    def __init__(
        self,
        event_sender: AbstractEventSender[BackendEvent],
        event_receiver: AbstractEventReceiver[FrontendEvent],
        n_snakes: int,
        n_players: int,
        respawn_cooldown: int,
        time_step: float,
    ) -> None:
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

        world = SnakeWorld(width, height, n_food, event_sender, event_receiver, respawn_cooldown)
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

        define_opponents(player_agents, ai_agents)

        for agent in chain(player_agents, ai_agents):
            world.attach_agent(agent)

        self.world = world
        self.time_step = time_step

    def get_time_step(self) -> float:
        return self.time_step

    def set_time_step(self, new_time_step: float) -> float:
        self.time_step = new_time_step

    def run(self) -> None:
        time.sleep(3)  # FIXME
        while True:
            self.world.simulate()
            time.sleep(self.time_step)
    # TODO: replace with an implementation of the following pseudo-code:

    # def run(self):  # boucle du thread principal
    #     while True:
    #         self.running.wait()  # self.running: threading.Event
    #         with self.world_lock:  # self.world_lock: threading.Lock
    #             self.world.simulate()
    #         time.sleep(self.time_step)

    # def event_receiver_loop(self):  # target d'un thread daemon secondaire qui écoute les évènements reçu
    #     while True:
    #         for event in self.event_receiver.recv():  # bloquant
    #             match event:
    #                 case RequestPause:
    #                     self.running.set()
    #                 case RequestResume:
    #                     self.running.clear()
    #                 case _:
    #                     with self.world_lock:
    #                         self.world.process_frontend_event(event)
