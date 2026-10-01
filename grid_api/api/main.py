"""
grid-api: local HTTP API around the Grid. It initialises the grid, applies what is requested
(move an agent, add obstacles, new mission, queries) and prints the last state of the grid on
the terminal it runs in. The grid only changes when a request changes it.
"""
import io
import json
import os
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from grid import DIRECTIONS, DISTANCES, Grid, viz_graph, viz_grid
from grid.errors import GridError, NotInitialized

Direction = Literal["N", "S", "E", "W", "NE", "NW", "SE", "SW"]

from .catalog import ENDPOINTS, RULES, banner
from .schemas import InitRequest, MissionIn, MoveRequest, ObstaclesRequest

_grid = None
_lock = threading.Lock()


def _get() -> Grid:
    if _grid is None:
        raise NotInitialized("grid not initialised: POST /init first")
    return _grid


def _show(event: str) -> None:
    print(f"\n--- {event} ---\n{viz_grid(_grid)}\n", flush=True)


def _init(req: InitRequest, event: str) -> None:
    global _grid
    g = Grid.from_config(size=req.size, connectivity=req.connectivity, agents=req.agents,
                         obstacles=[(o.node, o.weight) for o in req.obstacles],
                         mission=req.mission.model_dump())
    with _lock:
        _grid = g
    _show(event)


@asynccontextmanager
async def lifespan(_app):
    print(banner(), flush=True)
    path = Path(os.environ.get("GRID_CONFIG", "config/default.json"))
    if path.exists():
        try:
            _init(InitRequest.model_validate(json.loads(path.read_text())), f"init from {path}")
        except (GridError, ValueError, OSError) as e:
            print(f"[startup] could not initialise from {path}: {e}", flush=True)
    else:
        print(f"[startup] no config file at {path}: POST /init to create the grid", flush=True)
    yield


# No /docs and /redoc: their pages load scripts from a CDN, and the system is local only.
app = FastAPI(title="grid-api", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


# ---- simple error messages: always {"error": "..."} --------------------------------------
@app.exception_handler(GridError)
async def _grid_error(_req, exc: GridError):
    print(f"[refused] {exc}", flush=True)
    return JSONResponse({"error": str(exc)}, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def _validation_error(_req, exc: RequestValidationError):
    err = exc.errors()[0]
    where = ".".join(str(x) for x in err["loc"] if x not in ("body", "query", "path"))
    msg = f"invalid input at '{where}': {err['msg']}" if where else f"invalid input: {err['msg']}"
    print(f"[refused] {msg}", flush=True)
    return JSONResponse({"error": msg + " (see GET /help)"}, status_code=422)


@app.exception_handler(StarletteHTTPException)
async def _http_error(_req, exc: StarletteHTTPException):
    return JSONResponse({"error": f"{exc.detail} (see GET /help)"}, status_code=exc.status_code)


# ---- routes ----------------------------------------------------------------------------
@app.get("/help")
def help_():
    return {"endpoints": ENDPOINTS, "rules": RULES, "metrics": list(DISTANCES)}


@app.get("/health")
def health():
    return {"status": "ok", "initialised": _grid is not None}


@app.post("/init")
def init(req: InitRequest):
    _init(req, "init")
    return _get().state()


@app.get("/state")
def state():
    return _get().state()


@app.get("/mission")
def mission():
    return _get().mission_summary()


@app.post("/mission")
def new_mission(req: MissionIn):
    g = _get()
    with _lock:
        g.set_mission(req.start, req.target, req.threshold, req.agent)
    _show("new mission")
    return g.mission_summary()


@app.post("/obstacles")
def obstacles(req: ObstaclesRequest):
    g = _get()
    with _lock:
        g.add_obstacles([(o.node, o.weight) for o in req.obstacles])
    _show(f"{len(req.obstacles)} obstacle(s) set")
    return {"obstacles": g.obstacles()}


@app.get("/nodes/{r}/{c}/neighbors")
def neighbors(r: int, c: int):
    return _get().neighbors_info((r, c))


@app.get("/distance")
def distance(r1: int, c1: int, r2: int, c2: int, metric: str = "manhattan"):
    return {"metric": metric, "distance": _get().distance((r1, c1), (r2, c2), metric)}


@app.get("/agents/{name}")
def agent(name: str):
    a = _get()._agent(name)
    return {"name": a.name, "pose": list(a.pose),
            "total_weight": a.total_weight, "steps": a.steps}


@app.post("/agents/{name}/move")
def move(name: str, req: MoveRequest):
    g = _get()
    with _lock:
        cost = g.move_agent(name, req.to)
    a = g.agents[name]
    _show(f"{name} -> {tuple(req.to)}  (cost {cost:g})")
    return {"agent": name, "pose": list(a.pose), "move_cost": cost,
            "total_weight": a.total_weight, "mission": g.mission_summary()}


@app.get("/directions")
def directions():
    return {"directions": {d: list(delta) for d, delta in DIRECTIONS.items()},
            "note": "diagonal directions (NE, NW, SE, SW) need connectivity 8"}


@app.post("/agents/{name}/move/{direction}")
def move_direction(name: str, direction: Direction):
    g = _get()
    with _lock:
        cost = g.move_agent_direction(name, direction)
    a = g.agents[name]
    _show(f"{name} -> {direction} -> {tuple(a.pose)}  (cost {cost:g})")
    return {"agent": name, "direction": direction, "pose": list(a.pose), "move_cost": cost,
            "total_weight": a.total_weight, "mission": g.mission_summary()}


@app.get("/viz/grid")
def viz_grid_route():
    return PlainTextResponse(viz_grid(_get()) + "\n")


@app.get("/viz/graph")
def viz_graph_route():
    g = _get()
    buf = io.BytesIO()
    try:
        viz_graph(g, buf)
    except ImportError:
        return JSONResponse({"error": "matplotlib is not installed in this image "
                                      "(build with WITH_VIZ=1)"}, status_code=501)
    return Response(buf.getvalue(), media_type="image/png")