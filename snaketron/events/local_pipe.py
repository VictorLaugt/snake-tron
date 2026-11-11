from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from debug_tool import dbg
from events.abstract_pipe import AbstractEventPipe, AbstractEventReceiver, AbstractEventSender

if TYPE_CHECKING:
    from typing import Iterator

__all__ = ['LocalEventPipe', 'LocalEventSender', 'LocalEventReceiver']


class LocalEventPipe[Event](AbstractEventPipe):
    def __init__(self) -> None:
        self.fifo: deque[Event] = deque()

        self.sender = LocalEventSender(self)
        self.receiver = LocalEventReceiver(self)

    def get_sender(self) -> LocalEventSender[Event]:
        return self.sender

    def get_receiver(self) -> LocalEventReceiver[Event]:
        return self.receiver


class LocalEventSender[Event](AbstractEventSender):
    def __init__(self, pipe: LocalEventPipe[Event]) -> None:
        self.pipe = pipe

    def send(self, event: Event) -> None:
        self.pipe.fifo.append(event)


class LocalEventReceiver[Event](AbstractEventReceiver):
    def __init__(self, pipe: LocalEventPipe[Event]) -> None:
        self.pipe = pipe

    def recv(self) -> Iterator[Event]:
        while self.pipe.fifo:
            event = self.pipe.fifo.popleft()
            yield event
