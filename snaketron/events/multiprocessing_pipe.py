from __future__ import annotations

from multiprocessing import Queue
from queue import Empty
from typing import TYPE_CHECKING

from events.abstract_pipe import AbstractEventPipe, AbstractEventReceiver, AbstractEventSender

if TYPE_CHECKING:
    from typing import Iterator

__all__ = ['MultiprocessEventPipe', 'MultiprocessEventSender', 'MultiprocessEventReceiver']


class MultiprocessEventPipe[Event](AbstractEventPipe):
    def __init__(self) -> None:
        self.fifo: Queue[Event] = Queue()

        self.sender = MultiprocessEventSender(self.fifo)
        self.receiver = MultiprocessEventReceiver(self.fifo)

    def get_sender(self) -> MultiprocessEventSender[Event]:
        return self.sender

    def get_receiver(self) -> MultiprocessEventReceiver[Event]:
        return self.receiver


class MultiprocessEventSender[Event](AbstractEventSender):
    def __init__(self, fifo: Queue[Event]) -> None:
        self.fifo = fifo

    def send(self, event: Event) -> None:
        self.fifo.put(event)


class MultiprocessEventReceiver[Event](AbstractEventReceiver):
    def __init__(self, fifo: Queue[Event]) -> None:
        self.fifo = fifo

    def recv(self) -> Event:
        return self.fifo.get()
