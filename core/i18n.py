"""Chinese and English text resources shared by the desktop UI and sheet renderer."""
from __future__ import annotations

import re
from string import Formatter


ENGLISH = {
    "界面语言：": "Language:",
    "界面语言已更新": "Interface language updated",
    "语言切换失败": "Language change failed",
    "XXBeadPattern 启动失败": "XXBeadPattern failed to start",
    " 格": " cells",
    " 颗": " beads",
    " 颗宽": " beads wide",
    " 颗最长边": " beads on longest side",
    " 颗高": " beads tall",
    "PNG 图片 (*.png)": "PNG images (*.png)",
    "{value0} · {value1} 颗": "{value0} · {value1} beads",
    "保存 PNG": "Save PNG",
    "保存图纸": "Save pattern",
    "保存图纸…": "Save pattern…",
    "保存失败": "Save failed",
    "保存成功": "Saved successfully",
    "保持原图比例": "Keep aspect ratio",
    "全选此色号": "Select all of this color",
    "准备就绪": "Ready",
    "固定宽度": "Fixed width",
    "固定最长边": "Fixed longest side",
    "固定高度": "Fixed height",
    "图例排序失败": "Legend sorting failed",
    "图例排序已更新": "Legend order updated",
    "图例排序：": "Legend order:",
    "图片文件 (*.png *.jpg *.jpeg *.webp);;PNG 图片 (*.png);;所有文件 (*)": "Images (*.png *.jpg *.jpeg *.webp);;PNG images (*.png);;All files (*)",
    "图纸已更新｜{value0} 颗｜{value1} 种颜色": "Pattern updated | {value0} beads | {value1} colors",
    "图纸已经保存到：\n{value0}": "Pattern saved to:\n{value0}",
    "图纸设置": "Pattern settings",
    "图鉴模式（推荐）": "Collection (recommended)",
    "图鉴规格：": "Collection size:",
    "大型图鉴 · 约1200颗": "Large · ~1,200 beads",
    "小型图鉴 · 约550颗": "Small · ~550 beads",
    "尚未选择图片": "No image selected",
    "尺寸模式：": "Sizing mode:",
    "已保存：{value0}": "Saved: {value0}",
    "已全选 {value0}：{value1} 格，请选择目标色号并替换": "Selected all {value0}: {value1} cells. Choose a target color and replace.",
    "已切换为水平镜像": "Horizontal mirror enabled",
    "已恢复正常方向": "Normal direction restored",
    "已选中 {value0} 格；按住 Ctrl / ⌘ 可多选": "{value0} cells selected; hold Ctrl / ⌘ for multiple selection",
    "已选择：{value0}": "Selected: {value0}",
    "打开图片…": "Open image…",
    "找不到 MARD 色卡文件：\n{value0}\n\n请将色卡保存为 data/mard_221.csv。": "MARD palette file not found:\n{value0}\n\nSave the palette as data/mard_221.csv.",
    "按色号全选（当前图纸）：": "Select by color (current pattern):",
    "换色失败": "Color edit failed",
    "撤销换色": "Undo color edit",
    "文件": "File",
    "显示四边坐标": "Show coordinates on all sides",
    "显示颜色背景": "Show bead colors",
    "替换选中像素": "Replace selected cells",
    "替换颜色（MARD 221）：": "Target color (MARD 221):",
    "标准图鉴 · 约850颗": "Standard · ~850 beads",
    "格子大小：": "Cell size:",
    "正在生成图纸…": "Generating pattern…",
    "水平镜像": "Horizontal mirror",
    "没有可保存的图纸": "No pattern to save",
    "清除选择": "Clear selection",
    "点击图纸选格；按住 Ctrl / ⌘ 可多选": "Click a cell to select; hold Ctrl / ⌘ to select multiple cells",
    "生成图纸": "Generate pattern",
    "生成失败": "Generation failed",
    "生成完成｜{value0}｜{value1} × {value2}｜{value3} 颗｜{value4} 种颜色": "Generated | {value0} | {value1} × {value2} | {value3} beads | {value4} colors",
    "目标尺寸：": "Target size:",
    "粗线间隔：": "Major grid spacing:",
    "色卡：MARD\n已加载颜色：{value0}": "Palette: MARD\nColors loaded: {value0}",
    "色卡：MARD\n已加载颜色：{count}": "Palette: MARD\nColors loaded: {count}",
    "裁掉透明边缘": "Trim transparent borders",
    "请先生成图纸。": "Generate a pattern first.",
    "请先选择一张图片。": "Choose an image first.",
    "豆子数量：从多到少": "Bead count: high to low",
    "退出": "Quit",
    "选择图片": "Choose image",
    "透明区域显示棋盘格": "Checkerboard for empty cells",
    "透明阈值：": "Alpha threshold:",
    "镜像切换失败": "Mirror change failed",
    "颜色系列：A–M（色号升序）": "Color series: A–M (code order)",
    "请选择一张图片，然后点击“生成图纸”。": "Choose an image, then click Generate pattern.",
    "未命名图纸": "Untitled Pattern",
    "{width} × {height}    {beads} 颗    {colors} 种颜色": "{width} × {height}    {beads} Beads    {colors} Colors",
    "grid 必须是二维数组。": "grid must be a two-dimensional array.",
    "grid 不能为空。": "grid must not be empty.",
    "grid 中存在无效的颜色索引。有效值应为 -1，或 Palette 中颜色的索引。": "grid contains invalid color indices. Values must be -1 or valid palette indices.",
    "target_width 必须大于 0。": "target_width must be greater than zero.",
    "target_height 必须大于 0。": "target_height must be greater than zero.",
    "target_size 必须大于 0。": "target_size must be greater than zero.",
    "target_beads 必须大于 0。": "target_beads must be greater than zero.",
    "图片尺寸无效。": "Invalid image dimensions.",
    "图片中没有可见主体。": "The image has no visible subject.",
    "关闭保持比例时必须提供有效 height。": "A valid height is required when the aspect ratio is not preserved.",
    "max_width 必须大于 0。": "max_width must be greater than zero.",
    "max_width 太小，无法容纳图例边距。": "max_width is too small for the legend padding.",
    "不支持的图例排序方式：{mode}": "Unsupported legend sort mode: {mode}",
    "无效的 palette_index：{index}。": "Invalid palette_index: {index}.",
    "x 坐标超出范围：{value}，有效范围为 0 到 {limit}。": "x coordinate out of range: {value}; valid range is 0 to {limit}.",
    "y 坐标超出范围：{value}，有效范围为 0 到 {limit}。": "y coordinate out of range: {value}; valid range is 0 to {limit}.",
    "不支持的缩放算法：{method}。可选值：{options}": "Unsupported resizing method: {method}. Available methods: {options}",
    "未知 size_mode：{mode}。可选值：width、height、longest、collection。": "Unknown size_mode: {mode}. Choose width, height, longest, or collection.",
}


def translate(language: str, text: str, **values) -> str:
    """Translate a catalog template, leaving user-provided values untouched."""
    template = ENGLISH.get(text, text) if language == "en" else text
    return template.format(**values) if values else template


def translate_error(language: str, message: str) -> str:
    """Translate known core errors without rewriting filenames or external errors."""
    if language != "en":
        return message
    if message in ENGLISH:
        return ENGLISH[message]
    for template, english in ENGLISH.items():
        fields = []
        pattern = ""
        for literal, field, _, _ in Formatter().parse(template):
            pattern += re.escape(literal)
            if field is not None:
                fields.append(field)
                pattern += "(.*?)"
        if not fields:
            continue
        match = re.fullmatch(pattern, message, flags=re.DOTALL)
        if match:
            return english.format(**dict(zip(fields, match.groups())))
    return message
