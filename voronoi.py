from __future__ import annotations

import numpy as np
from scipy.spatial import Voronoi

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import TypeAlias, Literal
    Point: TypeAlias = np.ndarray[tuple[Literal[2]], float]
    PointArray: TypeAlias = np.ndarray[tuple[int, Literal[2]], float]


def furthest_voronoi_vertex(points: PointArray, x_lim: float, y_lim: float) -> Optional[Point]:
    vor = Voronoi(points)
    n_vertices = vor.vertices.shape[0]

    vertex_nearest_point = np.empty(n_vertices+1, dtype=np.int32)
    for point_idx, region_idx in enumerate(vor.point_region):
        vertice_idx = vor.regions[region_idx]
        vertex_nearest_point[vertice_idx] = point_idx
    vertex_nearest_point = vertex_nearest_point[:n_vertices]
    vertex_squared_radius = np.sum((vor.vertices - points[vertex_nearest_point])**2, axis=1)

    candidate_mask = (
        (vor.vertices[:, 0] >= 0) & (vor.vertices[:, 0] < x_lim) &
        (vor.vertices[:, 1] >= 0) & (vor.vertices[:, 1] < y_lim)
    )
    candidates = vor.vertices[candidate_mask]
    candidate_squared_radius = vertex_squared_radius[candidate_mask]

    if candidate_squared_radius.shape[0] > 0:
        return candidates[np.argmax(candidate_squared_radius)]
