from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .palette import Palette


@dataclass
class Pattern:
    """
    拼豆图案数据。

    grid 是二维 numpy 数组：

    -1:
        透明区域，不放拼豆

    >= 0:
        对应 Palette 中颜色的索引
    """

    grid: np.ndarray
    palette: Palette

    def __post_init__(self) -> None:
        """
        初始化后统一检查 grid 格式。
        """

        self.grid = np.asarray(
            self.grid,
            dtype=np.int32,
        )

        if self.grid.ndim != 2:
            raise ValueError("grid 必须是二维数组。")

        if self.grid.size == 0:
            raise ValueError("grid 不能为空。")

        invalid_values = self.grid[
            (self.grid < -1)
            | (self.grid >= len(self.palette))
        ]

        if invalid_values.size > 0:
            raise ValueError(
                "grid 中存在无效的颜色索引。"
                "有效值应为 -1，或 Palette 中颜色的索引。"
            )

    @property
    def width(self) -> int:
        """
        图纸宽度，单位为颗。
        """

        return int(self.grid.shape[1])

    @property
    def height(self) -> int:
        """
        图纸高度，单位为颗。
        """

        return int(self.grid.shape[0])

    @property
    def bead_count(self) -> int:
        """
        实际需要的拼豆总数。
        """

        return int(np.sum(self.grid >= 0))

    @property
    def color_count(self) -> int:
        """
        实际使用的颜色数量。
        """

        values = self.grid[self.grid >= 0]

        if values.size == 0:
            return 0

        return int(len(np.unique(values)))

    @property
    def visible_mask(self) -> np.ndarray:
        """
        返回可见拼豆区域的布尔数组。
        """

        return self.grid >= 0

    def get(
        self,
        x: int,
        y: int,
    ) -> int:
        """
        获取指定格子的 Palette 索引。

        Parameters
        ----------
        x
            横坐标，从 0 开始。

        y
            纵坐标，从 0 开始。
        """

        self._validate_position(x, y)

        return int(self.grid[y, x])

    def set(
        self,
        x: int,
        y: int,
        palette_index: int,
    ) -> None:
        """
        修改指定格子的颜色。

        palette_index:
            -1 表示透明
            >=0 表示 Palette 中的颜色索引
        """

        self._validate_position(x, y)
        self._validate_palette_index(palette_index)

        self.grid[y, x] = palette_index

    def erase(
        self,
        x: int,
        y: int,
    ) -> None:
        """
        将指定格子设为透明。
        """

        self.set(x, y, -1)

    def statistics(self) -> pd.DataFrame:
        """
        返回颜色使用统计。

        返回列：

        palette_index
            Palette 中的颜色索引

        code
            MARD 色号

        hex
            HEX 参考颜色

        count
            使用数量
        """

        values = self.grid[self.grid >= 0]

        columns = [
            "palette_index",
            "code",
            "hex",
            "count",
        ]

        if values.size == 0:
            return pd.DataFrame(columns=columns)

        counter = Counter(
            int(value)
            for value in values.tolist()
        )

        rows = []

        for palette_index, count in counter.most_common():
            color = self.palette[palette_index]

            rows.append(
                {
                    "palette_index": palette_index,
                    "code": color.code,
                    "hex": color.hex_color,
                    "count": count,
                }
            )

        return pd.DataFrame(
            rows,
            columns=columns,
        )

    def legend(self) -> dict[int, int]:
        """
        生成图纸内部编号。

        返回格式：

        {
            palette_index: 图纸编号
        }

        例如：

        {
            12: 1,
            35: 2,
            8: 3,
        }

        编号顺序按照颜色使用数量从多到少排列。
        """

        stats = self.statistics()

        mapping: dict[int, int] = {}

        for number, palette_index in enumerate(
            stats["palette_index"].tolist(),
            start=1,
        ):
            mapping[int(palette_index)] = number

        return mapping

    def legend_table(self) -> pd.DataFrame:
        """
        返回适合图纸显示和导出的图例表。

        返回列：

        number
            图纸内部编号

        palette_index
            Palette 中的颜色索引

        code
            MARD 色号

        hex
            HEX 参考颜色

        count
            使用数量
        """

        stats = self.statistics().copy()

        if stats.empty:
            return pd.DataFrame(
                columns=[
                    "number",
                    "palette_index",
                    "code",
                    "hex",
                    "count",
                ]
            )

        stats.insert(
            0,
            "number",
            range(1, len(stats) + 1),
        )

        return stats

    def number_grid(self) -> np.ndarray:
        """
        返回图纸内部编号组成的二维数组。

        -1:
            透明区域

        1、2、3……
            对应 legend() 中的图纸编号
        """

        result = np.full(
            self.grid.shape,
            fill_value=-1,
            dtype=np.int32,
        )

        legend_mapping = self.legend()

        for palette_index, number in legend_mapping.items():
            result[self.grid == palette_index] = number

        return result

    def code_grid(self) -> list[list[str]]:
        """
        返回 MARD 色号组成的二维列表。

        透明格子返回空字符串。
        """

        result: list[list[str]] = []

        for row in self.grid:
            output_row: list[str] = []

            for value in row:
                palette_index = int(value)

                if palette_index < 0:
                    output_row.append("")
                else:
                    output_row.append(
                        self.palette[palette_index].code
                    )

            result.append(output_row)

        return result

    def rgb_image(self) -> np.ndarray:
        """
        返回 RGBA 格式的 numpy 图片数组。

        透明格子的 Alpha 为 0。
        """

        image = np.zeros(
            (
                self.height,
                self.width,
                4,
            ),
            dtype=np.uint8,
        )

        visible = self.grid >= 0

        if not np.any(visible):
            return image

        palette_rgb = self.palette.rgb_array

        image[visible, :3] = palette_rgb[
            self.grid[visible]
        ]

        image[visible, 3] = 255

        return image

    def copy(self) -> Pattern:
        """
        返回 Pattern 的独立副本。
        """

        return Pattern(
            grid=self.grid.copy(),
            palette=self.palette,
        )

    def _validate_position(
        self,
        x: int,
        y: int,
    ) -> None:
        """
        检查坐标是否有效。
        """

        if not 0 <= x < self.width:
            raise IndexError(
                f"x 坐标超出范围：{x}，"
                f"有效范围为 0 到 {self.width - 1}。"
            )

        if not 0 <= y < self.height:
            raise IndexError(
                f"y 坐标超出范围：{y}，"
                f"有效范围为 0 到 {self.height - 1}。"
            )

    def _validate_palette_index(
        self,
        palette_index: int,
    ) -> None:
        """
        检查颜色索引是否有效。
        """

        if palette_index == -1:
            return

        if not 0 <= palette_index < len(self.palette):
            raise ValueError(
                f"无效的 palette_index：{palette_index}。"
            )