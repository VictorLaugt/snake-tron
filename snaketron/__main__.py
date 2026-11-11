#Pydroid should import kivy
from __future__ import annotations

from multiprocessing import Process
from pathlib import Path

from back.backend_builder import *
from events.multiprocessing_pipe import *
from front.app import *

"""
TODO:
 Priorité 1:
 - découpler le front et le back: le front doit être capable de mettre à jour son affichage uniquement en réceptionnant les évènements envoyés par le back
 - rendre dynamique le nombre d'agents dans le monde pour qu'il soit possible d'ajouter un nouveau joueur à la volée, par un appui fixe prolongé (réglable depuis le menu de pause)
 - créer un nouvel évènement pour prendre en charge les serpents qui traversent un bord de l'arène et réaparraissent de l'autre côté

Priorité 2:
 - essayer de faire des agents qui ignorent la latency pour le calcul de leurs chemins d'attaques, mais qui la respectent pour le calcul des chemins vers la nourriture
 - latency et caution variables grâce à une callback : dépendants de la taille du serpent, ou aléatoire

Priorité 3:
 - optimiser le path finding

IDÉE DE GAMEPLAY:
 - Dash utilisable au bout d'un certain nombre de nouriture mangée
 - Apparition aléatoire de zones carrées 3x3 qui forcent à changer de direction
"""


def run_backend(*args, **kwargs):
    backend = SnakeTronBackend(*args, **kwargs)
    backend.run()


if __name__ == '__main__':
    app_dir = Path(__file__).resolve().parent


    # dt = 1.0
    # dt = 0.15
    dt = 0.2
    # dt = 0.25
    # dt = 0.3

    back2front_pipe = MultiprocessEventPipe()  # Communicates events sent from backend to frontend
    front2back_pipe = MultiprocessEventPipe()  # Communicates events sent from frontend to backend

    backend_process = Process(
        kwargs=dict(
            event_sender=back2front_pipe.get_sender(),
            event_receiver=front2back_pipe.get_receiver(),

            n_snakes=4,
            n_players=1,
            respawn_cooldown=15,

            time_step=dt
        ),
        target=run_backend,
        daemon=True
    )

    frontend = SnakeTronFrontend(
        event_receiver=back2front_pipe.get_receiver(),
        event_sender=front2back_pipe.get_sender(),

        time_step=dt,  # FIXME: A partir d'un certain time_step, l'affichage initial de l'arène dans le frontend est extremement zoomé
        ai_explanations=False,
        layout_dir=app_dir.joinpath('front', 'kivy_layout', 'mobile'),
        color_file=app_dir.joinpath('front', 'color_scheme', 'dark.json'),
        input_sensitivity=1/100
    )

    backend_process.start()
    try:
        frontend.run()
    finally:
        backend_process.kill()
