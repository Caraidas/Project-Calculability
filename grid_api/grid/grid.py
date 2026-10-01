"""
Grid: an N x N grid held as a networkx graph, with agents and one mission.

Edges are created once, in __init__ (weight 1 horizontal/vertical, 1.5 diagonal).
Each node has an obstacle weight: an int, 1 by default, > 1 for an obstacle.

A move costs   edge_weight(u, v) x obstacle_weight(v)   (v = destination node).
The grid only changes when an agent moves or an obstacle is added: it is discrete.
"""
from typing import Iterable, Optional

import networkx as nx

from .directions import DIAGONAL, DIRECTIONS, step
from .distances import DISTANCES
from .errors import (InvalidConfig, InvalidMove, InvalidNode, MissionFinished,
                     UnknownAgent)
from .mission import FAILED, RUNNING, SUCCESS, Agent, Mission

Pose = tuple[int, int]

ORTHOGONAL_WEIGHT = 1.0
DIAGONAL_WEIGHT = 1.5
DEFAULT_OBSTACLE_VALUE = 1


def _fmt(p: Pose) -> str:
    return f"({p[0]}, {p[1]})"


class Grid:
    def __init__(self, n: int, connectivity: int = 4):
        if connectivity not in (4, 8):
            raise InvalidConfig(f"connectivity must be 4 or 8, got {connectivity!r}")
        if not isinstance(n, int) or isinstance(n, bool) or n < 1:
            raise InvalidConfig(f"size must be an integer >= 1, got {n!r}")
        self.n = n
        self.connectivity = connectivity
        self.G = nx.Graph()
        self.agents: dict[str, Agent] = dict()
        self.mission: Optional[Mission] = None
        self._build()

    # ---- construction --------------------------------------------------------------
    def _build(self) -> None:
        for r in range(self.n):
            for c in range(self.n):
                self.G.add_node((r, c), obstacle_value=DEFAULT_OBSTACLE_VALUE)
        for r in range(self.n):
            for c in range(self.n):
                if c + 1 < self.n:
                    self.G.add_edge((r, c), (r, c + 1), weight=ORTHOGONAL_WEIGHT)
                if r + 1 < self.n:
                    self.G.add_edge((r, c), (r + 1, c), weight=ORTHOGONAL_WEIGHT)
                if self.connectivity == 8:
                    if r + 1 < self.n and c + 1 < self.n:
                        self.G.add_edge((r, c), (r + 1, c + 1), weight=DIAGONAL_WEIGHT)
                    if r + 1 < self.n and c - 1 >= 0:
                        self.G.add_edge((r, c), (r + 1, c - 1), weight=DIAGONAL_WEIGHT)

    @classmethod
    def from_config(cls, size: int, connectivity: int, agents: list[str],
                    obstacles: Iterable[tuple[Pose, int]], mission: dict) -> "Grid":
        """Grid with at least one agent, N obstacles and a mission (A -> B)."""
        g = cls(size, connectivity)
        names = list(agents)
        if not names:
            raise InvalidConfig("at least one agent is required")
        if len(set(names)) != len(names):
            raise InvalidConfig("agent names must be unique")
        g.agents = {name: Agent(name, (0, 0)) for name in names}
        g.add_obstacles(obstacles)
        g.set_mission(mission["start"], mission["target"], mission["threshold"],
                      mission.get("agent"))
        return g

    # ---- helpers -------------------------------------------------------------------
    def in_bounds(self, node: Pose) -> bool:
        return node in self.G

    def _check_node(self, node: Pose) -> None:
        if not self.in_bounds(node):
            raise InvalidNode(f"node {_fmt(node)} is outside the grid")

    def _check_running(self) -> None:
        if self.mission is not None and self.mission.finished:
            raise MissionFinished(self.mission_message())

    def _agent(self, name: str) -> Agent:
        if name not in self.agents:
            raise UnknownAgent(f"unknown agent {name!r} (agents: {list(self.agents)})")
        return self.agents[name]

    # ---- obstacles (can be added at runtime) ---------------------------------------
    def add_obstacles(self, items: Iterable[tuple[Pose, int]]) -> None:
        """One node -> one weight (int > 1). All-or-nothing: nothing changes if one is invalid."""
        items = [(tuple(node), w) for node, w in items]
        for node, w in items:
            if not isinstance(w, int) or isinstance(w, bool):
                raise InvalidConfig(f"obstacle weight must be an int, got {w!r}")
            if w <= 1:
                raise InvalidConfig(f"obstacle weight must be > 1, got {w}")
            self._check_node(node)
        self._check_running()
        for node, w in items:
            self.G.nodes[node]["obstacle_value"] = w

    def add_obstacle(self, cells: Iterable[Pose], value: int) -> None:
        """Same weight for several nodes."""
        self.add_obstacles((cell, value) for cell in cells)

    def obstacle_value(self, node: Pose) -> int:
        return self.G.nodes[node]["obstacle_value"]

    def obstacles(self) -> list[dict]:
        return [{"node": list(v), "weight": d["obstacle_value"]}
                for v, d in self.G.nodes(data=True)
                if d["obstacle_value"] > DEFAULT_OBSTACLE_VALUE]

    # ---- queries -------------------------------------------------------------------
    def edge_weight(self, u: Pose, v: Pose) -> float:
        return self.G[u][v]["weight"]

    def traversal_cost(self, u: Pose, v: Pose) -> float:
        return self.edge_weight(u, v) * self.obstacle_value(v)

    def neighbors_info(self, node: Pose) -> list[dict]:
        """Every adjacent node with its edge weight, obstacle weight and move cost."""
        node = tuple(node)
        self._check_node(node)
        return [{"node": list(v), "edge_weight": self.edge_weight(node, v),
                 "obstacle_weight": self.obstacle_value(v),
                 "cost": self.traversal_cost(node, v)}
                for v in sorted(self.G.neighbors(node))]

    def distance(self, p1: Pose, p2: Pose, metric: str = "manhattan") -> float:
        try:
            return DISTANCES[metric](p1, p2)
        except KeyError:
            raise InvalidConfig(f"unknown metric {metric!r} (choose from {list(DISTANCES)})")

    # ---- mission and agents --------------------------------------------------------
    def set_mission(self, start: Pose, target: Pose, threshold: float,
                    agent: Optional[str] = None) -> None:
        """(Re)start a mission: every agent goes back to `start`, weights reset to 0."""
        start, target = tuple(start), tuple(target)
        agent = agent or next(iter(self.agents))
        self._agent(agent)
        self._check_node(start)
        self._check_node(target)
        if start == target:
            raise InvalidConfig("start and target must be different nodes")
        if not threshold > 0:
            raise InvalidConfig("threshold must be > 0")
        for a in self.agents.values():
            a.reset(start)
        self.mission = Mission(agent, start, target, float(threshold))

    def mission_weight(self) -> float:
        """Total weight accumulated so far by the mission agent."""
        return self.agents[self.mission.agent].total_weight

    def move_agent(self, name: str, to: Pose) -> float:
        """One step, to an adjacent node. Adds the move cost to the agent's total. Returns that cost."""
        to = tuple(to)
        agent = self._agent(name)
        self._check_running()
        if not self.in_bounds(to):
            raise InvalidMove(f"node {_fmt(to)} is outside the grid")
        if to not in self.G[agent.pose]:
            raise InvalidMove(f"node {_fmt(to)} is not adjacent to {_fmt(agent.pose)}")
        cost = self.traversal_cost(agent.pose, to)
        agent.pose = to
        agent.total_weight += cost
        agent.steps += 1
        m = self.mission
        if m is not None and name == m.agent:
            if agent.total_weight >= m.threshold:   # threshold first: reaching it cancels the mission
                m.status = FAILED
            elif agent.pose == m.target:
                m.status = SUCCESS
        return cost

    def move_agent_direction(self, name: str, direction: str) -> float:
        """One step in a compass direction (N, S, E, W, NE, NW, SE, SW).
        Diagonals need connectivity 8. Everything else (bounds, adjacency, mission
        state) is the same check as move_agent -- this just resolves the target."""
        if direction not in DIRECTIONS:
            raise InvalidMove(f"unknown direction {direction!r} (choose from {sorted(DIRECTIONS)})")
        if direction in DIAGONAL and self.connectivity != 8:
            raise InvalidMove(f"direction {direction!r} needs connectivity 8 (grid is {self.connectivity})")
        agent = self._agent(name)
        return self.move_agent(name, step(agent.pose, direction))

    def mission_message(self) -> str:
        m = self.mission
        if m is None:
            return "No mission."
        a = self.agents[m.agent]
        w, t = f"{a.total_weight:g}", f"{m.threshold:g}"
        if m.status == SUCCESS:
            return (f"Mission accomplished: {a.name} reached {_fmt(m.target)} "
                    f"with a total weight of {w} in {a.steps} steps.")
        if m.status == FAILED:
            return (f"Mission failed: total weight {w} reached the threshold {t} "
                    f"before {a.name} reached {_fmt(m.target)} ({a.steps} steps).")
        return (f"Mission running: {a.name} at {_fmt(a.pose)}, "
                f"total weight {w} / threshold {t}, {a.steps} steps.")

    def mission_summary(self) -> Optional[dict]:
        m = self.mission
        if m is None:
            return None
        a = self.agents[m.agent]
        return {"agent": m.agent, "start": list(m.start), "target": list(m.target),
                "threshold": m.threshold, "status": m.status,
                "total_weight": a.total_weight, "steps": a.steps,
                "message": self.mission_message()}

    def state(self) -> dict:
        return {"size": self.n, "connectivity": self.connectivity,
                "agents": [{"name": a.name, "pose": list(a.pose),
                            "total_weight": a.total_weight, "steps": a.steps}
                            for a in self.agents.values()],
                "obstacles": self.obstacles(),
                "mission": self.mission_summary()}

    def __repr__(self) -> str:
        return f"Grid({self.n}x{self.n}, connectivity={self.connectivity})"