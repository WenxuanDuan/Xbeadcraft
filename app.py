from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image

from core.palette import Palette
from core.image_processor import prepare_image
from core.color_matcher import match_image_to_palette
from core.renderer import (
    render_color_preview,
    render_numbered_grid,
    image_to_png_bytes,
)
from core.exporters import (
    pattern_csv_bytes,
    statistics_csv_bytes,
    create_pdf_bytes,
)


APP_ROOT = Path(__file__).resolve().parent
DEFAULT_PALETTE_PATH = APP_ROOT / "data" / "mard_221.csv"


st.set_page_config(
    page_title="XX Beads",
    page_icon="🟣",
    layout="wide",
)

st.title("XX Beads · MARD 拼豆图纸生成器")
st.caption(
    "上传图片，设置图纸尺寸，自动匹配 MARD 色号并生成可打印图纸。"
)


@st.cache_resource
def load_palette(path: str) -> Palette:
    return Palette(path)


with st.sidebar:
    st.header("图纸设置")

    width = st.number_input(
        "宽度（颗）",
        min_value=4,
        max_value=300,
        value=40,
        step=1,
    )

    keep_ratio = st.checkbox("保持原图比例", value=True)

    height = None
    if not keep_ratio:
        height = st.number_input(
            "高度（颗）",
            min_value=4,
            max_value=300,
            value=40,
            step=1,
        )

    trim_transparency = st.checkbox(
        "自动裁掉透明边缘",
        value=True,
    )

    resize_label = st.selectbox(
        "缩放算法",
        options=[
            "高质量缩小（推荐）",
            "像素风最近邻",
            "双三次插值",
        ],
    )
    resize_mode = {
        "高质量缩小（推荐）": "lanczos",
        "像素风最近邻": "nearest",
        "双三次插值": "bicubic",
    }[resize_label]

    alpha_threshold = st.slider(
        "透明阈值",
        min_value=0,
        max_value=255,
        value=128,
        help="Alpha 小于该值的像素视为没有拼豆。",
    )

    limit_colors = st.checkbox("限制使用颜色数量", value=True)

    max_colors = None
    if limit_colors:
        max_colors = st.slider(
            "最大颜色数",
            min_value=2,
            max_value=64,
            value=20,
        )

    waste_percent = st.slider(
        "材料损耗预留",
        min_value=0,
        max_value=20,
        value=5,
        format="%d%%",
    )

    cell_size = st.slider(
        "网格图单格大小",
        min_value=24,
        max_value=60,
        value=36,
    )


try:
    palette = load_palette(str(DEFAULT_PALETTE_PATH))
except Exception as exc:
    st.error(str(exc))
    st.info(
        "请把抓取到的 MARD 色卡 CSV 保存为："
        f"`{DEFAULT_PALETTE_PATH}`"
    )
    st.stop()


palette_count = len(palette.colors)
if palette_count != 221:
    st.warning(
        f"当前色卡包含 {palette_count} 种颜色，不是 221 种。"
        "程序仍可运行，但请确认 CSV 是否完整。"
    )
else:
    st.success("已加载 MARD 221 色色卡。")


uploaded_file = st.file_uploader(
    "上传图片",
    type=["png", "jpg", "jpeg", "webp"],
)

if uploaded_file is None:
    st.info("请上传一张 PNG、JPG 或 WEBP 图片。透明背景 PNG 效果最好。")
    st.stop()


try:
    source_image = Image.open(uploaded_file)

    processed_image = prepare_image(
        image=source_image,
        width=int(width),
        height=int(height) if height is not None else None,
        keep_ratio=keep_ratio,
        trim_transparency=trim_transparency,
        resize_mode=resize_mode,
    )

    pattern = match_image_to_palette(
        image=processed_image,
        palette=palette,
        alpha_threshold=alpha_threshold,
        max_colors=max_colors,
    )

    preview_image = render_color_preview(
        pattern=pattern,
        scale=max(8, min(24, 640 // max(pattern.width, 1))),
    )

    grid_image, _ = render_numbered_grid(
        pattern=pattern,
        cell_size=cell_size,
        major_grid_every=10,
    )

except Exception as exc:
    st.exception(exc)
    st.stop()


metric_1, metric_2, metric_3 = st.columns(3)
metric_1.metric("图纸尺寸", f"{pattern.width} × {pattern.height}")
metric_2.metric("总拼豆数", pattern.bead_count)
metric_3.metric("使用颜色数", pattern.used_color_count)


tab_preview, tab_grid, tab_stats, tab_export = st.tabs(
    ["彩色预览", "编号图纸", "材料统计", "导出"]
)


with tab_preview:
    left, right = st.columns(2)

    with left:
        st.subheader("原图")
        st.image(source_image, use_container_width=True)

    with right:
        st.subheader("MARD 匹配结果")
        st.image(preview_image, use_container_width=True)

    st.caption(
        "彩色预览中的方格代表一颗拼豆。透明区域不会生成拼豆。"
    )


with tab_grid:
    st.subheader("编号图纸")
    st.image(grid_image, use_container_width=True)
    st.caption(
        "每个格子中的数字对应材料统计表里的“图纸编号”。"
        "每 10 格会加粗一次网格线。"
    )


with tab_stats:
    stats_df = pattern.count_dataframe(
        waste_percent=float(waste_percent)
    )

    st.dataframe(
        stats_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "HEX": st.column_config.TextColumn("HEX"),
            "数量": st.column_config.NumberColumn("数量"),
            "建议准备数量": st.column_config.NumberColumn(
                f"建议准备数量（含 {waste_percent}%）"
            ),
        },
    )

    st.caption(
        "建议准备数量已经包含侧边栏设置的损耗预留。"
    )


with tab_export:
    st.subheader("下载文件")

    preview_png = image_to_png_bytes(preview_image)
    grid_png = image_to_png_bytes(grid_image)
    stats_csv = statistics_csv_bytes(
        pattern,
        waste_percent=float(waste_percent),
    )
    matrix_csv = pattern_csv_bytes(pattern)
    pdf_bytes = create_pdf_bytes(
        pattern=pattern,
        grid_image=grid_image,
        title="MARD 拼豆图纸",
        waste_percent=float(waste_percent),
    )

    col_1, col_2 = st.columns(2)

    with col_1:
        st.download_button(
            "下载彩色预览 PNG",
            data=preview_png,
            file_name="mard_preview.png",
            mime="image/png",
            use_container_width=True,
        )

        st.download_button(
            "下载材料统计 CSV",
            data=stats_csv,
            file_name="mard_materials.csv",
            mime="text/csv",
            use_container_width=True,
        )

        st.download_button(
            "下载 A4 PDF",
            data=pdf_bytes,
            file_name="mard_pattern.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    with col_2:
        st.download_button(
            "下载编号图纸 PNG",
            data=grid_png,
            file_name="mard_numbered_pattern.png",
            mime="image/png",
            use_container_width=True,
        )

        st.download_button(
            "下载图案矩阵 CSV",
            data=matrix_csv,
            file_name="mard_pattern_matrix.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.caption(
        "图案矩阵 CSV 中，每一行对应图纸的一行，每个单元格是 MARD 色号。"
    )
