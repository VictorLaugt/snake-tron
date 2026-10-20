from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional, Sequence

    from back.type_hints import *


__all__ = [
    'BackendEvent',

    'WorldEvent', 'ArenaUpdateSize', 'FoodCreated', 'FoodConsumed',

    'AgentEvent', 'SnakeConnectionUpdate', 'SnakeSpawn', 'SnakeDie',
    'SnakeMovementType', 'SnakeMovement', 'SnakeDash',

    'BackEventHandleNotImplemented'
]


class BackendEvent:
    pass


class WorldEvent(BackendEvent):
    pass

@dataclass
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
class SnakeConnectionUpdate(AgentEvent):
    is_player: bool
    is_connecting: bool

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
