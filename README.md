# XXBeadPattern

**Turn your favorite images into bead patterns you can follow, refine, and make.**

XXBeadPattern is a desktop tool built around the **MARD 221-color palette**. Import an image, generate a labeled bead grid, adjust individual cells or replace a color throughout the pattern, then export a complete PNG sheet.

[中文说明](#中文说明)

## Features

| Feature | What you can do |
| --- | --- |
| Image-to-pattern conversion | Import PNG, JPG, JPEG, or WEBP and automatically match colors to MARD 221 |
| Collection sizing | Aim for a similar bead count across characters with different shapes |
| Custom dimensions | Set the width, height, or longest side in bead cells |
| Transparent backgrounds | Trim transparent borders, adjust the alpha threshold, and show empty cells as a checkerboard |
| Readable bead grids | Show MARD codes, optional coordinates on all four sides, and configurable major grid lines |
| Cell editing | Select one or more cells, replace their colors, fill empty cells, and undo edits |
| Bulk color replacement | Select every cell of a MARD color and replace it with another palette color |
| Horizontal mirroring | Flip bead positions while keeping labels, coordinates, and legends readable |
| Legend sorting | Sort by descending bead count or by color series from A to M |
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

Menus, buttons, sizing options, file dialogs, notifications, and sheet statistics switch immediately. Your image, settings, selected cells, color edits, undo history, mirror direction, and legend order stay intact. MARD color codes and image filenames remain unchanged.

PNG export follows the language of the current preview. Switching languages does not regenerate the pattern or repeat color matching.

## Make your first pattern

### 1. Import and generate

Click **Choose image**, then choose a sizing mode:

| Mode | Best for |
| --- | --- |
| Collection (recommended) | A set of characters with similar bead counts |
| Fixed longest side | Keeping the pattern within a chosen maximum side length |
| Fixed width / Fixed height | Fitting a known horizontal or vertical dimension |

Collection presets target approximately **550, 850, or 1,200 beads**. Actual counts depend on the silhouette, transparency, and size limits; use the generated sheet's count as your reference.

Adjust cell size, major grid spacing, transparency threshold, and background or coordinate options as needed. Click **Generate pattern** to apply generation settings.

### 2. Refine the colors

**Edit selected cells:** Click a cell in the preview; a blue border marks the selection. Hold **Ctrl** (or **⌘** on Mac) to select multiple cells or deselect an already selected cell. Choose a swatch and MARD code under **Target color (MARD 221)**, then click **Replace selected cells**.

Empty cells can also be filled with a palette color. **Clear selection** removes the selection; **Undo color edit** restores previous edits one operation at a time.

**Replace a color everywhere:** Choose a source color under **Select by color (current pattern)**, click **Select all of this color**, choose the target color, then click **Replace selected cells**.

The source list shows only colors currently used, with their bead counts. Selecting a color replaces the previous selection. Each bulk replacement can be undone in one step; counts and legends update automatically.

### 3. Set the direction and legend order

- **Horizontal mirror:** Toggle the pattern's direction instantly. Cell editing follows the displayed positions, and edits remain when you switch back.
- **Bead count: high to low:** Sort the legend from most to least used. Ties are sorted by series and numeric color code.
- **Color series: A–M (code order):** Sort from A to M, with natural numeric ordering within each series—for example, A1, A2, A10.

Mirroring and legend sorting work immediately after generation, without repeating color matching.

### 4. Save your sheet

Click **Save PNG**. The exported image uses the current colors, direction, and legend order, without the blue selection borders.

> Manual edits are held in the current session. Regenerating clears color edits and undo history, and resets the mirror direction. Save the PNG you want to keep before regenerating or closing the app.

## Palette and project notes

Automatic matching and manual editing share [`data/mard_221.csv`](data/mard_221.csv), which contains 221 MARD colors and loads automatically at startup. The included series are A–H and M. Screen swatches are references; compare them with your actual beads when adjusting colors.

The app name is **XXBeadPattern**; the GitHub repository currently retains the name **Xbeadcraft**.

## Development

```text
app.py                  Desktop entry point
ui/main_window.py       Interface, selection, and color editing
core/image_processor.py Image preprocessing and sizing
core/color_matcher.py   MARD palette matching
core/i18n.py            Chinese and English text resources
core/pattern.py         Pattern data and bead statistics
core/renderer/          Sheet, grid, preview, and legend rendering
data/mard_221.csv       Shared MARD 221-color palette
tests/                  Automated regression tests
AGENTS.md               Project naming and language conventions
```

With the virtual environment activated, run:

```bash
python -m unittest discover -s tests -v
```

Tests cover mirroring, cell selection, individual and bulk color edits, undo, legend sorting, language switching and persistence, preservation of editing state, and PNG export consistency. Code comments and docstrings are written in English. This README keeps the complete English guide first and the complete Chinese guide below.

---

## 中文说明

**把喜欢的图片，变成可以照着摆豆的图纸。**

XXBeadPattern 是一款基于 **MARD 221 色卡**的拼豆图纸桌面工具。导入图片后，自动匹配拼豆颜色，生成带色号的网格；可以逐格调整配色，或批量替换某个色号，最后保存为完整的 PNG 图纸。

### 功能概览

| 功能 | 说明 |
| --- | --- |
| 图片转图纸 | 支持 PNG、JPG、JPEG、WEBP，自动匹配 MARD 221 色 |
| 图鉴模式 | 按目标豆子数量调整尺寸，让不同造型的角色使用接近的豆子数量 |
| 自定义尺寸 | 按宽度、高度或最长边设置目标尺寸 |
| 透明背景处理 | 裁掉透明边缘、调整透明阈值，并用棋盘格显示空白区域 |
| 清晰的摆豆参考 | 显示 MARD 色号、可选的四边坐标及可调整间隔的粗分隔线 |
| 逐格换色 | 支持单选、多选、透明格填色和连续撤销换色 |
| 按色号批量替换 | 一键选中某个色号的全部格子，统一替换为另一种色卡颜色 |
| 水平镜像 | 翻转拼豆位置，色号文字、坐标和图例保持正常阅读方向 |
| 图例排序 | 按豆子数量从多到少，或按 A–M 颜色系列排列 |
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

菜单、按钮、尺寸选项、文件对话框、提示和图纸统计文字会立即切换。当前图片、参数设置、选区、换色、撤销记录、镜像方向和图例顺序均会保留；MARD 色号和图片文件名保持不变。

保存 PNG 时使用当前预览的语言。切换语言无需重新生成图纸或重新匹配颜色。

### 制作第一张图纸

**1. 导入并生成**

点击「选择图片」，然后选择尺寸模式：

| 模式 | 适合的情况 |
| --- | --- |
| 图鉴模式 | 为一组角色制作豆子数量接近的作品 |
| 固定最长边 | 将图案控制在指定的最大边长内 |
| 固定宽度 / 固定高度 | 已确定作品的横向或纵向尺寸 |

图鉴提供三档规格：**约 550 颗、850 颗和 1,200 颗**。实际用量随轮廓、透明区域和尺寸限制变化，以生成结果为准。

按需要调整格子大小、粗线间隔、透明阈值，以及背景和坐标的显示方式，再点击「生成图纸」应用设置。

**2. 调整配色**

局部换色：点击预览中的格子，蓝框表示选中；按住 **Ctrl**（Mac 也可用 **⌘**）点击可多选，再次点击已选格可取消该格。参考「替换颜色（MARD 221）」中的色块和色号选择颜色，再点击「替换选中像素」。

透明格也可以填入颜色。「清除选择」只取消选区；「撤销换色」可逐次恢复之前的换色操作。

整种颜色替换：在「按色号全选（当前图纸）」中选择原色号 → 点击「全选此色号」 → 选择目标色号 → 点击「替换选中像素」。

原色号列表只显示当前使用的颜色及颗数。全选会替换原有选区，整批换色可一次撤销；用量统计和图例同步更新。

**3. 选择方向与图例顺序**

- **水平镜像**：勾选后立即左右翻转拼豆图案，取消勾选恢复正常方向。镜像状态下可按显示位置选格换色，切回后保留修改。
- **按数量排序**：图例按用量从多到少排列；数量相同时按系列及色号升序排列。
- **按系列排序**：图例按 A–M 排列，同系列按色号数字排序，例如 A1、A2、A10。

镜像和图例排序均可在生成后直接切换，无需重新匹配颜色。

**4. 保存图纸**

点击「保存 PNG」，选择保存位置。导出采用当前配色、图案方向和图例顺序，选区蓝框不会出现在图片中。

> 手动换色保存在当前运行中的图纸里。重新生成会清除换色与撤销记录，并恢复正常方向；重新生成或关闭程序前，请保存需要的 PNG。

### 色卡与项目说明

自动匹配与手动换色均使用 [`data/mard_221.csv`](data/mard_221.csv)，包含 MARD 221 色，启动时自动加载。内置色卡系列为 A–H 和 M。屏幕色块用于参考，调整配色时可结合实际材料确认。

软件名称统一为 **XXBeadPattern**；GitHub 仓库目前仍使用 **Xbeadcraft** 作为仓库名。

### 开发与测试

```text
app.py                  桌面程序入口
ui/main_window.py       界面、选格与换色交互
core/image_processor.py 图片处理与尺寸计算
core/color_matcher.py   MARD 色卡匹配
core/i18n.py            中英文翻译资源
core/pattern.py         图案数据与用量统计
core/renderer/          图纸、网格、预览和图例渲染
data/mard_221.csv       共用 MARD 221 色卡
tests/                  自动化回归测试
AGENTS.md               项目命名与语言约定
```

激活虚拟环境后，在项目目录中运行：

```bash
python -m unittest discover -s tests -v
```

测试覆盖水平镜像、选格、局部与批量换色、撤销、图例排序、语言切换与记忆、编辑状态保留及 PNG 导出一致性。代码注释和文档字符串统一使用英文；README 先完整英文、后完整中文，项目约定保存在 [`AGENTS.md`](AGENTS.md)。
