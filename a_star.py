from __future__ import annotations

import numpy as np
from world import oposite_dir

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from type_hints import Position, Path
    from world import AbstractGridGraph, AbstractHeuristic


NO_PATH_FOUND = (None, None)


def _get_path(graph: AbstractGridGraph, src: Position, dst: Position, parents: np.ndarray) -> Path:
    x_src, y_src = src
    x_dst, y_dst = dst
    path_x = []
    path_y = []
    path_dir = []
    x, y = x_dst, y_dst
    while x != x_src or y != y_src:
        direction = parents[x, y]
        path_x.append(x)
        path_y.append(y)
        path_dir.append(direction)
        x, y = graph.get_neighbor((x, y), oposite_dir(direction))
    return path_x, path_y, path_dir


def _minimizing_cost_position(
    positions: set[Position],
    dist_from_src: np.ndarray,
    heuristic: AbstractHeuristic
) -> Position:
    x_min, y_min = NO_PATH_FOUND
    h_min = np.inf
    c_min = np.inf
    for x, y in positions:
        d = dist_from_src[x, y]
        h = heuristic(x, y)
        c = d + h
        if c < c_min:
            x_min, y_min = x, y
            c_min = c
            h_min = h
        elif c == c_min and h < h_min:
            x_min, y_min = x, y
            h_min = h
    return x_min, y_min


# TODO: implement a max iteration parameter (use 500 iteration max)
def shortest_path(
    graph: AbstractGridGraph,
    src: Position,
    dst: Position,
    heuristic: AbstractHeuristic
) -> Path:
    parents = np.empty((graph.get_width(), graph.get_height(), 2), dtype=np.int32)
    dist_from_src = np.full((graph.get_width(), graph.get_height()), np.inf, dtype=np.float64)

    current = src
    dist_from_src[src] = 0.

    opened_positions = {src}
    closed_positions = set()

    while current != dst:
        for neighbor, direction in graph.iter_free_neighbors(current):
            if neighbor in closed_positions:
                continue

            d = dist_from_src[current]
            current_path_length = d + 1.
            if current_path_length < dist_from_src[neighbor]:
                dist_from_src[neighbor] = current_path_length
                parents[neighbor] = direction
                opened_positions.add(neighbor)

        opened_positions.remove(current)
        closed_positions.add(current)

        next_position = _minimizing_cost_position(opened_positions, dist_from_src, heuristic)
        if next_position == NO_PATH_FOUND:
            break
        current = next_position

    return _get_path(graph, src, current, parents)
