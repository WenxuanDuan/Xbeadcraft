from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RenderConfig:
    """Shared rendering options for bead grids, legends, and complete sheets."""

    # Pixel size of each bead cell
    cell_size: int = 28

    # Show actual bead colors
    show_color: bool = True

    # Show coordinates on all four sides
    show_coordinate: bool = True

    # Number of cells between major grid lines
    major_grid_every: int = 5

    # Use a checkerboard for empty cells
    checkerboard: bool = True

    # Bottom legend options
    legend_swatch_width: int = 118
    legend_swatch_height: int = 42
    legend_spacing: int = 10
    legend_padding: int = 16

    # Sheet layout options
    sheet_padding: int = 16
    sheet_spacing: int = 16

    # Mirror bead positions while keeping text, coordinates, and legends upright
    mirror_horizontal: bool = False

    # count: descending usage; series: ascending series and numeric color code
    legend_sort: str = "count"

    # Language used for sheet metadata; palette codes remain unchanged.
    language: str = "en"
