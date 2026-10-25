# XXBeadPattern

**Turn your favorite images into bead patterns you can follow, refine, and make.**

XXBeadPattern is a desktop bead-pattern tool with **20 bundled brand/series palettes**, CSV palette import, and Chinese and English interfaces. The original **MARD 221** palette remains the default. Import an image, generate a labeled bead grid, adjust individual cells or replace a color throughout the pattern, then export a complete PNG sheet.

[中文说明](#中文说明)

## Features

| Feature | What you can do |
| --- | --- |
| Image-to-pattern conversion | Import PNG, JPG, JPEG, or WEBP and automatically match colors to your selected palette |
| Collection sizing | Aim for a similar bead count across characters with different shapes |
| Photo sizing | Choose a 40 / 80 / 120 / 160-bead longest side, or set custom dimensions with crop or padding |
| Custom dimensions | Set the width, height, or longest side in bead cells |
| Transparent backgrounds | Trim transparent borders, adjust the alpha threshold, and show empty cells as a checkerboard |
| Readable bead grids | Show palette color codes, optional coordinates on all four sides, and configurable major grid lines |
| Cell editing | Select one or more cells, replace their colors, fill empty cells, and undo edits |
| Bulk color replacement | Select every cell of a palette color and replace it with another palette color |
| Horizontal mirroring | Flip bead positions while keeping labels, coordinates, and legends readable |
| Legend sorting | Sort by descending bead count or by natural series/code order |
| Multiple palettes | Choose a bundled brand/series or import your own CSV palette; undo palette conversion |
| Chinese and English | Switch languages instantly and remember your choice for the next launch |
| PNG export | Save the current pattern with its grid, labels, and color usage legend |

## Install and run

Requires **Python 3.10+**. Run these commands in a terminal on macOS or Linux:

```bash
git clone https://github.com/WenxuanDuan/Xbeadcraft.git XXBeadPattern
cd XXBeadPattern
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

The app opens in a desktop window. For later launches, enter the project folder, activate the virtual environment, and run `python app.py`.

If you already have a checkout, use its existing folder instead of cloning again. On Windows, activate the environment with `.venv\Scripts\activate`.

## Choose your language

Use **Language** near the top of the settings panel (labeled **界面语言** in Chinese) to select **English** or **中文**. The default is Chinese; your choice is saved and restored on the next launch.

Menus, buttons, sizing options, file dialogs, notifications, and sheet statistics switch immediately. Your image, settings, selected cells, color edits, undo history, mirror direction, and legend order stay intact. Palette color codes and image filenames remain unchanged.

PNG export follows the language of the current preview. Switching languages does not regenerate the pattern or repeat color matching.

## Make your first pattern

### 1. Import and generate

Choose a palette under **Bead palette**, click **Choose image**, then choose a sizing mode:

| Mode | Best for |
| --- | --- |
| Collection (recommended) | A set of characters with similar bead counts |
| Photo mode | A photo with a chosen grid size, using a preset or custom dimensions |
| Fixed longest side | Keeping the pattern within a chosen maximum side length |
| Fixed width / Fixed height | Fitting a known horizontal or vertical dimension |

Collection presets target approximately **550, 850, or 1,200 beads**. Actual counts depend on the silhouette, transparency, and size limits; use the generated sheet's count as your reference.

Adjust cell size, major grid spacing, transparency threshold, and background or coordinate options as needed. Click **Generate pattern** to apply generation settings.

**Photo mode**

Choose **Photo mode** under **Sizing mode**, then select a preset:

| Preset | Longest side |
| --- | --- |
| Small | 40 beads |
| Standard | 80 beads |
| Detailed | 120 beads |
| Large | 160 beads |
| Custom width and height | Set dimensions in bead cells |

Presets preserve the original aspect ratio: a 4:3 photo becomes an **80 × 60** grid with the Standard preset. For custom sizing, choose **Keep ratio (set width)** or **Keep ratio (set height)** to calculate the other side automatically, **Crop to fill** for a centered crop, or **Fit with empty borders** to keep the complete image with transparent padding. Images are never stretched in Photo mode.

Editable custom dimensions range from 1 to 200 beads per side; with aspect ratio locking, the other side is calculated from the image. The estimate shows final grid dimensions and maximum bead count before generation. Transparent and padded cells are excluded from actual bead usage. Border trimming and EXIF orientation are applied consistently to the estimate and generated pattern.

### 2. Refine the colors

**Edit selected cells:** Click a cell in the preview; a blue border marks the selection. Hold **Ctrl** (or **⌘** on Mac) to select multiple cells or deselect an already selected cell. Choose a swatch and color code under **Target color**, which shows the active palette name, then click **Replace selected cells**.

Empty cells can also be filled with a palette color. **Clear selection** removes the selection; **Undo edit** restores color edits and palette changes one operation at a time.

**Replace a color everywhere:** Choose a source color under **Select by color (current pattern)**, click **Select all of this color**, choose the target color, then click **Replace selected cells**.

The source list shows only colors currently used, with their bead counts. Selecting a color replaces the previous selection. Each bulk replacement can be undone in one step; counts and legends update automatically.

### 3. Set the direction and legend order

- **Horizontal mirror:** Toggle the pattern's direction instantly. Cell editing follows the displayed positions, and edits remain when you switch back.
- **Bead count: high to low:** Sort the legend from most to least used. Ties are sorted by series and numeric color code.
- **Color series / code order:** Sort by series and numeric color code—for example, A1, A2, A10 for MARD, or 001, 2, 10 for numeric codes.

Mirroring and legend sorting work immediately after generation, without repeating color matching.

### 4. Save your sheet

Click **Save PNG**. The exported image uses the current colors, direction, and legend order, without the blue selection borders.

> Manual edits are held in the current session. Regenerating clears color edits and undo history, and resets the mirror direction. Save the PNG you want to keep before regenerating or closing the app.

## Palettes and data sources

Choose **Bead palette** before generating a pattern. Automatic matching, cell editing, bulk replacement, legends, and PNG export all use that palette. Your choice is remembered for the next launch. The exported sheet also identifies its palette.

If a pattern already exists, switching palettes rematches its **current edited colors** into the new palette. Grid dimensions, empty cells, selection, mirror direction, and legend order remain intact. This conversion uses the current grid rather than the original photo, so results can differ from generating afresh from the photo. **Undo edit** restores the previous palette and its exact grid; earlier color edits can still be undone afterward.

### Bundled palettes

| Palette / series | Usable colors |
| --- | --- |
| MARD 221 · Original | 221 |
| MARD 291 | 291 |
| COCO 291 | 291 |
| Manman | 278 |
| Panpan | 285 |
| Mixiaowo | 286 |
| Artkal C · 2.6 mm | 188 |
| Artkal M · 2.6 mm | 220 |
| Artkal C+M · 2.6 mm | 408 |
| Artkal A · 2.6 mm | 145 |
| Artkal R · 5 mm | 89 |
| Artkal S · 5 mm | 199 |
| Perler · Midi | 103 |
| Perler · Mini | 41 |
| Perler · Caps | 26 |
| Hama · Midi | 92 |
| Hama · Mini | 78 |
| Hama · Maxi | 25 |
| Nabbi | 30 |
| Yant | 119 |

These are **versioned reference snapshots, not a claim to cover every commercial palette or the latest manufacturer inventory**. Different bead sizes and product series remain separate. Colors are not interchangeable between brands simply because they look similar.

The original [`data/mard_221.csv`](data/mard_221.csv) is unchanged. Other snapshots come from [BeadColors](https://github.com/maxcleme/beadcolors) and [pindou-color-data](https://github.com/HansBug/pindou-color-data), with their MIT notices preserved under [`data/licenses/`](data/licenses/). Some upstream Artkal records are transcribed from official charts; others are community references or sampled swatches. Screen RGB values approximate appearance, not material properties.

Unidentified color codes are excluded: 4 each from Panpan and Mixiaowo. Transparent material entries that this RGB-only matcher cannot represent reliably are excluded from Artkal C (9), M (1), and the combined C+M set (10). Other special-finish colors remain reference RGB approximations. The table and interface show the number actually available, not the source catalog total.

[`data/palettes.json`](data/palettes.json) records source URLs, pinned upstream revisions, source hashes, licenses, additional upstream references, and exclusions. All bundled palettes work offline. Maintainers can reproduce the snapshots with `python scripts/update_palettes.py`; only that update step needs internet access.

### Import a CSV palette

Click **Import palette CSV…** and choose a UTF-8 CSV containing `code,hex` or `code,r,g,b`. Optional `series` and `name` columns may be included. For example:

```csv
code,hex,series
001,#FFFFFF,Neutral
002,#000000,Neutral
A1,#FF0000,A
```

Color codes remain strings, including leading zeroes. RGB channels must be integers from 0 to 255; HEX values must contain six RGB digits. Duplicate or empty codes, invalid values, and conflicting HEX/RGB data are rejected. A palette can contain 1–4,096 colors and its file must not exceed 2 MB.

Imported palettes are copied into the app's user data folder, so they remain available after the original CSV is moved. They are personal local data and are not automatically added to this repository.

The app name is **XXBeadPattern**; the GitHub repository currently retains the name **Xbeadcraft**.

## Development

```text
app.py                  Desktop entry point
ui/main_window.py       Interface, selection, and color editing
core/image_processor.py Image preprocessing and sizing
core/color_matcher.py   Selected-palette color matching
core/i18n.py            Chinese and English text resources
core/pattern.py         Pattern data and bead statistics
core/renderer/          Sheet, grid, preview, and legend rendering
data/mard_221.csv       Original default MARD 221 palette
data/palettes.json     Bundled palette metadata and provenance
data/palettes/         Additional brand/series CSV palettes
data/licenses/         Upstream dataset license notices
core/palette_library.py Palette discovery and CSV import
scripts/update_palettes.py Reproducible snapshot updater
tests/                  Automated regression tests
AGENTS.md               Project naming and language conventions
```

With the virtual environment activated, run:

```bash
python -m unittest discover -s tests -v
```

Tests cover bundled palette validation, CSV import, palette switching and undo, photo sizing, crop and padding, size estimates, mirroring, cell selection, individual and bulk color edits, undo, legend sorting, language switching and persistence, preservation of editing state, and PNG export consistency. Code comments and docstrings are written in English. This README keeps the complete English guide first and the complete Chinese guide below.

---

## 中文说明

**把喜欢的图片，变成可以照着摆豆的图纸。**

XXBeadPattern 是一款支持**中英文界面、20 套内置品牌／系列色卡及 CSV 色卡导入**的拼豆图纸桌面工具，默认保留原版 **MARD 221 色卡**。导入图片后，自动匹配拼豆颜色，生成带色号的网格；可以逐格调整配色，或批量替换某个色号，最后保存为完整的 PNG 图纸。

### 功能概览

| 功能 | 说明 |
| --- | --- |
| 图片转图纸 | 支持 PNG、JPG、JPEG、WEBP，自动匹配所选色卡 |
| 图鉴模式 | 按目标豆子数量调整尺寸，让不同造型的角色使用接近的豆子数量 |
| 照片尺寸 | 提供最长边 40／80／120／160 颗预设，以及自定义宽高、裁剪或留白 |
| 自定义尺寸 | 按宽度、高度或最长边设置目标尺寸 |
| 透明背景处理 | 裁掉透明边缘、调整透明阈值，并用棋盘格显示空白区域 |
| 清晰的摆豆参考 | 显示所选色卡的色号、可选的四边坐标及可调整间隔的粗分隔线 |
| 逐格换色 | 支持单选、多选、透明格填色和连续撤销换色 |
| 按色号批量替换 | 一键选中某个色号的全部格子，统一替换为另一种色卡颜色 |
| 水平镜像 | 翻转拼豆位置，色号文字、坐标和图例保持正常阅读方向 |
| 图例排序 | 按豆子数量从多到少，或按系列和色号自然顺序排列 |
| 多品牌色卡 | 选择内置品牌／系列或导入 CSV 色卡，色卡转换可撤销 |
| 中英文界面 | 即时切换中文或 English，记住选择并在下次启动时恢复 |
| PNG 导出 | 保存当前图纸，包含网格、色号和颜色用量图例 |

### 安装与启动

需要 **Python 3.10 或更高版本**。在 macOS / Linux 终端中运行：

```bash
git clone https://github.com/WenxuanDuan/Xbeadcraft.git XXBeadPattern
cd XXBeadPattern
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

程序会打开独立桌面窗口。后续启动时，进入项目目录、激活虚拟环境，再运行 `python app.py` 即可。

已有本地项目时，直接进入原项目目录，无需重新克隆。Windows 用户可用 `.venv\Scripts\activate` 激活虚拟环境。

### 选择界面语言

在设置面板上方的「**界面语言 / Language**」中选择「**中文**」或「**English**」。默认使用中文，选择后会自动保存，下次启动时恢复。

菜单、按钮、尺寸选项、文件对话框、提示和图纸统计文字会立即切换。当前图片、参数设置、选区、换色、撤销记录、镜像方向和图例顺序均会保留；色卡色号和图片文件名保持不变。

保存 PNG 时使用当前预览的语言。切换语言无需重新生成图纸或重新匹配颜色。

### 制作第一张图纸

**1. 导入并生成**

先在「拼豆色卡」中选择品牌／系列，再点击「选择图片」，选择尺寸模式：

| 模式 | 适合的情况 |
| --- | --- |
| 图鉴模式 | 为一组角色制作豆子数量接近的作品 |
| 照片模式 | 按预设或自定义网格尺寸制作照片图纸 |
| 固定最长边 | 将图案控制在指定的最大边长内 |
| 固定宽度 / 固定高度 | 已确定作品的横向或纵向尺寸 |

图鉴提供三档规格：**约 550 颗、850 颗和 1,200 颗**。实际用量随轮廓、透明区域和尺寸限制变化，以生成结果为准。

按需要调整格子大小、粗线间隔、透明阈值，以及背景和坐标的显示方式，再点击「生成图纸」应用设置。

**照片模式**

在「尺寸模式」中选择「照片模式」，再选择规格：

| 规格 | 最长边 |
| --- | --- |
| 小型 | 40 颗 |
| 标准 | 80 颗 |
| 精细 | 120 颗 |
| 大型 | 160 颗 |
| 自定义宽高 | 按颗数输入网格尺寸 |

预设保持原图比例，例如 4:3 照片选择标准规格会生成 **80 × 60 格**。自定义时，可选择「保持比例（按宽度）」或「保持比例（按高度）」自动计算另一边；选择「裁剪填满」会居中裁剪，「留白完整显示」则保留完整画面并补透明空白。照片模式不会拉伸图像。

自定义可编辑尺寸范围为每边 1–200 颗；保持比例时，另一边按图片比例自动计算。生成前显示最终网格宽高和最多需要的豆子数量，实际用量不包含透明和留白格。尺寸预估与生成过程均使用相同的透明边缘裁剪和图片方向处理。

**2. 调整配色**

局部换色：点击预览中的格子，蓝框表示选中；按住 **Ctrl**（Mac 也可用 **⌘**）点击可多选，再次点击已选格可取消该格。参考「替换颜色」中的色块和色号选择颜色，该标题会显示当前色卡名称，再点击「替换选中像素」。

透明格也可以填入颜色。「清除选择」只取消选区；「撤销修改」可逐次恢复换色和色卡转换操作。

整种颜色替换：在「按色号全选（当前图纸）」中选择原色号 → 点击「全选此色号」 → 选择目标色号 → 点击「替换选中像素」。

原色号列表只显示当前使用的颜色及颗数。全选会替换原有选区，整批换色可一次撤销；用量统计和图例同步更新。

**3. 选择方向与图例顺序**

- **水平镜像**：勾选后立即左右翻转拼豆图案，取消勾选恢复正常方向。镜像状态下可按显示位置选格换色，切回后保留修改。
- **按数量排序**：图例按用量从多到少排列；数量相同时按系列及色号升序排列。
- **按系列／色号排序**：按系列与色号数字自然排序，例如 MARD 的 A1、A2、A10，或纯数字色号的 001、2、10。

镜像和图例排序均可在生成后直接切换，无需重新匹配颜色。

**4. 保存图纸**

点击「保存 PNG」，选择保存位置。导出采用当前配色、图案方向和图例顺序，选区蓝框不会出现在图片中。

> 手动换色保存在当前运行中的图纸里。重新生成会清除换色与撤销记录，并恢复正常方向；重新生成或关闭程序前，请保存需要的 PNG。

### 色卡与数据来源

生成前在「拼豆色卡」中选择品牌／系列。自动配色、手动换色、按色号全选、图例及 PNG 导出均使用所选色卡，下次启动会恢复选择。导出图纸也会标注色卡名称。

已有图纸时，切换色卡会把**当前已编辑的格子颜色**重新匹配到新色卡，保留尺寸、空白格、选区、镜像方向和图例顺序。转换依据当前网格，而非原始照片，因此可能与重新从照片生成的结果不同。「撤销修改」可恢复之前的色卡及精确网格，之前的手动换色记录也可继续撤销。

**内置色卡**

| 品牌／系列 | 可用色数 |
| --- | --- |
| MARD 221 · 原版 | 221 |
| MARD 291 | 291 |
| COCO 291 | 291 |
| 漫漫 | 278 |
| 盼盼 | 285 |
| 咪小窝 | 286 |
| Artkal / 优肯 C · 2.6 mm | 188 |
| Artkal / 优肯 M · 2.6 mm | 220 |
| Artkal / 优肯 C+M · 2.6 mm | 408 |
| Artkal / 优肯 A · 2.6 mm | 145 |
| Artkal / 优肯 R · 5 mm | 89 |
| Artkal / 优肯 S · 5 mm | 199 |
| Perler · Midi | 103 |
| Perler · Mini | 41 |
| Perler · Caps | 26 |
| Hama · Midi | 92 |
| Hama · Mini | 78 |
| Hama · Maxi | 25 |
| Nabbi | 30 |
| Yant | 119 |

这些数据是**具有固定版本的参考色卡，不代表涵盖市面所有色卡或品牌最新在售颜色**。不同尺寸与产品系列独立列出；不同品牌颜色相近，也不意味着色号或实物相同。

原版 [`data/mard_221.csv`](data/mard_221.csv) 保持不变。其他色卡来自 [BeadColors](https://github.com/maxcleme/beadcolors) 与 [pindou-color-data](https://github.com/HansBug/pindou-color-data)，MIT 许可声明保存在 [`data/licenses/`](data/licenses/)。部分 Artkal 数据由上游根据官方色卡整理，其他数据包含社区参考值或色块采样值。屏幕 RGB 仅用于近似配色，不能表达材质特性。

已排除盼盼、咪小窝各 4 个未确认色号，以及当前 RGB 匹配器无法可靠表达的 Artkal 透明材质色：C 系列 9 色、M 系列 1 色、C+M 合集 10 色。其余特殊质感颜色仍按参考 RGB 近似处理。表格和界面显示实际可用数量，而非来源色卡的标称总色数。

[`data/palettes.json`](data/palettes.json) 记录来源网址、固定上游版本、源文件哈希、许可、额外参考资料及排除项。内置色卡均可离线使用；维护者可运行 `python scripts/update_palettes.py` 重建数据，仅更新过程需要联网。

**导入自定义 CSV**

点击「导入色卡 CSV…」，选择 UTF-8 编码文件。支持 `code,hex` 或 `code,r,g,b`，也可附带 `series`、`name` 列。例如：

```csv
code,hex,series
001,#FFFFFF,Neutral
002,#000000,Neutral
A1,#FF0000,A
```

色号按文本保留，包括开头的零。RGB 各通道必须为 0–255 整数，HEX 为六位 RGB。重复或空白色号、无效颜色及相互矛盾的 HEX/RGB 会被拒绝；每套可包含 1–4,096 色，文件不超过 2 MB。

导入后会复制到应用的用户数据目录，移动原 CSV 不会影响使用。用户导入色卡属于本地个人数据，不会自动加入项目仓库。

软件名称为 **XXBeadPattern**；GitHub 仓库目前仍使用 **Xbeadcraft** 作为仓库名。

### 开发与测试

```text
app.py                  桌面程序入口
ui/main_window.py       界面、选格与换色交互
core/image_processor.py 图片处理与尺寸计算
core/color_matcher.py   所选色卡颜色匹配
core/i18n.py            中英文翻译资源
core/pattern.py         图案数据与用量统计
core/renderer/          图纸、网格、预览和图例渲染
data/mard_221.csv       原版默认 MARD 221 色卡
data/palettes.json     内置色卡清单与来源
data/palettes/         其他品牌／系列 CSV 色卡
data/licenses/         上游数据许可声明
core/palette_library.py 色卡管理与 CSV 导入
scripts/update_palettes.py 固定版本色卡更新脚本
tests/                  自动化回归测试
AGENTS.md               项目命名与语言约定
```

激活虚拟环境后，在项目目录中运行：

```bash
python -m unittest discover -s tests -v
```

测试覆盖内置色卡校验、CSV 导入、色卡切换与撤销、照片尺寸、裁剪与留白、尺寸预估、水平镜像、选格、局部与批量换色、撤销、图例排序、语言切换与记忆、编辑状态保留及 PNG 导出一致性。代码注释和文档字符串统一使用英文；README 先完整英文、后完整中文，项目约定保存在 [`AGENTS.md`](AGENTS.md)。
