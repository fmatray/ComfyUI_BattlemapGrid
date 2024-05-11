import numpy as np
import torch
from PIL import Image


def tensor_to_pil(image_tensor: torch.tensor):
    image_np = image_tensor.cpu().numpy()
    image_pil = Image.fromarray((image_np.squeeze(0) * 255).astype(np.uint8))
    return image_pil.convert("RGBA")


def pil_to_tensor(image_pil: Image):
    image_tensor_out = torch.tensor(
        np.array(image_pil).astype(np.float32) / 255.0)
    return torch.unsqueeze(image_tensor_out, 0)
