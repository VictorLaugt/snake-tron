import argparse

import front
import world

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

parser = argparse.ArgumentParser()
parser.add_argument('mode', choices=('singleplayer', 'versus'), default='singleplayer')
parser.add_argument('-e', '--explain-ai', action='store_true')
parser.add_argument('-t', '--time-step', type=int, default=100)
args = parser.parse_args()

world = world.SnakeWorld(width=20, height=20, n_food=4)

agent_1_initial_pos = ((1,1), (1,2), (1,3), (1,4), (1,5))
agent_1_initial_dir = (0,-1)

agent_2_initial_pos = ((3,1), (3,2), (3,3), (3,4), (3,5))
agent_2_initial_dir = (0,-1)

player_agents = []
ai_agents = []

player_agents.append(world.new_player_agent(agent_1_initial_pos, agent_1_initial_dir))
if args.mode == 'singleplayer':
    ai_agents.append(world.new_ai_agent(agent_2_initial_pos, agent_2_initial_dir))
else:
    player_agents.append(world.new_player_agent(agent_2_initial_pos, agent_2_initial_dir))

gui = front.SnakeGameWindow(
    world,
    player_agents=player_agents,
    ai_agents=ai_agents,
    explain_ai=args.explain_ai,
    ui_size_coeff=20,
    speed=args.time_step
)
gui.mainloop()
