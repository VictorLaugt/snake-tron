from __future__ import annotations

from back.agents.abstract_ai_snake_agent import AbstractAISnakeAgent
from back.agents.ai_snake_mixins import CautionAISnakeMixin, AttackAISnakeMixin

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Sequence, Type

    from back.type_hints import Position, Direction
    from back.world import SnakeWorld
    from back.a_star import AbstractHeuristic


INF = float('inf')


class PassiveAISnakeAgent(CautionAISnakeMixin, AbstractAISnakeAgent):
    """Implement a snake agent which always tries to grow."""
    def __init__(
        self,
        world: SnakeWorld,
        initial_pos: Sequence[Position],
        initial_dir: Direction,
        heuristic_type: Type[AbstractHeuristic],
        latency: int=0,
        caution: int=0,
        alive: bool=True
    ) -> None:
        assert caution >= 0
        super().__init__(
            world=world, initial_pos=initial_pos, initial_dir=initial_dir,
            heuristic_type=heuristic_type, latency=latency, caution=caution,
            alive=alive
        )

    def update_path(self) -> None:
        if self.compute_path_with_caution(self.world.iter_food(), 0, INF) is not None:
            return

        self.compute_shortest_path(self.world.iter_food(), 0, INF)


class OffensiveAISnakeAgent(AttackAISnakeMixin, CautionAISnakeMixin, AbstractAISnakeAgent):
    def __init__(
        self,
        world: SnakeWorld,
        initial_pos: Sequence[Position],
        initial_dir: Direction,
        heuristic_type: Type[AbstractHeuristic],
        latency: int=0,
        caution: int=0,
        attack_anticipation: int=15,
        alive: bool=True
    ) -> None:
        assert attack_anticipation >= 1
        super().__init__(
            world=world, initial_pos=initial_pos, initial_dir=initial_dir,
            heuristic_type=heuristic_type, latency=latency, caution=caution,
            attack_anticipation=attack_anticipation, alive=alive
        )

    def update_path(self) -> None:
        current_target = self.get_current_target()
        if current_target is not None and current_target.is_alive():
            potential_targets = (current_target,)
        else:
            potential_targets = (agent for agent in self.iter_opponents() if agent.is_alive())
        if self.compute_attack_path(potential_targets) is not None:
            return

        if self.compute_path_with_caution(self.world.iter_food(), 0, INF) is not None:
            return

        self.compute_shortest_path(self.world.iter_food(), 0, INF)
