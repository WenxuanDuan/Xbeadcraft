from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RenderConfig:
    """
    拼豆图纸统一渲染配置。
    """

    # 每个拼豆格子的像素尺寸
    cell_size: int = 28

    # 是否显示拼豆真实颜色
    show_color: bool = True

    # 是否显示上下左右坐标
    show_coordinate: bool = True

    # 每隔多少格绘制一条粗分隔线
    major_grid_every: int = 5

    # 透明区域是否使用棋盘背景
    checkerboard: bool = True

    # 底部图例配置
    legend_swatch_width: int = 118
    legend_swatch_height: int = 42
    legend_spacing: int = 10
    legend_padding: int = 16

    # 整体图纸配置
    sheet_padding: int = 16
    sheet_spacing: int = 16

    # 只水平镜像拼豆位置，文字、坐标和图例保持正常方向
    mirror_horizontal: bool = False

    # count：用量降序；series：系列及色号数字升序
    legend_sort: str = "count"
