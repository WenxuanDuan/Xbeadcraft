from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup


URL = "https://www.pixel-beads.com/zh/mard-bead-color-chart"
STANDARD_SERIES = set("ABCDEFGHM")


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def download_mard_palette() -> pd.DataFrame:
    response = requests.get(
        URL,
        timeout=30,
        headers={
            "User-Agent": (
                "Mozilla/5.0 MARD bead palette research tool"
            )
        },
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(" ", strip=True)

    # Match color codes followed by HEX values, such as A1#FAF4C8.
    matches = re.findall(
        r"\b((?:ZG|[A-Z])\d+)\s*(#[0-9A-Fa-f]{6})\b",
        text,
    )

    rows = []
    seen = set()

    for code, hex_color in matches:
        series_match = re.match(r"^[A-Z]+", code)

        if not series_match:
            continue

        series = series_match.group()

        # Keep only the standard 221 colors in series A-H and M.
        if series not in STANDARD_SERIES:
            continue

        if code in seen:
            continue

        seen.add(code)

        hex_color = hex_color.upper()
        red, green, blue = hex_to_rgb(hex_color)

        rows.append(
            {
                "code": code,
                "hex": hex_color,
                "r": red,
                "g": green,
                "b": blue,
                "series": series,
            }
        )

    palette = pd.DataFrame(rows)

    # Sort by series and numeric suffix, so A2 precedes A10.
    palette["number"] = (
        palette["code"]
        .str.extract(r"(\d+)")
        .astype(int)
    )

    series_order = {
        series: index
        for index, series in enumerate(
            ["A", "B", "C", "D", "E", "F", "G", "H", "M"]
        )
    }

    palette["series_order"] = palette["series"].map(series_order)

    palette = (
        palette
        .sort_values(["series_order", "number"])
        .drop(columns=["number", "series_order"])
        .reset_index(drop=True)
    )

    if len(palette) != 221:
        raise RuntimeError(
            f"预期提取221色，实际得到{len(palette)}色。"
            "网页结构可能发生变化，请检查解析结果。"
        )

    return palette


if __name__ == "__main__":
    output_path = Path("data/mard_221.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    palette = download_mard_palette()
    palette.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"已保存：{output_path}")
    print(f"颜色数量：{len(palette)}")
    print(palette.groupby("series").size())