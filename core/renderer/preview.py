from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

from core.pattern import Pattern


def render_preview(
    pattern: Pattern,
    scale: int = 20,
    checkerboard: bool = True,
) -> Image.Image:
    """Render enlarged bead colors with an optional checkerboard for empty cells."""

    scale = max(1, int(scale))

    width = pattern.width * scale
    height = pattern.height * scale

    canvas = Image.new(
        "RGBA",
        (width, height),
        (255, 255, 255, 0),
    )

    draw = ImageDraw.Draw(canvas)

    light = (245, 245, 245, 255)
    dark = (225, 225, 225, 255)

    for y in range(pattern.height):

        for x in range(pattern.width):

            left = x * scale
            top = y * scale

            right = left + scale
            bottom = top + scale

            value = pattern.grid[y, x]

            if value < 0:

                if checkerboard:

                    color = (
                        light
                        if (x + y) % 2 == 0
                        else dark
                    )

                    draw.rectangle(
                        (
                            left,
                            top,
                            right,
                            bottom,
                        ),
                        fill=color,
                    )

                continue

            rgb = pattern.palette[value].rgb

            draw.rectangle(
                (
                    left,
                    top,
                    right,
                    bottom,
                ),
                fill=(
                    rgb[0],
                    rgb[1],
                    rgb[2],
                    255,
                ),
            )

    return canvas