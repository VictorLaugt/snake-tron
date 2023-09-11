def launch_user_game():
    import snake_back, snake_front
    
    # world = snake_back.SnakeWorld(
    world = snake_back.PeriodicSnakeWorld(
        world_width=20, world_height=20,
        food_number=4,
        initial_snake=((1, 1), (1, 2), (1, 3), (1, 4), (1, 5)),
        initial_dir=snake_back.UP
    )
    
    graphic_ui = snake_front.SnakeGameWindow(
        world,
        ui_size_coeff=20,
        speed=150,
    )

    graphic_ui.mainloop()


def launch_ai_game():
    import snake_back, snake_front, path_finding_ai
    
    # world = snake_back.SnakeWorld(
    world = snake_back.PeriodicSnakeWorld(
        world_width=20, world_height=20,
        food_number=4,
        initial_snake=((1, 1), (1, 2), (1, 3), (1, 4), (1, 5)),
        initial_dir=snake_back.UP
    )
        
    graphic_ui = snake_front.AutomaticSnakeGameWindow(
        world,
        ui_size_coeff=20,
        speed=50,
        ai=path_finding_ai.NaiveSnakeAi(world)
    )

    graphic_ui.mainloop()


# launch_user_game()
launch_ai_game()
