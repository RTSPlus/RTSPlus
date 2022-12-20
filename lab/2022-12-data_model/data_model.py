from dataclasses import dataclass


@dataclass(frozen=True)
class Route:
    num: int
    name: str
    color: str