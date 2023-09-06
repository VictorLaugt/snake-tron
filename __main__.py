import snake_back
import snake_front
import path_finding_ai


# backend
# world = snake_back.SnakeWorld(
world = snake_back.PeriodicSnakeWorld(
    world_width=20, world_height=20,
    food_number = 3,
    # initial_snake = ((10, 10), (10, 11), (10, 12), (10, 13), (10, 14)),
    initial_snake = ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4)),
    initial_dir = snake_back.UP
)

ai = path_finding_ai.NaiveSnakeAi(world)


# frontend
ui_size_coeff = 20
# speed = 150
speed = 80
# graphic_ui = snake_front.SnakeGameWindow(world, speed, ui_size_coeff)
graphic_ui = snake_front.AutomaticSnakeGameWindow(world, speed, ui_size_coeff, ai)


graphic_ui.mainloop()
