from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from back.type_hints import Direction

__all__ = ['FrontendEvent', 'PlayerDirRequest']

class FrontendEvent:
    pass


@dataclass
class PlayerDirRequest(FrontendEvent):
    snake_id: int
    dir_request: Direction
