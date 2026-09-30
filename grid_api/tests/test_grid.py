import pytest
from grid import Grid
from grid.errors import (InvalidConfig, InvalidMove, InvalidNode, MissionFinished,
                         UnknownAgent)

MISSION = dict(start=(0, 0), target=(2, 2), threshold=10)


def make(n=3, connectivity=4, agents=("robot",), obstacles=(), mission=None):
    return Grid.from_config(n, connectivity, list(agents), obstacles, mission or MISSION)


def test_edges_built_once():
    g = make()
    n_edges = g.G.number_of_edges()
    g.add_obstacle([(1, 1)], 5)
    assert g.G.number_of_edges() == n_edges


def test_diagonal_weight_needs_8_connectivity():
    g = make(connectivity=8)
    assert g.edge_weight((0, 0), (0, 1)) == 1.0
    assert g.edge_weight((0, 0), (1, 1)) == 1.5


def test_default_obstacle_value_is_one():
    g = make()
    assert g.obstacle_value((1, 1)) == 1


def test_obstacle_one_node_one_weight():
    g = make()
    g.add_obstacles([((0, 1), 3), ((1, 0), 7)])
    assert g.obstacle_value((0, 1)) == 3
    assert g.obstacle_value((1, 0)) == 7
    assert g.obstacle_value((2, 2)) == 1


def test_obstacle_rejects_non_int_bool_and_leq_1():
    g = make()
    with pytest.raises(InvalidConfig):
        g.add_obstacle([(0, 1)], 2.5)
    with pytest.raises(InvalidConfig):
        g.add_obstacle([(0, 1)], True)
    with pytest.raises(InvalidConfig):
        g.add_obstacle([(0, 1)], 1)


def test_obstacle_out_of_bounds():
    g = make()
    with pytest.raises(InvalidNode):
        g.add_obstacle([(9, 9)], 2)


def test_obstacle_all_or_nothing():
    g = make()
    with pytest.raises(InvalidNode):
        g.add_obstacles([((0, 1), 3), ((9, 9), 2)])
    assert g.obstacle_value((0, 1)) == 1   # first one was NOT applied


def test_at_least_one_agent_required():
    with pytest.raises(InvalidConfig):
        Grid.from_config(3, 4, [], [], MISSION)


def test_agent_starts_at_mission_start():
    g = make(agents=("robot", "scout"), mission=dict(start=(1, 0), target=(2, 2), threshold=10))
    assert g.agents["robot"].pose == g.agents["scout"].pose == (1, 0)


def test_move_must_be_adjacent():
    g = make()
    with pytest.raises(InvalidMove):
        g.move_agent("robot", (2, 2))   # not a neighbor of (0,0)


def test_move_unknown_agent():
    g = make()
    with pytest.raises(UnknownAgent):
        g.move_agent("ghost", (0, 1))


def test_move_accumulates_weight():
    g = make(connectivity=8, obstacles=[((0, 1), 4)])
    cost = g.move_agent("robot", (0, 1))
    assert cost == 4.0
    assert g.agents["robot"].total_weight == 4.0


def test_mission_success_on_target():
    g = make(mission=dict(start=(0, 0), target=(0, 1), threshold=10))
    g.move_agent("robot", (0, 1))
    assert g.mission.status == "success"


def test_mission_failure_on_threshold():
    g = make(obstacles=[((0, 1), 3)], mission=dict(start=(0, 0), target=(2, 2), threshold=2))
    g.move_agent("robot", (0, 1))   # cost 3 >= threshold 2
    assert g.mission.status == "failed"


def test_threshold_checked_before_target():
    # reaching target exactly AT the threshold counts as failure, not success
    g = make(obstacles=[((0, 1), 5)], mission=dict(start=(0, 0), target=(0, 1), threshold=5))
    g.move_agent("robot", (0, 1))
    assert g.mission.status == "failed"


def test_finished_mission_blocks_moves():
    g = make(mission=dict(start=(0, 0), target=(0, 1), threshold=10))
    g.move_agent("robot", (0, 1))
    with pytest.raises(MissionFinished):
        g.move_agent("robot", (0, 0))


def test_finished_mission_blocks_obstacles():
    g = make(mission=dict(start=(0, 0), target=(0, 1), threshold=10))
    g.move_agent("robot", (0, 1))
    with pytest.raises(MissionFinished):
        g.add_obstacle([(1, 1)], 3)


def test_set_mission_resets_weight_and_pose():
    g = make(mission=dict(start=(0, 0), target=(0, 1), threshold=10))
    g.move_agent("robot", (0, 1))
    g.set_mission((1, 1), (2, 2), 10)
    assert g.agents["robot"].pose == (1, 1)
    assert g.agents["robot"].total_weight == 0.0
    assert g.mission.status == "running"


def test_distance_metrics():
    g = make(n=10, mission=dict(start=(0, 0), target=(1, 1), threshold=10))
    assert g.distance((0, 0), (3, 4), "manhattan") == 7
    assert g.distance((0, 0), (3, 4), "euclidean") == 5.0
    assert g.distance((0, 0), (3, 4), "chebyshev") == 4
    with pytest.raises(InvalidConfig):
        g.distance((0, 0), (1, 1), "mse")


def test_move_direction_orthogonal():
    g = make(connectivity=8)
    cost = g.move_agent_direction("robot", "E")
    assert g.agents["robot"].pose == (0, 1)
    assert cost == 1.0


def test_move_direction_diagonal_needs_connectivity_8():
    g = make(connectivity=4)
    with pytest.raises(InvalidMove):
        g.move_agent_direction("robot", "SE")


def test_move_direction_diagonal_on_8_connectivity():
    g = make(connectivity=8, obstacles=[((1, 1), 3)])
    cost = g.move_agent_direction("robot", "SE")
    assert g.agents["robot"].pose == (1, 1)
    assert cost == 1.5 * 3


def test_move_direction_unknown():
    g = make()
    with pytest.raises(InvalidMove):
        g.move_agent_direction("robot", "UP")


def test_move_direction_out_of_bounds():
    g = make(connectivity=4)
    with pytest.raises(InvalidMove):
        g.move_agent_direction("robot", "N")   # already at row 0