import torch
from aggdraw import Draw, Brush, Pen
import math
from .utils import tensor_to_pil, pil_to_tensor


class BaseHexagonGenerator(object):
    """
    Abstract classe for hexagon generators for hexagons of the specified size.
    thanks to Elmer de Looff for the code.
    https://variable-scope.com/posts/hexagon-tilings-with-pytho
    """

    def __init__(self, edge_length, center_x=0, center_y=0):
        self.edge_length = edge_length
        self.center_x = center_x
        self.center_y = center_y

    @property
    def col_width(self):
        return self.edge_length * 3

    @property
    def row_height(self):
        return math.sin(math.pi / 3) * self.edge_length


class HorizontalHexagonGenerator(BaseHexagonGenerator):
    def __call__(self, row, col):
        x = self.center_x + self.col_width / 3 + (
                col + 0.5 * (row % 2)) * self.col_width
        y = self.center_y + row * self.row_height
        for angle in range(0, 360, 60):
            x += math.cos(math.radians(angle)) * self.edge_length
            y += math.sin(math.radians(angle)) * self.edge_length
            yield x
            yield y


class VerticalHexagonGenerator(BaseHexagonGenerator):
    def __call__(self, row, col):
        x = self.center_x + row * self.row_height
        y = self.center_y + self.col_width / 3 + (
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
        return {"required": {
            "image": ("IMAGE",),
            "grid_type": (cls._grid_type, {"default": "square"}),
            "grid_side": ("INT", {"default": 64, "min": 10, "max": 2048}),
            "line_width": ("INT", {"default": 1, "min": 1, "max": 20}),
            "red": ("INT", {"default": 255, "min": 0, "max": 255}),
            "green": ("INT", {"default": 255, "min": 0, "max": 255}),
            "blue": ("INT", {"default": 255, "min": 0, "max": 255}),
            "alpha": ("INT", {"default": 255, "min": 0, "max": 255}),
        }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "grid_overlay"
    CATEGORY = "Battlemaps"

    def square_grid(self, image, draw, center_x, center_y,
                    pen, grid_side):
        for i in range(0, max(center_x, center_y), grid_side):
            draw.line((center_x - i, 0, center_x - i, image.height), pen)
            draw.line((center_x + i, 0, center_x + i, image.height), pen)
            draw.line((0, center_y - i, image.width, center_y - i), pen)
            draw.line((0, center_y + i, image.width, center_y + i), pen)

    def hexagon_grid(self, HexagonGenerator: BaseHexagonGenerator,
                     image, draw, center_x, center_y,
                     pen, grid_side):
        hexagon_generator = HexagonGenerator(grid_side, center_x, center_y)
        nb_row = math.ceil(
            (image.height / hexagon_generator.row_height) / 2) + 2
        nb_col = math.ceil((image.width / hexagon_generator.col_width) / 2) + 2
        for row in range(-nb_row, nb_row):
            for col in range(-nb_col, nb_col):
                hexagon = hexagon_generator(row, col)
                draw.polygon(list(hexagon), pen)

    def grid_overlay(self, image: torch.Tensor,
                     grid_type: str, grid_side: int, line_width: int,
                     red: int, green: int, blue: int, alpha: int):
        image_pil = tensor_to_pil(image)
        # Create Grid

        draw = Draw(image_pil)
        pen = Pen((red, green, blue, alpha), line_width)
        center_x, center_y = int(image_pil.width / 2), int(image_pil.height / 2)
        if grid_type == "square":
            self.square_grid(image_pil, draw, center_x, center_y, pen,
                             grid_side)
        elif grid_type == "vertical hexagon":
            self.hexagon_grid(VerticalHexagonGenerator,
                              image_pil, draw, center_x, center_y,
                              pen, grid_side)
        elif grid_type == "horizontal hexagon":
            self.hexagon_grid(HorizontalHexagonGenerator,
                              image_pil, draw, center_x, center_y,
                              pen, grid_side)
        else:
            raise Exception
        draw.flush()
        image_tensor_out = pil_to_tensor(image_pil)
        return (image_tensor_out,)
