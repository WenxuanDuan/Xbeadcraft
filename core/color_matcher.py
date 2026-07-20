from __future__ import annotations

import numpy as np
from PIL import Image
from skimage.color import rgb2lab

from .palette import Palette
from .pattern import Pattern


class ColorMatcher:
    """
    将RGBA图片匹配到拼豆色卡。

    图片中的每个非透明像素，会被转换为Lab颜色，
    然后寻找色卡中距离最近的颜色。
    """

    def __init__(self, palette: Palette):
        self.palette = palette

    def match(
        self,
        image: Image.Image,
        alpha_threshold: int = 128,
    ) -> Pattern:
        """
        将图片转换为Pattern。

        alpha_threshold:
            Alpha值小于该阈值的像素视为透明，
            在Pattern中记录为-1。
        """

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
        """
        分批寻找每个像素最接近的色卡颜色。

        分批处理是为了避免较大图纸时一次创建
        过大的“像素数 × 221色”距离矩阵。
        """

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