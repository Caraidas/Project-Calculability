"""What can be sent to the API. Unknown fields are rejected."""
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Node = tuple[int, int]                                        # [row, col], 0-based
ObstacleWeight = Annotated[int, Field(strict=True, gt=1)]     # an int > 1


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ObstacleIn(_Strict):
    node: Node
    weight: ObstacleWeight


class MissionIn(_Strict):
    start: Node
    target: Node
    threshold: Annotated[float, Field(gt=0)]
    agent: Optional[str] = None       # default: the first agent


class InitRequest(_Strict):
    size: Annotated[int, Field(strict=True, ge=1)]
    connectivity: Literal[4, 8] = 4
    agents: Annotated[list[str], Field(min_length=1)]
    obstacles: list[ObstacleIn] = []
    mission: MissionIn


class ObstaclesRequest(_Strict):
    obstacles: Annotated[list[ObstacleIn], Field(min_length=1)]


class MoveRequest(_Strict):
    to: Node