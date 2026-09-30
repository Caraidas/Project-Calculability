"""Geometric distances between two points. They ignore the graph and the obstacles."""
import math
from typing import Callable

Pose = tuple[int, int]


def manhattan(p1: Pose, p2: Pose) -> float:
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def euclidean(p1: Pose, p2: Pose) -> float:
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def chebyshev(p1: Pose, p2: Pose) -> float:
    return max(abs(p1[0] - p2[0]), abs(p1[1] - p2[1]))


DISTANCES: dict[str, Callable[[Pose, Pose], float]] = {
    "manhattan": manhattan,
    "euclidean": euclidean,
    "chebyshev": chebyshev,
}