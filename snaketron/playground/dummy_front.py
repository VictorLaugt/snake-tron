from __future__ import annotations

import pprint
from threading import Thread
from typing import TYPE_CHECKING

from kivy.app import App
from kivy.clock import mainthread
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

if TYPE_CHECKING:
    from events.abstract_pipe import AbstractEventReceiver, AbstractEventSender
    from events.back2front_protocol import BackendEvent
    from events.front2back_protocol import FrontendEvent


class DummySnakeTronFrontend(App):
    def __init__(
        self,
        event_receiver: AbstractEventReceiver[BackendEvent],
        event_sender: AbstractEventSender[FrontendEvent]
    ) -> None:
        super().__init__()
        self.event_receiver = event_receiver
        self.current_color = 0

    def build(self):
        layout = BoxLayout(orientation="vertical")

        self.label = Label(text="Waiting...")

        self.button = Button(
            text="Changer la couleur",
            size_hint=(1, 0.2)
        )
        self.button.bind(on_press=self.toggle_color)

        layout.add_widget(self.label)
        layout.add_widget(self.button)

        self.event_receiver_thread = Thread(target=self.event_receiver_loop, daemon=True)
        self.event_receiver_thread.start()

        return layout

    def toggle_color(self, instance):
        self.current_color = 1 - self.current_color

        colors = [
            (1, 1, 1, 1),  # Blanc
            (1, 0, 0, 1)   # Rouge
        ]

        self.label.color = colors[self.current_color]

    def event_receiver_loop(self):
        while True:
            for event in self.event_receiver.recv():
                print(f"frontend handling event {event}")
                self.process_backend_event(event)

    @mainthread
    def process_backend_event(self, event):
        self.label.text = pprint.pformat(event)
