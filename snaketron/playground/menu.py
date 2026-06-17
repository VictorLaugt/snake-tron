from kivy.app import App
from kivy.animation import Animation
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.utils import platform
from kivy.graphics import Color, Rectangle, RoundedRectangle, InstructionGroup
from kivy.properties import ListProperty, NumericProperty



KV = """
<AppWindow>:
    orientation: "vertical"

    SwipeControlZone:
        size_hint_y: 0.25

    WorldDisplay:
        size_hint_y: 0.5

    SwipeControlZone:
        size_hint_y: 0.25


<SwipeControlZone>:
    canvas.before:
        Color:
            rgba: 0, 0, 0, 1
        Rectangle:
            pos: self.pos
            size: self.size

    Label:
        text: "SwipeControlZone"
        pos: root.pos
        size: root.size
        halign: "center"
        valign: "middle"
        text_size: self.size


<WorldDisplay>:
    orientation: "vertical"

    canvas.before:
        Color:
            rgba: 0.1, 0.1, 0.1, 1
        Rectangle:
            pos: self.pos
            size: self.size

<PauseMenu>:
    background_color: 0, 0, 0, 0
    overlay_color: 0, 0, 0, 0

    BoxLayout:
        orientation: "vertical"
        padding: root.menu_padding
        spacing: root.menu_padding

        canvas.before:
            Color:
                rgba: root.menu_background_color
            Rectangle:
                pos: self.pos
                size: self.size

        FloatLayout:
            size_hint_y: 4

            canvas.before:
                Color:
                    rgba: 0.3, 0.3, 0.3, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

            Label:
                text: "Add or remove player or AI"
                pos: self.parent.pos
                halign: "center"
                valign: "middle"

        BoxLayout:
            orientation: "horizontal"
            spacing: root.menu_padding

            Button:
                id: button_resume
                text: "Resume"

            ToggleButton:
                text: "Explain AIs"

            ToggleButton:
                text: "Full speed"
"""


class DummyApp(App):
    def __init__(self):
        super().__init__()

    def build(self):
        Builder.load_string(KV)
        window = AppWindow()
        return window

class PauseMenu(ModalView):
    menu_background_color = ListProperty([0, 0, 1, 0.5])
    menu_padding = NumericProperty(10)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, opacity=0)
        self.ids.button_resume.bind(on_press=lambda *_: self.dismiss(animation=False))

    def on_open(self):
        start_size_hint = (0.8 * self.size_hint_x, 0.8 * self.size_hint_y)
        final_size_hint = (self.size_hint_x, self.size_hint_y)

        self.opacity = 0
        self.size_hint = start_size_hint
        anim = (
            Animation(opacity=1, d=0.18, t="out_quad") &
            Animation(size_hint=final_size_hint, d=0.12, t="out_back")
        )
        anim.start(self)

    def dismiss(self, *args, **kwargs):
        self.opacity = 1
        anim = Animation(opacity=0, d=0.18, t="out_quad")
        anim.bind(on_complete=lambda *_: super(PauseMenu, self).dismiss(*args, **kwargs))
        anim.start(self)


class SwipeControlZone(FloatLayout):
    pass


class WorldDisplay(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.draw_stuff, size=self.draw_stuff)

    def draw_stuff(self, *args):
        self.canvas.clear()

        with self.canvas:
            Color(1, 0, 0, 1)
            Rectangle(
                pos=(self.x + self.width * 0.1, self.y + self.height * 0.1),
                size=(self.width * 0.2, self.height * 0.2)
            )

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            PauseMenu(
                size=self.size,
                size_hint=(1, 0.5),
                auto_dismiss=True,
            ).open()
            return True
        return super().on_touch_down(touch)


class AppWindow(BoxLayout):
    def on_kv_post(self, base_widget):
        if platform in ('linux', 'win', 'macosx'):
            screen_width, screen_height = Window.system_size
            width, height = int(432/891 * screen_height), screen_height
            scale = screen_width / width
            if scale < 1:
                width, height = int(width * scale), int(height * scale)
            Window.size = (width, height)


if __name__ == '__main__':
    app = DummyApp()
    app.run()
