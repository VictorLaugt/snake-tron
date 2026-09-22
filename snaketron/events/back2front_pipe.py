from __future__ import annotations

from collections import defaultdict, deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterator

    from events.back2front_protocol import AgentEvent, ArenaEvent


class Back2FrontPipe:
    def __init__(self) -> None:
        self.arena_events: deque[ArenaEvent] = deque()
        self.agent_events: defaultdict[int, deque[AgentEvent]] = defaultdict(deque)
        self.disconnected_agent_ids: deque[int] = deque()

        self.sender = Back2FrontEventSender(self)
        self.receiver = Back2FrontEventReceiver(self)

    def get_sender(self) -> Back2FrontEventSender:
        return self.sender

    def get_receiver(self) -> Back2FrontEventReceiver:
        return self.receiver


class Back2FrontEventSender:
    def __init__(self, pipe: Back2FrontPipe) -> None:
        self.pipe = pipe

    def send_arena_event(self, event: ArenaEvent) -> None:
        # print(f"DEBUG: arena event: {repr(event)}")
        self.pipe.arena_events.append(event)

    def send_agent_event(self, agent_id: int, event: AgentEvent) -> None:
        # print(f"DEBUG: agent {agent_id} event: {repr(event)}")
        self.pipe.agent_events[agent_id].append(event)

    def disconnect_agent(self, agent_id: int) -> None:
        self.pipe.disconnected_agent_ids.append(agent_id)


class Back2FrontEventReceiver:
    def __init__(self, pipe: Back2FrontPipe) -> None:
        self.pipe = pipe

    def recv_arena_events(self) -> Iterator[ArenaEvent]:
        while self.pipe.arena_events:
            yield self.pipe.arena_events.popleft()

    def recv_agent_events(self) -> Iterator[tuple[int, AgentEvent]]:
        # consumes the event FIFO of each agent
        for agent_id, event_fifo in self.pipe.agent_events.items():
            while event_fifo:
                yield agent_id, event_fifo.popleft()

        # removes event FIFO of each agent which has been disconnected
        while self.pipe.disconnected_agent_ids:
            # print(f"DEBUG: disconnecting agent {agent_id}")
            agent_id = self.pipe.disconnected_agent_ids.popleft()
            self.pipe.agent_events.pop(agent_id)
