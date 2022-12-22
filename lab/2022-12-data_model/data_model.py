from dataclasses import dataclass
from typing import Dict, List, Literal


@dataclass(frozen=True)
class PathPoint:
    seq: int
    lat: int
    lon: int

    type: Literal["S", "W"] = "W"

    projected_dist: int = 0


@dataclass(frozen=True, kw_only=True)
class PathStopPoint(PathPoint):
    type: Literal["S"] = "S"

    name: str
    id: int
    reported_dist: int


@dataclass(frozen=True, kw_only=True)
class RoutePath:
    id: int
    length: int
    direction: Literal["INBOUND", "OUTBOUND"]
    path: List[PathPoint]

    dtrid: int
    dtrpt: List[PathPoint]


@dataclass(frozen=True)
class Route:
    num: int
    name: str
    color: str
    path: Dict[str, RoutePath]
