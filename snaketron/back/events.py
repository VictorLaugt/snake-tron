from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterator

    from back.type_hints import Position


class ArenaEvent:
    pass


@dataclass
class FoodCreated(ArenaEvent):
    pos: Position


@dataclass
class FoodConsumed(ArenaEvent):
    pos: Position


@dataclass
class AgentUpdated:
    new_head_pos: Position
    growth: int
    death: bool


class EventSender:
    def __init__(
        self,
        arena_events: list[ArenaEvent],
        agent_events: dict[int, AgentUpdated]
    ) -> None:
        self.arena_events = arena_events
        self.agent_events = agent_events

    def send_arena_event(self, event: ArenaEvent) -> None:
        print(f"DEBUG: arena event: {event}")
        self.arena_events.append(event)

    def send_agent_event(self, agent_id: int, event: AgentUpdated) -> None:
        print(f"DEBUG: agent {agent_id} event: {event}")
        self.agent_events[agent_id] = event


class EventReceiver:  # TODO: use in the frontend to update the world display
    def __init__(
        self,
        arena_events: list[ArenaEvent],
        agent_events: dict[int, AgentUpdated]
    ) -> None:
        self.arena_events = arena_events
        self.agent_events = agent_events

    def recv_arena_events(self) -> Iterator[ArenaEvent]:
        return iter(self.arena_events)

    def recv_agent_events(self) -> Iterator[tuple[int, AgentUpdated]]:
        while self.agent_events:
            yield self.agent_events.popitem()


def build_event_pipe() -> tuple[EventSender, EventReceiver]:
    arena_events = []
    agent_events = {}
    sender = EventSender(arena_events, agent_events)
    receiver = EventReceiver(arena_events, agent_events)
    return sender, receiver
