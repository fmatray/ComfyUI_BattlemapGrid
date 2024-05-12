from PIL import Image, ImageDraw, ImageColor, ImageFilter
import math
from dataclasses import dataclass
from random import random, randint, seed, choice
from .utils import pil_to_tensor, generate_noise
from .point import Point


@dataclass
class BattlemapMapGenerator:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "node_seed": (
                "INT", {"default": 0, "min": -1, "max": 0xffffffffffffffff,
                        "step": 1, "label": "seed"}),
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
            "trees": (
                "BOOLEAN",
                {"default": True, "label_off": "OFF", "label_on": "ON"}),
            "rocks": (
                "BOOLEAN",
                {"default": True, "label_off": "OFF", "label_on": "ON"}),

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
        pass

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

    def generate_path(self, image, draw, color,
                      start_point, start_angle, width=20,
                      depth=0, max_depth=3):
        if depth > max_depth:
            return
        point1, angle, length = start_point, start_angle, randint(100, 150)
        point_list = [point1.coord()]
        while -10 <= point1.x <= image.width + 10 and -10 <= point1.y <= image.height + 10:
            point2 = point1.add_polar(length, angle)
            point_list.append(point2.coord())
            match randint(0, 50):
                case 0:
                    break
                case 1:
                    self.generate_path(image, draw, color,
                                       point1, angle + randint(-30, 30),
                                       max(5, width + randint(-5, 5)),
                                       depth + 1, max_depth)
                case 2:
                    draw.ellipse([(point2 - width).coord(),
                                  (point2 + width).coord()],
                                 fill=color)
                case _:
                    pass
            point1, angle, length = (point2, angle + randint(-20, 20),
                                     randint(20, 200))
        draw.line(point_list, fill=color, width=width, joint="curve")

    def generate_rivers(self, image, draw):
        point, angle = self.start_point(image)
        color = (0, 0, 255, 255)
        self.generate_path(image, draw, color, point, angle)

    def generate_roads(self, image, draw):
        point, angle = self.start_point(image)
        color = "saddlebrown"
        self.generate_path(image, draw, color, point, angle)

    def generate_stars(self, image, draw, size_color):
        center = Point(randint(0, image.width), randint(0, image.height))
        size_multiplicator = random()
        for size, color in size_color:
            for angle in range(0, 360, 5):
                length = max(size / 5, size * random() * size_multiplicator)
                point = center.add_polar(length, angle)
                draw.line([center.coord(), point.coord()],
                          fill=color, width=7 + randint(-2, 2))
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
        max_size = 0
        for size, color in size_color:
            max_size = max(max_size, math.ceil(size * size_multiplicator))
            point1 = center - math.ceil(size * size_multiplicator) - randint(0, 10)
            point2 = center + math.ceil(size * size_multiplicator) + randint(0, 10)
            draw.ellipse([point1.coord(), point2.coord()],
                         fill=color, outline="black", width=2)
        generate_noise(image, center - max_size, center + max_size, 10)

    def generate_rocks(self, image, draw):
        for i in range(10):
            self.generate_ellipses(image, draw, [(60, "#111111"),
                                                 (50, "darkgray"),
                                                 (40, "gray")])
            # choice([3, 4, 5, 6, 8, 9, 10])

    def generate_trees(self, image, draw):
        for i in range(100):
            self.generate_stars(image, draw, [(45, "darkgray"),
                                              (40, "darkgreen"),
                                              (30, "green"),
                                              (20, "lightgreen")])

    def map_generator(self, node_seed, grid_width, grid_height,
                      grid_side, bg_color, river, road, trees, rocks):
        seed(node_seed)
        positive, negative = list(), list()
        image_pil, width, height, grid_width, grid_height, grid_side = (
            self._map_generator(node_seed, grid_width, grid_height, grid_side,
                                bg_color))
        draw = ImageDraw.Draw(image_pil)

        positive.append("Battlemap, outdoor, old medieval.")
        positive.append("lightgreen background grass with small flowers")
        if river:
            self.generate_rivers(image_pil, draw)
            positive.append("blue river, water")
        else:
            negative.append("blue river, water")
        if road:
            self.generate_roads(image_pil, draw)
            positive.append("saddlebrown road")
        else:
            negative.append("road")

        if trees:
            self.generate_trees(image_pil, draw)
            positive.append("gray rocks")
        else:
            negative.append("rocks")

        if rocks:
            self.generate_rocks(image_pil, draw)
            positive.append("green trees")
        else:
            negative.append("trees")

        return (pil_to_tensor(image_pil),
                width, height, grid_width, grid_height, grid_side,
                ".\n".join(positive), ".\n".join(negative))
