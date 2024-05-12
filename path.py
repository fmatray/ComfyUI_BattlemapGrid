from dataclasses import dataclass, field
from .point import Point


@dataclass
class Path:
    width: int
    points: list[Point] = field(default_factory=list)

    def add_point(self, point: Point):
        self.points.append(point)

    def coord(self):
        return [point.coord() for point in self.points]
