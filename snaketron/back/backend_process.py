from __future__ import annotations

import time
from typing import TYPE_CHECKING

from back.world import SnakeWorld
from back.world_factory import SnakeWorldFactory
from debug_tool import backend_debugspace as dbg
from events.abstract_pipe import AbstractEventSender
from events.back2front_protocol import BackendEvent

if TYPE_CHECKING:
    from events.abstract_pipe import AbstractEventReceiver
    from events.front2back_protocol import FrontendEvent

__all__ = ['run_backend_process']


class TrackedBackendEventSender(AbstractEventSender[list[BackendEvent]]):
    def __init__(self, event_sender: AbstractEventSender[list[BackendEvent]]) -> None:
        self.event_sender = event_sender

    def send(self, events: list[BackendEvent]) -> None:
        if len(events) > 0:
            dbg.dprint(f"sending events:\n" + "\n".join(f"  {e}" for e in events))
        else:
            dbg.dprint("sending empty event list")

        self.event_sender.send(events)


class SnakeTronBackend:
    def __init__(
        self,
        world: SnakeWorld,
        time_step: float,
        event_sender: AbstractEventSender[list[BackendEvent]],
        event_receiver: AbstractEventReceiver[FrontendEvent],
    ) -> None:
        self.world = world
        self.time_step = time_step
        self.event_sender = TrackedBackendEventSender(event_sender)
        self.event_receiver = event_receiver

    def get_time_step(self) -> float:
        return self.time_step

    def set_time_step(self, new_time_step: float) -> float:
        self.time_step = new_time_step

    def run(self) -> None:
        dbg.dprint("Start the backend process")
        time.sleep(3)  # FIXME
        while True:
            # event = self.event_receiver.recv()  # should not block
            # dbg.dprint(f"handling event: {event}")
            # self.world.interact(event)

            self.world.simulate()

            self.event_sender.send(self.world.flush_state_updates())
            time.sleep(self.time_step)
    # TODO: replace with an implementation of the following pseudo-code:

    # def run(self):  # boucle du thread principal
    #     while True:
    #         self.running.wait()  # self.running: threading.Event
    #         with self.simulation_interaction_lock:  # self.simulation_interaction_lock: threading.Lock
    #             self.world.simulate()
    #             events = self.world.flush_state_updates()

    #         self.event_sender.send(events)

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
    #                     with self.simulation_interaction_lock:
    #                         self.world.interact(event)


def run_backend_process(
    # configures the game world
    n_snakes: int,
    n_players: int,
    respawn_cooldown: int,

    # configures the interface with the backend
    time_step: float,
    event_sender: AbstractEventSender[BackendEvent],
    event_receiver: AbstractEventReceiver[FrontendEvent],
) -> None:
    world = SnakeWorldFactory.build(n_snakes, n_players, respawn_cooldown)
    backend = SnakeTronBackend(world, time_step, event_sender, event_receiver)
    backend.run()
