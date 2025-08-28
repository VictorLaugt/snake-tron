from __future__ import annotations

from typing import TYPE_CHECKING

from back.type_hints import Direction
if TYPE_CHECKING:
    from back.type_hints import Direction
    from typing import TypeAlias
    Real: TypeAlias = int|float

UP: Direction = (0, -1)
DOWN: Direction = (0, 1)
LEFT: Direction = (-1, 0)
RIGHT: Direction = (1, 0)


def toward_center(x: Real, y: Real, width: Real, height: Real) -> Direction:
    above_diag_0 = (y > (height/width * x))
    above_diag_1 = (y > (-height/width * (x-width)))
    if above_diag_0 and above_diag_1:
        return UP
    elif above_diag_0 and not above_diag_1:
        return RIGHT
    elif not above_diag_0 and above_diag_1:
        return LEFT
    elif not above_diag_0 and not above_diag_1:
        return DOWN


def away_from_center(x: Real, y: Real, width: Real, height: Real) -> Direction:
    above_diag_0 = (y > (height/width * x))
    above_diag_1 = (y > (-height/width * (x-width)))
    if above_diag_0 and above_diag_1:
        return DOWN
    elif above_diag_0 and not above_diag_1:
        return LEFT
    elif not above_diag_0 and above_diag_1:
        return RIGHT
    elif not above_diag_0 and not above_diag_1:
        return UP


def opposite_dir(d: Direction) -> Direction:
    return (-d[0], -d[1])
