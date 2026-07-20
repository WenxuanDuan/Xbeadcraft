from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from core.pattern import Pattern


def _load_font(size: int) -> ImageFont.ImageFont:
    """
    尝试加载系统字体，失败时使用 Pillow 默认字体。
    """

    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial.ttf",
        "Arial.ttf",
    ]

    for font_path in font_paths:
        try:
            return ImageFont.truetype(
                font_path,
                size=size,
            )
        except OSError:
            continue

    return ImageFont.load_default()


def render_legend(
    pattern: Pattern,
    row_height: int = 44,
    width: int = 460,
    title: str = "MARD Color Legend",
) -> Image.Image:
    """
    将 Pattern 的图例渲染成图片。

    每一行包含：

    - 图纸编号
    - 颜色色块
    - MARD 色号
    - HEX
    - 使用数量
    """

    legend_table = pattern.legend_table()

    row_height = max(32, int(row_height))
    width = max(360, int(width))

    title_height = 58
    header_height = 40
    bottom_padding = 20

    row_count = len(legend_table)

    image_height = (
        title_height
        + header_height
        + row_count * row_height
        + bottom_padding
    )

    image = Image.new(
        "RGB",
        (width, image_height),
        "white",
    )

    draw = ImageDraw.Draw(image)

    title_font = _load_font(24)
    header_font = _load_font(15)
    body_font = _load_font(15)

    # 各列起始位置
    number_x = 18
    color_x = 72
    code_x = 132
    hex_x = 226
    count_x = 344

    # 标题
    draw.text(
        (18, 14),
        title,
        fill="black",
        font=title_font,
    )

    header_top = title_height

    # 表头背景
    draw.rectangle(
        (
            0,
            header_top,
            width,
            header_top + header_height,
        ),
        fill=(235, 235, 235),
    )

    draw.text(
        (number_x, header_top + 10),
        "编号",
        fill="black",
        font=header_font,
    )

    draw.text(
        (color_x, header_top + 10),
        "颜色",
        fill="black",
        font=header_font,
    )

    draw.text(
        (code_x, header_top + 10),
        "MARD色号",
        fill="black",
        font=header_font,
    )

    draw.text(
        (hex_x, header_top + 10),
        "HEX",
        fill="black",
        font=header_font,
    )

    draw.text(
        (count_x, header_top + 10),
        "数量",
        fill="black",
        font=header_font,
    )

    # 表头下划线
    draw.line(
        (
            0,
            header_top + header_height,
            width,
            header_top + header_height,
        ),
        fill=(80, 80, 80),
        width=2,
    )

    for row_index, row in legend_table.iterrows():
        top = (
            title_height
            + header_height
            + row_index * row_height
        )

        bottom = top + row_height

        # 隔行背景
        if row_index % 2 == 1:
            draw.rectangle(
                (0, top, width, bottom),
                fill=(248, 248, 248),
            )

        number = int(row["number"])
        code = str(row["code"])
        hex_color = str(row["hex"])
        count = int(row["count"])

        palette_index = int(row["palette_index"])
        rgb = pattern.palette[palette_index].rgb

        text_y = top + max(
            4,
            (row_height - 16) // 2,
        )

        # 编号
        draw.text(
            (number_x, text_y),
            str(number),
            fill="black",
            font=body_font,
        )

        # 色块
        swatch_size = min(28, row_height - 10)

        swatch_top = top + (row_height - swatch_size) // 2

        draw.rectangle(
            (
                color_x,
                swatch_top,
                color_x + swatch_size,
                swatch_top + swatch_size,
            ),
            fill=rgb,
            outline="black",
            width=1,
        )

        # MARD 色号
        draw.text(
            (code_x, text_y),
            code,
            fill="black",
            font=body_font,
        )

        # HEX
        draw.text(
            (hex_x, text_y),
            hex_color,
            fill="black",
            font=body_font,
        )

        # 数量
        draw.text(
            (count_x, text_y),
            str(count),
            fill="black",
            font=body_font,
        )

        # 行分隔线
        draw.line(
            (
                0,
                bottom,
                width,
                bottom,
            ),
            fill=(215, 215, 215),
            width=1,
        )

    return image