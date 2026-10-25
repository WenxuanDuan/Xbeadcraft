from __future__ import annotations

from dataclasses import dataclass
import re

from PIL import Image, ImageDraw, ImageFont

from core.pattern import Pattern
from .config import RenderConfig


@dataclass(frozen=True)
class LegendChip:
    """Color data, bead count, and layout width for a legend chip."""

    palette_index: int
    code: str
    count: int
    rgb: tuple[int, int, int]
    width: int


def _load_font(size: int) -> ImageFont.ImageFont:
    """Load a system font, falling back to the default Pillow font."""

    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial.ttf",
        "Arial.ttf",
    ]

    for path in font_paths:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue

    return ImageFont.load_default()


def _measure_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
) -> tuple[int, int]:
    """Return the pixel width and height of rendered text."""

    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font,
    )

    return (
        bbox[2] - bbox[0],
        bbox[3] - bbox[1],
    )


def _build_chips(
    pattern: Pattern,
    draw: ImageDraw.ImageDraw,
    font: ImageFont.ImageFont,
    chip_height: int,
    sort_mode: str = "count",
) -> list[LegendChip]:
    """Build adaptive-width color chips and sort by usage or MARD series."""

    table = pattern.legend_table()

    chips: list[LegendChip] = []

    swatch_size = max(16, chip_height - 14)

    left_padding = 8
    right_padding = 10
    element_gap = 8

    for _, row in table.iterrows():
        palette_index = int(row["palette_index"])
        code = str(row["code"])
        count = int(row["count"])

        count_text = f"×{count}"

        code_width, _ = _measure_text(
            draw,
            code,
            font,
        )

        count_width, _ = _measure_text(
            draw,
            count_text,
            font,
        )

        chip_width = (
            left_padding
            + swatch_size
            + element_gap
            + code_width
            + element_gap
            + count_width
            + right_padding
        )

        color = pattern.palette[palette_index]

        chips.append(
            LegendChip(
                palette_index=palette_index,
                code=code,
                count=count,
                rgb=color.rgb,
                width=chip_width,
            )
        )

    def series_key(chip: LegendChip):
        color = pattern.palette[chip.palette_index]
        match = re.fullmatch(r"([A-Za-z]+)([0-9]+)", chip.code.strip())
        series = str(color.series).strip().upper()
        if match:
            return (series or match[1].upper(), int(match[2]), chip.code)
        return (series, 0, chip.code)

    if sort_mode == "series":
        chips.sort(key=series_key)
    elif sort_mode == "count":
        chips.sort(key=lambda chip: (-chip.count, series_key(chip)))
    else:
        raise ValueError(f"不支持的图例排序方式：{sort_mode}")

    return chips


def _layout_rows(
    chips: list[LegendChip],
    max_content_width: int,
    gap: int,
) -> list[list[LegendChip]]:
    """Wrap legend chips into rows within the available content width."""

    rows: list[list[LegendChip]] = []
    current_row: list[LegendChip] = []
    current_width = 0

    for chip in chips:
        required_width = chip.width

        if current_row:
            required_width += gap

        if (
            current_row
            and current_width + required_width > max_content_width
        ):
            rows.append(current_row)
            current_row = [chip]
            current_width = chip.width
        else:
            current_row.append(chip)
            current_width += required_width

    if current_row:
        rows.append(current_row)

    return rows


def _draw_centered_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
) -> None:
    """Center text horizontally and vertically inside a rectangle."""

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
        fill=fill,
        font=font,
    )


def _draw_chip(
    draw: ImageDraw.ImageDraw,
    chip: LegendChip,
    x: int,
    y: int,
    height: int,
    font: ImageFont.ImageFont,
) -> None:
    """Draw a legend chip with a color swatch, MARD code, and bead count."""

    border_color = (210, 210, 210)
    background_color = (249, 249, 249)
    secondary_text_color = (70, 70, 70)

    draw.rounded_rectangle(
        (
            x,
            y,
            x + chip.width,
            y + height,
        ),
        radius=6,
        fill=background_color,
        outline=border_color,
        width=1,
    )

    swatch_size = max(16, height - 14)
    swatch_left = x + 8
    swatch_top = y + (height - swatch_size) // 2

    draw.rectangle(
        (
            swatch_left,
            swatch_top,
            swatch_left + swatch_size,
            swatch_top + swatch_size,
        ),
        fill=chip.rgb,
        outline=(125, 125, 125),
        width=1,
    )

    code_left = swatch_left + swatch_size + 8

    code_width, _ = _measure_text(
        draw,
        chip.code,
        font,
    )

    code_box = (
        code_left,
        y,
        code_left + code_width,
        y + height,
    )

    _draw_centered_text(
        draw=draw,
        box=code_box,
        text=chip.code,
        font=font,
        fill=(20, 20, 20),
    )

    count_text = f"×{chip.count}"

    count_width, _ = _measure_text(
        draw,
        count_text,
        font,
    )

    count_right = x + chip.width - 10

    count_box = (
        count_right - count_width,
        y,
        count_right,
        y + height,
    )

    _draw_centered_text(
        draw=draw,
        box=count_box,
        text=count_text,
        font=font,
        fill=secondary_text_color,
    )


def render_bottom_legend(
    pattern: Pattern,
    config: RenderConfig,
    max_width: int,
) -> Image.Image:
    """Render the sorted bottom legend within max_width pixels."""

    if max_width <= 0:
        raise ValueError("max_width 必须大于 0。")

    chip_height = max(
        28,
        int(config.legend_swatch_height),
    )

    gap = max(
        0,
        int(config.legend_spacing),
    )

    padding = max(
        0,
        int(config.legend_padding),
    )

    font_size = max(
        10,
        int(chip_height * 0.36),
    )

    font = _load_font(font_size)

    temporary_image = Image.new(
        "RGB",
        (1, 1),
        "white",
    )
    temporary_draw = ImageDraw.Draw(temporary_image)

    chips = _build_chips(
        pattern=pattern,
        draw=temporary_draw,
        font=font,
        chip_height=chip_height,
        sort_mode=config.legend_sort,
    )

    if not chips:
        return Image.new(
            "RGB",
            (max_width, 1),
            "white",
        )

    content_width = max_width - padding * 2

    if content_width <= 0:
        raise ValueError(
            "max_width 太小，无法容纳图例边距。"
        )

    # Clamp chip widths to the available content area.
    normalized_chips = [
        LegendChip(
            palette_index=chip.palette_index,
            code=chip.code,
            count=chip.count,
            rgb=chip.rgb,
            width=min(chip.width, content_width),
        )
        for chip in chips
    ]

    rows = _layout_rows(
        chips=normalized_chips,
        max_content_width=content_width,
        gap=gap,
    )

    image_height = (
        padding * 2
        + len(rows) * chip_height
        + max(0, len(rows) - 1) * gap
    )

    image = Image.new(
        "RGB",
        (max_width, image_height),
        "white",
    )

    draw = ImageDraw.Draw(image)

    current_y = padding

    for row in rows:
        current_x = padding

        for chip in row:
            _draw_chip(
                draw=draw,
                chip=chip,
                x=current_x,
                y=current_y,
                height=chip_height,
                font=font,
            )

            current_x += chip.width + gap

        current_y += chip_height + gap

    return image