import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from core.pattern import Pattern
from core.renderer import RenderConfig, render_sheet
from ui.main_window import MainWindow


class ColorEditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = MainWindow(language="zh")
        self.addCleanup(self.window.close)
        self.window.pattern = Pattern(np.array([[0, 1, -1, 2], [1, 2, 0, -1]]), self.window.palette)
        self.window.pattern.title = 'Edit test'
        self.window.render_config = RenderConfig(cell_size=30)
        self.window._display_sheet(self.window.pattern, self.window.render_config)
        self.window.mirror_check.setEnabled(True)
        self.window.color_combo.setEnabled(True)
        self.window.show()
        self.app.processEvents()

    def click(self, x, y, modifier=Qt.KeyboardModifier.NoModifier):
        left, top, cell = self.window._grid_geometry()
        QTest.mouseClick(self.window.preview_label, Qt.MouseButton.LeftButton,
                         modifier, QPoint(left+x*cell+cell//2, top+y*cell+cell//2))

    def test_mard_palette_multi_selection_export_and_undo(self):
        window = self.window
        self.assertEqual(window.color_combo.count(), 221)
        for i, color in enumerate(window.palette.colors):
            self.assertEqual(window.color_combo.itemText(i), color.code)
            self.assertEqual(window.color_combo.itemData(i), i)
        original = window.sheet_image.tobytes()
        self.click(0, 0)
        self.click(2, 0, Qt.KeyboardModifier.ControlModifier)
        self.assertEqual(window.selected_cells, {(0, 0), (2, 0)})
        QTest.mouseClick(window.preview_label, Qt.MouseButton.LeftButton,
                         pos=QPoint(1, 1))
        self.assertEqual(len(window.selected_cells), 2)
        window.color_combo.setCurrentIndex(5)
        with patch.object(window.matcher, 'match', side_effect=AssertionError('Do not rematch')):
            window.replace_selected_cells()
        np.testing.assert_array_equal(window.pattern.grid, [[5, 1, 5, 2], [1, 2, 0, -1]])
        self.assertEqual(window.pattern.bead_count, 7)
        self.assertEqual(window.pattern.statistics().set_index('palette_index').loc[5, 'count'], 2)
        self.assertEqual(window.pattern.title, 'Edit test')
        expected = render_sheet(window.pattern, window.render_config)
        self.assertEqual(window.sheet_image.tobytes(), expected.tobytes())
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'edit.png'
            with patch('ui.main_window.QFileDialog.getSaveFileName', return_value=(str(output), '')), patch('ui.main_window.QMessageBox.information'):
                window.save_sheet()
            with Image.open(output) as image:
                self.assertEqual(image.tobytes(), expected.tobytes())
        window.undo_color_edit()
        self.assertEqual(window.sheet_image.tobytes(), original)
        self.assertFalse(window.undo_button.isEnabled())

    def test_mirrored_clicks_and_selection_toggle(self):
        window = self.window
        self.click(0, 0)
        window.mirror_check.setChecked(True)
        self.assertEqual(window.selected_cells, {(0, 0)})
        self.click(0, 1)
        self.assertEqual(window.selected_cells, {(3, 1)})
        self.click(1, 1, Qt.KeyboardModifier.MetaModifier)
        self.assertEqual(window.selected_cells, {(3, 1), (2, 1)})
        self.click(1, 1, Qt.KeyboardModifier.MetaModifier)
        self.assertEqual(window.selected_cells, {(3, 1)})
        window.color_combo.setCurrentIndex(6)
        window.replace_selected_cells()
        self.assertEqual(window.pattern.get(3, 1), 6)
        window.mirror_check.setChecked(False)
        self.assertEqual(window.pattern.get(3, 1), 6)
        window._clear_selection()
        self.assertFalse(window.replace_button.isEnabled())

    def test_render_failure_preserves_edit_and_undo_state(self):
        window = self.window
        self.click(0, 0)
        window.color_combo.setCurrentIndex(5)
        original = window.sheet_image.tobytes()
        with patch('ui.main_window.render_sheet', side_effect=RuntimeError('failure')), patch('ui.main_window.QMessageBox.critical'):
            window.replace_selected_cells()
        self.assertEqual(window.pattern.get(0, 0), 0)
        self.assertEqual(window.sheet_image.tobytes(), original)
        self.assertEqual(window.edit_history, [])
        window.replace_selected_cells()
        with patch('ui.main_window.render_sheet', side_effect=RuntimeError('failure')), patch('ui.main_window.QMessageBox.critical'):
            window.undo_color_edit()
        self.assertEqual(window.pattern.get(0, 0), 5)
        self.assertEqual(len(window.edit_history), 1)

    def test_select_all_color_replace_merge_and_undo(self):
        window = self.window
        original = window.sheet_image.tobytes()
        self.assertEqual(window.source_color_combo.count(), 3)
        window.source_color_combo.setCurrentIndex(window.source_color_combo.findData(1))
        self.click(2, 0)  # A previous manual selection must be replaced.
        window.mirror_check.setChecked(True)
        window.select_color_button.click()
        self.assertEqual(window.selected_cells, {(1, 0), (0, 1)})
        window.color_combo.setCurrentIndex(2)
        window.replace_button.click()
        np.testing.assert_array_equal(window.pattern.grid, [[0, 2, -1, 2], [2, 2, 0, -1]])
        self.assertEqual(window.source_color_combo.findData(1), -1)
        position = window.source_color_combo.findData(2)
        self.assertIn("4 颗", window.source_color_combo.itemText(position))
        self.assertEqual(window.pattern.bead_count, 6)
        self.assertEqual(len(window.edit_history), 1)
        window.undo_color_edit()
        self.assertGreaterEqual(window.source_color_combo.findData(1), 0)
        window.mirror_check.setChecked(False)
        self.assertEqual(window.sheet_image.tobytes(), original)

    def test_select_color_noop_and_empty_pattern(self):
        window = self.window
        window.source_color_combo.setCurrentIndex(window.source_color_combo.findData(0))
        window.select_all_of_color()
        window.color_combo.setCurrentIndex(0)
        window.replace_selected_cells()
        self.assertEqual(window.edit_history, [])
        self.assertEqual(window.selected_cells, {(0, 0), (2, 1)})
        window.pattern = Pattern(np.full((2, 4), -1), window.palette)
        window._clear_selection()
        window._display_sheet(window.pattern, window.render_config)
        self.assertEqual(window.source_color_combo.count(), 0)
        self.assertFalse(window.select_color_button.isEnabled())
        window.select_all_of_color()
        self.assertEqual(window.selected_cells, set())

    def test_generation_resets_selection_and_history(self):
        window = self.window
        self.click(0, 0)
        window.color_combo.setCurrentIndex(5)
        window.replace_selected_cells()
        with tempfile.TemporaryDirectory() as directory:
            window.source_path = Path(directory)/'source.png'
            Image.fromarray(window.pattern.rgb_image()).save(window.source_path)
            window.generate_sheet()
        self.assertEqual(window.selected_cells, set())
        self.assertEqual(window.edit_history, [])
        self.assertFalse(window.undo_button.isEnabled())
        self.assertFalse(window.replace_button.isEnabled())


if __name__ == '__main__':
    unittest.main()
