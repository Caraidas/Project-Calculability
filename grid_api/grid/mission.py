"""Agent and Mission: the state the grid keeps. No decision logic here."""
from dataclasses import dataclass

Pose = tuple[int, int]

RUNNING, SUCCESS, FAILED = "running", "success", "failed"


@dataclass
class Agent:
    name: str
    pose: Pose
    total_weight: float = 0.0
    steps: int = 0

    def reset(self, pose: Pose) -> None:
        self.pose, self.total_weight, self.steps = pose, 0.0, 0


@dataclass
class Mission:
    agent: str          # the agent whose pose and total weight decide the outcome
    start: Pose         # A
    target: Pose        # B
    threshold: float    # the mission fails when the agent's total weight reaches it
    status: str = RUNNING

    @property
    def finished(self) -> bool:
        return self.status != RUNNING