from kivy.app import App
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.modalview import ModalView
from kivy.utils import platform
from kivy.graphics import Color, Rectangle, RoundedRectangle, InstructionGroup
from kivy.properties import ListProperty, NumericProperty



KV = """
<AppWindow>:
    orientation: "vertical"

    SwipeControlZone:
        size_hint_y: 0.1

    WorldDisplay:
        size_hint_y: 0.5

    SwipeControlZone:
        size_hint_y: 0.4


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
    canvas.before:
        Color:
            rgba: root.menu_background_color
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        id: menu_content

        pos: root.pos
        size: root.size
        orientation: "vertical"
        padding: root.menu_padding
        spacing: root.menu_padding

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
            size_hint_y: 1
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

class PauseMenu(FloatLayout):
    menu_background_color = ListProperty([0, 0, 1, 0.5])
    menu_padding = NumericProperty(10)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, opacity=0)
        self.ids.button_resume.bind(on_press=lambda *_: self.request_resume())

    def on_touch_down(self, touch):
        if super().on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos):
            return True
        return False

    def request_pause(self):
        content = self.ids.menu_content

        duration = 0.12
        start_size_hint = (0.8 * content.size_hint_x, 0.8 * content.size_hint_y)
        final_size_hint = (content.size_hint_x, content.size_hint_y)
        zoom_in_anim = Animation(size_hint=final_size_hint, d=duration, t="out_back")
        fade_in_anim = Animation(opacity=1, d=duration, t="out_quad")

        content.size_hint = start_size_hint
        zoom_in_anim.start(content)
        fade_in_anim.start(self)

    def request_resume(self):
        content = self.ids.menu_content

        duration = 0.12
        final_size_hint = (0.8 * content.size_hint_x, 0.8 * content.size_hint_y)
        zoom_out_anim = Animation(size_hint=final_size_hint, d=duration, t="out_back")
        fade_out_anim = Animation(opacity=0, d=duration, t="out_quad")

        fade_out_anim.bind(on_complete=lambda *_: self.parent.remove_widget(self))
        zoom_out_anim.start(content)
        fade_out_anim.start(self)


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
        print("DEBUG: WorldDisplay detect touch")

        if super().on_touch_down(touch):
            return True

        if self.collide_point(*touch.pos):
            pause_menu = PauseMenu(
                size_hint=(None, None),
                size=self.size,
                pos=self.to_window(*self.pos),
            )
            self.add_widget(pause_menu)
            pause_menu.request_pause()
            return True

        return False


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
