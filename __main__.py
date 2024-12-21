import argparse
import snake_front
import snake_world
import path_finding_ai

"""
TODO list:
- terminer de remanier le code pour faire en sorte que le monde soit un système
multi-agent dans lequel chaque agent est un snake pouvant être controllé par un
algorithme (IA) ou un utilisateur
- Quand un snake se tape la queue, il se coupe mais reste en vie
- Quand un snake tape la queue d'un autre, il meurt
- Quand un snake mange une pomme, il grandit d'une case
- Dès qu'un snake IA se déplace d'une seule case, il recalcule en entier le chemin
le plus court vers la pomme la plus proche.
- Faire un mode 1 joueur (par défaut) où un agent utilisateur combat un agent IA
- Faire un mode 2 joueurs où deux agents utilisateurs se combattent
"""


def launch_user_game():
    world = snake_world.SnakeWorld(
        width=10, height=10,
        n_food=2,
        initial_snake=((1, 1), (1, 2), (1, 3), (1, 4), (1, 5)),
        initial_dir=(0, -1)
    )

    graphic_ui = snake_front.SnakeGameWindow(
        world,
        ui_size_coeff=20,
        speed=150,
    )

    graphic_ui.mainloop()


def launch_ai_game():
    world = snake_world.SnakeWorld(
        width=20, height=20,
        n_food=4,
        initial_snake=((1, 1), (1, 2), (1, 3), (1, 4), (1, 5)),
        initial_dir=(0, -1)
    )

    graphic_ui = snake_front.AutomaticSnakeGameWindow(
        world,
        ui_size_coeff=20,
        speed=50,
        ai=path_finding_ai.NaiveSnakeAi(world)
    )

    graphic_ui.mainloop()


parser = argparse.ArgumentParser()
parser.add_argument('-a', '--ai', action='store_true')
args = parser.parse_args()
if args.ai:
    launch_ai_game()
else:
    launch_user_game()

