from __future__ import annotations

import numpy as np
from PIL import Image
from skimage.color import rgb2lab

from .palette import Palette
from .pattern import Pattern


class ColorMatcher:
    """Match visible RGBA pixels to the closest selected palette colors in Lab space."""

    def __init__(self, palette: Palette):
        self.palette = palette

    def match(
        self,
        image: Image.Image,
        alpha_threshold: int = 128,
    ) -> Pattern:
        """Build a pattern from an image; pixels below alpha_threshold become empty cells."""

        rgba = np.asarray(
            image.convert("RGBA"),
            dtype=np.uint8,
        )

        rgb = rgba[:, :, :3].astype(np.float32) / 255.0
        alpha = rgba[:, :, 3]

        height, width, _ = rgb.shape

        pixel_lab = rgb2lab(rgb).reshape(-1, 3)

        matched_indices = self._find_nearest_colors(
            pixel_lab,
        )

        grid = matched_indices.reshape(
            height,
            width,
        )

        grid[alpha < alpha_threshold] = -1

        return Pattern(
            grid=grid,
            palette=self.palette,
        )

    def _find_nearest_colors(
        self,
        pixel_lab: np.ndarray,
        chunk_size: int = 4096,
    ) -> np.ndarray:
        """Find nearest palette colors in chunks to limit the pixel-by-palette distance matrix."""

        result = np.empty(
            len(pixel_lab),
            dtype=np.int32,
        )

        palette_lab = self.palette.lab_array

        for start in range(
            0,
            len(pixel_lab),
            chunk_size,
        ):
            end = min(
                start + chunk_size,
                len(pixel_lab),
            )

            pixels = pixel_lab[start:end]

            distances = np.sum(
                (
                    pixels[:, None, :]
                    - palette_lab[None, :, :]
                ) ** 2,
                axis=2,
            )

            result[start:end] = np.argmin(
                distances,
                axis=1,
            )

        return result