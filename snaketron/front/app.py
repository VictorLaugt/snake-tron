from __future__ import annotations

import json
from threading import Thread
from typing import TYPE_CHECKING

from kivy.app import App
from kivy.clock import mainthread
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.utils import platform

from debug_tool import dbg
from front.controls import *
from front.score_board import *
from front.window import SnakeTronWindow
from front.world_display import *

if TYPE_CHECKING:
    from pathlib import Path

    from back.world import SnakeWorld
    from events.abstract_pipe import AbstractEventReceiver, AbstractEventSender
    from events.back2front_protocol import BackendEvent
    from events.front2back_protocol import FrontendEvent

__all__ = ['SnakeTronFrontend']


class SnakeTronFrontend(App):
    def __init__(
        self,
        event_receiver: AbstractEventReceiver[BackendEvent],
        event_sender: AbstractEventSender[FrontendEvent],
        time_step: float,
        ai_explanations: bool,
        layout_dir: Path,
        color_file: Path,
        input_sensitivity: float,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.event_receiver = event_receiver
        self.event_sender = event_sender
        self.time_step = time_step
        self.ai_explanations = ai_explanations
        self.layout_dir = layout_dir
        self.color_file = color_file
        self.input_sensitivity = input_sensitivity

        self.main_window: SnakeTronWindow = None
        self.event_receiver_thread = Thread(target=self.event_receiver_loop, daemon=True)

    def build(self) -> SnakeTronWindow:
        for layout_file in self.layout_dir.rglob('*.kv'):
            Builder.load_file(str(layout_file))

        with self.color_file.open(mode='r') as fp:
            colors = json.load(fp)

        if platform in ('linux', 'win', 'macosx'):
            screen_width, screen_height = Window.system_size
            width, height = int(432/891 * screen_height), screen_height
            scale = screen_width / width
            if scale < 1:
                width, height = int(width * scale), int(height * scale)
            Window.size = (width, height)

        self.main_window = SnakeTronWindow()
        self.main_window.init_logic(
            self.event_receiver,
            self.event_sender,
            self.time_step,
            self.ai_explanations,
            colors,
            self.input_sensitivity
        )
        self.event_receiver_thread.start()
        return self.main_window

    def event_receiver_loop(self) -> None:
        while True:
            for event in self.event_receiver.recv():
                self.process_backend_event(event)

    @mainthread
    def process_backend_event(self, event: BackendEvent) -> None:
        dbg.dprint(f"frontend handling event: {event}")
        self.main_window.process_backend_event(event)
