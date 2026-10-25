import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageDraw
from PySide6.QtWidgets import QApplication

from core.palette import Palette
from core.pattern import Pattern
from core.renderer import RenderConfig, render_sheet
from core.renderer.bottom_legend import _build_chips, _load_font
from ui.main_window import MainWindow, PALETTE_PATH


class LegendSortTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.palette = Palette(str(PALETTE_PATH))

    def setUp(self):
        self.indices = {color.code: index for index, color in enumerate(self.palette.colors)}
        codes = ['M1']*4 + ['A10']*3 + ['B1']*2 + ['A2']*2 + ['A1']
        self.pattern = Pattern(np.array([[self.indices[code] for code in codes]]), self.palette)
        self.pattern.title = 'Sort test'

    def chips(self, mode):
        return _build_chips(self.pattern, ImageDraw.Draw(Image.new('RGB', (1, 1))),
                            _load_font(15), 42, sort_mode=mode)

    def test_count_and_natural_series_order(self):
        count = self.chips('count')
        series = self.chips('series')
        self.assertEqual([c.code for c in count], ['M1', 'A10', 'A2', 'B1', 'A1'])
        self.assertEqual([c.count for c in count], [4, 3, 2, 2, 1])
        self.assertEqual([c.code for c in series], ['A1', 'A2', 'A10', 'B1', 'M1'])
        self.assertEqual({c.code: c.count for c in count}, {c.code: c.count for c in series})

    def test_empty_pattern(self):
        self.pattern = Pattern(np.full((1, 4), -1), self.palette)
        self.assertEqual(self.chips('count'), [])
        self.assertEqual(self.chips('series'), [])

    def test_ui_sort_export_edit_mirror_and_failure(self):
        window = MainWindow()
        self.addCleanup(window.close)
        window.pattern = self.pattern
        window.render_config = RenderConfig()
        window._display_sheet(self.pattern, window.render_config)
        normal = window.sheet_image.copy()
        grid = self.pattern.grid.copy()
        window.legend_sort_combo.setCurrentIndex(1)
        self.assertEqual(window.render_config.legend_sort, 'series')
        self.assertNotEqual(normal.tobytes(), window.sheet_image.tobytes())
        # Header, bead grid, and coordinates are unchanged.
        bottom = 16 + 76 + 16 + 24*2 + 28 + 1
        self.assertEqual(normal.crop((0, 0, normal.width, bottom)).tobytes(),
                         window.sheet_image.crop((0, 0, normal.width, bottom)).tobytes())
        np.testing.assert_array_equal(self.pattern.grid, grid)
        window._toggle_mirror(True)
        window.selected_cells = {(0, 0)}
        window.color_combo.setCurrentIndex(self.indices['A1'])
        window.replace_selected_cells()
        self.assertEqual(window.render_config.legend_sort, 'series')
        expected = render_sheet(window.pattern, window.render_config)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'sorted.png'
            with patch('ui.main_window.QFileDialog.getSaveFileName', return_value=(str(output), '')), patch('ui.main_window.QMessageBox.information'):
                window.save_sheet()
            with Image.open(output) as exported:
                self.assertEqual(exported.tobytes(), expected.tobytes())
        with patch('ui.main_window.render_sheet', side_effect=RuntimeError('failure')), patch('ui.main_window.QMessageBox.critical'):
            window.legend_sort_combo.setCurrentIndex(0)
        self.assertEqual(window.legend_sort_combo.currentData(), 'series')
        self.assertEqual(window.render_config.legend_sort, 'series')
        self.assertEqual(window.sheet_image.tobytes(), expected.tobytes())
        window.legend_sort_combo.setCurrentIndex(0)
        self.assertEqual(window.render_config.legend_sort, 'count')


if __name__ == '__main__':
    unittest.main()
