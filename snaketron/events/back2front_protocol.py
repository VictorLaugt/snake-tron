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
    """When the size of the arena is updated"""
    width: int
    height: int


@dataclass
class FoodCreated(WorldEvent):
    """When a food item is created"""
    pos: Position  # Position where the food appeared

@dataclass
class FoodConsumed(WorldEvent):
    """When a food item is consumed"""
    pos: Position  # Position where the food was before being consumed
    by: Optional[int]  # Id of the agent which ate the food if any, None otherwise


@dataclass
class AgentEvent(BackendEvent):
    agent_id: int

@dataclass
class SnakeConnectionUpdate(AgentEvent):
    """When a snake is connecting to or is disconnecting from the world"""
    is_player: bool
    is_connecting: bool

@dataclass
class SnakeSpawn(AgentEvent):
    """When an already connected snake (re)spawns"""
    pos: Sequence[Position]

@dataclass
class SnakeDie(AgentEvent):
    """When a snake despawns because it died"""
    pass

class SnakeMovementType(IntEnum):
    COMMON = auto()
    WRAP = auto()
    TELEPORT = auto()

@dataclass
class SnakeMovement(AgentEvent):
    """When a snake moves"""
    movement_type: SnakeMovementType
    new_head_pos: Position
    new_dir: Direction
    growth: int

@dataclass
class SnakeDash(AgentEvent):
    """When a snake dashes"""
    movements: Sequence[SnakeMovement]


class BackEventHandleNotImplemented(Exception):
    pass
