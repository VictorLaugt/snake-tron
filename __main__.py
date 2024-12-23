from itertools import chain

from front import SnakeGameWindow
from agent import PlayerSnakeAgent, AStarSnakeAgent
from world import SnakeWorld, EuclidianDistanceHeuristic, ManhattanDistanceHeuristic


world = SnakeWorld(width=30, height=30, n_food=1)

agent_1_initial_pos = ((2,9), (2,8), (2,7), (2,6), (2,5), (2,4), (2,3), (2,2), (2,1))
agent_1_initial_dir = (0,1)

agent_2_initial_pos = ((5,1), (5,2), (5,3), (5,4), (5,5))
agent_2_initial_dir = (0,-1)

# agent_3_initial_pos = ((8,9), (8,8), (8,7), (8,6), (8,5), (8,4), (8,3), (8,2), (8,1))
# agent_3_initial_dir = (0,1)


player_agents = [
    PlayerSnakeAgent(
        world,
        agent_1_initial_pos,
        agent_1_initial_dir
    )
]

ai_agents = [
    AStarSnakeAgent(
        world,
        agent_2_initial_pos,
        agent_2_initial_dir,
        EuclidianDistanceHeuristic
    )
]

for agent in chain(ai_agents, player_agents):
    world.attach_agent(agent)

gui = SnakeGameWindow(
    world,
    player_agents=player_agents,
    ai_agents=ai_agents,
    explain_ai=True,
    ui_size_coeff=20,
    time_step=100
)
gui.mainloop()
