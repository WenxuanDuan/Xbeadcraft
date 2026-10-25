# XX Beads — MARD 拼豆图纸生成器

## 功能

- 上传 PNG / JPG / WEBP
- 设置图纸宽度或固定宽高
- 保持原图比例
- 支持透明背景
- 使用 MARD 221 色自动匹配
- 可限制最终使用颜色数量
- 生成彩色预览图
- 生成带网格和色号编号的图纸
- 统计每种颜色的使用数量
- 导出：
  - 彩色预览 PNG
  - 网格图纸 PNG
  - 材料统计 CSV
  - 图案矩阵 CSV
  - A4 PDF 图纸

## 目录

```text
xxbeads/
├── app.py
├── requirements.txt
├── README.md
├── core/
│   ├── __init__.py
│   ├── palette.py
│   ├── image_processor.py
│   ├── color_matcher.py
│   ├── pattern.py
│   ├── renderer.py
│   └── exporters.py
├── data/
│   └── mard_221.csv
└── output/
```

## 色卡文件要求

把你抓取到的 MARD 221 色 CSV 放到：

```text
data/mard_221.csv
```

程序支持以下两种格式。

格式 1：

```csv
code,hex
A1,#FAF4C8
A2,#FFFFD5
```

格式 2：

```csv
code,hex,r,g,b,series
A1,#FAF4C8,250,244,200,A
A2,#FFFFD5,255,255,213,A
```

色号列也可以叫：

- `code`
- `color_code`
- `色号`

HEX 列也可以叫：

- `hex`
- `hex_color`
- `颜色值`

## 安装与运行

```bash
cd ~/Desktop/xxbeads
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

浏览器通常会自动打开：

```text
http://localhost:8501
```

## 说明

网页色卡中的 HEX 只是屏幕参考值。实体拼豆会受批次、光线和屏幕影响，因此程序生成结果仍建议人工微调。


## 桌面版水平镜像

使用 `.venv/bin/python app.py` 启动桌面程序。生成图纸后，可勾选「水平镜像」立即左右翻转拼豆图案，取消勾选恢复正常方向，无需重新匹配颜色。格内色号文字、四边坐标和底部图例保持正常方向，保存 PNG 与当前预览一致。每次重新生成图纸默认恢复正常方向。

镜像功能测试：

```bash
.venv/bin/python -m unittest discover -s tests -v
```


## 选格换色（MARD 221）

生成图纸后，点击预览中的拼豆格子进行选择；按住 Ctrl（Mac 也可用 ⌘）点击可多选，再次点击已选格可取消该格。选中格子显示蓝色边框。

在「替换颜色（MARD 221）」中通过色块和色号选择颜色，再点击「替换选中像素」。所有可选颜色都来自项目的 `data/mard_221.csv`，共 221 色。透明格也可填入拼豆颜色。

换色后，格内色号、颜色用量图例和总数立即更新，保存 PNG 使用当前图纸，选择边框不会导出。水平镜像时按当前显示位置选格，切回正常方向仍保留修改。可以连续「撤销换色」，或「清除选择」；重新生成图纸会清除本次手动换色及撤销记录。


### 按色号批量替换

生成图纸后，在「按色号全选（当前图纸）」中选择原色号，点击「全选此色号」，再从「替换颜色（MARD 221）」中选择目标色号，点击「替换选中像素」。原色号列表仅显示当前图纸实际使用的颜色及颗数，换色和撤销后自动更新。全选会替换之前的选区；镜像状态也支持，整批换色可一次撤销。


## 图例排序

「图例排序」支持「豆子数量：从多到少」（默认）与「颜色系列：A–M（色号升序）」。同一系列按色号数字排列，例如 A1、A2、A10；数量相同时也按系列及色号升序排列。生成前可选择，生成后切换立即更新图纸下方图例，PNG 导出与当前预览一致。换色、撤销和水平镜像会保留当前排序方式。
