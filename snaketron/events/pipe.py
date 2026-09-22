from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING, Generic, TypeVar

from debug_tool import dbg

if TYPE_CHECKING:
    from typing import Iterator


Event = TypeVar("Event")
class EventPipe(Generic[Event]):
    def __init__(self) -> None:
        self.fifo: deque[Event] = deque()

        self.sender = EventSender(self)
        self.receiver = EventReceiver(self)

    def get_sender(self) -> EventSender[Event]:
        return self.sender

    def get_receiver(self) -> EventReceiver[Event]:
        return self.receiver


class EventSender(Generic[Event]):
    def __init__(self, pipe: EventPipe) -> None:
        self.pipe = pipe

    def send(self, event: Event) -> None:
        dbg.dprint(f"send event: {event}")
        self.pipe.fifo.append(event)


class EventReceiver(Generic[Event]):
    def __init__(self, pipe: EventPipe) -> None:
        self.pipe = pipe

    def recv(self) -> Iterator[Event]:
        while self.pipe.fifo:
            event = self.pipe.fifo.popleft()
            dbg.dprint(f"recv event: {event}")
            yield event
