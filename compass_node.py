import torch
from PIL import ImageDraw, ImageFont
from .utils import tensor_to_pil, pil_to_tensor
from .point import Point

BLACK = (0, 0, 0, 128)
WHITE = (255, 255, 255, 128)


class CompassGrid:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "font": ("STRING", {
                    "default": "/System/Library/Fonts/Supplemental/Arial.ttf"}),
                "cardinals": (["NWSE", "NOSE"], {"default": "NWSE"}),
                "size": ("INT", {"default": 64, "min": 10, "max": 2048}),
                "rotation": ("INT", {"default": 0, "min": 0, "max": 360}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "compass_overlay"
    CATEGORY = "Battlemaps"

    def draw_arrow(self, draw: ImageDraw.Draw, font, center: Point,
                   angle: int, size: int, cardinal=None):
        point1 = center.add_polar(size / 4, 45 + angle)
        point2 = center.add_polar(size, 90 + angle)
        point3 = center.add_polar(size / 4, 135 + angle)
        color1, color2 = BLACK, WHITE
        if cardinal:
            card_point = center.add_polar(size + size / 8, 90 + angle)
            draw.text(card_point.coord(), cardinal, font=font, fill=BLACK,
                      anchor="mm")
        draw.polygon([center.coord(), point1.coord(), point2.coord()],
                     fill=color1, width=2)

        draw.polygon([center.coord(), point2.coord(), point3.coord()],
                     fill=color2, width=2)

    def compass_overlay(self, image: torch.Tensor, font: str, cardinals: str,
                        size: int, rotation: int):
        image_pil = tensor_to_pil(image)
        # Create Gri
        draw = ImageDraw.Draw(image_pil)
        font = ImageFont.truetype(font, int(size / 4))
        point = Point(image_pil.width / 2, image_pil.height / 2)
        draw.ellipse(
            [(point - size * 0.8).coord(), (point + size * 0.8).coord()],
            outline=BLACK, width=2)
        draw.ellipse(
            [(point - size * 0.7).coord(), (point + size * 0.7).coord()],
            outline=BLACK, width=2)
        for i in range(0, 360, 90):
            self.draw_arrow(draw, font, point, i + 45 + rotation, size)
        for i, card in zip(range(0, 360, 90), cardinals):
            self.draw_arrow(draw, font, point, i + rotation, size,
                            cardinal=card)
        image_tensor_out = pil_to_tensor(image_pil)
        return (image_tensor_out,)
