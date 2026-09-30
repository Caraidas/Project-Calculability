"""
Compass directions -> (row, col) step. Row increases downward, so N decreases the
row and S increases it (matches the grid's own (row, col) convention, see grid.py).
"""
Delta = tuple[int, int]

DIRECTIONS: dict[str, Delta] = {
    "N": (-1, 0), "S": (1, 0), "E": (0, 1), "W": (0, -1),
    "NE": (-1, 1), "NW": (-1, -1), "SE": (1, 1), "SW": (1, -1),
}
ORTHOGONAL = {"N", "S", "E", "W"}
DIAGONAL = {"NE", "NW", "SE", "SW"}


def step(pose: tuple[int, int], direction: str) -> tuple[int, int]:
    dr, dc = DIRECTIONS[direction]
    return pose[0] + dr, pose[1] + dc