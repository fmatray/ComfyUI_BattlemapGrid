from PIL import Image, ImageDraw, ImageColor, ImageFilter
import math
from colorsys import rgb_to_hsv, hsv_to_rgb
from random import random, randint, seed, choice
from .utils import pil_to_tensor


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
            "bg_color": ("STRING", {"default": "#FFFFFF"}),
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

        }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING",
                    "INT", "INT",
                    "INT", "INT", "INT")
    RETURN_NAMES = ("image", "positive prompt", "negative prompt",
                    "image width", "image height",
                    "grid width", "grid height", "grid side")
    FUNCTION = "map_generator"
    CATEGORY = "Battlemaps"

    def generate_noise(self, image, x1, y1, x2, y2, padding=0):
        def noise_color(i, j, color_index):
            noise = randint(-128, 128)
            return max(0, min(pixels[i, j][color_index] + noise, 255))

        pixels = image.load()
        for i in range(x1 - padding, x2 + padding):
            for j in range(y1 - padding, y2 + padding):
                try:
                    pixels[i, j] = (
                        noise_color(i, j, 0),
                        noise_color(i, j, 1),
                        noise_color(i, j, 2)
                    )
                except IndexError:
                    pass

    def generate_image(self, width, height, bg_color):
        image = Image.new("RGBA", (width, height), bg_color)
        return image

    def generate_bg(self, image, draw, bg_color):
        r, g, b = ImageColor.getcolor(bg_color, "RGB")

        for x in range(0, image.width + 10, 10):
            for y in range(0, image.height + 10, 10):
                color = (min(abs(r + randint(-100, 100)), 255),
                         min(abs(g + randint(-100, 100)), 255),
                         min(abs(b + randint(-100, 100)), 255))
                draw.ellipse([(x - 4, y - 4), (x + 4, y + 4)], fill=color)
        self.generate_noise(image, 0, 0, image.width, image.height)

    def generator_flowers(self, image, draw):
        pass

    def start_point(self, image):
        match randint(0, 3):
            case 0:
                point = (randint(0, image.width), 0)
                angle = randint(200, 340)
            case 1:
                point = (randint(0, image.width), image.height)
                angle = randint(2, 160)
            case 2:
                point = (0, randint(0, image.height))
                angle = 70 - randint(0, 140)
            case 3:
                point = (image.width, randint(0, image.height))
                angle = randint(110, 250)
        return point, angle

    def generate_path(self, image, draw, color,
                      start_point, start_angle, width=20,
                      depth=0, max_depth=3):
        if depth > max_depth:
            return
        point1, angle, length = start_point, start_angle, randint(100, 150)
        point_list = [point1]
        while 0 <= point1[0] <= image.width or 0 <= point1[
            1] <= image.height:
            point2 = (
                int(point1[0] + length * math.cos(angle * math.pi / 180)),
                int(point1[0] + length * math.sin(angle * math.pi / 180))
            )
            point_list.append(point2)
            match randint(0, 50):
                case 0:
                    break
                case 1:
                    self.generate_path(image, draw, color,
                                       point1, angle + randint(-10, 10),
                                       max(5, width + randint(-5, 5)),
                                       depth + 1, max_depth)
                case 2:
                    draw.ellipse([(point2[0] - width, point2[1] - width),
                                  (point2[0] + width, point2[1] + width)],
                                 fill=color)
                case _:
                    pass
            point1, angle, length = (point2, angle + randint(-10, 10),
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
        point = randint(0, image.width), randint(0, image.height)
        size_multiplicator = random()
        for size, color in size_color:
            for angle in range(0, 360, 5):
                l = max(size / 5, size * random() * size_multiplicator)
                x = point[0] + math.ceil(l * math.cos(angle * math.pi / 180))
                y = point[1] + math.ceil(l * math.sin(angle * math.pi / 180))
                draw.line([point, (x, y)],
                          fill=color, width=7 + randint(-2, 2))
        self.generate_noise(image, point[0] - size, point[1] - size,
                            point[0] + size, point[1] + size, 10)

    def generate_polygon(self, image, draw, size_color, nb_point):
        point = randint(0, image.width), randint(0, image.height)
        size_multiplicator = max(0.5, random())
        for size, color in size_color:
            point_list = list()
            for angle in range(0, 360, int(360 / nb_point)):
                l = max(size / 5, size * random() * size_multiplicator)
                x = point[0] + math.ceil(l * math.cos(angle * math.pi / 180))
                y = point[1] + math.ceil(l * math.sin(angle * math.pi / 180))
                point_list.append((x, y))
            draw.polygon(point_list, fill=color, outline="black", width=2)
        self.generate_noise(image, point[0] - size, point[1] - size,
                            point[0] + size, point[1] + size, 10)

    def generate_ellipses(self, image, draw, size_color):
        point = randint(0, image.width), randint(0, image.height)
        x_min, y_min = image.width, image.height
        x_max, y_max = 0, 0
        size_multiplicator = random()
        for size, color in size_color:
            _size = math.ceil(size * size_multiplicator)
            x1, y1 = (point[0] - _size + randint(-5, 5),
                      point[1] - _size + randint(-5, 5))
            x2, y2 = (point[0] + _size + randint(-5, 5),
                      point[1] + _size + randint(-5, 5))
            x_min, y_min = min(x_min, x1), min(y_min, y1)
            x_max, y_max = max(x_max, x2), max(y_max, y2)
            draw.ellipse(
                [(min(x1, x2), min(y1, y2)), (max(x1, x2), max(y1, y2))],
                fill=color, outline="black", width=2)
        self.generate_noise(image, x_min, y_min, x_max, y_max, 10)

    def generate_rocks(self, image, draw):
        for i in range(10):
            self.generate_polygon(image, draw, [(60, "#111111"),
                                                (50, "darkgray"),
                                                (40, "gray")],
                                  choice([3, 4, 5, 6, 8, 9, 10]))

    def generate_trees(self, image, draw):
        for i in range(30):
            self.generate_stars(image, draw, [(45, "darkgray"),
                                              (40, "darkgreen"),
                                              (30, "green"),
                                              (20, "lightgreen")])

    def map_generator(self, node_seed, grid_width, grid_height,
                      grid_side, bg_color, river, road, trees, rocks):
        seed(node_seed)
        positive, negative = list(), list()
        width, height = grid_width * grid_side, grid_height * grid_side
        image_pil = self.generate_image(width, height, bg_color)
        draw = ImageDraw.Draw(image_pil)
        self.generate_bg(image_pil, draw, bg_color)

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
            self.generate_rocks(image_pil, draw)
            positive.append("gray rocks")
        else:
            negative.append("rocks")

        if rocks:
            self.generate_trees(image_pil, draw)
            positive.append("green trees")
        else:
            negative.append("trees")

        return (pil_to_tensor(image_pil),
                ".\n".join(positive), ".\n".join(negative),
                width, height, grid_width, grid_height, grid_side)
