from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from skimage.color import rgb2lab


@dataclass
class BeadColor:
    code: str
    rgb: tuple[int, int, int]
    lab: tuple[float, float, float]
    hex_color: str
    series: str


class Palette:
    """A validated, brand-specific palette with original color codes and Lab values."""

    def __init__(self, csv_path: str, *, palette_id: str | None = None,
                 name: str | None = None, name_zh: str | None = None,
                 source: str = "", reference: str = "custom"):
        self.csv_path = Path(csv_path)
        self.id = palette_id or self.csv_path.stem
        self.name = name or self.csv_path.stem
        self.name_zh = name_zh or self.name
        self.source = source
        self.reference = reference
        self.colors: list[BeadColor] = []
        self.load()

    def display_name(self, language: str) -> str:
        return self.name if language == "en" else self.name_zh

    @staticmethod
    def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        value = hex_color.strip().lstrip('#')
        if not re.fullmatch(r'[0-9A-Fa-f]{6}', value):
            raise ValueError("色卡 HEX 必须为六位 RGB 颜色。")
        return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))

    def load(self) -> None:
        # Read codes as strings so numeric codes keep their leading zeroes.
        df = pd.read_csv(self.csv_path, dtype=str, keep_default_na=False, encoding='utf-8-sig')
        df.columns = [column.strip().lower() for column in df.columns]
        if df.columns.duplicated().any() or 'code' not in df.columns:
            raise ValueError("色卡必须包含 code 列，且列名不能重复。")
        if not 1 <= len(df) <= 4096:
            raise ValueError("色卡必须包含 1 至 4096 个颜色。")
        codes = df['code'].str.strip()
        if (codes == '').any() or codes.str.casefold().duplicated().any():
            raise ValueError("色卡色号不能为空或重复。")
        if 'hex' in df.columns:
            rgb = np.array([self.hex_to_rgb(value) for value in df['hex']], dtype=np.int32)
        elif all(channel in df.columns for channel in ['r', 'g', 'b']):
            rgb = df[['r', 'g', 'b']].apply(pd.to_numeric, errors='coerce').to_numpy(dtype=float)
        else:
            raise ValueError("色卡必须包含 hex 列，或完整的 r、g、b 列。")
        if not np.isfinite(rgb).all() or ((rgb < 0) | (rgb > 255) | (rgb != np.floor(rgb))).any():
            raise ValueError("色卡 RGB 必须是 0 至 255 的整数。")
        # Reject ambiguous data rather than silently preferring conflicting channels.
        if 'hex' in df.columns and all(channel in df.columns for channel in ['r', 'g', 'b']):
            channels = df[['r', 'g', 'b']].apply(pd.to_numeric, errors='coerce').to_numpy(dtype=float)
            if not np.array_equal(rgb, channels):
                raise ValueError("色卡中的 HEX 与 RGB 数值不一致。")
        lab = rgb2lab((rgb.astype(np.float32)/255).reshape(1, -1, 3)).reshape(-1, 3)
        colors = []
        for position, code in enumerate(codes):
            declared = df.iloc[position].get('series', '').strip()
            prefix = re.match(r'[A-Za-z]+', code)
            series = declared or (prefix[0].upper() if prefix else '')
            red, green, blue = (int(value) for value in rgb[position])
            colors.append(BeadColor(code, (red, green, blue), tuple(float(x) for x in lab[position]),
                                    f'#{red:02X}{green:02X}{blue:02X}', series))
        self.colors = colors
        self.rgb_array = rgb.astype(np.uint8)
        self.lab_array = lab.astype(np.float32)

    @staticmethod
    def natural_key(value: str) -> tuple:
        """Sort mixed numeric and alphanumeric codes without losing their original spelling."""
        return tuple((1, int(part)) if part.isdigit() else (0, part.casefold())
                     for part in re.split(r'(\d+)', value) if part)

    def color_sort_key(self, index: int) -> tuple:
        color = self.colors[index]
        return self.natural_key(color.series), self.natural_key(color.code), color.code

    def __len__(self):
        return len(self.colors)

    def __getitem__(self, item):
        return self.colors[item]
