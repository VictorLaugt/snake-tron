from typing import TypeAlias

__all__ = ['ColorValue', 'Coordinate', 'KeyboardSet']

ColorValue: TypeAlias = tuple[float, float, float, float]
Coordinate: TypeAlias = tuple[float, float]
KeyboardSet: TypeAlias = tuple[str, str, str, str]
