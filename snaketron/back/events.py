from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterator

    from back.type_hints import Position


@dataclass
class FoodUpdate:
    pos: Position
    created: bool


@dataclass
class AgentUpdate:
    new_head_pos: Position
    growth: int
    death: bool


class EventSender:  # TODO: use in the backend class: SnakeWorld
    def __init__(
        self,
        arena_events: list[FoodUpdate],
        agent_events: dict[int, AgentUpdate]
    ) -> None:
        self.arena_events = arena_events
        self.agent_events = agent_events

    def send_arena_event(self, event: FoodUpdate) -> None:
        self.arena_events.append(event)

    def send_agent_event(self, agent_id: int, event: AgentUpdate) -> None:
        self.agent_events[agent_id] = event


class EventReceiver:  # TODO: use in the frontend
    def __init__(
        self,
        arena_events: list[FoodUpdate],
        agent_events: dict[int, AgentUpdate]
    ) -> None:
        self.arena_events = arena_events
        self.agent_events = agent_events

    def recv_arena_events(self) -> Iterator[FoodUpdate]:
        return iter(self.arena_events)

    def recv_agent_events(self) -> Iterator[tuple[int, AgentUpdate]]:
        while self.agent_events:
            yield self.agent_events.popitem()


def new_event_pipe() -> tuple[EventSender, EventReceiver]:  # TODO: use in the __main__.py to link backend and frontend together
    arena_events = []
    agent_events = {}
    sender = EventSender(arena_events, agent_events)
    receiver = EventReceiver(arena_events, agent_events)
    return sender, receiver
