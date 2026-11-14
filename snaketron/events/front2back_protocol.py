from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional

    from back.type_hints import Direction

__all__ = ['FrontendEvent', 'SimulationSpeedUpdateRequest', 'PlayerDirRequest']

class FrontendEvent:
    __slots__ = ()


@dataclass(slots=True)
class SimulationSpeedUpdateRequest(FrontendEvent):
    time_step: Optional[float]
    pause: Optional[bool]


@dataclass(slots=True)
class PlayerDirRequest(FrontendEvent):
    snake_id: int
    dir_request: Direction
