"""The list of everything the API accepts. Served by GET /help and printed at launch."""
INIT_INPUT = ('{"size": int>=1, "connectivity": 4|8, "agents": ["name", ...], '
              '"obstacles": [{"node": [r, c], "weight": int>1}], '
              '"mission": {"start": [r, c], "target": [r, c], "threshold": number>0, "agent": "name" (optional)}}')

ENDPOINTS = [
    {"method": "GET", "path": "/help", "input": "-", "summary": "This list"},
    {"method": "POST", "path": "/init", "input": INIT_INPUT,
     "summary": "(Re)create the grid with agents, obstacles and a mission A -> B"},
    {"method": "GET", "path": "/state", "input": "-", "summary": "Whole state: agents, obstacles, mission"},
    {"method": "GET", "path": "/mission", "input": "-", "summary": "Mission status and total weight"},
    {"method": "POST", "path": "/mission",
     "input": '{"start": [r, c], "target": [r, c], "threshold": number>0, "agent": "name" (optional)}',
     "summary": "New mission on the current grid (agents back to start, weights reset)"},
    {"method": "POST", "path": "/obstacles", "input": '{"obstacles": [{"node": [r, c], "weight": int>1}, ...]}',
     "summary": "Set obstacle weights, one node -> one weight"},
    {"method": "GET", "path": "/nodes/{r}/{c}/neighbors", "input": "-",
     "summary": "Adjacent nodes: edge weight, obstacle weight, move cost"},
    {"method": "GET", "path": "/distance", "input": "query: r1, c1, r2, c2, metric=manhattan|euclidean|chebyshev",
     "summary": "Geometric distance between two points"},
    {"method": "GET", "path": "/agents/{name}", "input": "-", "summary": "Agent pose and total weight"},
    {"method": "GET", "path": "/directions", "input": "-", "summary": "Valid direction names and their row/col deltas"},
    {"method": "POST", "path": "/agents/{name}/move/{direction}", "input": "- (direction is in the URL)",
     "summary": "Move one step: N, S, E, W, NE, NW, SE, SW (diagonals need connectivity 8)"},
    {"method": "POST", "path": "/agents/{name}/move", "input": '{"to": [r, c]}',
     "summary": "Move the agent one step, to an ADJACENT node (absolute target)"},
    {"method": "GET", "path": "/viz/grid", "input": "-", "summary": "Grid drawing (text), last state"},
    {"method": "GET", "path": "/viz/graph", "input": "-", "summary": "Graph drawing (PNG, needs matplotlib)"},
    {"method": "GET", "path": "/health", "input": "-", "summary": "Liveness check"},
]

RULES = [
    "Nodes are [row, col], 0-based.",
    "Obstacle weight: an integer > 1. A free node weighs 1.",
    "A move costs edge_weight x obstacle weight of the destination node. "
    "Edge weight: 1 horizontal/vertical, 1.5 diagonal (connectivity 8 only).",
    "Simplest way to move: POST /agents/{name}/move/{direction}, e.g. .../robot/move/N.",
    "The mission succeeds when the agent's pose is the target. It fails, and is cancelled, "
    "as soon as the agent's total weight reaches the threshold (checked first).",
    "Once the mission is finished, only POST /init and POST /mission are accepted.",
    "Unknown fields are rejected.",
]


def banner(host: str = "127.0.0.1", port: int = 8000) -> str:
    lines = ["", "=" * 78, f" grid-api  (local only, no internet needed)  http://{host}:{port}", "=" * 78]
    for e in ENDPOINTS:
        lines.append(f" {e['method']:<4} {e['path']:<28} {e['summary']}")
        if e["input"] != "-":
            lines.append(f"      send: {e['input']}")
    lines += ["", " Rules:"] + [f"  - {r}" for r in RULES] + ["=" * 78, ""]
    return "\n".join(lines)