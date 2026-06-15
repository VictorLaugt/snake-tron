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
"""


class DummyApp(App):
    def __init__(self):
        super().__init__()

    def build(self):
        Builder.load_string(KV)
        window = AppWindow()
        return window


class SwipeControlZone(FloatLayout):
    pass


class PauseMenu(ModalView):
    def __init__(self, **kwargs):
        super().__init__(
            background_color=(0, 0, 0, 0),
            overlay_color=(0, 0, 0, 0),
            opacity=0,  # start invisible
            **kwargs
        )

        # --- container principal ---
        self.container = BoxLayout(
            orientation="vertical",
            padding=20,
            spacing=15
        )

        with self.container.canvas.before:
            Color(0.5, 1, 0.5, 0.12)  # effet verre
            self.bg = Rectangle(
                pos=self.container.pos,
                size=self.container.size
            )

        self.container.bind(pos=self.update_bg, size=self.update_bg)

        # TODO: extract content into another class whose layout is defined in the KV string
        self.container.add_widget(Label(
            text="Pause",
            bold=True,
            color=(1, 1, 1, 1)
        ))

        btn = Button(
            text="Resume",
            size_hint=(1, 0.3)
        )
        btn.bind(on_release=lambda x: self.dismiss())

        self.container.add_widget(btn)
        self.add_widget(self.container)

    def update_bg(self, *args):
        self.bg.pos = self.container.pos
        self.bg.size = self.container.size

    def on_open(self):
        self.scale = 0.9
        self.opacity = 0

        anim = Animation(
            opacity=1,
            d=0.18*10,
            t="out_quad"
        ) + Animation(
            d=0.12*10,
            scale=1,
            t="out_back"
        )

        anim.start(self)


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
            # self.show_modal()
            PauseMenu(
                size=self.size,
                size_hint=(1, 0.5),
                auto_dismiss=False,
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
