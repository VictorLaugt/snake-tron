from __future__ import annotations

from collections import deque
import numpy as np
from math import atan2, pi
from array import array

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Ellipse, InstructionGroup


RIGHT = 0
LEFT = 1
UP = 2
DOWN = 3

def angle_diff(alpha, beta):
    delta = beta - alpha
    return min(delta, delta+2*pi, delta-2*pi, key=abs)

def angle_abs_diff(alpha, beta):
    delta = beta - alpha
    return min(abs(delta), abs(delta+2*pi), abs(delta-2*pi))

class TouchArea(Widget):
    def __init__(self, feedback_label, **kwargs):
        super().__init__(**kwargs)
        self.feedback_label = feedback_label

        self.last_pos = None
        self.last_dir = None

        self.instr_line = InstructionGroup()
        self.instr_dot = InstructionGroup()
        self.line_colors = ((0, 1, 0), (0, 1, 1), (0, 0, 1), (1, 0, 1))
        self.canvas.add(self.instr_line)
        self.canvas.add(self.instr_dot)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return

        self.instr_line.clear()
        self.instr_dot.clear()
        self.instr_line.add(Color(*self.line_colors[0]))
        self.instr_dot.add(Color(1, 0, 0, 1))
        self.last_pos = touch.pos

    def _circle(self, center, radius):
        x, y = center
        return Ellipse(pos=(x-radius/2, y-radius/2), size=(radius, radius))

    def on_touch_move(self, touch):
        if not self.collide_point(*touch.pos) or self.last_pos is None:
            return

        x_prev, y_prev = self.last_pos
        x, y = touch.pos
        dx, dy = x-x_prev, y-y_prev
        if dx*dx + dy*dy < 800:
            return

        if abs(dx) > abs(dy):
            direction = RIGHT if dx > 0 else LEFT
        else:
            direction = UP if dy > 0 else DOWN

        if direction != self.last_dir:
            self.instr_line.add(Color(*self.line_colors[direction]))
            self.last_dir = direction

        self.instr_dot.add(self._circle(touch.pos, 10))
        self.instr_line.add(Line(points=(*self.last_pos, *touch.pos), width=2))

        self.last_pos = touch.pos
        return

    def on_touch_up(self, touch):
        self.last_pos = None


class DragApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        feedback_label = Label(text="Glisse ton doigt...", size_hint=(1, 0.1))

        touch_area = TouchArea(feedback_label, size_hint=(1, 0.9))

        layout.add_widget(touch_area)
        layout.add_widget(feedback_label)

        return layout


if __name__ == "__main__":
    DragApp().run()
