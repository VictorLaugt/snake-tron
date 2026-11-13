from __future__ import annotations

import abc

__all__ = ['AbstractEventPipe', 'AbstractEventSender', 'AbstractEventReceiver']


class AbstractEventPipe[Event](abc.ABC):
    @abc.abstractmethod
    def get_sender(self) -> AbstractEventSender[Event]:
        pass

    @abc.abstractmethod
    def get_receiver(self) -> AbstractEventReceiver[Event]:
        pass

class AbstractEventSender[Event](abc.ABC):
    @abc.abstractmethod
    def send(self, event: Event) -> None:
        pass


class AbstractEventReceiver[Event](abc.ABC):
    @abc.abstractmethod
    def recv(self) -> Event:
        pass
