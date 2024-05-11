import numpy as np
import torch
from PIL import Image
from random import randint


def tensor_to_pil(image_tensor: torch.tensor):
    image_np = image_tensor.cpu().numpy()
    image_pil = Image.fromarray((image_np.squeeze(0) * 255).astype(np.uint8))
    return image_pil.convert("RGBA")


def pil_to_tensor(image_pil: Image):
    image_tensor_out = torch.tensor(
        np.array(image_pil).astype(np.float32) / 255.0)
    return torch.unsqueeze(image_tensor_out, 0)


def generate_noise(image, x1, y1, x2, y2, padding=0):
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
