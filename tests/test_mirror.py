import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image
from PySide6.QtWidgets import QApplication

from core.pattern import Pattern
from core.renderer import RenderConfig, render_sheet
from core.renderer.grid import render_grid
from ui.main_window import MainWindow, PALETTE_PATH
from core.palette import Palette


class MirrorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.palette = Palette(str(PALETTE_PATH))

    def setUp(self):
        self.pattern = Pattern(np.array([[0, 1, -1, 2], [2, -1, 1, 0]]), self.palette)
        self.pattern.title = 'Asymmetric test'
        self.config = RenderConfig(cell_size=30)

    def test_only_bead_positions_change(self):
        normal = render_grid(self.pattern, self.config)
        mirrored = render_grid(self.pattern, replace(self.config, mirror_horizontal=True))
        margin, cell = 27, 30
        # Compare cell interiors to prove glyphs move without being flipped.
        for y in range(2):
            for x in range(4):
                if self.pattern.grid[y, x] < 0:
                    continue
                def box(col):
                    return (margin + col*cell + 2, margin + y*cell + 2,
                            margin + (col+1)*cell - 1, margin + (y+1)*cell - 1)
                self.assertEqual(normal.crop(box(x)).tobytes(),
                                 mirrored.crop(box(3-x)).tobytes())
        for box in [(0, 0, normal.width, margin),
                    (0, normal.height-margin, normal.width, normal.height),
                    (0, 0, margin, normal.height),
                    (normal.width-margin, 0, normal.width, normal.height)]:
            self.assertEqual(normal.crop(box).tobytes(), mirrored.crop(box).tobytes())
        # Transparency follows the pattern and uses the destination checkerboard.
        self.assertEqual(mirrored.getpixel((margin+cell+4, margin+4)), (232, 232, 232))
        normal_sheet = render_sheet(self.pattern, self.config)
        mirror_sheet = render_sheet(self.pattern, replace(self.config, mirror_horizontal=True))
        grid_bottom = self.config.sheet_padding + 76 + self.config.sheet_spacing + normal.height
        for box in [(0, 0, normal_sheet.width, self.config.sheet_padding+76),
                    (0, grid_bottom, normal_sheet.width, normal_sheet.height)]:
            self.assertEqual(normal_sheet.crop(box).tobytes(), mirror_sheet.crop(box).tobytes())
        np.testing.assert_array_equal(self.pattern.grid, [[0, 1, -1, 2], [2, -1, 1, 0]])

    def test_ui_toggle_export_regenerate_and_failure(self):
        window = MainWindow()
        self.addCleanup(window.close)
        self.assertFalse(window.mirror_check.isEnabled())
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)/'source.png'
            Image.fromarray(self.pattern.rgb_image()).save(source)
            window.source_path = source
            window.size_mode_combo.setCurrentIndex(2)
            window.target_size_spin.setValue(4)
            window.trim_check.setChecked(False)
            window.generate_sheet()
            self.assertTrue(window.mirror_check.isEnabled())
            original = window.sheet_image.tobytes()
            grid = window.pattern.grid.copy()
            with patch.object(window.matcher, 'match', side_effect=AssertionError('Must not rematch')):
                window.mirror_check.setChecked(True)
                expected = render_sheet(window.pattern, replace(window.render_config, mirror_horizontal=True))
                self.assertEqual(window.sheet_image.tobytes(), expected.tobytes())
                self.assertNotEqual(original, expected.tobytes())
                preview = window.sheet_pixmap.toImage()
                for x, y in [(0, 0), (50, 150), (100, 150)]:
                    self.assertEqual(preview.pixelColor(x, y).getRgb()[:3], expected.getpixel((x, y)))
                output = Path(directory)/'mirror.png'
                with patch('ui.main_window.QFileDialog.getSaveFileName', return_value=(str(output), '')), patch('ui.main_window.QMessageBox.information'):
                    window.save_sheet()
                with Image.open(output) as exported:
                    self.assertEqual(exported.tobytes(), expected.tobytes())
                window.mirror_check.setChecked(False)
                self.assertEqual(window.sheet_image.tobytes(), original)
                window.mirror_check.setChecked(True)
                with patch('ui.main_window.render_sheet', side_effect=RuntimeError('render failed')), patch('ui.main_window.QMessageBox.critical'):
                    window.mirror_check.setChecked(False)
                self.assertTrue(window.mirror_check.isChecked())
                self.assertEqual(window.sheet_image.tobytes(), expected.tobytes())
            np.testing.assert_array_equal(window.pattern.grid, grid)
            window.generate_sheet()
            self.assertFalse(window.mirror_check.isChecked())
            self.assertEqual(window.sheet_image.tobytes(), original)


if __name__ == '__main__':
    unittest.main()
