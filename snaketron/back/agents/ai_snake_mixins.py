from __future__ import annotations

from back.agents.abstract_ai_snake_agent import AbstractAISnakeAgent

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Optional, Sequence, Iterable, Iterator

    from back.type_hints import Position, Direction
    from back.agents.abstract_snake_agent import AbstractSnakeAgent


"""
The mixin pattern

# example of a mixin definition over AbstractAISnakeAgent
class AISnakeMixin(AbstractAISnakeAgent):
    def __init__(self, *, mixin_argument, **kwargs) -> None:
        super().__init__(**kwargs)
        self.mixin_constant_attribute = mixin_argument
        self.mixin_variable_attribute = None

    def reset(self) -> None:
        self.mixin_variable_attribute = None

    def _internal_mixin_method(self)
        ...

    def exposed_mixin_method(self):
        ...


# create an implemantation by composing several mixins over the AbstractAISnakeAgent base
class AISnakeAgentImplementation(Mixin1, Mixin2, ..., AbstractAISnakeAgent):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
"""


class CautionAISnakeMixin(AbstractAISnakeAgent):
    def __init__(self, *, caution: int=0, **kwargs) -> None:
        assert caution >= 0
        super().__init__(**kwargs)

        self.caution_radius = caution

    def reset(self, pos = None, d = None):
        return super().reset(pos, d)

    def _start_avoid(self, dangerous_agents: Iterable[AbstractSnakeAgent]) -> list[list[Position]]:
        """Add virtual obstacles in the world to avoid positions that are to close
        to the dangerous snakes' heads.
        """
        danger_layers = []
        for agent in dangerous_agents:
            layer = (agent.get_head(),)
            for _ in range(self.caution_radius):
                new_layer = []
                for position in layer:
                    for neighbor, direction in self.world.iter_free_neighbors(position):
                        self.world.incr_obstacle_count(neighbor, 1)
                        new_layer.append(neighbor)
                danger_layers.append(new_layer)
                layer = new_layer
        return danger_layers

    def _stop_avoid(self, danger_layers: list[list[Position]]) -> None:
        """Removes the virtual obstacles from the world."""
        for layer in danger_layers:
            for position in layer:
                self.world.incr_obstacle_count(position, -1)

    def compute_path_with_caution(
        self,
        destinations: Iterable[Position],
        inf_len: int,
        sup_len: int|float = float('inf')
    ) -> Optional[int]:
        danger_zone = self._start_avoid(a for a in self.world.iter_alive_agents() if self is not a)
        destination_idx = self.compute_shortest_path(destinations, inf_len, sup_len)
        self._stop_avoid(danger_zone)

        return destination_idx


class AttackAISnakeMixin(AbstractAISnakeAgent):
    def __init__(self, *, attack_anticipation: int=15, **kwargs) -> None:
        super().__init__(**kwargs)
        self.attack_anticipation = attack_anticipation
        self.current_target: Optional[AbstractSnakeAgent] = None
        self.opponents: list[AbstractSnakeAgent] = []

    def get_current_target(self) -> Optional[AbstractSnakeAgent]:
        return self.current_target

    def add_opponent(self, opponent: AbstractSnakeAgent) -> None:
        self.opponents.append(opponent)

    def iter_opponents(self) -> Iterator[AbstractSnakeAgent]:
        return iter(self.opponents)

    def reset(self, pos: Optional[Sequence[Position]]=None, d: Optional[Direction]=None) -> None:
        super().reset(pos, d)
        self.current_target = None

    def compute_attack_path(self, potential_targets: Iterable[AbstractSnakeAgent]) -> Optional[int]:
        """Tries to compute a path to attack one of the given target.
        If success, returns the index of the selected target in the
        potential_targets sequence, else returns None.
        """
        # initialize the list of potential attack destinations
        impact_positions = [a.get_head() for a in potential_targets]

        for impact_delay in range(1, self.attack_anticipation+1):
            # update the list of potential attack destinations
            new_potential_targets: list[AbstractSnakeAgent] = []
            new_impact_positions: list[Position] = []
            for agent, pos in zip(potential_targets, impact_positions):
                pos = self.world.get_neighbor(pos, agent.get_direction())
                if self.world.get_obstacle_count(pos) == 0:
                    new_impact_positions.append(pos)
                    new_potential_targets.append(agent)
            potential_targets = new_potential_targets
            impact_positions = new_impact_positions

            # arriving before the target implies len(attack_path) < impact_delay
            # not arriving too early implies len(attack_path) + len(self) > impact_delay
            # the resulting criterion is impact_delay - len(self) < len(attack_path) < impact_delay
            i = self.compute_shortest_path(impact_positions, impact_delay - len(self), impact_delay)
            if i is not None:
                self.current_target = potential_targets[i]
                return i

        self.current_target = None
