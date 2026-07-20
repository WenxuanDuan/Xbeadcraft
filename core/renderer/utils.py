from __future__ import annotations

from PIL import ImageFont


def load_font(size: int):
    """
    加载系统字体，失败则使用 Pillow 默认字体。
    """

    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "Arial.ttf",
    ]

    for path in font_paths:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue

    return ImageFont.load_default()