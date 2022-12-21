from dataclasses import dataclass
from typing import Dict, Literal

@dataclass(frozen=True)
class PathPoint:
    lat: int
    lon: int

    type: Literal["S", "W"] = "W"

@dataclass(frozen=True, kw_only=True)
class PathStopPoint(PathPoint):
    type: Literal["S"] = "S"

    name: str
    id: int
    dist: int

@dataclass(frozen=True, kw_only=True)
class RoutePath:
    id: int
    length: int
    direction: Literal["INBOUND", "OUTBOUND"]
    path: Dict[int, PathPoint]

    dtrid: int
    dtrpt: Dict[str, PathPoint]

@dataclass(frozen=True)
class Route:
    num: int
    name: str
    color: str
    path: Dict[str, RoutePath]