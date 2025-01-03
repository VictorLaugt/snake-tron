from itertools import chain

from front import SnakeGameWindow
from agent import PlayerSnakeAgent, AStarSnakeAgent
from world import SnakeWorld, EuclidianDistanceHeuristic, ManhattanDistanceHeuristic

width = 30
height = 30
world = SnakeWorld(width, height, n_food=2)

agent_1_initial_pos = [(4, y) for y in range(10, 1, -1)]
agent_1_initial_dir = (0,1)

agent_2_initial_pos = [(width-5, y) for y in range(6, 1, -1)]
agent_2_initial_dir = (0,1)

agent_3_initial_pos = [(4, y) for y in range(height-6, height-1, 1)]
agent_3_initial_dir = (0,-1)

agent_4_initial_pos = [(width-5, y) for y in range(height-6, height-1, 1)]
agent_4_initial_dir = (0,-1)



player_agents = [
    PlayerSnakeAgent(
        world,
        agent_1_initial_pos,
        agent_1_initial_dir
    ),
]

ai_agents = [
    AStarSnakeAgent(
        world,
        agent_2_initial_pos,
        agent_2_initial_dir,
        EuclidianDistanceHeuristic,
        latency=0,
        caution=0
    ),
    AStarSnakeAgent(
        world,
        agent_3_initial_pos,
        agent_3_initial_dir,
        EuclidianDistanceHeuristic,
        latency=0,
        caution=2
    ),
    AStarSnakeAgent(
        world,
        agent_4_initial_pos,
        agent_4_initial_dir,
        EuclidianDistanceHeuristic,
        latency=0,
        caution=3
    ),
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
