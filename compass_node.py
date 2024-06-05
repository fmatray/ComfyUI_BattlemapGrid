import torch
from PIL.ImageDraw import Draw
from PIL import ImageFont
from .utils import tensor_to_pil, pil_to_tensor
from .point import Point
import random


class CompassGrid:

    def __init__(self):
        self.black_pen = (0, 0, 0)
        self.white_pen = (255, 255, 255)
        self.gray_pen = (80, 80, 80)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "font": ("STRING", {
                    "default": "/System/Library/Fonts/Supplemental/Arial.ttf"}),
                "cardinals": (["NWSE", "NOSE"], {"default": "NWSE"}),
                "position": (
                    ["top left", "top right", "bottom left", "bottom right"],
                    {"default": "bottom right"}),
                "size": ("INT", {"default": 64, "min": 10, "max": 2048}),
                "rotation": ("INT", {"default": 0, "min": 0, "max": 360}),
                "seed": (
                    "INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "random_rotation": ("BOOLEAN",
                                    {"default": True, "label_off": "OFF",
                                     "label_on": "ON"}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "compass_overlay"
    CATEGORY = "Battlemaps"

    def get_center_position(self, image_pil, position: str,
                            size: int) -> Point:
        point = Point(0, 0)
        padding = int(size / 2)
        if "top" in position:
            point.y = size + padding
        elif "bottom" in position:
            point.y = image_pil.height - size - padding
        else:
            raise ValueError("Cannot position the compass")

        if "left" in position:
            point.x = size + padding
        elif "right" in position:
            point.x = image_pil.width - size - padding
        else:
            raise ValueError("Cannot position the compass")

        return point

    def draw_arrow(self, draw: Draw, font, center: Point,
                   angle: int, size: int, cardinal=None):

        if cardinal:
            card_point = center.add_polar(size * 1.2, 90 + angle)
            draw.text(card_point.coord(), cardinal, font=font, anchor="mm",
                      fill=self.black_pen,
                      stroke_width=1, stroke_fill=self.gray_pen)
        else:
            size = size * 0.75

        point1 = center.add_polar(size / 4, 45 + angle)
        point2 = center.add_polar(size, 90 + angle)
        point3 = center.add_polar(size / 4, 135 + angle)
        draw.polygon(
            [center.coord(), point1.coord(), point2.coord()], self.black_pen)
        draw.polygon(
            [center.coord(), point2.coord(), point3.coord()], self.white_pen)

    def compass_overlay(self, image: torch.Tensor, font: str, cardinals: str,
                        position: str, size: int,
                        seed: int,
                        rotation: int, random_rotation: bool):
        image_pil = tensor_to_pil(image)
        draw = Draw(image_pil, "RGBA")
        if random_rotation:
            random.seed(seed)
            rotation = random.randint(0, 360)

        font = ImageFont.truetype(font, int(size / 4))
        center = self.get_center_position(image_pil, position, size)
        draw.ellipse(
            [(center - size * 0.8).coord(), (center + size * 0.8).coord()],
            outline=self.black_pen, width=min(6, round(size / 12)))
        draw.ellipse(
            [(center - size * 0.7).coord(), (center + size * 0.7).coord()],
            outline=self.black_pen, width=min(4, round(size / 16)))
        for i in range(0, 360, 90):
            self.draw_arrow(draw, font, center, i + 45 + rotation, size)
        for i, card in zip(range(0, 360, 90), cardinals):
            self.draw_arrow(draw, font, center, i + rotation, size,
                            cardinal=card)
        image_tensor_out = pil_to_tensor(image_pil)
        return (image_tensor_out,)
