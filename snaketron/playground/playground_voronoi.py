import numpy as np
from scipy.spatial import Voronoi, voronoi_plot_2d
import matplotlib.pyplot as plt

from snaketron.voronoi import furthest_voronoi_vertex

# ---- flat voronoi input error
# QH6013 qhull input error: input is less than 3-dimensional since all points have the same x coordinate    94
points = np.array([[94, 0], [94, 1], [94, 2]])

# scipy.spatial._qhull.QhullError: QH6154 Qhull precision error: Initial simplex is flat (facet 1 is coplanar with the interior point)
# points = np.array([[0, 0], [1, 0], [2, 0], [3, 0]])
# points = np.array([[0, 0], [1, 1], [2, 2], [3, 3]])


# ---- valid voronoi inputs
# points = np.array([[0, 0], [1, 0], [0, 1], [.8, .8]])
# points = np.array([[0, 0], [1, 0], [0, 1]])

try:
    vor = Voronoi(points)
except Exception as err:
    print(type(err))
    # raise
    exit()

fig, ax = plt.subplots()
voronoi_plot_2d(vor, ax=ax)
print(f"{vor.vertices = }")
print(f"furthest voronoi vertex = {furthest_voronoi_vertex(points, float('inf'), float('inf'))}")
plt.show()
plt.close(fig)


import scipy.spatial

scipy.spatial.QhullError
