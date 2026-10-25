from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from core.pattern import Pattern
from .config import RenderConfig


def _load_font(size: int) -> ImageFont.ImageFont:
    """
    加载适合显示英文字母和数字的字体。
    """

    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial.ttf",
        "Arial.ttf",
    ]

    for font_path in font_paths:
        try:
            return ImageFont.truetype(font_path, size=size)
        except OSError:
            continue

    return ImageFont.load_default()


def _center_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int] | str,
) -> None:
    """
    将文字绘制在指定矩形中心。
    """

    left, top, right, bottom = box

    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font,
    )

    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = left + (right - left - text_width) / 2
    y = top + (bottom - top - text_height) / 2 - bbox[1]

    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill,
    )


def _text_color_for_background(
    rgb: tuple[int, int, int],
) -> tuple[int, int, int]:
    """
    根据背景亮度选择黑色或白色文字。
    """

    red, green, blue = rgb

    luminance = (
        0.299 * red
        + 0.587 * green
        + 0.114 * blue
    )

    if luminance < 145:
        return (255, 255, 255)

    return (35, 35, 35)


def render_grid(
    pattern: Pattern,
    config: RenderConfig,
) -> Image.Image:
    """
    生成可直接照着摆豆的拼豆网格图。

    图纸特点：

    - 每格显示真实 MARD 色号
    - 上下左右显示坐标
    - 每 major_grid_every 格绘制粗线
    - 透明区域显示浅色棋盘背景
    - 可选显示实际颜色或淡化颜色
    """

    cell_size = max(18, int(config.cell_size))
    major_every = max(1, int(config.major_grid_every))

    coordinate_margin = max(
        24,
        int(cell_size * 0.9),
    )

    width = pattern.width
    height = pattern.height

    image_width = (
        coordinate_margin * 2
        + width * cell_size
        + 1
    )

    image_height = (
        coordinate_margin * 2
        + height * cell_size
        + 1
    )

    image = Image.new(
        "RGB",
        (image_width, image_height),
        "white",
    )

    draw = ImageDraw.Draw(image)

    cell_font_size = max(
        8,
        min(
            int(cell_size * 0.34),
            int(cell_size * 0.52),
        ),
    )

    coordinate_font_size = max(
        9,
        int(cell_size * 0.34),
    )

    cell_font = _load_font(cell_font_size)
    coordinate_font = _load_font(coordinate_font_size)

    grid_left = coordinate_margin
    grid_top = coordinate_margin

    # =========================
    # 单元格背景与色号
    # =========================

    for y in range(height):
        for x in range(width):
            x0 = grid_left + x * cell_size
            y0 = grid_top + y * cell_size
            x1 = x0 + cell_size
            y1 = y0 + cell_size

            source_x = width - 1 - x if config.mirror_horizontal else x
            palette_index = int(pattern.grid[y, source_x])

            if palette_index < 0:
                if config.checkerboard:
                    checker_color = (
                        (244, 244, 244)
                        if (x + y) % 2 == 0
                        else (232, 232, 232)
                    )
                else:
                    checker_color = (248, 248, 248)

                draw.rectangle(
                    (x0, y0, x1, y1),
                    fill=checker_color,
                )

                continue

            bead_color = pattern.palette[palette_index]
            rgb = bead_color.rgb

            if config.show_color:
                fill_color = rgb
            else:
                fill_color = (
                    int(rgb[0] * 0.28 + 255 * 0.72),
                    int(rgb[1] * 0.28 + 255 * 0.72),
                    int(rgb[2] * 0.28 + 255 * 0.72),
                )

            draw.rectangle(
                (x0, y0, x1, y1),
                fill=fill_color,
            )

            text_color = _text_color_for_background(
                fill_color
            )

            _center_text(
                draw=draw,
                box=(x0, y0, x1, y1),
                text=bead_color.code,
                font=cell_font,
                fill=text_color,
            )

    # =========================
    # 普通网格线
    # =========================

    normal_line_color = (185, 185, 185)
    major_line_color = (245, 140, 40)

    for x in range(width + 1):
        px = grid_left + x * cell_size

        is_major = (
            x == 0
            or x == width
            or x % major_every == 0
        )

        draw.line(
            (
                px,
                grid_top,
                px,
                grid_top + height * cell_size,
            ),
            fill=(
                major_line_color
                if is_major
                else normal_line_color
            ),
            width=(
                2
                if is_major
                else 1
            ),
        )

    for y in range(height + 1):
        py = grid_top + y * cell_size

        is_major = (
            y == 0
            or y == height
            or y % major_every == 0
        )

        draw.line(
            (
                grid_left,
                py,
                grid_left + width * cell_size,
                py,
            ),
            fill=(
                major_line_color
                if is_major
                else normal_line_color
            ),
            width=(
                2
                if is_major
                else 1
            ),
        )

    # =========================
    # 上下坐标
    # =========================

    if config.show_coordinate:
        for x in range(width):
            number = str(x + 1)

            x0 = grid_left + x * cell_size
            x1 = x0 + cell_size

            top_box = (
                x0,
                0,
                x1,
                coordinate_margin,
            )

            bottom_box = (
                x0,
                grid_top + height * cell_size,
                x1,
                image_height,
            )

            _center_text(
                draw,
                top_box,
                number,
                coordinate_font,
                "black",
            )

            _center_text(
                draw,
                bottom_box,
                number,
                coordinate_font,
                "black",
            )

    # =========================
    # 左右坐标
    # =========================

    if config.show_coordinate:
        for y in range(height):
            number = str(y + 1)

            y0 = grid_top + y * cell_size
            y1 = y0 + cell_size

            left_box = (
                0,
                y0,
                coordinate_margin,
                y1,
            )

            right_box = (
                grid_left + width * cell_size,
                y0,
                image_width,
                y1,
            )

            _center_text(
                draw,
                left_box,
                number,
                coordinate_font,
                "black",
            )

            _center_text(
                draw,
                right_box,
                number,
                coordinate_font,
                "black",
            )

    return image