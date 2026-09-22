from __future__ import annotations

from collections import defaultdict, deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterator

    from events.back2front_protocol import AgentEvent, ArenaEvent


class Back2FrontEventSender:
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


class Back2FrontEventReceiver:
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


def build_event_pipe() -> tuple[Back2FrontEventSender, Back2FrontEventReceiver]:
    arena_events = deque()
    agent_events = defaultdict(deque)
    disconnected_agent_ids = deque()
    sender = Back2FrontEventSender(arena_events, agent_events, disconnected_agent_ids)
    receiver = Back2FrontEventReceiver(arena_events, agent_events, disconnected_agent_ids)
    return sender, receiver
