from PIL import Image

from core.palette import Palette
from core.image_processor import ImageProcessor
from core.color_matcher import ColorMatcher
from core.renderer import (
    RenderConfig,
    render_grid,
    render_bottom_legend,
)


def main() -> None:
    palette = Palette("data/mard_221.csv")

    processor = ImageProcessor()
    matcher = ColorMatcher(palette)

    source_image = Image.open("test.png")

    processed_image = processor.process(
        image=source_image,
        width=39,
        keep_ratio=True,
        trim=True,
        method="lanczos",
    )

    pattern = matcher.match(
        image=processed_image,
        alpha_threshold=128,
    )

    config = RenderConfig(
        cell_size=30,
        show_color=True,
        show_coordinate=True,
        major_grid_every=5,
        checkerboard=True,
        legend_swatch_height=42,
        legend_spacing=10,
        legend_padding=16,
    )

    grid_image = render_grid(
        pattern=pattern,
        config=config,
    )

    legend_image = render_bottom_legend(
        pattern=pattern,
        config=config,
        max_width=grid_image.width,
    )

    grid_image.save("test_grid.png")
    legend_image.save("bottom_legend.png")

    print(
        f"图纸尺寸：{pattern.width} × {pattern.height}"
    )
    print(f"拼豆总数：{pattern.bead_count}")
    print(f"颜色数量：{pattern.color_count}")
    print(f"网格图片宽度：{grid_image.width}")
    print(f"图例图片尺寸：{legend_image.size}")
    print("已生成 bottom_legend.png")


if __name__ == "__main__":
    main()