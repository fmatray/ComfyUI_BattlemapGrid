from dataclasses import dataclass
import math


@dataclass
class Point:
    x: int
    y: int

    def __add__(self, value):
        if isinstance(value, (int, float)):
            return Point(self.x + value, self.y + value)
        elif isinstance(value, (tuple, list)):
            return Point(self.x + value[0], self.y + value[1])
        return Point(self.x + value.x, self.y + value.y)

    def __sub__(self, value):
        if isinstance(value, (int, float)):
            return Point(self.x - value, self.y - value)
        elif isinstance(value, (tuple, list)):
            return Point(self.x - value[0], self.y - value[1])
        return Point(self.x - value.x, self.y - value.y)


    def __iter__(self):
        yield self.x
        yield self.y

    def coord(self):
        return (self.x, self.y)

    def add_polar(self, length, angle):
        return self + (
            math.ceil(length * math.cos(angle * math.pi / 180)),
            -math.ceil(length * math.sin(angle * math.pi / 180)))

    def angle_between(self, target):
        return math.degrees(math.atan2(self.y - target.y, target.x - self.x))
