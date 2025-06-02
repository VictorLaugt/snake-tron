from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.properties import StringProperty

# Configuration de la fenêtre
Window.size = (400, 400)

SWIPE_THRESHOLD = 50  # seuil de détection du swipe

class SwipeDetector(Widget):
    swipe_direction = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_pos = None

    def on_touch_down(self, touch):
        self.start_pos = (touch.x, touch.y)

    def on_touch_up(self, touch):
        end_pos = (touch.x, touch.y)
        if self.start_pos:
            dx = end_pos[0] - self.start_pos[0]
            dy = end_pos[1] - self.start_pos[1]

            if abs(dx) < SWIPE_THRESHOLD and abs(dy) < SWIPE_THRESHOLD:
                return

            if abs(dx) > abs(dy):
                self.swipe_direction = "→ Droite" if dx > 0 else "← Gauche"
            else:
                self.swipe_direction = "↓ Bas" if dy > 0 else "↑ Haut"

            self.start_pos = None

class MainApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')
        self.swipe_detector = SwipeDetector()
        self.label = Label(text="", font_size='32sp', color=(1, 1, 1, 1))

        # Liaison de la propriété à la mise à jour du label
        self.swipe_detector.bind(swipe_direction=self.update_label)

        layout.add_widget(self.swipe_detector)
        layout.add_widget(self.label)

        return layout

    def update_label(self, instance, value):
        self.label.text = value

if __name__ == '__main__':
    MainApp().run()
