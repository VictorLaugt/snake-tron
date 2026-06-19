from __future__ import annotations

from typing import TYPE_CHECKING

from kivy.animation import Animation
from kivy.properties import ListProperty, NumericProperty
from kivy.utils import get_color_from_hex
from kivy.uix.floatlayout import FloatLayout

if TYPE_CHECKING:
    from kivy.inputs import MotionEvent

    from front.window import SnakeTronWindow



class PauseMenu(FloatLayout):
    menu_background_color = ListProperty(get_color_from_hex("#000000A0"))
    menu_padding = NumericProperty(15)

    def __init__(self, main_window: SnakeTronWindow, *args, **kwargs):
        super().__init__(*args, **kwargs, opacity=0)
        self.main_window = main_window
        self.ids.button_resume.bind(on_press=lambda _: self._request_resume())
        self.ids.button_toggle_ai_explanations.bind(on_press=lambda _: self._toggle_ai_explanations())
        self.ids.button_toggle_fullspeed.bind(on_press=lambda _: self._toggle_fullspeed())

        if self.main_window.ai_explanations_is_enabled():
            self.ids.button_toggle_ai_explanations.state = "down"
        if self.main_window.fullspeed_is_enabled():
            self.ids.button_toggle_fullspeed.state = "down"

    def on_touch_down(self, touch: MotionEvent) -> bool:
        return super().on_touch_down(touch) or self.collide_point(touch.x, touch.y)

    def _toggle_ai_explanations(self) -> None:
        self.main_window.toggle_ai_explanations()

    def _toggle_fullspeed(self) -> None:
        self.main_window.toggle_fullspeed()

    def _request_resume(self) -> None:
        content = self.ids.menu_content

        duration = 0.12
        final_size_hint = (0.8 * content.size_hint_x, 0.8 * content.size_hint_y)
        zoom_out_anim = Animation(size_hint=final_size_hint, d=duration, t="out_back")
        fade_out_anim = Animation(opacity=0, d=duration, t="out_quad")

        def resume_game(*args, **kwargs):
            self.parent.remove_widget(self)
            self.main_window.toggle_pause()

        fade_out_anim.bind(on_complete=resume_game)
        zoom_out_anim.start(content)
        fade_out_anim.start(self)

    def request_pause(self) -> None:
        self.main_window.toggle_pause()

        content = self.ids.menu_content

        duration = 0.12
        start_size_hint = (0.8 * content.size_hint_x, 0.8 * content.size_hint_y)
        final_size_hint = (content.size_hint_x, content.size_hint_y)
        zoom_in_anim = Animation(size_hint=final_size_hint, d=duration, t="out_back")
        fade_in_anim = Animation(opacity=1, d=duration, t="out_quad")

        content.size_hint = start_size_hint
        zoom_in_anim.start(content)
        fade_in_anim.start(self)
