#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep  1 19:05:01 2023

@author: victor
"""
import numpy as np

from typing import Iterable, Tuple, List, Callable
from numbers import Real

Position = Tuple[int, int]
Path = Tuple[List[int], List[int]]

NO_PATH_FOUND = (None, None)


class GridGraph:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

        # array which represents the state of each (x, y) positions.
        # True: free
        # False: obstacle
        self.vertices = np.ones((self.height, self.width), dtype=np.bool8)

    def __repr__(self):
        return str(self.vertices)

    def _build_heuristic(self, x_dst: int, y_dst: int) -> Callable[[int, int], Real]:
        def heuristic(x, y):
            dx, dy = x_dst - x, y_dst - y
            return dx*dx + dy*dy
        return heuristic

    def free_every_positions(self):
        """Removes the obstacles from every positions"""
        self.vertices[:] = True

    def free_position(self, x: int, y: int):
        """Removes the obstacle on the position (x, y)."""
        self.vertices[y, x] = True

    def obstruct_position(self, x: int, y: int):
        """Puts an obstacle on the position (x, y)."""
        self.vertices[y, x] = False

    def is_free(self, x: int, y: int) -> bool:
        """Returns True if the position (x, y) is not obstructed by an obstacle,
        False otherwise.
        """
        return self.vertices[y, x]

    def iter_neighbors(self, position: Position) -> Iterable[Position]:
        """Iterates over each neighbor of `position`."""
        x, y = position

        y_up, x_up= (y-1) % self.height, x
        y_down, x_down = (y+1) % self.height, x
        y_left, x_left = y, (x-1) % self.width
        y_right, x_right = y, (x+1) % self.width

        if self.vertices[y_up, x_up]:
            yield x_up, y_up
        if self.vertices[y_down, x_down]:
            yield x_down, y_down
        if self.vertices[y_left, x_left]:
            yield x_left, y_left
        if self.vertices[y_right, x_right]:
            yield x_right, y_right
    
    def shortest_path(self, src: Position, dst: Position) -> Path:
        """Returns the shortest path from the position `src` to the position
        `dst`.
        """
        return _shortest_path(self, src, dst, self._build_heuristic(*dst))


def _get_path(src, dst, parents):
    x_src, y_src = src
    x_dst, y_dst = dst
    path_x = []
    path_y = []
    x, y = x_dst, y_dst
    while x != x_src or y != y_src:
        path_x.append(x)
        path_y.append(y)
        x, y = parents[x, y]
    return path_x, path_y


def _minimizing_cost_position(positions, dist_from_src, heuristic):
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


def _shortest_path(graph, src, dst, heuristic):
    parents = np.empty((graph.width, graph.height, 2), dtype=np.int64)
    dist_from_src = np.full((graph.width, graph.height), np.inf, dtype=np.float64)

    current = src
    dist_from_src[src] = 0.

    opened_positions = {src}
    closed_positions = set()

    while current != dst:
        for neighbor in graph.iter_neighbors(current):
            if current in closed_positions:
                continue

            d = dist_from_src[current]
            current_path_length = d + 1.
            if current_path_length < dist_from_src[neighbor]:
                dist_from_src[neighbor] = current_path_length
                parents[neighbor] = current
                opened_positions.add(neighbor)

        opened_positions.remove(current)
        closed_positions.add(current)
        
        next_position = _minimizing_cost_position(opened_positions, dist_from_src, heuristic)
        if next_position == NO_PATH_FOUND:
            break
        current = next_position

    return _get_path(src, current, parents)

