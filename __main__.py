import argparse

import front
import world


parser = argparse.ArgumentParser()
parser.add_argument('mode', choices=('singleplayer', 'versus', 'twoplayers'), nargs='?', default='singleplayer')
parser.add_argument('-e', '--explain-ai', action='store_true')
parser.add_argument('-t', '--time-step', type=int, default=100)
args = parser.parse_args()

world = world.SnakeWorld(width=30, height=30, n_food=1)

agent_1_initial_pos = ((2,9), (2,8), (2,7), (2,6), (2,5), (2,4), (2,3), (2,2), (2,1))
agent_1_initial_dir = (0,1)

agent_2_initial_pos = ((5,1), (5,2), (5,3), (5,4), (5,5))
agent_2_initial_dir = (0,-1)

agent_3_initial_pos = ((8,9), (8,8), (8,7), (8,6), (8,5), (8,4), (8,3), (8,2), (8,1))
agent_3_initial_dir = (0,1)

player_agents = []
ai_agents = []

player_agents.append(world.new_player_agent(agent_1_initial_pos, agent_1_initial_dir))
if args.mode == 'singleplayer':
    ai_agents.append(world.new_a_star_agent(agent_2_initial_pos, agent_2_initial_dir))
elif args.mode == 'versus':
    player_agents.append(world.new_player_agent(agent_2_initial_pos, agent_2_initial_dir))
elif args.mode == 'twoplayers':
    ai_agents.append(world.new_a_star_agent(agent_2_initial_pos, agent_2_initial_dir))
    player_agents.append(world.new_player_agent(agent_3_initial_pos, agent_3_initial_dir))


gui = front.SnakeGameWindow(
    world,
    player_agents=player_agents,
    ai_agents=ai_agents,
    explain_ai=args.explain_ai,
    ui_size_coeff=20,
    time_step=args.time_step
)
gui.mainloop()
