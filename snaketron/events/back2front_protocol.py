from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional

    from back.type_hints import Direction, Position


class ArenaEvent:
    pass

@dataclass  # TODO: send UpdateSize event to communicate initial (width, height) and each value update
class UpdateSize(ArenaEvent):
    width: int
    height: int


@dataclass
class FoodCreated(ArenaEvent):
    pos: Position

@dataclass
class FoodConsumed(ArenaEvent):
    pos: Position
    by: Optional[int]


class AgentEvent:
    pass

class SnakeSimpleEvent(AgentEvent, IntEnum):
    SPAWN = auto()  # REFACTOR: SPAWN can no longer be a simple event: it should store the positions of the spawning snake cells
    DIE = auto()
    DASH = auto()


class SnakeMovementType(IntEnum):
    COMMON = auto()
    WRAP = auto()
    TELEPORT = auto()


@dataclass
class SnakeMovement(AgentEvent):
    new_head_pos: Position
    new_dir: Direction
    growth: int
    movement_type: SnakeMovementType
