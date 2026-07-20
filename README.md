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
