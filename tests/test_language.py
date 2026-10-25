import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import ast
import re
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from string import Formatter
from unittest.mock import patch

import numpy as np
from PIL import Image
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from core.i18n import ENGLISH, translate, translate_error
from core.pattern import Pattern
from core.renderer import RenderConfig, render_sheet
from ui.main_window import MainWindow


class LanguageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.settings = QSettings(str(Path(self.directory.name)/'settings.ini'), QSettings.Format.IniFormat)

    def window(self, language=None):
        window = MainWindow(language=language, settings=self.settings)
        self.addCleanup(window.close)
        return window

    def test_catalog_covers_ui_and_preserves_placeholders(self):
        root = Path(__file__).resolve().parents[1]
        for name in ['ui/main_window.py', 'app.py', 'core/renderer/sheet.py']:
            for node in ast.walk(ast.parse((root/name).read_text())):
                if not isinstance(node, ast.Call):
                    continue
                function = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, 'id', '')
                position = {'_tr': 0, '_text_widget': 1, '_add_item': 1, '_add_menu': 1, 'translate': 1}.get(function)
                if position is None or len(node.args) <= position:
                    continue
                value = node.args[position]
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    self.assertIn(value.value, ENGLISH, (name, value.value))
        for chinese, english in ENGLISH.items():
            fields = lambda text: {key for _, key, _, _ in Formatter().parse(text) if key is not None}
            self.assertEqual(fields(chinese), fields(english), chinese)
            self.assertFalse(re.search('[\u4e00-\u9fff]', english), english)
        self.assertEqual(translate('en', '已选择：{value0}', value0='测试{image}.png'), 'Selected: 测试{image}.png')

    def test_switch_before_generation_and_persist_language(self):
        window = self.window('zh')
        window.target_size_spin.setValue(63)
        window.size_mode_combo.setCurrentIndex(2)
        window.language_combo.setCurrentIndex(window.language_combo.findData('en'))
        self.assertEqual(window.save_button.text(), 'Save PNG')
        self.assertEqual(window.menuBar().actions()[0].text(), 'File')
        self.assertEqual(window.size_mode_combo.currentData(), 'width')
        self.assertEqual(window.target_size_spin.value(), 63)
        self.assertEqual(window.target_size_spin.suffix(), ' beads wide')
        self.assertIn('Choose an image', window.preview_label.text())
        self.assertEqual(self.settings.value('language'), 'en')
        self.assertEqual(self.window().language, 'en')
        window.language_combo.setCurrentIndex(0)
        self.assertEqual(window.save_button.text(), '保存 PNG')
        self.assertEqual(window.target_size_spin.suffix(), ' 颗宽')
        self.settings.setValue('language', 'unsupported')
        self.assertEqual(self.window().language, 'zh')

    def test_switch_preserves_edits_and_export_matches_sheet(self):
        window = self.window('zh')
        window.pattern = Pattern(np.array([[0, 1, -1, 2], [1, 2, 0, -1]]), window.palette)
        window.pattern.title = '测试{image}'
        window.render_config = RenderConfig(language='zh', mirror_horizontal=True, legend_sort='series')
        window._display_sheet(window.pattern, window.render_config)
        window.source_path = Path('测试{image}.png')
        window.file_label.setText(window.source_path.name)
        window.selected_cells = {(0, 0), (2, 0)}
        window.color_combo.setCurrentIndex(5)
        window.replace_selected_cells()
        original = window.pattern.grid.copy()
        history = list(window.edit_history)
        chinese_image = window.sheet_image.copy()
        window.source_color_combo.setCurrentIndex(window.source_color_combo.findData(5))
        with patch.object(window.matcher, 'match', side_effect=AssertionError('Must not rematch')):
            window.language_combo.setCurrentIndex(1)
        self.assertEqual(window.language, 'en')
        self.assertEqual(window.render_config.language, 'en')
        self.assertTrue(window.render_config.mirror_horizontal)
        self.assertEqual(window.render_config.legend_sort, 'series')
        self.assertEqual(window.selected_cells, {(0, 0), (2, 0)})
        self.assertEqual(window.edit_history, history)
        self.assertEqual(window.file_label.text(), '测试{image}.png')
        self.assertEqual(window.source_color_combo.currentData(), 5)
        self.assertIn('2 beads', window.source_color_combo.currentText())
        self.assertEqual(window.color_combo.currentData(), 5)
        np.testing.assert_array_equal(window.pattern.grid, original)
        english_image = render_sheet(window.pattern, replace(window.render_config, language='en'))
        self.assertEqual(window.sheet_image.tobytes(), english_image.tobytes())
        self.assertNotEqual(chinese_image.tobytes(), english_image.tobytes())
        output = Path(self.directory.name)/'english.png'
        with patch('ui.main_window.QFileDialog.getSaveFileName', return_value=(str(output), '')) as dialog, patch('ui.main_window.QMessageBox.information') as message:
            window.save_sheet()
        self.assertEqual(dialog.call_args.args[1], 'Save pattern')
        self.assertEqual(message.call_args.args[1], 'Saved successfully')
        with Image.open(output) as exported:
            self.assertEqual(exported.tobytes(), english_image.tobytes())
        window.language_combo.setCurrentIndex(0)
        self.assertEqual(window.sheet_image.tobytes(), chinese_image.tobytes())
        window.undo_color_edit()
        self.assertEqual(window.pattern.get(0, 0), 0)
        self.assertEqual(window.pattern.get(2, 0), -1)

    def test_generation_dialogs_and_core_errors_in_english(self):
        window = self.window('en')
        with patch('ui.main_window.QMessageBox.information') as message:
            window.generate_sheet()
        self.assertEqual(message.call_args.args[2], 'Choose an image first.')
        with patch('ui.main_window.QFileDialog.getOpenFileName', return_value=('', '')) as dialog:
            window.open_image()
        self.assertEqual(dialog.call_args.args[1], 'Choose image')
        self.assertIn('All files', dialog.call_args.args[3])
        source = Path(self.directory.name)/'source.png'
        Image.new('RGBA', (4, 2), (255, 0, 0, 255)).save(source)
        window.source_path = source
        window.generate_sheet()
        self.assertEqual(window.render_config.language, 'en')
        self.assertIn('Generated', window.statusBar().currentMessage())
        with patch.object(window.processor, 'process', side_effect=ValueError('图片中没有可见主体。')), patch('ui.main_window.QMessageBox.critical') as message:
            window.generate_sheet()
        self.assertEqual(message.call_args.args[2], 'The image has no visible subject.')
        self.assertEqual(translate_error('en', 'x 坐标超出范围：9，有效范围为 0 到 3。'),
                         'x coordinate out of range: 9; valid range is 0 to 3.')
        self.assertEqual(translate_error('en', 'OS error: 文件.png'), 'OS error: 文件.png')

    def test_failed_switch_keeps_previous_language_and_image(self):
        window = self.window('zh')
        window.pattern = Pattern(np.array([[0, 1]]), window.palette)
        window.render_config = RenderConfig(language='zh')
        window._display_sheet(window.pattern, window.render_config)
        before = window.sheet_image.tobytes()
        with patch('ui.main_window.render_sheet', side_effect=RuntimeError('failure')), patch('ui.main_window.QMessageBox.critical'):
            window.language_combo.setCurrentIndex(1)
        self.assertEqual(window.language, 'zh')
        self.assertEqual(window.render_config.language, 'zh')
        self.assertEqual(window.language_combo.currentData(), 'zh')
        self.assertEqual(window.sheet_image.tobytes(), before)
        self.assertIsNone(self.settings.value('language'))


if __name__ == '__main__':
    unittest.main()
