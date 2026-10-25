import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from core.image_processor import ImageProcessor
from core.renderer import render_sheet
from ui.main_window import MainWindow


class PhotoProcessingTests(unittest.TestCase):
    def setUp(self):
        self.processor = ImageProcessor()

    def test_presets_keep_landscape_and_portrait_ratio(self):
        for size in [(400, 300), (300, 400)]:
            source = Image.new('RGBA', size, 'red')
            for longest in [40, 80, 120, 160]:
                with self.subTest(size=size, longest=longest):
                    result = self.processor.process(source, size_mode='photo', width=longest,
                                                    height=longest, photo_fit='longest')
                    expected = (longest, longest*3//4) if size[0] > size[1] else (longest*3//4, longest)
                    self.assertEqual(result.size, expected)

    def test_custom_ratio_crop_and_empty_padding(self):
        source = Image.new('RGBA', (80, 40), 'red')
        result = self.processor.process(source, size_mode='photo', width=30, height=30, photo_fit='width')
        self.assertEqual(result.size, (30, 15))
        result = self.processor.process(source, size_mode='photo', width=30, height=30, photo_fit='height')
        self.assertEqual(result.size, (60, 30))
        for fit in ['crop', 'contain']:
            result = self.processor.process(source, size_mode='photo', width=20, height=20, photo_fit=fit)
            self.assertEqual(result.size, (20, 20))
            visible = np.asarray(result.getchannel('A')) > 0
            self.assertEqual(int(visible.sum()), 400 if fit == 'crop' else 200)
            self.assertEqual(result.getpixel((10, 10)), (255, 0, 0, 255))
            if fit == 'contain':
                self.assertEqual(result.getpixel((10, 0))[3], 0)

    def test_crop_uses_center_and_preprocessing_matches_estimate(self):
        source = Image.new('RGBA', (120, 40), 'red')
        source.paste('green', (40, 0, 80, 40))
        source.paste('blue', (80, 0, 120, 40))
        result = self.processor.process(source, size_mode='photo', width=8, height=8,
                                        photo_fit='crop', method='nearest')
        self.assertEqual({tuple(pixel) for pixel in np.asarray(result).reshape(-1, 4)}, {(0, 128, 0, 255)})
        canvas = Image.new('RGBA', (120, 120))
        canvas.paste(Image.new('RGBA', (80, 40), 'red'), (20, 40))
        prepared = self.processor.prepare_source(canvas, True, 128)
        self.assertEqual(prepared.size, (80, 40))
        predicted = self.processor.photo_dimensions(prepared.size, 40, 40, 'longest')
        result = self.processor.process(canvas, size_mode='photo', width=40, height=40, photo_fit='longest')
        self.assertEqual(result.size, predicted)
        exif = Image.new('RGB', (40, 80), 'red')
        exif.getexif()[274] = 6
        self.assertEqual(self.processor.prepare_source(exif, False, 128).size, (80, 40))

    def test_invalid_photo_dimensions_and_fit(self):
        for width, height, fit in [(0, 20, 'crop'), (20, -1, 'contain'), (20, 20, 'stretch')]:
            with self.subTest(width=width, height=height, fit=fit), self.assertRaises(ValueError):
                self.processor.photo_dimensions((80, 40), width, height, fit)


class PhotoInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        settings = QSettings(str(Path(self.directory.name)/'settings.ini'), QSettings.Format.IniFormat)
        self.window = MainWindow(language='zh', settings=settings)
        self.addCleanup(self.window.close)
        self.window.source_path = Path(self.directory.name)/'photo.png'
        Image.new('RGB', (80, 40), 'red').save(self.window.source_path)
        self.window.size_mode_combo.setCurrentIndex(self.window.size_mode_combo.findData('photo'))

    def test_estimate_controls_and_generation_do_not_use_collection_sizing(self):
        window = self.window
        self.assertFalse(window.collection_size_combo.isEnabled())
        self.assertFalse(window.target_size_spin.isEnabled())
        self.assertFalse(window.keep_ratio_check.isEnabled())
        self.assertIn('80 × 40', window.photo_estimate_label.text())
        with patch.object(window.matcher, 'match', side_effect=AssertionError('Estimation must not rematch')):
            window.photo_preset_combo.setCurrentIndex(0)
        self.assertIn('40 × 20', window.photo_estimate_label.text())
        with patch.object(window.processor, 'resize_for_collection', side_effect=AssertionError('Wrong mode')):
            window.generate_sheet()
        self.assertEqual((window.pattern.width, window.pattern.height), (40, 20))
        self.assertEqual(window.pattern.bead_count, 800)

    def test_custom_padding_statistics_language_and_export(self):
        window = self.window
        window.photo_preset_combo.setCurrentIndex(4)
        window.photo_fit_combo.setCurrentIndex(window.photo_fit_combo.findData('contain'))
        window.photo_width_spin.setValue(20)
        window.photo_height_spin.setValue(20)
        window.alpha_spin.setValue(0)
        self.assertIn('20 × 20', window.photo_estimate_label.text())
        window.language_combo.setCurrentIndex(1)
        self.assertEqual(window.size_mode_combo.currentData(), 'photo')
        self.assertIn('up to 400 beads', window.photo_estimate_label.text())
        window.generate_sheet()
        self.assertEqual((window.pattern.width, window.pattern.height), (20, 20))
        self.assertEqual(window.pattern.bead_count, 200)
        self.assertEqual(int((window.pattern.grid == -1).sum()), 200)
        window._toggle_mirror(True)
        expected = render_sheet(window.pattern, window.render_config)
        output = Path(self.directory.name)/'sheet.png'
        with patch('ui.main_window.QFileDialog.getSaveFileName', return_value=(str(output), '')), patch('ui.main_window.QMessageBox.information'):
            window.save_sheet()
        with Image.open(output) as exported:
            self.assertEqual(exported.tobytes(), expected.tobytes())

    def test_custom_ratio_fields_and_return_to_collection(self):
        window = self.window
        window.photo_preset_combo.setCurrentIndex(4)
        window.photo_width_spin.setValue(30)
        self.assertTrue(window.photo_width_spin.isEnabled())
        self.assertFalse(window.photo_height_spin.isEnabled())
        self.assertEqual(window.photo_height_spin.value(), 15)
        window.photo_fit_combo.setCurrentIndex(window.photo_fit_combo.findData('height'))
        self.assertFalse(window.photo_width_spin.isEnabled())
        self.assertTrue(window.photo_height_spin.isEnabled())
        window.photo_height_spin.setValue(20)
        self.assertEqual(window.photo_width_spin.value(), 40)
        window.size_mode_combo.setCurrentIndex(0)
        self.assertTrue(window.collection_size_combo.isEnabled())
        self.assertTrue(window.keep_ratio_check.isEnabled())
        self.assertTrue(window.photo_controls.isHidden())


if __name__ == '__main__':
    unittest.main()
