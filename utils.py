import numpy as np
import torch
from PIL import Image
from random import randint
from .point import Point


def tensor_to_pil(image_tensor: torch.tensor):
    image_np = image_tensor.cpu().numpy()
    image_pil = Image.fromarray((image_np.squeeze(0) * 255).astype(np.uint8))
    return image_pil.convert("RGBA")


def pil_to_tensor(image_pil: Image):
    image_tensor_out = torch.tensor(
        np.array(image_pil).astype(np.float32) / 255.0)
    return torch.unsqueeze(image_tensor_out, 0)


def generate_noise(image, point1: Point, point2: Point, padding=0):
    def noise_color(i, j, color_index):
        noise = randint(-64, 64)
        return max(0, min(pixels[i, j][color_index] + noise, 255))

    pixels = image.load()
    for i in range(point1.x - padding, point2.x + padding):
        for j in range(point1.y - padding, point2.y + padding):
            try:
                pixels[i, j] = (
                    noise_color(i, j, 0),
                    noise_color(i, j, 1),
                    noise_color(i, j, 2)
                )
            except IndexError:
                pass
