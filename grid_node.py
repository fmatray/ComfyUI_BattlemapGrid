import torch
from aggdraw import Draw, Brush, Pen
import math
from .utils import tensor_to_pil, pil_to_tensor
from .point import Point
from dataclasses import dataclass


@dataclass
class BaseHexagonGenerator(object):
    """
    Abstract classe for hexagon generators for hexagons of the specified size.
    thanks to Elmer de Looff for the code.
    https://variable-scope.com/posts/hexagon-tilings-with-pytho
    """

    edge_length: int = 0
    center: Point = None

    @property
    def col_width(self):
        return self.edge_length * 3

    @property
    def row_height(self):
        return math.sin(math.pi / 3) * self.edge_length


class HorizontalHexagonGenerator(BaseHexagonGenerator):
    def __call__(self, row, col):
        x = self.center.x + self.col_width / 3 + (
                col + 0.5 * (row % 2)) * self.col_width
        y = self.center.y + row * self.row_height
        for angle in range(0, 360, 60):
            x += math.cos(math.radians(angle)) * self.edge_length
            y += math.sin(math.radians(angle)) * self.edge_length
            yield x
            yield y


class VerticalHexagonGenerator(BaseHexagonGenerator):
    def __call__(self, row, col):
        x = self.center.x + row * self.row_height
        y = self.center.y + self.col_width / 3 + (
                col + 0.5 * (row % 2)) * self.col_width
        for angle in range(0, 360, 60):
            x += math.sin(math.radians(angle)) * self.edge_length
            y += math.cos(math.radians(angle)) * self.edge_length
            yield x
            yield y


class BattlemapGrid:
    _grid_type = ["square", "vertical hexagon", "horizontal hexagon"]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "grid_type": (cls._grid_type, {"default": "square"}),
                "grid_side": ("INT", {"default": 64, "min": 10, "max": 2048}),
                "line_width": ("INT", {"default": 1, "min": 1, "max": 20}),
                "red": ("INT", {"default": 255, "min": 0, "max": 255}),
                "green": ("INT", {"default": 255, "min": 0, "max": 255}),
                "blue": ("INT", {"default": 255, "min": 0, "max": 255}),
                "alpha": ("INT", {"default": 255, "min": 0, "max": 255})
            },
            "optional": {
                "orig_grid_width": ("INT",
                                    {"default": None, "min": 0, "max": 128,
                                     "forceInput": True}),
                "orig_grid_height": ("INT",
                                     {"default": None, "min": 00, "max": 128,
                                      "forceInput": True}),

            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "grid_overlay"
    CATEGORY = "Battlemaps"

    def square_grid(self, image, draw, center,
                    pen, grid_side):
        for i in range(0, max(center.x, center.y), grid_side):
            draw.line((center.x - i, 0, center.x - i, image.height), pen)
            draw.line((center.x + i, 0, center.x + i, image.height), pen)
            draw.line((0, center.y - i, image.width, center.y - i), pen)
            draw.line((0, center.y + i, image.width, center.y + i), pen)

    def hexagon_grid(self, hexagon_generator: BaseHexagonGenerator,
                     image, draw, center, pen, grid_side):
        hexagon_generator = hexagon_generator(grid_side, center)
        nb_row = math.ceil(
            (image.height / hexagon_generator.row_height) / 2) + 2
        nb_col = math.ceil((image.width / hexagon_generator.col_width) / 2) + 2
        for row in range(-nb_row, nb_row):
            for col in range(-nb_col, nb_col):
                hexagon = hexagon_generator(row, col)
                draw.polygon(list(hexagon), pen)

    def grid_overlay(self, image: torch.Tensor,
                     grid_type: str, grid_side: int, line_width: int,
                     red: int, green: int, blue: int, alpha: int,
                     orig_grid_width=None, orig_grid_height=None):
        image_pil = tensor_to_pil(image)
        # Create Grid

        draw = Draw(image_pil)
        pen = Pen((red, green, blue, alpha), line_width)
        center = Point(int(image_pil.width / 2), int(image_pil.height / 2))
        if (orig_grid_width and orig_grid_height):
            width_rate = (image_pil.width / orig_grid_width)
            height_rate = (image_pil.height / orig_grid_height)
            if 0.99 <= (width_rate / height_rate) <= 1.01:
                grid_side = round(image_pil.width / orig_grid_width)
        if grid_type == "square":
            self.square_grid(image_pil, draw, center, pen,
                             grid_side)
        elif grid_type == "vertical hexagon":
            self.hexagon_grid(VerticalHexagonGenerator,
                              image_pil, draw, center, pen, grid_side)
        elif grid_type == "horizontal hexagon":
            self.hexagon_grid(HorizontalHexagonGenerator,
                              image_pil, draw, center, pen, grid_side)
        else:
            raise Exception
        draw.flush()
        image_tensor_out = pil_to_tensor(image_pil)
        return (image_tensor_out,)
