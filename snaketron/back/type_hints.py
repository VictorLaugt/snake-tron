from typing import TypeAlias

__all__ = ['Direction', 'Position', 'Path']


Direction: TypeAlias = tuple[int, int]
Position: TypeAlias = tuple[int, int]
Path: TypeAlias = tuple[list[int], list[int], list[Direction]]
