import io
import json

import pytest
from fastapi.testclient import TestClient

import api.main as main_module

INIT = {
    "size": 5, "connectivity": 8, "agents": ["robot"],
    "obstacles": [{"node": [1, 1], "weight": 4}],
    "mission": {"start": [0, 0], "target": [4, 4], "threshold": 30},
}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GRID_CONFIG", str(tmp_path / "missing.json"))   # no auto-init at startup
    main_module._grid = None
    with TestClient(main_module.app) as c:
        yield c


def test_help_lists_endpoints(client):
    r = client.get("/help")
    assert r.status_code == 200
    paths = {e["path"] for e in r.json()["endpoints"]}
    assert {"/init", "/state", "/mission", "/obstacles", "/agents/{name}/move"} <= paths


def test_queries_before_init_return_clean_error(client):
    r = client.get("/state")
    assert r.status_code == 409
    assert r.json()["error"].startswith("grid not initialised")


def test_init_then_state(client):
    r = client.post("/init", json=INIT)
    assert r.status_code == 200
    body = r.json()
    assert body["agents"][0]["pose"] == [0, 0]
    assert body["obstacles"] == [{"node": [1, 1], "weight": 4}]
    assert body["mission"]["status"] == "running"


def test_unknown_field_rejected(client):
    bad = dict(INIT, extra_field=True)
    r = client.post("/init", json=bad)
    assert r.status_code == 422
    assert "invalid input" in r.json()["error"]


def test_bad_obstacle_weight_rejected(client):
    client.post("/init", json=INIT)
    r = client.post("/obstacles", json={"obstacles": [{"node": [0, 1], "weight": 1}]})
    assert r.status_code == 422


def test_neighbors_and_distance(client):
    client.post("/init", json=INIT)
    r = client.get("/nodes/0/0/neighbors")            # (0,0) -> (1,1) is a diagonal step
    by_node = {tuple(n["node"]): n for n in r.json()}
    assert by_node[(1, 1)]["obstacle_weight"] == 4
    assert by_node[(1, 1)]["cost"] == pytest.approx(1.5 * 4)   # diagonal * obstacle

    r = client.get("/distance", params={"r1": 0, "c1": 0, "r2": 3, "c2": 4, "metric": "euclidean"})
    assert r.json()["distance"] == 5.0


def test_move_must_be_adjacent(client):
    client.post("/init", json=INIT)
    r = client.post("/agents/robot/move", json={"to": [4, 4]})
    assert r.status_code == 400


def test_full_mission_success_flow(client):
    client.post("/init", json={
        "size": 3, "connectivity": 4, "agents": ["robot"], "obstacles": [],
        "mission": {"start": [0, 0], "target": [0, 1], "threshold": 5},
    })
    r = client.post("/agents/robot/move", json={"to": [0, 1]})
    assert r.status_code == 200
    body = r.json()
    assert body["mission"]["status"] == "success"

    r = client.post("/agents/robot/move", json={"to": [0, 0]})
    assert r.status_code == 409   # mission finished -> further moves refused


def test_mission_failure_flow(client):
    client.post("/init", json={
        "size": 3, "connectivity": 4, "agents": ["robot"],
        "obstacles": [{"node": [0, 1], "weight": 5}],
        "mission": {"start": [0, 0], "target": [2, 2], "threshold": 3},
    })
    r = client.post("/agents/robot/move", json={"to": [0, 1]})
    assert r.json()["mission"]["status"] == "failed"


def test_viz_grid_text(client):
    client.post("/init", json=INIT)
    r = client.get("/viz/grid")
    assert r.status_code == 200
    assert "Mission running" in r.text


def test_viz_graph_png(client):
    client.post("/init", json=INIT)
    r = client.get("/viz/graph")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_move_direction_endpoint(client):
    client.post("/init", json=INIT)
    r = client.post("/agents/robot/move/SE")
    assert r.status_code == 200
    body = r.json()
    assert body["pose"] == [1, 1]
    assert body["move_cost"] == pytest.approx(1.5 * 4)   # diagonal * obstacle at (1,1)


def test_move_direction_unknown_rejected(client):
    client.post("/init", json=INIT)
    r = client.post("/agents/robot/move/UP")
    assert r.status_code == 422   # Literal type rejects it before reaching Grid


def test_move_direction_diagonal_on_4_connectivity_rejected(client):
    client.post("/init", json={
        "size": 3, "connectivity": 4, "agents": ["robot"], "obstacles": [],
        "mission": {"start": [1, 1], "target": [2, 2], "threshold": 10},
    })
    r = client.post("/agents/robot/move/SE")
    assert r.status_code == 400


def test_directions_endpoint(client):
    r = client.get("/directions")
    assert r.json()["directions"]["N"] == [-1, 0]
    assert r.json()["directions"]["SE"] == [1, 1]