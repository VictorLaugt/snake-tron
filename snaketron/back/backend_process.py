from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING

from back.world import SnakeWorld
from back.world_factory import SnakeWorldFactory
from debug_tool import backend_debugspace as dbg
from events.abstract_pipe import AbstractEventSender
from events.back2front_protocol import BackendEvent
from events.front2back_protocol import *

if TYPE_CHECKING:
    from typing import Optional
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

        self.is_running = threading.Event()
        self.simulation_lock = threading.Lock()
        self.event_receiver_thread = threading.Thread(target=self.event_receiver_loop, daemon=True)

    def _update_simulation_speed(self, pause: Optional[bool], time_step: Optional[float]) -> None:
        if time_step is not None:
            with self.simulation_lock:
                self.time_step = time_step

        if pause is not None:
            if pause:
                self.is_running.clear()
            else:
                self.is_running.set()

    def _interact_with_world(self, event: FrontendEvent) -> None:
        with self.simulation_lock:
            self.world.interact(event)

    def run(self) -> None:
        initial_events = self.world.flush_state_updates()
        self.event_sender.send(initial_events)

        self.event_receiver_thread.start()
        self.is_running.set()
        while True:
            self.is_running.wait()

            with self.simulation_lock:
                self.world.simulate()
                events = self.world.flush_state_updates()
                time_step = self.time_step

            self.event_sender.send(events)
            time.sleep(time_step)

    def event_receiver_loop(self):
        while True:
            event = self.event_receiver.recv()
            dbg.dprint(f"handling event: {event}")
            match event:
                case SimulationSpeedUpdateRequest(pause, time_step):
                    self._update_simulation_speed(pause, time_step)
                case _:
                    self._interact_with_world(event)


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
