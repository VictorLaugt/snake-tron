from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.lang import Builder
from kivy.graphics import InstructionGroup, Color, Rectangle
from kivy.uix.boxlayout import BoxLayout

KV = '''
<SnakeTronWindow>:
    orientation: 'vertical'

    # Button:
    #     text: "Bouton du haut"
    #     size_hint_y: 0.1
    #     on_press: root.bouton_clique()

    WorldDisplay:
        on_pos: self.redraw()
        on_size: self.redraw()
        size_hint_y: 0.8

    # BoxLayout:
    #     size_hint_y: 0.1
    #     spacing: 10
    #     # padding: 10

    #     Button:
    #         text: "Bouton bas gauche"
    #         on_press: root.action_gauche()

    #     Button:
    #         text: "Bouton bas droite"
    #         on_press: root.action_droite()
'''

class WorldDisplay(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.draw_instr = InstructionGroup()
        self.canvas.add(self.draw_instr)

    def redraw(self):
        square_size = min(self.width, self.height)
        self.draw_instr.clear()
        self.draw_instr.add(Color(1, 0, 0))
        self.draw_instr.add(Rectangle(pos=(self.x, self.y), size=(square_size, square_size)))


class SnakeTronWindow(BoxLayout):
    def bouton_clique(self):
        print("Le premier bouton a été cliqué !")

    def action_gauche(self):
        print("Le bouton de gauche a été cliqué !")

    def action_droite(self):
        print("Le bouton de droite a été cliqué !")


class MonApp(App):
    def build(self):
        Builder.load_string(KV)
        return SnakeTronWindow()

if __name__ == '__main__':
    MonApp().run()
