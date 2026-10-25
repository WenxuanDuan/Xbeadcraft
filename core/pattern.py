from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .palette import Palette


@dataclass
class Pattern:
    """Bead pattern backed by a two-dimensional palette-index array.

    A value of -1 represents an empty cell; nonnegative values index the palette."""

    grid: np.ndarray
    palette: Palette

    def __post_init__(self) -> None:
        """Normalize the grid to int32 and validate its dimensions and palette indices."""

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
        """Return the pattern width in bead cells."""

        return int(self.grid.shape[1])

    @property
    def height(self) -> int:
        """Return the pattern height in bead cells."""

        return int(self.grid.shape[0])

    @property
    def bead_count(self) -> int:
        """Return the total number of occupied cells."""

        return int(np.sum(self.grid >= 0))

    @property
    def color_count(self) -> int:
        """Return the number of distinct colors in use."""

        values = self.grid[self.grid >= 0]

        if values.size == 0:
            return 0

        return int(len(np.unique(values)))

    @property
    def visible_mask(self) -> np.ndarray:
        """Return a Boolean mask of occupied bead cells."""

        return self.grid >= 0

    def get(
        self,
        x: int,
        y: int,
    ) -> int:
        """Return the palette index at zero-based coordinates (x, y)."""

        self._validate_position(x, y)

        return int(self.grid[y, x])

    def set(
        self,
        x: int,
        y: int,
        palette_index: int,
    ) -> None:
        """Set a cell to a valid palette index, or -1 to make it empty."""

        self._validate_position(x, y)
        self._validate_palette_index(palette_index)

        self.grid[y, x] = palette_index

    def erase(
        self,
        x: int,
        y: int,
    ) -> None:
        """Clear the cell at zero-based coordinates (x, y)."""

        self.set(x, y, -1)

    def statistics(self) -> pd.DataFrame:
        """Return color usage with palette_index, code, hex, and count columns."""

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
        """Map palette indices to one-based legend numbers in descending usage order."""

        stats = self.statistics()

        mapping: dict[int, int] = {}

        for number, palette_index in enumerate(
            stats["palette_index"].tolist(),
            start=1,
        ):
            mapping[int(palette_index)] = number

        return mapping

    def legend_table(self) -> pd.DataFrame:
        """Return usage statistics with a one-based number column for display and export."""

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
        """Return a grid of legend numbers, using -1 for empty cells."""

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
        """Return palette color codes as rows of strings; empty cells use an empty string."""

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
        """Return an RGBA array with alpha zero for empty cells."""

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
        """Return a copy with independent grid storage and the same palette."""

        return Pattern(
            grid=self.grid.copy(),
            palette=self.palette,
        )

    def _validate_position(
        self,
        x: int,
        y: int,
    ) -> None:
        """Validate zero-based cell coordinates."""

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
        """Validate a palette index, allowing -1 for an empty cell."""

        if palette_index == -1:
            return

        if not 0 <= palette_index < len(self.palette):
            raise ValueError(
                f"无效的 palette_index：{palette_index}。"
            )