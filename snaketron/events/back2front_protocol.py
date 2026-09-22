from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional, Sequence

    from back.type_hints import Direction, Position


class BackendEvent:
    pass


class WorldEvent(BackendEvent):
    pass

@dataclass  # TODO: send UpdateSize event to communicate initial (width, height) and each value update
class ArenaUpdateSize(WorldEvent):
    width: int
    height: int


@dataclass
class FoodCreated(WorldEvent):
    pos: Position

@dataclass
class FoodConsumed(WorldEvent):
    pos: Position
    by: Optional[int]


@dataclass
class AgentEvent(BackendEvent):
    agent_id: int

@dataclass
class SnakeSpawn(AgentEvent):
    pos: Sequence[Position]

@dataclass
class SnakeDie(AgentEvent):
    pass

class SnakeMovementType(IntEnum):
    COMMON = auto()
    WRAP = auto()
    TELEPORT = auto()

@dataclass
class SnakeMovement(AgentEvent):
    movement_type: SnakeMovementType
    new_head_pos: Position
    new_dir: Direction
    growth: int

@dataclass
class SnakeDash(AgentEvent):
    movements: Sequence[SnakeMovement]


class BackEventHandleNotImplemented(Exception):
    pass
