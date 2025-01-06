from itertools import chain

from front import SnakeGameWindow
from agent import PlayerSnakeAgent, AStarSnakeAgent, AStarOffensiveSnakeAgent
from world import SnakeWorld, EuclidianDistanceHeuristic, ManhattanDistanceHeuristic

width = 30
height = 30
world = SnakeWorld(width, height, n_food=2)

# blue
agent_0 = PlayerSnakeAgent(
    world,
    initial_pos=[(4, y) for y in range(10, 1, -1)],
    initial_dir=(0, 1)
)

# yellow
agent_1 = AStarOffensiveSnakeAgent(
    world,
    initial_pos=[(width-5, y) for y in range(10, 1, -1)],
    initial_dir=(0, 1),
    heuristic_type=EuclidianDistanceHeuristic,
    latency=0,
    caution=1
)

# purple
agent_2 = AStarOffensiveSnakeAgent(
    world,
    initial_pos=[(4, y) for y in range(height-6, height-1, 1)],
    initial_dir=(0, -1),
    heuristic_type=EuclidianDistanceHeuristic,
    latency=0,
    caution=2
)

# green
agent_3 = AStarSnakeAgent(
    world,
    initial_pos=[(width-5, y) for y in range(height-6, height-1, 1)],
    initial_dir=(0, -1),
    heuristic_type=EuclidianDistanceHeuristic,
    latency=0,
    caution=3
)

agent_1.add_opponent(agent_2)
agent_1.add_opponent(agent_3)

agent_2.add_opponent(agent_0)
agent_2.add_opponent(agent_1)

player_agents = [agent_0]
ai_agents = [agent_1, agent_2, agent_3]

for agent in chain(player_agents, ai_agents):
    world.attach_agent(agent)

gui = SnakeGameWindow(
    world,
    player_agents=player_agents,
    ai_agents=ai_agents,
    explain_ai=False,
    ui_size_coeff=20,
    time_step=100
)
gui.mainloop()
