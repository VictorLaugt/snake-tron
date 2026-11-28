from __future__ import annotations

import threading
import logging
import time
from typing import TYPE_CHECKING

from snaketron.back.world import SnakeWorld
from snaketron.back.world_factory import SnakeWorldFactory
from snaketron.events.abstract_pipe import AbstractEventSender
from snaketron.events.back2front_protocol import *
from snaketron.events.front2back_protocol import *

if TYPE_CHECKING:
    from typing import Optional
    from snaketron.events.abstract_pipe import AbstractEventReceiver
    from snaketron.events.front2back_protocol import FrontendEvent

__all__ = ['run_backend_process']

logger = logging.getLogger(__name__)


class TrackedBackendEventSender(AbstractEventSender[list[BackendEvent]]):
    def __init__(self, event_sender: AbstractEventSender[list[BackendEvent]]) -> None:
        self.event_sender = event_sender

    def send(self, events: list[BackendEvent]) -> None:
        if len(events) > 0:
            logger.info(f"sending events:\n" + "\n".join(f"  {e}" for e in events))
        else:
            logger.info("sending empty event list")

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

        self.inspected_ai_snakes: list[int] = []

    def _simulate(self) -> list[BackendEvent]:
        self.world.simulate()
        events = self.world.flush_state_updates()

        for snake_id in self.inspected_ai_snakes:
            ai_inspection = AiSnakeInspection(snake_id, list(self.world.inspect_ai(snake_id)))
            events.append(ai_inspection)

        return events

    def _update_simulation_speed(self, time_step: Optional[float], pause: Optional[bool]) -> None:
        if time_step is not None:
            self.time_step = time_step

        if pause is not None:
            if pause:
                self.is_running.clear()
            else:
                self.is_running.set()

    def run(self) -> None:
        initial_events = self.world.flush_state_updates()
        self.event_sender.send(initial_events)

        self.event_receiver_thread.start()
        self.is_running.set()
        while True:
            self.is_running.wait()

            with self.simulation_lock:
                events = self._simulate()
                time_step = self.time_step

            self.event_sender.send(events)
            time.sleep(time_step)

    def event_receiver_loop(self):
        while True:
            event = self.event_receiver.recv()
            with self.simulation_lock:
                logger.info(f"handling event: {event}")
                match event:
                    case SimulationSpeedUpdateRequest(time_step, pause):
                        self._update_simulation_speed(time_step, pause)

                    case AiInspectionRequest(snake_id, enable_inspection=True):
                        self.inspected_ai_snakes.append(snake_id)
                    case AiInspectionRequest(snake_id, enable_inspection=False):
                        self.inspected_ai_snakes.remove(snake_id)

                    case PlayerDirRequest(snake_id, dir_request):
                        self.world.add_player_dir_request(snake_id, dir_request)


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
