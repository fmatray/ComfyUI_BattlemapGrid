from PIL import Image, ImageDraw, ImageColor, ImageFilter
import math
from dataclasses import dataclass
from colorsys import rgb_to_hsv, hsv_to_rgb
from random import random, randint, seed, choice
from .utils import pil_to_tensor, generate_noise
from .point import Point
from .path import Path


@dataclass
class BattlemapMapGenerator:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "node_seed": (
                "INT", {"default": 0, "min": -1, "max": 0xffffffffffffffff,
                        "step": 1, "label": "seed", "forceInput": True}),
            "grid_width": ("INT", {"default": 24, "min": 10, "max": 128}),
            "grid_height": ("INT", {"default": 32, "min": 10, "max": 128}),
            "grid_side": ("INT", {"default": 32, "min": 10, "max": 2048}),
            "bg_color": ("STRING", {"default": "#00FF00"}),
        }
        }

    @classmethod
    @property
    def RETURN_TYPES(cls):
        return ("IMAGE", "INT", "INT",
                "INT", "INT", "INT")

    @classmethod
    @property
    def RETURN_NAMES(cls):
        return ("image", "image width", "image height",
                "grid width", "grid height", "grid side")

    FUNCTION = "map_generator"
    CATEGORY = "Battlemaps"

    def generate_image(self, width, height, bg_color):
        image = Image.new("RGBA", (width, height), bg_color)
        return image

    def generate_bg(self, image, draw, bg_color):
        r, g, b = ImageColor.getcolor(bg_color, "RGB")
        steps = 5
        for x in range(0, image.width + steps, steps):
            for y in range(0, image.height + steps, steps):
                color = (min(abs(r + randint(-100, 100)), 255),
                         min(abs(g + randint(-100, 100)), 255),
                         min(abs(b + randint(-100, 100)), 255))
                point1 = Point(x - int(steps / 2), y - int(steps / 2))
                point2 = Point(x + int(steps / 2), y + int(steps / 2))
                draw.ellipse([point1.coord(), point2.coord()], fill=color)
        generate_noise(image, Point(0, 0), Point(image.width, image.height))

    def _map_generator(self, node_seed, grid_width, grid_height,
                       grid_side, bg_color):
        seed(node_seed)
        width, height = grid_width * grid_side, grid_height * grid_side
        image_pil = self.generate_image(width, height, bg_color)
        draw = ImageDraw.Draw(image_pil)
        self.generate_bg(image_pil, draw, bg_color)

        return (image_pil, width, height, grid_width, grid_height, grid_side)

    def map_generator(self, node_seed, grid_width, grid_height,
                      grid_side, bg_color):
        image_pil, width, height, grid_width, grid_height, grid_side = self._map_generator(
            node_seed, grid_width, grid_height, grid_side, bg_color)
        return (pil_to_tensor(image_pil),
                width, height, grid_width, grid_height, grid_side)


