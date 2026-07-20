from __future__ import annotations

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

    def __init__(self, csv_path: str):

        self.csv_path = Path(csv_path)

        self.colors: list[BeadColor] = []

        self.rgb_array = None
        self.lab_array = None

        self.load()

    @staticmethod
    def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:

        hex_color = hex_color.strip().replace("#", "")

        return (
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16),
        )

    def load(self):

        df = pd.read_csv(self.csv_path)

        # 自动兼容大小写
        df.columns = [c.lower() for c in df.columns]

        # 如果没有RGB，就由HEX生成
        if "r" not in df.columns:

            rgb = df["hex"].apply(self.hex_to_rgb)

            df["r"] = rgb.apply(lambda x: x[0])
            df["g"] = rgb.apply(lambda x: x[1])
            df["b"] = rgb.apply(lambda x: x[2])

        rgb = (
            df[["r", "g", "b"]]
            .to_numpy(dtype=np.float32)
            / 255.0
        )

        lab = rgb2lab(
            rgb.reshape(1, -1, 3)
        ).reshape(-1, 3)

        self.colors.clear()

        for i, row in df.iterrows():

            self.colors.append(

                BeadColor(

                    code=row["code"],

                    rgb=(
                        int(row["r"]),
                        int(row["g"]),
                        int(row["b"]),
                    ),

                    lab=(
                        float(lab[i][0]),
                        float(lab[i][1]),
                        float(lab[i][2]),
                    ),

                    hex_color=row["hex"],

                    series=row.get("series", ""),

                )

            )

        self.rgb_array = np.array(
            [c.rgb for c in self.colors],
            dtype=np.uint8,
        )

        self.lab_array = np.array(
            [c.lab for c in self.colors],
            dtype=np.float32,
        )

    def __len__(self):

        return len(self.colors)

    def __getitem__(self, item):

        return self.colors[item]