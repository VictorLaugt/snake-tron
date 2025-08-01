from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy.graphics import InstructionGroup, Color, Rectangle
from kivy.uix.boxlayout import BoxLayout

from direction import UP, DOWN, LEFT, RIGHT

# KV = '''
# <MyAppWindow>:
#     SwipeControlWidget:
#         id: swipe_control

#     Label:
#         id: label
# '''


KV = '''
<MyAppWindow>:
    orientation: 'vertical'

    SwipeControlWidget:
        id: swipe_control
        size_hint_y: None
        height: "300dp"
        canvas.before:
            Color:
                rgba: 1, 0, 0, 1
            Line:
                rectangle: self.x, self.y, self.width, self.height
                width: 2

    Label:
        id: label
        text: "Swipe quelque part"
        size_hint_y: None
        height: "100dp"
        canvas.before:
            Color:
                rgba: 1, 0, 0, 1  # Rouge
            Line:
                rectangle: self.x, self.y, self.width, self.height
                width: 2
'''

class SwipeControlWidget(Widget):
    def on_kv_post(self, base_widget):
        self.touch_starts = {}

    def init_logic(self, label):
        self.label = label

    def on_kv_post(self, base_widget):
        self.touch_starts: dict[int, tuple[float, float]] = {}

    def on_touch_down(self, touch):
        if not self.collide_point(touch.x, touch.y):
            return False

        self.touch_starts[touch.uid] = (touch.x, touch.y)
        print(f"[{touch.uid}] touch down at ({touch.x}, {touch.y})")
        return True

    def on_touch_up(self, touch):
        start_pos = self.touch_starts.pop(touch.uid, None)
        if start_pos is None:
            return False

        start_x, start_y = start_pos
        dx, dy = touch.x - start_x, touch.y - start_y

        if abs(dx) > abs(dy):
            direction = RIGHT if dx > 0 else LEFT
        else:
            direction = UP if dy > 0 else DOWN

        direction_name = {RIGHT: 'RIGHT', LEFT: 'LEFT', UP: 'UP', DOWN: 'DOWN'}
        self.label.text = f"{direction_name[direction]}, {len(self.touch_starts) = }"
        print(f"[{touch.uid}] swipe: {direction_name[direction]}")

        return True

class MyAppWindow(BoxLayout):
    def init_logic(self):
        self.ids.swipe_control.init_logic(self.ids.label)

class MyApp(App):
    def build(self):
        Builder.load_string(KV)
        window = MyAppWindow()
        window.init_logic()
        return window

if __name__ == '__main__':
    MyApp().run()
