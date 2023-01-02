from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from typing import Dict, List, Literal


@dataclass(frozen=True)
class PathPoint:
    lat: int
    lon: int

    type: Literal["S", "W"] = "W"

    projected_dist: int = 0
    interpolated: bool = False


@dataclass(frozen=True, kw_only=True)
class PathStopPoint(PathPoint):
    type: Literal["S"] = "S"

    name: str
    id: int
    reported_dist: int


@dataclass(frozen=True, kw_only=True)
class RoutePath:
    id: int
    reported_length: int
    direction: Literal["INBOUND", "OUTBOUND"]

    # Path will only contain WayPoints
    path: List[PathPoint]
    path_orig: List[PathPoint]

    stops: List[PathStopPoint]

    dtrid: int
    dtrpt: List[PathPoint]
    dtrstops: List[PathStopPoint]


@dataclass(frozen=True)
class Route:
    num: int
    name: str
    color: str
    path: Dict[str, RoutePath]


def project_pdist_path(path: List[PathPoint], pdist: float) -> tuple[float, float]:
    """
    Expects sorted path
    """
    path_len = path[-1].projected_dist

    # Clip pdist to path length
    if pdist > path_len:
        return (path[-1].lat, path[-1].lon)
    if pdist < 0:
        return (path[0].lat, path[0].lon)

    index = bisect_left(path, pdist, key=lambda p: p.projected_dist)
    if index == 0:
        return (path[0].lat, path[0].lon)
    if index == len(path):
        return (path[-1].lat, path[-1].lon)
    if path[index].projected_dist == pdist:
        return (path[index].lat, path[index].lon)

    # Interpolate
    prev = path[index - 1]
    next = path[index]
    ratio = (pdist - prev.projected_dist) / (next.projected_dist - prev.projected_dist)
    lat = prev.lat + ratio * (next.lat - prev.lat)
    lon = prev.lon + ratio * (next.lon - prev.lon)
    return (lat, lon)
