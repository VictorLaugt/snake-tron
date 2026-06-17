from __future__ import annotations

from collections import deque, defaultdict
from dataclasses import dataclass
from enum import IntEnum, auto

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterator, Optional

    from back.type_hints import Position, Direction


class ArenaEvent:
    pass

@dataclass
class FoodCreated(ArenaEvent):
    pos: Position

@dataclass
class FoodConsumed(ArenaEvent):
    pos: Position
    by: Optional[int]
    # TODO: the frontend should use the field `FoodConsumed.by` to slide the
    # food in the mouth of the snake which eat the food, if any


class AgentEvent:
    pass

class SnakeSimpleEvent(AgentEvent, IntEnum):
    SPAWN = auto()
    DIE = auto()
    DASH = auto()

@dataclass
class SnakeMovement(AgentEvent):
    new_head_pos: Position
    new_dir: Direction
    growth: int

@dataclass
class SnakeWrap(AgentEvent):
    cell_idx: int
    new_cell_pos: Position
    wrap_dir: Direction


class EventSender:
    def __init__(
        self,
        arena_events: deque[ArenaEvent],
        agent_events: defaultdict[int, deque[AgentEvent]],
        disconnected_agent_ids: deque[int],
    ) -> None:
        self.arena_events = arena_events
        self.agent_events = agent_events
        self.disconnected_agent_ids = disconnected_agent_ids

    def send_arena_event(self, event: ArenaEvent) -> None:
        # print(f"DEBUG: arena event: {repr(event)}")
        self.arena_events.append(event)

    def send_agent_event(self, agent_id: int, event: AgentEvent) -> None:
        # print(f"DEBUG: agent {agent_id} event: {repr(event)}")
        self.agent_events[agent_id].append(event)

    def disconnect_agent(self, agent_id: int) -> None:
        self.disconnected_agent_ids.append(agent_id)


class EventReceiver:
    def __init__(
        self,
        arena_events: deque[ArenaEvent],
        agent_events: dict[int, deque[AgentEvent]],
        disconnected_agent_ids: deque[int]
    ) -> None:
        self.arena_events = arena_events
        self.agent_events = agent_events
        self.disconnected_agent_ids = disconnected_agent_ids

    def recv_arena_events(self) -> Iterator[ArenaEvent]:
        while self.arena_events:
            yield self.arena_events.popleft()

    def recv_agent_events(self) -> Iterator[tuple[int, AgentEvent]]:
        # consumes the event FIFO of each agent
        for agent_id, event_fifo in self.agent_events.items():
            while event_fifo:
                yield agent_id, event_fifo.popleft()

        # removes event FIFO of each agent which has been disconnected
        while self.disconnected_agent_ids:
            # print(f"DEBUG: disconnecting agent {agent_id}")
            agent_id = self.disconnected_agent_ids.popleft()
            self.agent_events.pop(agent_id)


def build_event_pipe() -> tuple[EventSender, EventReceiver]:
    arena_events = deque()
    agent_events = defaultdict(deque)
    disconnected_agent_ids = deque()
    sender = EventSender(arena_events, agent_events, disconnected_agent_ids)
    receiver = EventReceiver(arena_events, agent_events, disconnected_agent_ids)
    return sender, receiver
