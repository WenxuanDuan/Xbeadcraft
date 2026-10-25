import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageDraw
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from core.color_matcher import ColorMatcher
from core.palette import Palette
from core.palette_library import PaletteLibrary
from core.pattern import Pattern
from core.renderer import RenderConfig, render_sheet
from core.renderer.bottom_legend import _build_chips, _load_font
from ui.main_window import MainWindow, PROJECT_ROOT


class PaletteDataTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.library = PaletteLibrary(PROJECT_ROOT/'data', self.root/'imported')

    def write(self, text, filename='test.csv'):
        path = self.root/filename
        path.write_text(text, encoding='utf-8')
        return path

    def test_all_bundled_palettes_validate_and_match_their_own_colors(self):
        self.assertEqual(len(self.library.specs), 20)
        for spec in self.library.specs.values():
            with self.subTest(palette=spec.id):
                palette = spec.load()
                self.assertEqual(len(palette), spec.count)
                self.assertEqual(len(set(c.code.casefold() for c in palette.colors)), len(palette))
                self.assertTrue(np.isfinite(palette.lab_array).all())
                source = Image.fromarray(palette.rgb_array.reshape(1, -1, 3))
                pattern = ColorMatcher(palette).match(source)
                # Equal-RGB entries may tie, but the resulting colors must still be exact.
                np.testing.assert_array_equal(pattern.rgb_image()[0, :, :3], palette.rgb_array)
                self.assertFalse(any(color.code.startswith('UNKNOWN-') for color in palette.colors))
                if spec.reference == 'community':
                    self.assertTrue(spec.source.startswith('https://raw.githubusercontent.com/'))
        manifest = json.loads((PROJECT_ROOT/'data'/'palettes.json').read_text())
        for entry in manifest:
            if entry.get('license'):
                self.assertTrue((PROJECT_ROOT/'data'/entry['license']).is_file())
        self.assertEqual(self.library.specs['panpan-289'].count, 285)
        self.assertEqual(self.library.specs['mixiaowo-290'].count, 286)
        self.assertEqual(self.library.specs['mard_221'].count, 221)

    def test_import_preserves_numeric_codes_and_survives_source_removal(self):
        source = self.write('code,hex\n001,#FF0000\n2,#00FF00\n10,#0000FF\n')
        spec = self.library.import_csv(source)
        palette = spec.load()
        self.assertEqual([c.code for c in palette.colors], ['001', '2', '10'])
        source.unlink()
        reloaded = PaletteLibrary(PROJECT_ROOT/'data', self.root/'imported')
        self.assertEqual(len(reloaded.specs[spec.id].load()), 3)
        pattern = Pattern(np.array([[2, 1, 0]]), palette)
        chips = _build_chips(pattern, ImageDraw.Draw(Image.new('RGB',(1,1))), _load_font(15), 42, 'series')
        self.assertEqual([chip.code for chip in chips], ['001', '2', '10'])
        second = self.write('code,hex\n001,#FF0000\n2,#00FF00\n10,#0000FF\n', 'copy.csv')
        self.assertEqual(self.library.import_csv(second).id, spec.id)

    def test_invalid_imports_are_rejected_before_installation(self):
        invalid = [
            'code,hex\nA1,#FFF\n',
            'code,hex\nA1,#FFFFFF\nA1,#000000\n',
            'code,hex\n,#FFFFFF\n',
            'code,r,g,b\nA,256,0,0\n',
            'code,r,g,b\nA,1.5,0,0\n',
            'code,r,g,b\nA,nan,0,0\n',
            'code,r,g\nA,1,0\n',
            'name,hex\nA,#FF0000\n',
            'code,hex,r,g,b\nA,#FF0000,0,0,0\n',
            'code,hex\n',
        ]
        for text in invalid:
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.library.import_csv(self.write(text))
        self.assertEqual(len(self.library.specs), 20)
        self.assertFalse((self.root/'imported').exists())

    def test_rgb_only_import_and_natural_mixed_codes(self):
        palette = Palette(str(self.write('code,r,g,b\nA10,255,0,0\nA2,0,255,0\n80-19001,0,0,255\n')))
        self.assertEqual(palette[0].hex_color, '#FF0000')
        self.assertLess(palette.color_sort_key(1), palette.color_sort_key(0))
        (self.root/'imported').mkdir()
        (self.root/'imported'/'bad.json').write_text('{not json')
        self.library.reload()
        self.assertEqual(len(self.library.specs), 20)


class PaletteInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.settings = QSettings(str(self.root/'settings.ini'), QSettings.Format.IniFormat)
        self.window = MainWindow(language='zh', settings=self.settings, palette_directory=self.root/'palettes')
        self.addCleanup(self.window.close)

    def select(self, key):
        combo = self.window.palette_combo
        combo.setCurrentIndex(combo.findData(key))

    def prepare_pattern(self):
        window = self.window
        window.pattern = Pattern(np.array([[0, 1, -1, 2], [1, -1, 0, 2]]), window.palette)
        window.pattern.title = 'Palette test'
        window.render_config = RenderConfig(language='zh', mirror_horizontal=True, legend_sort='series')
        window._display_sheet(window.pattern, window.render_config)
        window.selected_cells = {(0, 0), (1, 0)}
        window.color_combo.setCurrentIndex(5)
        window.replace_selected_cells()

    def test_generation_and_editing_use_selected_palette(self):
        window = self.window
        self.select('hama')
        self.assertEqual(window.palette.id, 'hama')
        self.assertEqual(window.matcher.palette.id, 'hama')
        self.assertEqual(window.color_combo.count(), 92)
        self.assertIn('Hama', window.target_color_label.text())
        window.source_path = self.root/'source.png'
        Image.new('RGB', (8, 4), 'red').save(window.source_path)
        window.size_mode_combo.setCurrentIndex(window.size_mode_combo.findData('width'))
        window.target_size_spin.setValue(8)
        window.generate_sheet()
        self.assertEqual(window.pattern.palette.id, 'hama')
        window.selected_cells = {(0, 0)}
        window.color_combo.setCurrentIndex(2)
        window.replace_selected_cells()
        self.assertEqual(window.pattern.palette[window.pattern.get(0, 0)].code, window.palette[2].code)
        window.language_combo.setCurrentIndex(1)
        self.assertEqual(window.palette.id, 'hama')
        self.assertIn('Hama', window.target_color_label.text())
        self.assertIn('Community', window.palette_note.text())

    def test_switch_and_undo_preserve_transparency_size_and_previous_edits(self):
        window = self.window
        self.prepare_pattern()
        original = window.pattern.grid.copy()
        old_image = window.sheet_image.tobytes()
        self.select('perler')
        self.assertEqual(window.pattern.palette.id, 'perler')
        self.assertEqual(window.pattern.grid.shape, original.shape)
        np.testing.assert_array_equal(window.pattern.grid == -1, original == -1)
        self.assertEqual(window.selected_cells, {(0, 0), (1, 0)})
        self.assertTrue(window.render_config.mirror_horizontal)
        self.assertEqual(window.render_config.legend_sort, 'series')
        self.assertEqual(len(window.edit_history), 2)
        window.selected_cells = {(2, 0)}
        window.color_combo.setCurrentIndex(3)
        window.replace_selected_cells()
        window.undo_color_edit()
        self.assertEqual(window.pattern.get(2, 0), -1)
        window.undo_color_edit()
        self.assertEqual(window.palette.id, 'mard_221')
        self.assertEqual(window.palette_combo.currentData(), 'mard_221')
        np.testing.assert_array_equal(window.pattern.grid, original)
        self.assertEqual(window.sheet_image.tobytes(), old_image)
        window.undo_color_edit()
        self.assertEqual(window.pattern.get(0, 0), 0)
        self.assertEqual(window.pattern.get(1, 0), 1)

    def test_switch_failure_preserves_all_current_state(self):
        window = self.window
        self.prepare_pattern()
        previous = window.pattern
        image = window.sheet_image.tobytes()
        with patch('ui.main_window.render_sheet', side_effect=RuntimeError('failure')), patch('ui.main_window.QMessageBox.critical'):
            self.select('hama')
        self.assertIs(window.pattern, previous)
        self.assertEqual(window.palette.id, 'mard_221')
        self.assertEqual(window.palette_combo.currentData(), 'mard_221')
        self.assertEqual(window.sheet_image.tobytes(), image)
        self.assertEqual(len(window.edit_history), 1)

    def test_import_persistence_and_export(self):
        window = self.window
        source = self.root/'My palette.csv'
        source.write_text('code,hex\n001,#FF0000\n002,#000000\n')
        with patch('ui.main_window.QFileDialog.getOpenFileName', return_value=(str(source), '')):
            window.import_palette()
        self.assertTrue(window.palette.id.startswith('custom-'))
        self.assertEqual(window.color_combo.count(), 2)
        restored = MainWindow(language='en', settings=self.settings, palette_directory=self.root/'palettes')
        self.addCleanup(restored.close)
        self.assertEqual(restored.palette.id, window.palette.id)
        self.assertIn('My palette', restored.target_color_label.text())
        window.pattern = Pattern(np.array([[0, 1, -1]]), window.palette)
        window.render_config = RenderConfig()
        window._display_sheet(window.pattern, window.render_config)
        output = self.root/'output.png'
        with patch('ui.main_window.QFileDialog.getSaveFileName', return_value=(str(output), '')), patch('ui.main_window.QMessageBox.information'):
            window.save_sheet()
        with Image.open(output) as image:
            self.assertEqual(image.tobytes(), render_sheet(window.pattern, window.render_config).tobytes())


if __name__ == '__main__':
    unittest.main()