class BattlemapMapGeneratorOutdoors(BattlemapMapGenerator):
    @classmethod
    def INPUT_TYPES(cls):
        inputs = super().INPUT_TYPES()
        inputs['required'].update({
            "river": (
                "BOOLEAN",
                {"default": True, "label_off": "OFF", "label_on": "ON"}),
            "road": (
                "BOOLEAN",
                {"default": True, "label_off": "OFF", "label_on": "ON"}),
            "rocks": (
                "BOOLEAN",
                {"default": True, "label_off": "OFF", "label_on": "ON"}),
            "trees": (
                "BOOLEAN",
                {"default": True, "label_off": "OFF", "label_on": "ON"}),

            "positive": ("STRING", {"default": '', "multiline": True}),
            "negative": ("STRING", {"default": '', "multiline": True}),
        })
        return inputs

    @classmethod
    @property
    def RETURN_TYPES(cls):
        return_types = list(super().RETURN_TYPES)
        return_types.extend(["STRING", "STRING"])
        return tuple(return_types)

    @classmethod
    @property
    def RETURN_NAMES(cls):
        return_names = list(super().RETURN_NAMES)
        return_names.extend(["positive prompt", "negative prompt"])
        return tuple(return_names)

    def generator_flowers(self, image, draw):
        for i in range(100, 500):
            point = Point(randint(0, image.width), randint(0, image.height))
            size = randint(2, 6)
            draw.ellipse([(point - size).coord(), (point + size).coord()],
                         fill=choice(list(ImageColor.colormap.keys())),
                         outline="black", width=2)

    def start_point(self, image):
        match randint(0, 3):
            case 0:
                point = Point(randint(0, image.width), -10)
            case 1:
                point = Point(randint(0, image.width), image.height + 10)
            case 2:
                point = Point(-10, randint(0, image.height))
            case 3:
                point = Point(image.width + 10, randint(0, image.height))
        angle = point.angle_between(Point(image.width / 2, image.height / 2))
        return point, angle + randint(-45, 45)

    def generate_path(self, image, paths: list[Path], start_point, start_angle,
                      width=20,
                      depth=0, depth_max=5):
        if depth > depth_max or width <= 5:
            return
        point1, angle, length = start_point, start_angle, randint(100, 150)
        path = Path(width=width)
        path.add_point(point1)
        while -10 <= point1.x <= image.width + 10 and -10 <= point1.y <= image.height + 10:
            point2 = point1.add_polar(length, angle)
            path.add_point(point2)
            match randint(0, 20):
                case 0:
                    break
                case 1 | 2:
                    new_angle = angle + randint(10, 30) * choice([-1, 1])
                    self.generate_path(image, paths, point1, new_angle,
                                       width=math.ceil(width * 2 / 3),
                                       depth=depth + 1, depth_max=depth_max)
                case _:
                    pass
            point1, angle, length = (point2, angle + randint(-20, 20),
                                     randint(20, 200))
        paths.append(path)

    def draw_path(self, draw, color, paths: list):
        width_max = 0
        for path in paths:
            width_max = max(width_max, path.width)
            draw.line(path.coord(), fill="black", width=path.width + 2,
                      joint="curve")
        for i in range(width_max, 0, -1):
            h, s, v = rgb_to_hsv(*ImageColor.getcolor(color, "RGB"))
            r, g, b = map(int, hsv_to_rgb(h, s, v / i ** 0.3))
            for path in filter(lambda x: x.width <= width_max, paths):
                draw.line(path.coord(), fill=(r, g, b), width=i, joint="curve")

    def generate_rivers(self, image, draw):
        point, angle = self.start_point(image)
        paths = list()
        self.generate_path(image, paths, point, angle)
        self.draw_path(draw, "blue", paths)

    def generate_roads(self, image, draw):
        point, angle = self.start_point(image)
        paths = list()
        self.generate_path(image, paths, point, angle)
        self.draw_path(draw, "saddlebrown", paths)

    def generate_stars(self, image, draw, size_color):
        center = Point(randint(0, image.width), randint(0, image.height))
        size_multiplicator = random()
        for size, color in size_color:
            for angle in range(0, 360, 5):
                length = max(size / 5, size * random() * size_multiplicator)
                point = center.add_polar(length, angle)
                witdh = randint(5, 10)
                draw.line([center.coord(), point.coord()],
                          fill="black", width=witdh + 2)
                draw.line([center.coord(), point.coord()],
                          fill=color, width=witdh)
        generate_noise(image, center - size, center + size, 10)

    def generate_polygon(self, image, draw, size_color, nb_point):
        center = Point(randint(0, image.width), randint(0, image.height))
        size_multiplicator = max(0.5, random())
        for size, color in size_color:
            point_list = list()
            for angle in range(0, 360, int(360 / nb_point)):
                length = max(size / 5, size * random() * size_multiplicator)
                point = center.add_polar(length, angle)
                point_list.append(point.coord())
            draw.polygon(point_list, fill=color, outline="black", width=2)
        generate_noise(image, center - size, center + size, 10)

    def generate_ellipses(self, image, draw, size_color):
        center = Point(randint(0, image.width), randint(0, image.height))
        size_multiplicator = random()
        size_max = 0
        for size, color in size_color:
            size_max = max(size_max, math.ceil(size * size_multiplicator))
            point1 = center - math.ceil(size * size_multiplicator) - randint(0,
                                                                             10)
            point2 = center + math.ceil(size * size_multiplicator) + randint(0,
                                                                             10)
            draw.ellipse([point1.coord(), point2.coord()],
                         fill=color, outline="black", width=2)
        generate_noise(image, center - size_max, center + size_max, 10)

    def generate_rocks(self, image, draw):
        for i in range(10):
            self.generate_polygon(image, draw, [(50, "#111111"),
                                                (35, "darkgray"),
                                                (25, "gray")],
                                  choice([3, 4, 5, 6, 8, 9]))

    def generate_trees(self, image, draw):
        for i in range(100):
            self.generate_stars(image, draw, [(45, "darkgray"),
                                              (40, "darkgreen"),
                                              (30, "green"),
                                              (20, "lightgreen")])

    def map_generator(self, node_seed, grid_width, grid_height,
                      grid_side, bg_color, river, road, rocks, trees,
                      positive, negative):
        seed(node_seed)
        image, width, height, grid_width, grid_height, grid_side = (
            self._map_generator(node_seed, grid_width, grid_height, grid_side,
                                bg_color))
        draw = ImageDraw.Draw(image)
        self.generator_flowers(image, draw)
        if river:
            self.generate_rivers(image, draw)
            positive += "blue river, water."
        else:
            negative += "blue river, water."
        if road:
            self.generate_roads(image, draw)
            positive += "saddlebrown road."
        else:
            negative += "road."

        if rocks:
            self.generate_rocks(image, draw)
            positive += "green trees."
        else:
            negative += "trees."

        if trees:
            self.generate_trees(image, draw)
            positive += "gray rocks."
        else:
            negative += "rocks."

        return (pil_to_tensor(image),
                width, height, grid_width, grid_height, grid_side,
                positive, negative)
